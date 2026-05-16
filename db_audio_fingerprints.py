import os
import struct
import requests

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate

# ---------------------------------------------------------
# Path setup
# ---------------------------------------------------------

FM = FileManipulate()
DB_PATH = os.path.join(FM.get_app_path(), "db")

(file_exist, is_file) = FM.validate_path_file(DB_PATH)
if not file_exist:
    os.makedirs(DB_PATH)

db_path = os.path.join(DB_PATH, "audiofp_index.db")

# ---------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------

def init_fingerprint_db(db_path: str):
    """Create the fingerprints table if it doesn't exist."""
    db = SQLiteDatabase(db_path)  # connection auto-created
    try:
        db.create_table(
            "fingerprints",
            [
                ("filepath", "TEXT", False),
                ("artist",   "TEXT", False),
                ("title",    "TEXT", False),
                ("album",    "TEXT", False),
                ("year",     "TEXT", False),
                ("hashes",   "BLOB", False),
            ]
        )
    finally:
        db.close_connection()

def pack_hashes(hashes: list[int]) -> bytes:
    return struct.pack(f"{len(hashes)}I", *hashes)

def unpack_hashes(blob: bytes) -> list[int]:
    count = len(blob) // 4
    return list(struct.unpack(f"{count}I", blob))

# ---------------------------------------------------------
# Python-side DB wrapper
# ---------------------------------------------------------

class FingerprintDB:
    def __init__(self, path=db_path):
        self.db = SQLiteDatabase(path)

    def add(self, filepath, artist, title, album, year, hashes):
        blob = pack_hashes(hashes)
        self.db.insert_data_to_table(
            "fingerprints",
            [(filepath, artist, title, album, year, blob)]
        )

    def delete(self, fid):
        self.db.delete_data_from_table("fingerprints", f"id = {fid}")

    def delete_by_path(self, filepath):
        self.db.delete_data_from_table(
            "fingerprints",
            where=f"filepath = {self.db.quotes(filepath)}"
        )

    def load_all(self):
        return self.db.get_data_from_table("fingerprints", "*")

    def close(self):
        self.db.close_connection()

# ---------------------------------------------------------
# HTTP client for the Rust server
# ---------------------------------------------------------

SERVER = "http://127.0.0.1:5000"

def server_add(filepath, artist, title, album, year):
    """Send a file to the Rust server to fingerprint + store."""
    payload = {
        "filepath": filepath,
        "artist": artist,
        "title": title,
        "album": album,
        "year": year,
    }
    r = requests.post(f"{SERVER}/api/add", json=payload)
    return r.json()

def server_delete(fid):
    """Delete a fingerprint by ID."""
    r = requests.post(f"{SERVER}/api/delete", json={"id": fid})
    return r.json()

def server_match(filepath):
    """Ask the server to fingerprint a file and match it."""
    r = requests.post(f"{SERVER}/api/match", json={"filepath": filepath})
    return r.json()

def server_status():
    """Check if the server is alive."""
    r = requests.get(f"{SERVER}/api/status")
    return r.json()

def server_shutdown():
    """Tell the Rust server to shut down cleanly."""
    r = requests.post(f"{SERVER}/api/shutdown")
    return r.json()

# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------

if __name__ == "__main__":
    print("Server status:", server_status())

    # Example: add a file
    # print(server_add("/path/to/song.mp3", "Artist", "Title", "Album", "2024"))

    # Example: match a file
    # print(server_match("/path/to/song.mp3"))

    # Example: delete by ID
    # print(server_delete(3))

    input("Press ENTER to Shutdown server")
    # Example: shutdown server
    print(server_shutdown())
