"""Text-only licensed RSS pilot and immutable local source-info archive. Stdlib only."""
import datetime
import email.utils
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

RIGHTS = {
 'heise': ('heise online', 'https://www.heise.de/news-extern/news.html', 'RSS-Anrisstext unverändert übernommen. Nutzung nach den RSS-Bedingungen von heise; die Erlaubnis ist widerruflich. Keine Bilder übernommen.'),
 'destatis': ('Statistisches Bundesamt (Destatis)', 'https://www.destatis.de/DE/Service/Impressum/copyright-allgemein.html', 'Quelle: Statistisches Bundesamt (Destatis), RSS-Pressemitteilung. Gelieferter RSS-Textauszug; keine inhaltliche Bearbeitung, Darstellung ohne HTML-Formatierung. Keine Bilder übernommen.'),
 'ecb': ('Europäische Zentralbank (EZB)', 'https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.de.html', 'Quelle: Europäische Zentralbank (EZB). Standard-Pressemitteilung aus dem offiziellen RSS-Feed; keine Übersetzung oder inhaltliche Bearbeitung. Die Informationen sind bei der EZB kostenlos verfügbar. Keine Bilder übernommen.'),
 'fn': ('FinanzNachrichten', 'https://www.finanznachrichten.de/service/rss.htm', 'Externe Schlagzeile mit direktem Quellenlink.')
}
FEEDS = {
 'heise': 'https://www.heise.de/rss/heise-atom.xml',
 'destatis': 'https://www.destatis.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/Aktuell.xml?nn=3624',
 'ecb': 'https://www.ecb.europa.eu/rss/press.html',
}
AI = re.compile(r'\b(?:KI|AI|LLMs?|GPT|ChatGPT|OpenAI|Claude|Gemini|Nvidia|Anthropic|DeepSeek|Robotik|Machine Learning)\b|künstlich.{0,3}Intelligenz', re.I)
MODE = {'fa': {'destatis', 'ecb', 'fn'}, 'iw': {'heise'}, 'kfb': {'heise'}}

class Text(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]; self.ignore=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'): self.ignore+=1
  if tag in ('p','br','div','li'): self.parts.append(' ')
 def handle_endtag(self,tag):
  if tag in ('script','style'): self.ignore=max(0,self.ignore-1)
  if tag in ('p','div','li'): self.parts.append(' ')
 def handle_data(self,data):
  if not self.ignore:self.parts.append(data)
def text(value):
 p=Text();p.feed(value or '');return re.sub(r'\s+',' ',''.join(p.parts)).strip()
def host(url):
 try:
  p=urllib.parse.urlsplit(url)
  return (p.hostname or '').lower().removeprefix('www.') if p.scheme=='https' and not p.username and not p.password else ''
 except ValueError:return ''
def matches(key,url):
 try:p=urllib.parse.urlsplit(url).path
 except ValueError:return False
 h=host(url)
 return bool((key=='heise' and h=='heise.de' and p.startswith('/news/') and p.endswith('.html')) or
  (key=='destatis' and h=='destatis.de' and re.fullmatch(r'/DE/Presse/Pressemitteilungen/\d{4}/\d{2}/PD\d+_[A-Za-z0-9_]+\.html',p)) or
  (key=='ecb' and h=='ecb.europa.eu' and re.fullmatch(r'/+press/pr/date/\d{4}/html/ecb\.pr[\w~.-]+\.html',p)) or
  (key=='fn' and h=='finanznachrichten.de'))
def valid(i,mode):
 return isinstance(i,dict) and i.get('license_key') in MODE[mode] and matches(i['license_key'],i.get('url','')) and isinstance(i.get('title'),str) and bool(i['title']) and len(i['title'])<=2000 and isinstance(i.get('teaser',''),str) and len(i.get('teaser',''))<=5000 and isinstance(i.get('ts'),(int,float)) and (i['license_key']!='fn' or not i.get('teaser'))
def detail_path(i):
 slug=unicodedata.normalize('NFKD',i['title']).encode('ascii','ignore').decode().lower()
 slug=re.sub('[^a-z0-9]+','-',slug).strip('-')[:76].rstrip('-') or 'meldung'
 return '/'+('nachrichten' if i.get('license_key') in ('fn','destatis','ecb') else 'news')+'/'+slug+'-'+hashlib.sha256(i['url'].encode()).hexdigest()[:12]+'/'
