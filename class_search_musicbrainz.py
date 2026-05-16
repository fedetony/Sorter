# -*- coding: utf-8 -*-
# Search engine class for Music metadata.
########################
# F.Garcia
# creation: 16.05.2026
########################


import json
import requests
import yaml
import time
import os
from class_file_manipulate import FileManipulate
from class_sqlite_database import SQLiteDatabase
from class_audiofp_client import AudioFPClient
import acoustid # pip install pyacoustid
FM = FileManipulate()

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

API_KEY = config["acoustid_api_key"]
print(API_KEY)
HEADERS = config["headers"]
FINGERPRINT_SERVER = config.get("fingerprint_server")
APP_PATH=FM.get_app_path()
SERVER_PATH = config.get("server_path")
SERVER_NAME = config.get("server_file")
DB_PATH = config.get("database")
(dbfile_exist, dbis_file) = FM.validate_path_file(DB_PATH)
if not dbfile_exist:
    DB_PATH=os.path.join(APP_PATH,DB_PATH)
    (dbfile_exist, dbis_file) = FM.validate_path_file(DB_PATH)
if dbfile_exist and dbis_file:
    print(f"Database {DB_PATH} Found")
else:
    raise FileExistsError(f"{DB_PATH} Path Not Found")

CACHE_DB_PATH = config.get("cache_database")
BASE_URL = FINGERPRINT_SERVER.get("base")
(file_exist, is_file) = FM.validate_path_file(SERVER_PATH)
if not file_exist:
    SERVER_PATH=os.path.join(APP_PATH,SERVER_PATH)
    (file_exist, is_file) = FM.validate_path_file(SERVER_PATH)
if file_exist and not is_file:
    SERVER_FULL_PATH=os.path.join(SERVER_PATH,SERVER_NAME)
    (sfile_exist, sis_file)=FM.validate_path_file(SERVER_FULL_PATH)
    if sfile_exist and sis_file:
        print(f"Server {SERVER_FULL_PATH} Found")
    else:
        raise FileExistsError(f"{SERVER_FULL_PATH} File Not Found")    
else:
    raise FileExistsError(f"{SERVER_PATH} Path Not Found")

class SearchMusicBrainz:
    BASE = "https://musicbrainz.org/ws/2"

    def __init__(self, headers=None, cache=None, retries=3, backoff=0.4):
        self.HEADERS = headers or {"User-Agent": "AudioFP/1.0 (contact@example.com)"}
        self.cache = cache
        self.retries = retries
        self.backoff = backoff

    # ---------------------------------------------------------
    # Internal cached GET with retry/backoff
    # ---------------------------------------------------------
    def _cached_get(self, cache_key, url, params):
        # 1. Cache lookup
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        # 2. Retry logic
        for attempt in range(self.retries):
            try:
                r = requests.get(url, params=params, headers=self.HEADERS, timeout=5)
                data = r.json()

                if self.cache:
                    self.cache.set(cache_key, data)

                return data

            except requests.exceptions.SSLError:
                time.sleep(self.backoff * (attempt + 1))

        raise RuntimeError("MusicBrainz request failed after retries")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def search_artist(self, name):
        key = f"artist:{name.lower()}"
        url = f"{self.BASE}/artist"
        params = {"query": f'artist:"{name}"', "fmt": "json"}
        data = self._cached_get(key, url, params)
        return data.get("artists", [])

    def search_recording(self, title, artist=None):
        if artist:
            key = f"recording:{title.lower()}|{artist.lower()}"
            query = f'recording:"{title}" AND artist:"{artist}"'
        else:
            key = f"recording:{title.lower()}"
            query = f'recording:"{title}"'

        url = f"{self.BASE}/recording"
        params = {"query": query, "fmt": "json"}
        data = self._cached_get(key, url, params)
        return data.get("recordings", [])

    def search_release(self, album, artist=None):
        if artist:
            key = f"release:{album.lower()}|{artist.lower()}"
            query = f'release:"{album}" AND artist:"{artist}"'
        else:
            key = f"release:{album.lower()}"
            query = f'release:"{album}"'

        url = f"{self.BASE}/release"
        params = {"query": query, "fmt": "json"}
        data = self._cached_get(key, url, params)
        return data.get("releases", [])

    def lookup_recording(self, mbid):
        key = f"mbid:{mbid}"
        url = f"{self.BASE}/recording/{mbid}"
        params = {"fmt": "json", "inc": "artists releases"}
        return self._cached_get(key, url, params)
    
    def get_artist_albums(self, artist_mbid):
        """Return all album releases for a given artist MBID."""
        url = f"{self.BASE}/release"
        params = {
            "artist": artist_mbid,
            "fmt": "json",
            "inc": "release-groups"
        }

        key = f"artist_albums:{artist_mbid}"
        data = self._cached_get(key, url, params)

        albums = []
        for rel in data.get("releases", []):
            albums.append({
                "title": rel["title"],
                "release_mbid": rel["id"],
                "date": rel.get("date"),
                "country": rel.get("country"),
                "status": rel.get("status")
            })

        return albums
    
    def get_artist_tracks(self, artist_mbid):
        """Return all recordings for a given artist MBID."""
        url = f"{self.BASE}/recording"
        params = {
            "artist": artist_mbid,
            "fmt": "json",
            "limit": 100
        }

        key = f"artist_tracks:{artist_mbid}"
        data = self._cached_get(key, url, params)

        tracks = []
        for rec in data.get("recordings", []):
            tracks.append({
                "title": rec["title"],
                "recording_mbid": rec["id"],
                "length": rec.get("length"),
                "score": rec.get("score")
            })

        return tracks
    
    def get_artist_tracks(self, artist_mbid):
        """Return all recordings for a given artist MBID."""
        url = f"{self.BASE}/recording"
        params = {
            "artist": artist_mbid,
            "fmt": "json",
            "limit": 100
        }

        r = requests.get(url, params=params, headers=self.HEADERS)
        data = r.json()

        tracks = []
        for rec in data.get("recordings", []):
            tracks.append({
                "title": rec["title"],
                "recording_mbid": rec["id"],
                "length": rec.get("length"),
                "score": rec.get("score")
            })

        return tracks

