mod audio_loader;
use audio_loader::load_audio;

use axum::{
    routing::{get, post},
    Json, Router,
};
use once_cell::sync::{Lazy,OnceCell};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use std::{
    net::SocketAddr,
    sync::{Arc, Mutex},
};
use thiserror::Error;
use tokio::sync::oneshot;

use axum::serve;
use tokio::net::TcpListener;

use audiofp::classical::Wang;
use audiofp::Fingerprinter;

use std::process::Command;
use serde_json::Value;

// ---------------------------
// Error Handling
// ---------------------------

#[derive(Debug, Error)]
enum AppError {
    #[error("db error: {0}")]
    Db(#[from] rusqlite::Error),
    #[error("other: {0}")]
    Other(String),
}

type AppResult<T> = Result<T, AppError>;

// ---------------------------
// Fingerprint Item
// ---------------------------

#[derive(Clone, Debug)]
struct FingerprintItem {
    id: i64,
    filepath: String,
    artist: String,
    title: String,
    album: String,
    year: String,
    hashes: Vec<u32>,
}

#[derive(Deserialize)]
struct FingerprintRequest {
    filepath: String,
}

#[derive(Serialize)]
struct FingerprintResponse {
    wang_hashes: Vec<u32>,
    wang_duration: u32,
    chromaprint: String,
    chroma_duration: u32,
}

// ---------------------------
// Matcher (in-memory)
// ---------------------------

#[derive(Default)]
struct Matcher {
    items: Vec<FingerprintItem>,
}

impl Matcher {
    fn insert(&mut self, item: FingerprintItem) {
        self.items.push(item);
    }

    fn delete_by_id(&mut self, id: i64) {
        self.items.retain(|it| it.id != id);
    }