def parse_feed(data,key):
 root=ET.fromstring(data);ns='{http://www.w3.org/2005/Atom}'
 rows=root.findall('.//item') if key!='heise' else root.findall(ns+'entry');out=[]
 for row in rows:
  if key=='heise':
   title=text(row.findtext(ns+'title'));link=next((x.get('href','') for x in row.findall(ns+'link') if x.get('rel','alternate')=='alternate'),'');summary=row.findtext(ns+'summary') or '';stamp=row.findtext(ns+'published') or row.findtext(ns+'updated') or ''
  else:
   title=text(row.findtext('title'));link=(row.findtext('link') or '').strip();summary=row.findtext('description') or '';stamp=row.findtext('pubDate') or ''
  # Only direct official feeds can supply a teaser. Existing aggregator snippets never enter this archive.
  if not matches(key,link) or not title or (key=='heise' and (not AI.search(title) or re.search(r'heise-Angebot|Webinar|Anzeige|Gesponsert|Rabatt',title,re.I))):continue
  if row.findtext('author') or row.find('{http://purl.org/dc/elements/1.1/}creator') is not None:continue
  try:ts=(datetime.datetime.fromisoformat(stamp.replace('Z','+00:00')) if key=='heise' else email.utils.parsedate_to_datetime(stamp)).timestamp()
  except (ValueError,TypeError,AttributeError):continue
  teaser=text(summary)
  if len(teaser)>5000:continue
  now=datetime.datetime.now(datetime.timezone.utc).isoformat()
  out.append(dict(title=title,url=link,ts=ts,src=RIGHTS[key][0],sum='',teaser=teaser,license_key=key,feed_url=FEEDS[key],captured_at=now,rights_checked='2026-10-19'))
 return out

def collect(root,mode,existing=(),fetch=True):
 root=Path(root);store=root/'data/news-pages.json'
 if store.exists():
  # Do not overwrite or hide a damaged permanent archive.
  old=json.loads(store.read_text())
  if not isinstance(old,list) or any(not valid(i,mode) for i in old):raise ValueError('Invalid persistent news archive: '+str(store))
 else:old=[]
 by_url={i['url']:i for i in old};fresh=[]
 if mode=='fa':
  for i in existing:
   if matches('fn',i.get('url','')):
    fresh.append(dict(title=i['title'],url=i['url'],ts=i.get('ts',0),src='FinanzNachrichten',sum='',teaser='',license_key='fn',captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),rights_checked='2026-10-19'))
 if fetch:
  for key in sorted(MODE[mode]-{'fn'}):
   try:
    req=urllib.request.Request(FEEDS[key],headers={'User-Agent':'Mozilla/5.0 (compatible; LicensedNewsPilot/1.0)'})
    with urllib.request.urlopen(req,timeout=20) as r:data=r.read(2_000_001)
    if len(data)>2_000_000:raise ValueError('RSS response too large')
    fresh+=parse_feed(data,key)
   except Exception as e:print('::warning::Licensed RSS '+key+' unavailable; keeping saved source-info pages: '+type(e).__name__)
 for i in fresh:
  if valid(i,mode) and i['url'] not in by_url:by_url[i['url']]=i
 rows=sorted(by_url.values(),key=lambda x:(-x['ts'],x['url']))
 store.parent.mkdir(exist_ok=True);tmp=store.with_suffix('.json.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');tmp.replace(store)
 return rows

def merge_current(current,archive):
 by_url={i['url']:i for i in current}
 for i in archive:by_url[i['url']]=i
 return sorted(by_url.values(),key=lambda i:-i.get('ts',0))