class MusicBrainzCache:
    def __init__(self, db: SQLiteDatabase):
        self.db = db
        self.init_mb_cache(db)
    
    def init_mb_cache(self,db):
        if not db.table_exists("mb_cache"):
            db.create_table("mb_cache", [
                ("key", "TEXT PRIMARY KEY", True),
                ("value", "TEXT", True),
                ("timestamp", "INTEGER", True)
            ])


    def get(self, key):
        rows = self.db.get_data_from_table("mb_cache", "*", f"key = '{key}'")
        if not rows:
            return None
        return json.loads(rows[0]["value"])

    def set(self, key, value):
        payload = json.dumps(value)
        ts = int(time.time())
        self.db.insert_data_to_table("mb_cache", [(key, payload, ts)])


class MusicBrainzPicker:
    def pick_artist(self, artists):
        """
        Present multiple artists and let the user choose.
        You can replace input() with GUI selection later.
        """
        print("\nPossible artist matches:")
        for i, a in enumerate(artists):
            print(f"{i}: {a['name']} ({a.get('type', 'Unknown')}) "
                  f"{a.get('country', '')} - score {a.get('score')} "
                  f"{'[' + a.get('disambiguation','') + ']' if a.get('disambiguation') else ''}")

        choice = int(input("Select artist index: "))
        return artists[choice]

    def pick_release(self, releases):
        print("\nPossible album matches:")
        for i, r in enumerate(releases):
            print(f"{i}: {r['title']} ({r.get('date','unknown')})")

        choice = int(input("Select album index: "))
        return releases[choice]

    def pick_recording(self, recordings):
        print("\nPossible song matches:")
        for i, r in enumerate(recordings):
            print(f"{i}: {r['title']} - {r['artist-credit'][0]['name']}")

        choice = int(input("Select song index: "))
        return recordings[choice]

