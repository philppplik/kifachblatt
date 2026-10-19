"""Permanent, licensed heise source-info pages and discoverable source archive."""
from pathlib import Path
import re
from licensed_news import collect, body, archive_body, detail_path, write_css, noindex

def build():
 from build import head, BASE
 rows=collect('.', 'kfb')
 shell=Path('index.html').read_text()
 top=shell[shell.index('<body>'):shell.index('<main id="main">')]
 bottom=shell[shell.index('</main>')+len('</main>'):]
 write_css('.')
 for item in rows:
  path=detail_path(item);target=Path(path.strip('/'))/'index.html';target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(head(item['title']+' | Quelleninfo | KI Fachblatt','Externe KI-Meldung mit RSS-Anrisstext und Original-Link.',BASE+path,robots='noindex,follow')+top+body(item,'KI Fachblatt')+bottom)
  noindex(target)
 target=Path('news/index.html');target.parent.mkdir(exist_ok=True)
 target.write_text(head('KI-News: Quellenarchiv | KI Fachblatt','Gesicherte externe KI-Meldungen mit erlaubtem Textauszug.',BASE+'/news/',robots='noindex,follow')+top+archive_body(rows,'KI Fachblatt')+bottom)
 noindex(target)
 # A small source-archive link, not a full navigation redesign.
 for page in [Path('index.html'),target]+[Path(detail_path(i).strip('/'))/'index.html' for i in rows]:
  s=page.read_text()
  if 'href="/news/"' not in s[s.index('<header'):s.index('</header>')]:
   s=re.sub(r'(<nav class="main"[^>]*>)',r'\1<a href="/news/">KI-News</a>',s,count=1)
  page.write_text(s)
 print('Licensed KI news: %d permanent text-only source-info pages'%len(rows))