    fn match_hashes(&self, hashes: &[u32]) -> Option<&FingerprintItem> {
        let mut best: Option<(&FingerprintItem, usize)> = None;

        for item in &self.items {
            let score = item.hashes
                .iter()
                .filter(|h| hashes.contains(h))
                .count();

            if let Some((_, best_score)) = best {
                if score > best_score {
                    best = Some((item, score));
                }
            } else {
                best = Some((item, score));
            }
        }

        best.map(|(item, _)| item)
    }

}

// Global matcher
static MATCHER: Lazy<Mutex<Matcher>> = Lazy::new(|| Mutex::new(Matcher::default()));

// ---------------------------
// SQLite connection (global)
// ---------------------------

static DB_CONN: OnceCell<Mutex<Connection>> = OnceCell::new();

pub fn init_database(path: &str) {
    let conn = Connection::open(path).expect("cannot open db");
    init_db(&conn).expect("cannot init db");
    DB_CONN.set(Mutex::new(conn)).expect("DB already initialized");
}

// ---------------------------
// DB Init + Load
// ---------------------------

fn init_db(conn: &Connection) -> AppResult<()> {
    conn.execute_batch(
        r#"
        CREATE TABLE IF NOT EXISTS fingerprints (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath        TEXT,
            artist          TEXT,
            title           TEXT,
            album           TEXT,
            year            TEXT,

            -- Wang fingerprint
            hashes          BLOB,
            wang_duration   INTEGER,

            -- Chromaprint fingerprint
            chromaprint     TEXT,
            chroma_duration INTEGER,

            -- MusicBrainz ID (to be filled later)
            mbid            TEXT
        );
        "#,
    )?;
    Ok(())
}



fn load_matcher_from_db() -> AppResult<()> {
    let conn = DB_CONN.get().expect("DB not initialized").lock().unwrap();
    let mut stmt = conn.prepare(
        "SELECT id, filepath, artist, title, album, year, hashes FROM fingerprints",
    )?;

    let rows = stmt.query_map([], |row| {
        let blob: Vec<u8> = row.get(6)?;
        let hashes: Vec<u32> = bincode::deserialize(&blob).unwrap_or_default();
        Ok(FingerprintItem {
            id: row.get(0)?,
            filepath: row.get(1)?,
            artist: row.get(2)?,
            title: row.get(3)?,
            album: row.get(4)?,
            year: row.get(5)?,
            hashes,
        })
    })?;

    let mut matcher = MATCHER.lock().unwrap();
    matcher.items.clear();
    for r in rows {
        matcher.insert(r?);
    }
    Ok(())
}

// ---------------------------
// API Types
// ---------------------------

#[derive(Deserialize)]
struct AddRequest {
    filepath: String,
    artist: String,
    title: String,
    album: String,
    year: String,
}

#[derive(Deserialize)]
struct DeleteRequest {
    id: i64,
}

#[derive(Deserialize)]
struct MatchRequest {
    filepath: String,
}

#[derive(Serialize)]
struct StatusResponse {
    status: String,
}

#[derive(Serialize)]
struct MatchResponse {
    artist: String,
    title: String,
    album: String,
    year: String,
    confidence: f32,
}

// ---------------------------
// Fingerprinting Stub
// ---------------------------

// For chromaprint (contains fpcalc)
// sudo apt update
// sudo apt install libchromaprint-tools 

fn chromaprint_fingerprint(path: &str) -> AppResult<(String, u32)> {
    let output = Command::new("fpcalc")
        .arg("-json")
        .arg(path)
        .output()
        .map_err(|e| AppError::Other(format!("fpcalc error: {e}")))?;

    let json: Value =
        serde_json::from_slice(&output.stdout)
            .map_err(|e| AppError::Other(format!("fpcalc parse error: {e}")))?;

    let fingerprint = json["fingerprint"]
        .as_str()
        .unwrap_or("")
        .to_string();

    let duration = json["duration"]
        .as_f64()
        .unwrap_or(0.0) as u32;

    Ok((fingerprint, duration))
}

fn wang_fingerprint(path: &str) -> AppResult<(Vec<u32>, u32)> {
    let (audio, duration) = load_audio(path)
        .map_err(|e| AppError::Other(format!("audio load error: {e}")))?;

    let mut fingerprinter = Wang::default();

    let fp = fingerprinter
        .extract(audio)
        .map_err(|e| AppError::Other(format!("fingerprint error: {e}")))?
        .hashes;

    let hashes: Vec<u32> = fp.iter().map(|h| h.hash).collect();

    Ok((hashes, duration))
}

fn fingerprint_file(path: &str) -> AppResult<(Vec<u32>, u32, String, u32)> {
    let (wang_hashes, wang_duration) = wang_fingerprint(path)?;
    let (chromaprint, chroma_duration) = chromaprint_fingerprint(path)?;
    Ok((wang_hashes, wang_duration, chromaprint, chroma_duration))
}

// ---------------------------
// Handlers
// ---------------------------

async fn api_fingerprint(Json(req): Json<FingerprintRequest>) -> Json<FingerprintResponse> {
    let (wang_hashes, wang_duration, chromaprint, chroma_duration) =
        fingerprint_file(&req.filepath)
            .unwrap_or((vec![], 0, "".to_string(), 0));

    Json(FingerprintResponse {
        wang_hashes,
        wang_duration,
        chromaprint,
        chroma_duration,
    })
}

async fn api_status() -> Json<StatusResponse> {
    Json(StatusResponse { status: "ok".into() })
}

async fn api_add(Json(req): Json<AddRequest>) -> Json<StatusResponse> {
    // Extract BOTH fingerprints
    let (wang_hashes, wang_duration, chromaprint, chroma_duration) =
        match fingerprint_file(&req.filepath) {
            Ok(v) => v,
            Err(e) => {
                return Json(StatusResponse {
                    status: format!("error: {e}"),
                })
            }
        };

    // Serialize Wang hashes for DB storage
    let blob = bincode::serialize(&wang_hashes).unwrap();

    // Insert into DB
    let conn = DB_CONN.get().expect("DB not initialized").lock().unwrap();
    conn.execute(
        "INSERT INTO fingerprints (
            filepath, artist, title, album, year,
            hashes, wang_duration,
            chromaprint, chroma_duration,
            mbid
        )
        VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
        params![
            req.filepath,
            req.artist,
            req.title,
            req.album,
            req.year,

            blob,               // Wang hashes
            wang_duration,      // Wang duration

            chromaprint,        // Chromaprint fingerprint
            chroma_duration,    // Chromaprint duration

            ""                  // mbid (empty for now)
        ],
    )
    .unwrap();

