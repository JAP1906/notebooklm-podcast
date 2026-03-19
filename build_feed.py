import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timezone

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = "1It7ZHkkL-mo_wcbAmuqhjSQbUmEkscoi"

creds = service_account.Credentials.from_service_account_file(
    "creds.json", scopes=SCOPES)

service = build('drive', 'v3', credentials=creds)

results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id,name,createdTime)").execute()

files = results.get('files', [])

episodes = {}

for f in files:
    name = f["name"]
    if name.endswith(".m4a"):
        key = name.replace(".m4a","")
        episodes.setdefault(key,{})["audio"] = f["id"]
        episodes.setdefault(key,{})["created"] = f.get("createdTime","")
    if name.endswith(".txt"):
        key = name.replace(".txt","")
        episodes.setdefault(key,{})["meta"] = f["id"]

items = []

for k,v in episodes.items():
    if "audio" in v and "meta" in v:
        meta = service.files().get_media(fileId=v["meta"]).execute().decode("utf-8", errors="replace")

        lines = [l.strip() for l in meta.splitlines()]
        all_lines = lines[:]
        lines = [l for l in lines if l]  # sem linhas vazias para parsing

        title = k  # fallback: nome do ficheiro
        desc = ""

        for i, l in enumerate(lines):
            # Aceita "Titulo:" e "Título:" (com ou sem acento)
            if re.match(r'[Tt][ií]tulo\s*:', l, re.IGNORECASE):
                val = re.split(r':\s*', l, 1)
                if len(val) > 1 and val[1].strip():
                    title = val[1].strip()
                elif i + 1 < len(lines):
                    title = lines[i + 1]

            # Aceita "Descricao:" e "Descrição:"
            if re.match(r'[Dd]escri[cç][aã]o\s*:', l, re.IGNORECASE):
                val = re.split(r':\s*', l, 1)
                if len(val) > 1 and val[1].strip():
                    desc = val[1].strip()
                else:
                    # Tudo o que vem a seguir
                    idx = all_lines.index(l)
                    desc = "\n".join(all_lines[idx+1:]).strip()

        # Escapar caracteres especiais XML
        def xml_escape(s):
            return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

        title = xml_escape(title)
        desc = xml_escape(desc)

        audio_url = f"https://drive.usercontent.google.com/download?id={v['audio']}&amp;export=download"

        # pubDate a partir da data de criação no Drive
        try:
            dt = datetime.fromisoformat(v["created"].replace("Z","+00:00"))
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        item = f"""
<item>
  <title>{title}</title>
  <description>{desc}</description>
  <enclosure url="{audio_url}" length="0" type="audio/mp4"/>
  <guid isPermaLink="false">{k}</guid>
  <pubDate>{pub_date}</pubDate>
</item>"""
        items.append((pub_date, item))

# Ordenar por data (mais recente primeiro)
items.sort(key=lambda x: x[0], reverse=True)
rss_items = "\n".join(i[1] for i in items)

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
  <title>NotebookLM2Overcast</title>
  <description>Audios NotebookLM</description>
  <link>https://github.com/JAP1906/delta-7f4k2</link>
  <language>pt-pt</language>
  <itunes:author>JAP</itunes:author>
{rss_items}
</channel>
</rss>
"""

open("feed-n3vx8kp2.xml","w", encoding="utf-8").write(rss)
