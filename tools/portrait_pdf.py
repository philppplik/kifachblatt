"""Portrait downloads through the existing report_core Chrome pipeline. Stdlib only.
Each print view uses the exact portrait markup, local logos, full FAQs and sources.
No network requests; rendering failure never offers a stale PDF as current.
"""
import re, json, base64, hashlib, html
from pathlib import Path
from report_core import render, to_pdf, logo_inline
from daily_archive import valid_pdf

PRINT_CSS='''
@page:first{margin:16mm 15mm 18mm 15mm}
@page:first{@bottom-left{margin-left:0}@bottom-right{margin-right:0}}
body{--p-bg:#fff;--p-fg:#1a1c24;--p-muted:#4a4e5c;--p-line:#d9dfe9;--p-ac:ACCENT;--p-soft:SOFT}
.cover{margin:0 0 6mm;padding:6mm}.cover h1{margin-top:5mm;font-size:26pt}
.pg:first-of-type .wrap{padding:0}.pg{break-after:auto}.cover,.p-panel,.mr-answer,.mr-card,.co-block,.co-stat,.co-timeline li,.co-stack,.mr-visual,details{break-inside:avoid}
h1{font-size:25pt}h2,.mr h2,.co-rich h2{font-size:16pt;line-height:1.25;margin:6mm 0 3mm;break-after:avoid}h3,.mr h3,.co-block h3{font-size:11pt;break-after:avoid}
p,li,.mr p,.mr li,.co-block p,.p-panel p,.p-panel li,.co-repo{font-size:9.5pt;line-height:1.55}
.p-lead,.co-intro{font-size:11pt;line-height:1.6}.p-topline,.p-stand,.p-source,.co-foot,.co-ref,.mr-note{font-size:8pt!important;line-height:1.5;overflow-wrap:anywhere}
.p-layout{display:block;margin-top:5mm}.p-panel,.mr-answer,.mr-card,.co-block{padding:4mm;border:1px solid #d9dfe9;border-radius:3mm;margin-bottom:3mm}
.mr,.co-rich{margin:5mm 0}.mr-grid,.co-grid{display:grid;grid-template-columns:1fr 1fr;gap:4mm;margin:4mm 0}.mr-grid>*{margin:0}
.mr-stat{font-size:24pt;margin:2mm 0}.mr-unit{font-size:8pt}.mr-answer p{font-size:11pt}.mr-nav,.mr-related{display:none}
.mr-visual,.co-stack{padding:4mm;background:var(--p-soft);border-radius:3mm}.mr-visual svg{max-height:45mm}.co-stack svg{max-height:62mm}
.co-layers-text,.mr-textchart{display:none!important}.co-timeline{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;padding:0;list-style:none}.co-timeline li{padding:3mm;background:var(--p-soft);border-top:2px solid var(--p-ac)}.co-timeline b{display:block;font-size:14pt;margin-bottom:2mm}
.co-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm}.co-stat{padding:3mm;border:1px solid #d9dfe9}.co-stat strong{display:block;font-size:18pt}.co-stat span{font-size:8pt}
.co-models{display:grid;grid-template-columns:1fr 1fr;gap:2mm}.co-models a{font-size:9pt;padding:2mm;border:1px solid #d9dfe9}
.p-logo{display:block;width:45mm;height:15mm;margin:0 0 4mm}.p-logo img{width:100%;height:100%;object-fit:contain;object-position:left center}.p-logo-dark{background:#161616;padding:2mm}.p-logo-icon img{width:15mm}.p-avatar{display:inline-block;padding:3mm;background:var(--p-soft);font-weight:bold}
.p-facts{margin:0}.p-facts>div{padding:2mm 0;border-top:1px solid #d9dfe9;break-inside:avoid}.p-facts dt{font-size:8pt;color:#4a4e5c}.p-facts dd{margin:1mm 0;font-size:10pt;font-weight:bold}
details{border:1px solid #d9dfe9;padding:3mm;margin:3mm 0;border-radius:2mm}summary{font-weight:bold;font-size:10pt;list-style:none}details p{margin:2mm 0 0}a{overflow-wrap:anywhere}svg{display:block;width:100%;height:auto}table{table-layout:fixed}td,th{white-space:normal!important;overflow-wrap:anywhere}
.p-panel>ol.p-source{margin:0;padding-left:5mm}.p-panel>ol.p-source li{font-size:8pt;line-height:1.45;margin:0 0 1mm}.p-source{margin:2mm 0}.export-end{border-top:1px solid #d9dfe9;margin-top:5mm;padding-top:3mm;font-size:8pt;color:#4a4e5c}
@media screen{body{max-width:210mm;margin:20px auto;padding:16mm 15mm;box-shadow:0 2px 20px #ddd}.cover{margin-top:0}html{background:#eee}.print-btn{z-index:5}}
'''
BUTTON_CSS='''.p-export{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:22px 0}.p-export a{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:10px 16px;border:1px solid var(--p-ac);border-radius:8px;font-size:14px;font-weight:600;text-decoration:none}.p-export a:first-child{background:var(--p-ac);color:var(--p-bg)}.p-export small{flex-basis:100%;font-size:12px;color:var(--p-muted);line-height:1.6}@media(max-width:540px){.p-export a{flex:1 1 100%;text-align:center}}'''