    let id = conn.last_insert_rowid();

    // Insert Wang hashes into matcher
    let mut matcher = MATCHER.lock().unwrap();
    matcher.insert(FingerprintItem {
        id,
        filepath: req.filepath,
        artist: req.artist,
        title: req.title,
        album: req.album,
        year: req.year,
        hashes: wang_hashes,
    });

    Json(StatusResponse { status: "ok".into() })
}

async fn api_delete(Json(req): Json<DeleteRequest>) -> Json<StatusResponse> {
    let conn = DB_CONN.get().expect("DB not initialized").lock().unwrap();
    let rows = conn
        .execute("DELETE FROM fingerprints WHERE id = ?1", params![req.id])
        .unwrap();

    if rows == 0 {
        return Json(StatusResponse {
            status: "not_found".into(),
        });
    }

    let mut matcher = MATCHER.lock().unwrap();
    matcher.delete_by_id(req.id);

    Json(StatusResponse {
        status: "deleted".into(),
    })
}

async fn api_match(Json(req): Json<MatchRequest>) -> Json<MatchResponse> {
    let (wang_hashes, _wang_duration, _chromaprint, _chroma_duration) =
        fingerprint_file(&req.filepath)
            .unwrap_or((vec![], 0, "".to_string(), 0));

    let matcher = MATCHER.lock().unwrap();

    if let Some(item) = matcher.match_hashes(&wang_hashes) {
        Json(MatchResponse {
            artist: item.artist.clone(),
            title: item.title.clone(),
            album: item.album.clone(),
            year: item.year.clone(),
            confidence: 0.9,
        })
    } else {
        Json(MatchResponse {
            artist: "Unknown".into(),
            title: req.filepath.clone(),
            album: "Unknown".into(),
            year: "Unknown".into(),
            confidence: 0.0,
        })
    }
}

async fn api_shutdown(
    tx: Arc<Mutex<Option<oneshot::Sender<()>>>>,
) -> Json<StatusResponse> {
    if let Some(sender) = tx.lock().unwrap().take() {
        let _ = sender.send(());
        Json(StatusResponse {
            status: "shutting_down".into(),
        })
    } else {
        Json(StatusResponse {
            status: "already_shutting_down".into(),
        })
    }
}

// ---------------------------
// Main
// ---------------------------

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // -----------------------------------------
    // Parse command-line args for --db <path>
    // -----------------------------------------
    let args: Vec<String> = std::env::args().collect();
    let mut db_path = "database/audiofp.db".to_string(); // default fallback

    if let Some(pos) = args.iter().position(|a| a == "--db") {
        if pos + 1 < args.len() {
            db_path = args[pos + 1].clone();
        }
    }

    println!("Using database: {}", db_path);

    // -----------------------------------------
    // Initialize DB using provided path
    // -----------------------------------------
    init_database(&db_path);

    // -----------------------------------------
    // Load matcher AFTER DB is initialized
    // -----------------------------------------
    load_matcher_from_db().expect("failed to load matcher");

    // -----------------------------------------
    // Setup shutdown channel
    // -----------------------------------------
    let (tx, rx) = oneshot::channel::<()>();
    let tx_arc = Arc::new(Mutex::new(Some(tx)));

    // -----------------------------------------
    // Build Axum router
    // -----------------------------------------
    let app = Router::new()
        .route("/api/status", get(api_status))
        .route("/api/add", post(api_add))
        .route("/api/delete", post(api_delete))
        .route("/api/match", post(api_match))
        .route("/api/fingerprint", post(api_fingerprint)) 
        .route(
            "/api/shutdown",
            post({
                let tx_arc = tx_arc.clone();
                move || api_shutdown(tx_arc.clone())
            }),
        );

    // -----------------------------------------
    // Start server
    // -----------------------------------------
    let addr = SocketAddr::from(([127, 0, 0, 1], 5000));
    let listener = TcpListener::bind(addr).await?;
    println!("listening on {addr}");

    let server = serve(listener, app.into_make_service());

    tokio::select! {
        _ = server => {},
        _ = rx => {
            println!("shutdown signal received");
        }
    }

    Ok(())
}