class SearchAcoustID:
    BASE = "https://api.acoustid.org/v2"
    HEADERS = {"User-Agent": "AudioFP/1.0 (contact@example.com)"}

    def __init__(self, api_key, headers=None):
        self.api_key = api_key
        if isinstance(headers,dict):
            self.HEADERS=headers
    
    @staticmethod
    def lookup_file(path, api_key):
        match_dict={}
        data=acoustid.match(api_key, path)
        if 'error' in data:
             print(f"Error in AcoustID match: {data}")
             return match_dict
        for iii,(score, rid, title, artist) in enumerate(data):
            match_dict[iii]=[score, rid, title, artist]
            print(score, rid, title, artist)
        return match_dict

    @staticmethod
    def lookup_fp(fp, duration, api_key):
        data = acoustid.lookup(api_key, fp, duration, meta=["recordings", "releases"])
        if 'error' in data:
             print(f"Error in AcoustID lookup: {data}")
             return []
        return list(acoustid.parse_lookup_result(data))

    def lookup(self, fingerprint, duration):
        """
        Lookup an AcoustID fingerprint.
        Returns a list of candidate recordings with MBIDs and scores.
        
        Look up a fingerprint with the Acoustid Web service. Returns the
        Python object reflecting the response JSON data. To get more data
        back, ``meta`` can be a list of keywords from this list: recordings,
        recordingids, releases, releaseids, releasegroups, releasegroupids,
        tracks, compress, usermeta, sources.
        """
        url = f"{self.BASE}/lookup"
        params = {
            "client": self.api_key,
            "meta": "recordings releases releasegroups tracks compress",
            "duration": int(duration),
            "fingerprint": fingerprint,
            "fingerprint_version": 2,
            "format": "json",
        }
        r = requests.post(url, data=params, headers=self.HEADERS)
        data = r.json()
        if 'error' in data:
            print(f"Error in AcoustID lookup: {data}")
        return data.get("results", [])
        # Same issue with their api...
        return self.lookup_fp(fingerprint, duration, self.api_key)


    def best_match(self, fingerprint, duration):
        """
        Return the highest‑score match (if any).
        """
        results = self.lookup(fingerprint, duration)
        if not results:
            return None

        # AcoustID returns results sorted by score, but we enforce it
        results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
        return results[0]

    def extract_mbids(self, fingerprint, duration):
        """
        Return a flat list of all MBIDs found in the fingerprint lookup.
        """
        results = self.lookup(fingerprint, duration)
        mbids = []

        for result in results:
            for rec in result.get("recordings", []):
                mbids.append(rec.get("id"))

        return mbids

class MetadataResolver:
    def __init__(self, fp_server: AudioFPClient, acoustid: SearchAcoustID, mb: SearchMusicBrainz):
        self.fp_server = fp_server
        self.ac = acoustid
        self.mb = mb

    def resolve_metadata(self, filepath):
        # 1. Ask Rust server for BOTH fingerprints
        fp = self.fp_server.fingerprint(filepath)

        wang_hashes     = fp["wang_hashes"]       # used for internal matching only
        wang_duration   = fp["wang_duration"]

        chromaprint_fp  = fp["chromaprint"]       # used for AcoustID
        chroma_duration = fp["chroma_duration"]

        # 2. AcoustID lookup using Chromaprint (NOT Wang)
        best = self.ac.best_match(chromaprint_fp, chroma_duration)
        if not best:
            return {"error": "No AcoustID match"}

        recording = best["recordings"][0]
        mbid = recording["id"]

        # 3. MusicBrainz lookup
        mb_data = self.mb.lookup_recording(mbid)

        # 4. Extract metadata
        artist = mb_data["artists"][0]["name"]
        title = mb_data["title"]
        album = (
            mb_data["releases"][0]["title"]
            if mb_data.get("releases")
            else None
        )

        return {
            "artist": artist,
            "title": title,
            "album": album,
            "mbid": mbid,
            "acoustid_score": best.get("score"),
            #"wang_hashes": wang_hashes,  # optional, useful for debugging
        }


if __name__ == "__main__":
    pass
    
    # duration = 213
    # Step 2: lookup AcoustID
    # result = ac.best_match(fp, duration)
    # result = ac.best_match(fingerprint, duration)
    # mbid = result["recordings"][0]["id"]

    # # Search by artist only
    # artists = mb.search_artist("NoFx")
    # print(f"artists= {artists}")

    # # Search by song only
    # songs = mb.search_recording("Linoleum")
    # print(f"songs = {songs}")

    # # Search by album only
    # albums = mb.search_release("Punk in Drublic")
    # print(f"albums= {albums}")

    # # Search by artist + song
    # song = mb.search_recording("Linoleum", artist="NOFX")
    # print(f'"Linoleum", artist="NOFX"= {song}')

    # # Get tracklist for an album
    # #tracks = mb.get_album_tracks("<release_mbid>")


    # # Resolve metadata from partial tags
    # meta = mb.resolve_metadata(artist="NoFx", title="Linoleum")
    # print(f'"meta Linoleum", artist="NOFX"= {meta}')