def evidence(i):
 key=i['license_key'];name,url,note=RIGHTS[key];e=lambda s:html.escape(str(s),quote=True)
 date=datetime.datetime.fromtimestamp(i['ts'],datetime.timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Europe/Berlin')).strftime('%d.%m.%Y, %H:%M')
 return '<p class="ln-rights">%s <a href="%s" target="_blank" rel="noopener noreferrer nofollow">Nutzungsbedingungen ↗</a><br>Fundstelle: <a href="%s" target="_blank" rel="noopener noreferrer nofollow">%s</a>, veröffentlicht %s. Gesichert am %s.</p>'%(e(note),e(url),e(i['url']),e(name),date,e(i.get('captured_at','')[:10]))

def body(i,brand,archive_url='/news/'):
 e=lambda s:html.escape(str(s),quote=True);name=RIGHTS[i['license_key']][0];url=e(i['url'])
 original='<a class="ln-original" href="%s" target="_blank" rel="noopener noreferrer nofollow">Original bei %s lesen <span aria-hidden="true">↗</span></a>'%(url,e(name))
 return '''<link rel="stylesheet" href="/licensed-news.css"><main class="ln-wrap" id="main"><a class="ln-back" href="%s">← Zum Quellenarchiv</a><section class="ln-card"><p class="ln-kicker">EXTERNE MELDUNG / QUELLENINFO</p><p class="ln-source">%s</p><h1>%s</h1><p class="ln-disclosure">Eine externe Meldung, kein eigener Artikel von %s. Den vollständigen Beitrag findest du beim Originalanbieter.</p><aside class="ln-leaving"><span aria-hidden="true">↗</span><p>Beim Klick auf den Original-Link verlässt du %s und wechselst zu <strong>%s</strong>. Der Beitrag öffnet sich in einem neuen Tab.</p></aside>%s%s%s</section><aside class="ln-report"><p class="ln-kicker">DER TAGESÜBERBLICK</p><h2>Dein Tagesbericht als PDF.</h2><p>Kostenlos, ohne Anmeldung und ohne E-Mail.</p><a href="/berichte/">Zum Tagesbericht und PDF-Archiv →</a></aside><section class="ln-card ln-bottom"><h2>Zur vollständigen Meldung</h2>%s<p>Es gelten die Bedingungen des Anbieters. %s ist nicht mit der Quelle verbunden.</p></section></main>'''%(archive_url,e(name),e(i['title']),e(brand),e(brand),e(host(i['url'])),original,('<p class="ln-teaser">'+e(i['teaser'])+'</p>') if i.get('teaser') else '',evidence(i),original,e(brand))

def archive_body(rows,brand):
 e=lambda s:html.escape(str(s),quote=True)
 cards=''.join('<li><p>%s · %s</p><h2><a href="%s">%s →</a></h2><a class="ln-direct" href="%s" target="_blank" rel="noopener noreferrer nofollow">Direkt zum Original ↗</a></li>'%(e(RIGHTS[i['license_key']][0]),datetime.datetime.fromtimestamp(i['ts'],datetime.timezone.utc).strftime('%d.%m.%Y'),detail_path(i),e(i['title']),e(i['url'])) for i in rows)
 return '<link rel="stylesheet" href="/licensed-news.css"><main class="ln-wrap" id="main"><section class="ln-card"><p class="ln-kicker">QUELLENARCHIV / TEXT-PILOT</p><h1>KI-News aus externen Quellen.</h1><p>Schlagzeilen und erlaubte RSS-Anrisstexte von heise online. Mit direktem Original-Link, ohne übernommene Bilder. Die Quelleninfos bleiben unter ihrer festen Adresse gespeichert.</p><a href="/">← Zur Startseite</a></section><ul class="ln-list">'+cards+'</ul></main>'

CSS='''
.ln-wrap{--ln-ac:var(--ac,#7454b9);--ln-bg:var(--p,#fff);--ln-soft:var(--p2,#f6f5f9);--ln-ink:var(--hd,#1d1925);--ln-mut:var(--mut,#686473);--ln-line:var(--b,#e1dee8);max-width:980px;margin:auto;padding:36px 24px 64px;color:var(--ln-ink)}
.ln-wrap *{box-sizing:border-box}.ln-back{display:inline-block;font-size:13px;margin-bottom:24px;color:var(--ln-mut)}.ln-card,.ln-report,.ln-list li{background:var(--ln-bg);border:1px solid var(--ln-line);border-radius:16px;padding:32px;margin:0 0 22px}.ln-kicker{color:var(--ln-ac);font-weight:700;font-size:11px;letter-spacing:.1em;margin:0 0 18px}.ln-source{font-size:13px;color:var(--ln-mut)}.ln-wrap h1{font-size:clamp(28px,4vw,42px);line-height:1.18;letter-spacing:-.025em;margin:18px 0;overflow-wrap:anywhere}.ln-disclosure{font-size:15px;line-height:1.7;color:var(--ln-mut)}.ln-leaving{display:flex;gap:10px;background:var(--ln-soft);border:1px solid var(--ln-line);border-radius:9px;padding:12px 14px;margin:20px 0 14px;font-size:12px;line-height:1.6;color:var(--ln-mut)}.ln-leaving>span{color:var(--ln-ac);font-size:17px;flex:none}.ln-leaving p{margin:0;min-width:0;overflow-wrap:anywhere}.ln-original{display:inline-flex;align-items:center;justify-content:space-between;gap:16px;background:var(--ln-ac);color:#fff!important;padding:13px 18px;border-radius:8px;font-size:14px;font-weight:700;max-width:100%;text-decoration:none!important;overflow-wrap:anywhere}.ln-original:focus-visible,.ln-wrap a:focus-visible{outline:3px solid var(--ln-ac);outline-offset:3px}.ln-teaser{font-size:18px;line-height:1.75;margin:24px 0;color:var(--ln-ink)}.ln-rights{font-size:12px;color:var(--ln-mut);line-height:1.7;margin:24px 0 0;overflow-wrap:anywhere}.ln-rights a,.ln-report a,.ln-direct{color:var(--ln-ac);text-decoration:underline;text-underline-offset:3px}.ln-report{background:var(--ln-soft)}.ln-wrap h2{font-size:24px;line-height:1.3;margin:0 0 14px}.ln-bottom>p{color:var(--ln-mut);font-size:12px;margin-top:18px}.ln-list{list-style:none;margin:0;padding:0}.ln-list li>p{color:var(--ln-mut);font-size:12px}.ln-list h2 a{color:var(--ln-ink);text-decoration:none}.ln-list h2 a:hover{color:var(--ln-ac)}.ln-direct{font-size:13px}.ln-list h2{font-size:23px;overflow-wrap:anywhere}@media(max-width:640px){.ln-wrap{padding:24px 16px 40px}.ln-card,.ln-report,.ln-list li{padding:22px 18px;border-radius:12px}.ln-original{display:flex;width:100%;font-size:13px;padding:13px}.ln-teaser{font-size:17px}.ln-wrap h2{font-size:22px}}
'''

def noindex(target):
 p=Path(target);s=p.read_text();s=re.sub(r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>','<meta name="robots" content="noindex,follow">',s);s=re.sub(r'<link rel="canonical"[^>]*>','',s);p.write_text(s)
def write_css(out):
 p=Path(out)/'licensed-news.css';p.write_text(CSS)
