#!/usr/bin/env python3
"""Replace only existing branded share SVGs; never adds a share UI or changes destinations."""
import json,re,sys
from pathlib import Path
ICONS=json.loads((Path(__file__).parent/'share-icons/logos.json').read_text())
def patch(root):
 count=0
 for p in Path(root).rglob('*.html'):
  if any(x in p.parts for x in ['.git','tools','content']):continue
  text=p.read_text();old=text
  for name,label in [('X','Auf X teilen'),('LinkedIn','Auf LinkedIn teilen'),('WhatsApp','Per WhatsApp teilen'),('Facebook','Auf Facebook teilen'),('Reddit','Auf Reddit teilen')]:
   text=re.sub(r'(<a\b[^>]*aria-label="'+label+r'[^"]*"[^>]*>)<svg\b.*?</svg>',lambda m:m.group(1)+ICONS[name],text,flags=re.S)
  if text!=old:p.write_text(text);count+=1
 print('iconify share: updated',count,'pages')
if __name__=='__main__':patch(sys.argv[1])
