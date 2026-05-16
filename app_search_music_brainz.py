# -*- coding: utf-8 -*-
"""App for music info library search.
########################
# F.Garcia
# creation: 16.05.2026
########################
"""

from class_search_musicbrainz import SearchMusicBrainz
from class_textual_tui import MenuApp ,TreeViewer ,CheckTreeApp, TextualInputApp

class MusicBrainzTUI:

    def __init__(self):
        self.mb = SearchMusicBrainz()

    def run(self):
        while True:
            choice = MenuApp(
                ["Search Artist", "Search Album", "Search Song", "Exit"],
                {
                    "title": "MusicBrainz Search",
                    "subtitle": "[yellow]Choose a search mode[/yellow]",
                    "enumerate": True,
                    "prefix": ". "
                }
            ).run()

            if choice == "Search Artist":
                self.search_artist()

            elif choice == "Search Album":
                self.search_album()

            elif choice == "Search Song":
                self.search_song()

            elif choice == "Exit":
                break

    # ---------------------------------------------------------
    # ARTIST SEARCH
    # ---------------------------------------------------------
    def search_artist(self):        
        name = TextualInputApp(
            title="Artist Search",
            prompt="Enter artist name:",
            default=""
        ).run()

        if name is None:
            print("Cancelled.")
            return

        results = self.mb.search_artist(name)

        if not results:
            print("No results found.")
            input("Press ENTER to continue")
            return

        # Build tree structure
        tree_struct = {"Artists": []}

        for a in results:
            artist_name = a["name"]

            artist_info = [
                (f"MBID: {a['id']}", 0),
                (f"Type: {a.get('type','')}", 0),
                (f"Country: {a.get('country','')}", 0),
                (f"Disambiguation: {a.get('disambiguation','')}", 0),
                (f"Score: {a.get('score','')}", 0),
            ]

            tree_struct["Artists"].append({artist_name: artist_info})

        tree_mode = {
            "one_selection": True,
            "root_selectable": False,
            "dir_selectable": True,
            "only_dir": False,
            "locked_items": [],
            "default_selected_items": [],
            "return_id": True
        }

        tree_viewer = TreeViewer(tree_struct, {"name": 0, "size": 1})
        tree_viewer.expand_all_treenodes(True)

        result = CheckTreeApp(tree_viewer, tree_mode).run()

        if not result:
            print("No selection.")
            input("Press ENTER to continue")
            return

        selected_id = result[0]

        # Get the selected node
        node = tree_viewer.get_nodes_by_attribute("id", selected_id)[0]

        # Walk up to the artist node
        artist_node = node
        while artist_node.parent and artist_node.parent.parent:
            artist_node = artist_node.parent

        artist_name = artist_node.name

        # Extract MBID from the artist's children
        mbid = None
        for child in artist_node.children:
            if child.info and isinstance(child.info, tuple):
                text = child.info[0]
                if isinstance(text, str) and text.startswith("MBID:"):
                    mbid = text.replace("MBID:", "").strip()
                    break

        if not mbid:
            print("ERROR: Could not extract MBID")
            input("Press ENTER to continue")
            return

        # Find the matching MusicBrainz dict
        chosen = next((a for a in results if a["id"] == mbid), None)

        if not chosen:
            print("ERROR: MBID not found in results")
            print("Extracted MBID:", mbid)
            print("Available MBIDs:", [a["id"] for a in results])
            input("Press ENTER to continue")
            return

        print("\nChosen Artist:")
        print("Name:", chosen["name"])
        print("MBID:", chosen["id"])
        print()
        input("Press ENTER to continue")


    # ---------------------------------------------------------
    # ALBUM SEARCH
    # ---------------------------------------------------------
    def search_album(self):
        album = TextualInputApp(
            title="Album Search",
            prompt="Enter album title:",
            default=""
        ).run()

        if album is None:
            print("Cancelled.")
            return
        results = self.mb.search_release(album)

        if not results:
            print("No results found.")
            input("Press ENTER to continue")
            return

        # Build tree structure
        tree_struct = {"Albums": []}

        for r in results:
            title = r["title"]

            # Extract artist name (MusicBrainz stores it inside 'artist-credit')
            artist_name = ""
            try:
                artist_name = r["artist-credit"][0]["name"]
            except Exception:
                artist_name = "Unknown Artist"

            album_info = [
                (f"MBID: {r['id']}", 0),
                (f"Artist: {artist_name}", 0),
                (f"Date: {r.get('date','unknown')}", 0),
                (f"Country: {r.get('country','')}", 0),
                (f"Status: {r.get('status','')}", 0),
                (f"Packaging: {r.get('packaging','')}", 0),
                (f"Score: {r.get('score','')}", 0),
            ]

            # Display album as "Album Title (Artist)"
            display_name = f"{title} ({artist_name})"

            tree_struct["Albums"].append({display_name: album_info})

        tree_mode = {
            "one_selection": True,
            "root_selectable": False,
            "dir_selectable": True,
            "only_dir": False,
            "locked_items": [],
            "default_selected_items": [],
            "return_id": True
        }

        tree_viewer = TreeViewer(tree_struct, {"name": 0, "size": 1})
        tree_viewer.expand_all_treenodes(True)

        result = CheckTreeApp(tree_viewer, tree_mode).run()

        if not result:
            print("No selection.")
            input("Press ENTER to continue")
            return

        selected_id = result[0]

        # Get the selected node
        node = tree_viewer.get_nodes_by_attribute("id", selected_id)[0]

        # Walk up to the album node
        album_node = node
        while album_node.parent and album_node.parent.parent:
            album_node = album_node.parent

        # Extract MBID
        mbid = None
        for child in album_node.children:
            if child.info and isinstance(child.info, tuple):
                text = child.info[0]
                if isinstance(text, str) and text.startswith("MBID:"):
                    mbid = text.replace("MBID:", "").strip()
                    break

        if not mbid:
            print("ERROR: Could not extract MBID")
            input("Press ENTER to continue")
            return

        # Find matching MB dict
        chosen = next((r for r in results if r["id"] == mbid), None)

        if not chosen:
            print("ERROR: MBID not found in results")
            print("Extracted MBID:", mbid)
            print("Available MBIDs:", [r["id"] for r in results])
            input("Press ENTER to continue")
            return

        print("\nChosen Album:")
        print("Title:", chosen["title"])
        print("Artist:", chosen["artist-credit"][0]["name"])
        print("MBID:", chosen["id"])
        print()
        input("Press ENTER to continue")

    # ---------------------------------------------------------
    # SONG SEARCH
    # ---------------------------------------------------------
    def search_song(self):
        title = TextualInputApp(
            title="Song Search",
            prompt="Enter song title:",
            default=""
        ).run()

        if title is None:
            print("Cancelled.")
            return
        
        results = self.mb.search_recording(title)

        if not results:
            print("No results found.")
            input("Press ENTER to continue")
            return

        # Build tree structure
        tree_struct = {"Songs": []}

        for r in results:
            song_title = r["title"]
            artist = r["artist-credit"][0]["name"]

            song_info = [
                (f"MBID: {r['id']}", 0),
                (f"Artist: {artist}", 0),
                (f"Length: {r.get('length','')}", 0),
                (f"Disambiguation: {r.get('disambiguation','')}", 0),
                (f"Score: {r.get('score','')}", 0),
            ]

            tree_struct["Songs"].append({f"{song_title} - {artist}": song_info})

        tree_mode = {
            "one_selection": True,
            "root_selectable": False,
            "dir_selectable": False,
            "only_dir": False,
            "locked_items": [],
            "default_selected_items": [],
            "return_id": True
        }

        tree_viewer = TreeViewer(tree_struct, {"name": 0, "size": 1})
        tree_viewer.expand_all_treenodes(True)

        result = CheckTreeApp(tree_viewer, tree_mode).run()

        if not result:
            print("No selection.")
            input("Press ENTER to continue")
            return

        selected_id = result[0]

        # Get the selected node
        node = tree_viewer.get_nodes_by_attribute("id", selected_id)[0]

        # Walk up to the song node
        song_node = node
        while song_node.parent and song_node.parent.parent:
            song_node = song_node.parent

        label = song_node.name
        song_title = label.split(" - ")[0]

        # Extract MBID
        mbid = None
        for child in song_node.children:
            if child.info[0].startswith("MBID:"):
                mbid = child.info[0].replace("MBID:", "").strip()
                break

        if not mbid:
            print("ERROR: Could not extract MBID")
            input("Press ENTER to continue")
            return

        # Find matching MB dict
        chosen = next((r for r in results if r["id"] == mbid), None)

        if not chosen:
            print("ERROR: MBID not found in results")
            input("Press ENTER to continue")
            return

        print("\nChosen Song:")
        print("Title:", chosen["title"])
        print("Artist:", chosen["artist-credit"][0]["name"])
        print("MBID:", chosen["id"])
        print()
        input("Press ENTER to continue")


if __name__ == "__main__":
    MusicBrainzTUI().run()
