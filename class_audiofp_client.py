########################
# F.garcia
# creation: 15.05.2026
########################

import os
import time
import subprocess
import requests
from class_file_manipulate import FileManipulate
FM = FileManipulate()

class AudioFPClient:
    def __init__(self, base_url, db_path, server_path=None, autostart=True):
        """
        base_url: e.g. "http://127.0.0.1:5000"
        server_path: folder containing ./audiofp-server binary
        autostart: automatically start server if offline
        """
        self.base = base_url.rstrip("/")
        self.server_path = server_path
        self.autostart = autostart
        self.db_path=db_path
        if not os.path.exists(db_path):
            raise FileExistsError(f"Database File {self.db_path} not found!")
        
        (file_exist, is_file)=FM.validate_path_file(self.server_path)
        if not file_exist or is_file:
            raise FileExistsError(f"File audiofp-server not found in {self.server_path}")

        # Build URLs
        self.url_status = f"{self.base}/api/status"
        self.url_match  = f"{self.base}/api/match"
        self.url_add    = f"{self.base}/api/add"
        self.url_delete = f"{self.base}/api/delete"
        self.url_fingerprint = f"{self.base}/api/fingerprint"

        if autostart:
            self.ensure_server_running()

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _safe_json(self, resp):
        try:
            return resp.json()
        except:
            return {"error": resp.text, "status": resp.status_code}

    def ensure_server_running(self):
        """Ping server; if offline, start it."""
        try:
            r = requests.get(self.url_status, timeout=0.5)
            if r.status_code == 200:
                return True
        except:
            pass

        if not self.server_path:
            raise RuntimeError("Server offline and no server_path provided")

        print("Starting audiofp-server…")
        fullpath = os.path.join(self.server_path, "audiofp-server")
        subprocess.Popen(
            [fullpath, "--db", self.db_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for server to come online
        for _ in range(20):
            try:
                r = requests.get(self.url_status)
                if r.status_code == 200:
                    print("Server is online")
                    return True
            except:
                pass
            time.sleep(0.2)

        raise RuntimeError("Server did not start")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def fingerprint(self, filepath):
        """Fingerprint a file and return fingerprint info."""
        resp = requests.post(
            self.url_fingerprint,
            json={"filepath": filepath}
        )
        return self._safe_json(resp)

    def match(self, filepath):
        """Match a file against the fingerprint DB."""
        resp = requests.post(self.url_match, json={"filepath": filepath})
        return self._safe_json(resp)

    def add(self, filepath, artist, title, album, year, mbid=""):
        """Add a fingerprint + metadata to the DB."""
        payload = {
            "filepath": filepath,
            "artist": artist,
            "title": title,
            "album": album,
            "year": year,
            "mbid": mbid  # empty string on initial add
        }
        resp = requests.post(self.url_add, json=payload)
        return self._safe_json(resp)

    def delete(self, id_path):
        """Delete a fingerprint entry by ID."""
        resp = requests.post(self.url_delete, json={"id": id_path})
        return self._safe_json(resp)
    


if __name__ == "__main__":
    
    import yaml
    from class_file_manipulate import FileManipulate
    FM = FileManipulate()
    # Path to compiled server binary
    server_path = os.path.join(FM.get_app_path(),"audiofp-server","target","release")

    config = yaml.safe_load(open("config.yaml"))

    server = AudioFPClient(
        base_url=config["server"]["base"],
        server_path=server_path,
        autostart=True
    )

    info = server.fingerprint("song.mp3")
    print(info)

    match = server.match("other.mp3")
    print(match)
