"""Server-rendered daily-report breaker, inserted between complete body blocks.
No JavaScript, storage, third-party assets or tracking. Idempotent final build pass.
The right-hand PDF mockup reuses the real preview the report build already renders.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

PDF = '/berichte/ki-tagesbericht.pdf'
BRAND = 'kfb'
MOCK_ALT = 'Erste Seite des aktuellen KI-Tagesberichts vom KI Fachblatt als PDF-Vorschau'
MOCK_ARIA = 'KI-Tagesbericht als PDF öffnen (Vorschau der ersten Seite)'
CSS = """<style id="report-breaker-style">
.report-breaker{box-sizing:border-box;clear:both;display:flex;align-items:center;gap:26px;margin:32px 0;padding:24px;border:1px solid var(--line);border-radius:12px;background:var(--bg2);color:var(--ink);max-width:100%;overflow-wrap:anywhere}
.report-breaker .rb-text{flex:1 1 auto;min-width:0}
.report-breaker .rb-label{display:block;color:#7040cd;font:700 11px/1.4 system-ui,sans-serif;letter-spacing:.09em;text-transform:uppercase;margin:0 0 10px}
.report-breaker .rb-title{display:block;font:700 23px/1.25 system-ui,sans-serif;letter-spacing:-.02em;color:var(--ink);margin:0 0 10px}
.report-breaker p.rb-copy{font:400 15px/1.6 system-ui,sans-serif;margin:0 0 18px;color:var(--mute)}
.report-breaker a.rb-button{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:10px;max-width:100%;min-height:44px;padding:12px 18px;border:1px solid transparent;border-radius:8px;background:#7040cd;color:#fff!important;font:600 14px/1.4 system-ui,sans-serif;text-decoration:none!important;text-align:center}
.report-breaker a.rb-button:hover{filter:brightness(.92)}
.report-breaker a.rb-button:focus-visible{outline:3px solid #7040cd;outline-offset:4px}
.report-breaker small{display:block;font:400 12px/1.5 system-ui,sans-serif;margin-top:12px;color:var(--mute)}
.report-breaker a.rb-mock{flex:0 0 auto;display:block;margin:6px 16px 6px 0;transform:rotate(3deg);transition:transform .18s ease-out;line-height:0}
.report-breaker a.rb-mock:hover{transform:rotate(1.4deg)}
.report-breaker a.rb-mock img{display:block;width:148px;height:auto;border-radius:4px;background:#fff;box-shadow:0 0 0 1px rgba(12,18,32,.10),0 4px 10px rgba(12,18,32,.16),0 14px 30px rgba(12,18,32,.22)}
.report-breaker a.rb-mock:focus-visible{outline:3px solid #7040cd;outline-offset:6px}
@media(max-width:640px){.report-breaker{gap:18px}.report-breaker a.rb-mock{margin-right:12px}.report-breaker a.rb-mock img{width:124px}}
@media(max-width:480px){.report-breaker{flex-direction:column;align-items:stretch;padding:20px 18px;margin:28px 0}.report-breaker .rb-title{font-size:21px}.report-breaker a.rb-button{width:100%}.report-breaker a.rb-mock{align-self:center;margin:4px 0 2px;transform:rotate(2.5deg)}.report-breaker a.rb-mock img{width:132px}}
.report-breaker a.rb-mock img.rb-p2{display:none}
@media(max-width:480px){.report-breaker a.rb-mock.rb-mocks{order:-1;display:flex;justify-content:center;align-items:flex-start;align-self:center;margin:0 0 4px;transform:none}.report-breaker a.rb-mock.rb-mocks:hover{transform:none}.report-breaker a.rb-mock img.rb-p1{width:112px;position:relative;z-index:1;transform:rotate(-3.5deg);transform-origin:bottom right}.report-breaker a.rb-mock img.rb-p2{display:block;width:112px;margin:18px 0 0 -40px;transform:rotate(4deg)}}
@media print{.report-breaker{display:none}}
</style>"""

# Compact thumbnail rendered by the report build; the full page-1.jpg is the fallback.
PREVIEW = ('page-1.jpg', 707, 1000)
PREVIEW2 = None

def second():
    if not PREVIEW2: return ''
    n, w, h = PREVIEW2
    return '<img class="rb-p2" src="/assets/report-preview/'+n+'" width="'+str(w)+'" height="'+str(h)+'" alt="'+MOCK_ALT.replace('Erste','Zweite').replace('der ersten','der zweiten')+'" loading="lazy" decoding="async">'

def box():
    name, w, h = PREVIEW
    return ('<aside class="report-breaker" aria-label="Kostenloser Tagesbericht">'
       '<div class="rb-text">'
       '<span class="rb-label">KI Fachblatt · Tagesbericht</span>'
       '<strong class="rb-title">Mehr Überblick. Auch offline.</strong>'
       '<p class="rb-copy">Modelle und KI-Artikel kompakt in der aktuellen Tagesausgabe.</p>'
       '<a class="rb-button" href="'+PDF+'">Tagesbericht gratis herunterladen <span aria-hidden="true">↓</span></a>'
       '<small>PDF · Kostenlos, ohne Anmeldung und ohne E-Mail. Ein Angebot von KI Fachblatt.</small></div>'
       '<a class="rb-mock rb-mocks" href="'+PDF+'" aria-label="'+MOCK_ARIA+'"><img class="rb-p1" src="/assets/report-preview/'+name+'" width="'+str(w)+'" height="'+str(h)+'" alt="'+MOCK_ALT+'" loading="lazy" decoding="async">'+second()+'</a></aside>')

STYLE_RE = re.compile(r'<style id="report-breaker-style">.*?</style>', re.S)
BOX_RE = re.compile(r'<aside class="report-breaker".*?</aside>', re.S)

def upgrade(html):
    """Swap a breaker from an earlier generation for the current markup and style."""
    new = BOX_RE.sub(lambda m: box(), html, count=1)
    if STYLE_RE.search(new): return STYLE_RE.sub(lambda m: CSS, new, count=1)
    return new.replace('</head>', CSS+'</head>', 1)

class Blocks(HTMLParser):
    """Record only complete, direct children, never nested paragraphs or cells."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text=text; self.stack=[]; self.blocks=[]; self.start=0; self.tag=''
        self.lines=[0]+[m.end() for m in re.finditer('\n',text)]
    def position(self):
        line,col=self.getpos(); return self.lines[line-1]+col
    def handle_starttag(self, tag, attrs):
        if tag in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'): return
        if not self.stack: self.start=self.position(); self.tag=tag
        self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag not in self.stack: return
        while self.stack:
            if self.stack.pop()==tag: break
        if not self.stack: self.blocks.append((self.start,self.position()+len('</'+tag+'>'),self.tag))

def inject_body(text):
    if 'class="report-breaker"' in text: return text
    p=Blocks(text); p.feed(text)
    blocks=p.blocks
    if len(blocks)<2: return text
    # Prefer a section boundary near the middle. Do not strand a heading from its text.
    mid=len(text)/2
    options=[b[0] for b in blocks[1:] if b[2]=='h2']
    if not options: options=[blocks[i][0] for i in range(1,len(blocks)) if blocks[i-1][2] not in ('h2','h3')]
    if not options: return text
    pos=min(options,key=lambda x:abs(x-mid))
    return text[:pos]+box()+text[pos:]

def patch(html):
    if 'rb-mocks' in html: return html
    if 'class="report-breaker"' in html: return upgrade(html)
    match=re.search(r'<div class="body"[^>]*>',html)
    if not match: return html
    start=match.end()
    # A synthetic wrapper gives the exact closing div, even with nested tables/callouts.
    depth=1; end=None
    for m in re.finditer(r'<div\b[^>]*>|</div\s*>',html[start:],re.I):
        depth += -1 if m.group().startswith('</') else 1
        if depth==0: end=start+m.start(); break
    if end is None: return html
    body=html[start:end]
    # Legacy hand-written pages keep FAQ/sources in the body container: leave them below the CTA.
    cutoff=re.search(r'<(?:h2|div|section)\b[^>]*(?:id="(?:faq|quellen)"|class="(?:faq|refs)")',body)
    stop=cutoff.start() if cutoff else len(body)
    new=inject_body(body[:stop])+body[stop:]
    if new==body: return html
    return (html[:start]+new+html[end:]).replace('</head>',CSS+'</head>',1)

def main(out):
    global PREVIEW
    root=Path(out)
    if (root/'assets/report-preview/breaker-thumb.jpg').is_file():
        PREVIEW=('breaker-thumb.jpg',297,420)
    global PREVIEW2
    if (root/'assets/report-preview/breaker-thumb2.jpg').is_file(): PREVIEW2=('breaker-thumb2.jpg',297,420)
    elif (root/'assets/report-preview/page-2.jpg').is_file(): PREVIEW2=('page-2.jpg',707,1000)
    candidates=sorted(root.glob('artikel/*/index.html')) if BRAND!='kfb' else sorted(root.glob('*.html'))
    changed=0
    for path in candidates:
        text=path.read_text()
        if BRAND=='kfb' and 'property="og:type" content="article"' not in text: continue
        new=patch(text)
        if new!=text: path.write_text(new); changed+=1
    print('Report breaker:',changed,'article pages updated')

if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.')