def export(root,out,site,group,item,body,mark,note,source_url,reviewed,css):
 root=Path(root);out=Path(out);technical=site=='kfb';brand='KI Fachblatt' if technical else 'Intelligenz Welt'
 ac,dk,soft,line=('#7040cd','#3d2380','#f5f1fc','#dcd0f3') if technical else ('#1d6bc0','#093a6a','#eef5fc','#cfe0f3')
 folder='unternehmen' if group=='companies' else 'ki-modelle';stem=folder+'-'+item['slug'];dest=out/'portrait-pdf';dest.mkdir(exist_ok=True)
 # Fragment references remain local, all real links become absolute for offline readers.
 content=mark+note+re.sub(r'<div class="p-topline">.*?</div><h1>.*?</h1>','',body,count=1,flags=re.S)
 content=re.sub(r'<script\b[^>]*>.*?</script>','',content,flags=re.S)
 content=content.replace('<details>','<details open>')
 content=re.sub(r'<h2>Weiterlesen und vergleichen</h2><div class="mr-related">.*?</div>','',content,flags=re.S)
 base='https://kifachblatt.de' if technical else 'https://intelligenz-welt.de'
 content=re.sub(r'href="(/[^\"]*)"',lambda m:'href="'+base+m[1]+'"',content)
 def embed(m):
  f=out/m[1].lstrip('/');mime='image/svg+xml' if f.suffix=='.svg' else 'image/png'
  if not f.is_file():raise ValueError('Missing local portrait logo: '+str(f))
  return 'src="data:'+mime+';base64,'+base64.b64encode(f.read_bytes()).decode()+'"'
 content=re.sub(r'src="(/assets/portrait-logos/[^\"]+)"',embed,content)
 content+='<div class="export-end">'+html.escape(brand)+' · Redaktion: Philipp Paulik · Quellenstand: '+html.escape(reviewed)+'<br>Vollständiges Webportrait: <a href="'+html.escape(source_url)+'">'+html.escape(source_url)+'</a><br>Statischer Export, kein Live-Datenblatt. Preise, Zugriff und Anbieterangaben können sich ändern. Quellen und ihre jeweiligen Abrufstände stehen oben. <a href="'+base+('/impressum' if technical else '/impressum/')+'">Impressum</a> · <a href="'+base+('/transparenz' if technical else '/transparenz/')+'">Transparenz</a></div>'
 logo=logo_inline(str(root/'assets/logo.svg')) if technical else logo_inline(str(root/'content/branding/logo.svg'), '0 0 637 641')
 doc=render(brand,'Portrait',reviewed,ac,dk,soft,line,logo,item['name'],('Unternehmensportrait' if group=='companies' else 'KI-Modellportrait')+' · Quellenstand '+reviewed,[content],'')
 doc=doc.replace('<div class="pg last"><div class="wrap"></div></div>','')
 doc=doc.replace('</head>','<meta name="robots" content="noindex,follow"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="canonical" href="'+html.escape(source_url)+'"><style>'+css+PRINT_CSS.replace('ACCENT',ac).replace('SOFT',soft)+'</style></head>')
 hp=dest/(stem+'.html');pp=dest/(stem+'.pdf');hp.write_text(doc)
 # A matching sidecar permits repeat builds without dozens of redundant Chrome launches.
 digest=hashlib.sha256(doc.encode()).hexdigest();cache=dest/(stem+'.sha256')
 ok=valid_pdf(pp) and cache.exists() and cache.read_text()==digest
 if not ok:
  ok=to_pdf(str(hp),str(pp))
  if ok:cache.write_text(digest)
  else:
   pp.unlink(missing_ok=True);cache.unlink(missing_ok=True)
   print('::warning::Portrait PDF unavailable for '+stem+'; print view remains available')
 pdf='<a href="/portrait-pdf/'+stem+'.pdf" download>↓ Portrait als PDF</a>' if ok else ''
 return '<nav class="p-export" aria-label="Portrait exportieren">'+pdf+'<a href="/portrait-pdf/'+stem+'.html">Druckansicht / als PDF speichern</a><small>Mit Fakten, Quellen und Stand '+html.escape(reviewed)+'. Kostenlos, ohne Anmeldung. '+('PDF direkt herunterladen oder Druckansicht öffnen.' if ok else 'PDF-Download derzeit nicht verfügbar. In der Druckansicht „Als PDF speichern“ wählen.')+'</small></nav>'
