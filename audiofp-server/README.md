
# AudioFP Server

A lightweight Rust HTTP server that exposes the **AudioFP** audio‑fingerprinting engine through a simple JSON API.  
This server is designed to be used by Python scripts (or any other client) to identify audio files, extract metadata, and build a searchable fingerprint database.

---

## 🚀 Features

- Fast, modern Rust HTTP server using **Axum 0.7**
- Compatible with the **AudioFP** fingerprinting library
- JSON API endpoints for:
  - Server health check
  - Audio matching
  - Indexing directories (fingerprinting)
- Designed to integrate with Python tag‑fixing tools

---

## 📂 Project Structure

```
audiofp-server/
  ├── Cargo.toml
  ├── src/
  │    └── main.rs
  └── target/
       └── release/
            └── audiofp-server   ← compiled binary
```

The server depends on the AudioFP library located in a sibling folder:

```
../audiofp
```

---

## 🔧 Building the Server

Make sure Rust is installed:

```
rustc --version
cargo --version
```

Then build in release mode:

```
cargo build --release
```

The compiled binary will appear at:

```
target/release/audiofp-server
```

---

## ▶️ Running the Server

Start the server:

```
./target/release/audiofp-server
```

You should see:

```
AudioFP server running on [http://127.0.0.1:5000](http://127.0.0.1:5000)
```

---

## 🧪 Testing the Server

### Check server status

Open in your browser:

```
http://localhost:5000/api/status
```

Expected response:

```json
{"status":"ok"}
```

---

## 📡 API Endpoints

### `GET /api/status`
Returns server health.

### `POST /api/match`
Identify an audio file.

Example request:

```json
{
  "filepath": "/path/to/audio.mp3"
}
```

### `POST /api/index`
Index (fingerprint) a directory.

Example request:

```json
{
  "directory": "/path/to/music/"
}
```

---

## 🐍 Python Integration

The server is designed to be used from Python.  
A typical workflow:

1. Start the Rust server  
2. Python sends audio files to `/api/match`  
3. The server returns artist/title/confidence  
4. Python updates tags using `eyeD3`

Example Python call:

```python
import requests

resp = requests.post(
    "http://localhost:5000/api/match",
    json={"filepath": "/path/song.mp3"}
)

print(resp.json())
```

---

## 🛠️ Next Steps

- Integrate real AudioFP fingerprinting logic
- Add file upload support
- Build a full Python tag‑repair pipeline

---

## 📄 License

MIT License

---


