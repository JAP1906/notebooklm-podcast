import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = "1It7ZHkkL-mo_wcbAmuqhjSQbUmEkscoi"

creds = service_account.Credentials.from_service_account_file(
    "creds.json", scopes=SCOPES)

service = build('drive', 'v3', credentials=creds)

results = service.files().list(
    q=f"'{FOLDER_ID}' in parents",
    fields="files(id,name)").execute()

files = results.get('files', [])

episodes = {}

for f in files:
    name = f["name"]
    if name.endswith(".m4a"):
        key = name.replace(".m4a","")
        episodes.setdefault(key,{})["audio"] = f["id"]
    if name.endswith(".txt"):
        key = name.replace(".txt","")
        episodes.setdefault(key,{})["meta"] = f["id"]

items = []

for k,v in episodes.items():
    if "audio" in v and "meta" in v:
        meta = service.files().get_media(fileId=v["meta"]).execute().decode()

        title=""
        desc=""

        for line in meta.splitlines():
            if line.startswith("Titulo:"):
                title=line.replace("Titulo:","").strip()
            if line.startswith("Descricao:"):
                desc=line.replace("Descricao:","").strip()

        audio_url=f"https://drive.google.com/uc?export=download&id={v['audio']}"

        item=f"""
<item>
<title>{title}</title>
<description>{desc}</description>
<enclosure url="{audio_url}" length="0" type="audio/mp4"/>
<guid>{k}</guid>
</item>
"""
        items.append(item)

rss=f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>NotebookLM Audio</title>
<description>Audios NotebookLM</description>
<link>https://github.com/JAP1906/notebooklm-podcast</link>
{''.join(items)}
</channel>
</rss>
"""

open("podcast.xml","w").write(rss)
