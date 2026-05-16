# -*- coding: utf-8 -*-
# Search engine using acoustid.
########################
# F.Garcia
# creation: 16.05.2026
########################

from class_search_musicbrainz import *

def main():
    key_in = None
    key_txt=DB_PATH.replace(".db","_key.txt")
    if os.path.exists("mydatabase_key.txt"):
        with open("mydatabase_key.txt", "rb") as efff:
            key_in = efff.read()

    db = SQLiteDatabase(DB_PATH, True, key_in)

    cache = MusicBrainzCache(db)
    mb = SearchMusicBrainz(headers=HEADERS, cache=cache)
    ac = SearchAcoustID(api_key=API_KEY, headers=HEADERS)
    fp_server = AudioFPClient(base_url=BASE_URL,db_path=DB_PATH, server_path=SERVER_PATH)

    resolver = MetadataResolver(fp_server, ac, mb)
    from class_tui_file_explorer import FileExplorer
    from class_textual_tui import ConfirmInputApp
    result=FileExplorer().run()
    selection_list=[]
    
    # Filter only mp3 files
    for file in result.get("Selection",[]):
        fnwe=FM.extract_filename(file,True)
        if fnwe.endswith(".mp3"):
            selection_list.append(file)
    
    for file in selection_list:
        meta = resolver.resolve_metadata(file)
        print(meta)
        if "error" in meta:
            break
        answer=ConfirmInputApp("Add to Database",f"Would you like to add\n{meta}\n entry to {CACHE_DB_PATH}?","y").run()
        if answer:
            fp_server.add(filepath=file,
                          artist=meta.get("artist"),
                          title=meta.get("title"),
                          album=meta.get("album"),
                          # year=???
                          mbid=meta.get("mbid")
                          )

if __name__ == "__main__":
    main()