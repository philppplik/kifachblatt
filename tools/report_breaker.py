"""Server-rendered daily-report breaker, inserted between complete body blocks.
No JavaScript, storage, third-party assets or tracking. Idempotent final build pass.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

PDF = '/berichte/ki-tagesbericht.pdf'
BRAND = 'kfb'
CSS = """<style id="report-breaker-style">
.report-breaker{box-sizing:border-box;clear:both;display:block;margin:32px 0;padding:24px;border:1px solid var(--line);border-left:4px solid #7040cd;border-radius:12px;background:var(--bg2);color:var(--ink);max-width:100%;overflow-wrap:anywhere}
.report-breaker .rb-label{display:block;color:#7040cd;font:700 11px/1.4 system-ui,sans-serif;letter-spacing:.09em;text-transform:uppercase;margin:0 0 10px}
.report-breaker .rb-title{display:block;font:700 23px/1.25 system-ui,sans-serif;letter-spacing:-.02em;color:var(--ink);margin:0 0 10px}
.report-breaker p.rb-copy{font:400 15px/1.6 system-ui,sans-serif;margin:0 0 18px;color:var(--mute)}
.report-breaker a.rb-button{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:10px;max-width:100%;min-height:44px;padding:12px 18px;border:1px solid transparent;border-radius:8px;background:#7040cd;color:#fff!important;font:600 14px/1.4 system-ui,sans-serif;text-decoration:none!important;text-align:center}
.report-breaker a.rb-button:hover{filter:brightness(.92)}
.report-breaker a.rb-button:focus-visible{outline:3px solid #7040cd;outline-offset:4px}
.report-breaker small{display:block;font:400 12px/1.5 system-ui,sans-serif;margin-top:12px;color:var(--mute)}
@media(max-width:480px){.report-breaker{padding:20px 18px;margin:28px 0}.report-breaker .rb-title{font-size:21px}.report-breaker a.rb-button{width:100%}}
@media print{.report-breaker{display:none}}
</style>"""
BOX = ('<aside class="report-breaker" aria-label="Kostenloser Tagesbericht">'
       '<span class="rb-label">KI Fachblatt · Tagesbericht</span>'
       '<strong class="rb-title">Mehr Überblick. Auch offline.</strong>'
       '<p class="rb-copy">Modelle und KI-Artikel kompakt in der aktuellen Tagesausgabe.</p>'
       '<a class="rb-button" href="'+PDF+'">Tagesbericht gratis herunterladen <span aria-hidden="true">↓</span></a>'
       '<small>PDF · Kostenlos, ohne Anmeldung und ohne E-Mail. Ein Angebot von KI Fachblatt.</small></aside>')

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
    return text[:pos]+BOX+text[pos:]

def patch(html):
    if 'class="report-breaker"' in html: return html
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
    root=Path(out)
    candidates=sorted(root.glob('artikel/*/index.html')) if BRAND!='kfb' else sorted(root.glob('*.html'))
    changed=0
    for path in candidates:
        text=path.read_text()
        if BRAND=='kfb' and 'property="og:type" content="article"' not in text: continue
        new=patch(text)
        if new!=text: path.write_text(new); changed+=1
    print('Report breaker:',changed,'article pages updated')

if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.')
