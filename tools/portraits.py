#!/usr/bin/env python3
"""Versioned, sourced portraits. Stdlib only. No network calls during rendering.
Usage: python3 tools/portraits.py [kfb|iw] [output-directory]
"""
import sys,json,re,html,os,shutil
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
E=lambda s:html.escape(str(s),quote=True)
# Portable Datumsableitung (Patch 2026-10-31): Standard ist d['reviewed'];
# pro Eintrag optional x['checked'] (Pruefstand), x['published'] (datePublished),
# pro Score die accessed-Angabe der jeweiligen Quelle, aber nur bei Eintraegen mit
# explizitem 'checked'. Altdaten ohne diese Felder rendern unveraendert
# (IW reviewed 2026-10-19, KIFB reviewed 2026-10-20).
MONTHS=['','Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']
def fmt_de(iso):
 y,m,dd=str(iso).split('-');return '%d. %s %s'%(int(dd),MONTHS[int(m)],y)
def fmt_dot(iso):
 y,m,dd=str(iso).split('-');return '%d.%d.%s'%(int(dd),int(m),y)
CSS='''
/* Sourced portrait directory */
.portraits{padding-top:34px;padding-bottom:48px}.portraits h1{font-size:clamp(32px,5vw,56px);line-height:1.1;letter-spacing:-.03em;margin:16px 0}.portraits .p-lead{font-size:19px;max-width:760px;color:var(--p-muted);line-height:1.6}.p-topline{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--p-ac)}.p-tabs{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}.p-tabs a{font-size:13px;border:1px solid var(--p-line);border-radius:999px;padding:8px 15px;text-decoration:none}.p-tabs a[aria-current=page],.p-tabs a:hover{background:var(--p-fg);color:var(--p-bg)}.p-note{border:1px solid rgba(127,127,127,.28);background:var(--p-soft);padding:15px 18px;font-size:13px;line-height:1.6;margin:24px 0;color:var(--p-muted)}.p-filter{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin:28px 0 18px}.p-filter label{font-size:12px;display:flex;flex-direction:column;gap:6px}.p-filter label:first-child{flex:1;min-width:180px}.p-filter input,.p-filter select{font:inherit;font-size:15px;min-height:44px;border:1px solid var(--p-line);border-radius:8px;padding:9px 12px;background:var(--p-bg);color:var(--p-fg);width:100%}.p-filter input:focus-visible,.p-filter select:focus-visible{outline:3px solid var(--p-ac);outline-offset:2px}.p-count{font-size:12px;color:var(--p-muted)}.p-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.p-card{border:1px solid var(--p-line);padding:24px;border-radius:14px;min-width:0;background:var(--p-bg)}.p-logo{display:inline-flex;width:160px;height:64px;align-items:center;justify-content:flex-start;vertical-align:middle;margin:4px 0 12px;background:#fff;flex:none}.p-logo img{display:block;width:100%;height:100%;object-fit:contain;object-position:left center}.p-logo-dark{background:#161616;padding:12px}.p-card .p-type{display:block;margin:0}.p-logo+.p-source{max-width:720px}.p-card:hover{border-color:var(--p-ac)}.p-card h2{font-size:21px;line-height:1.25;margin:14px 0 10px;letter-spacing:-.02em}.p-card h2 a{text-decoration:none}.p-card p{font-size:14px;color:var(--p-muted);margin:10px 0 18px}.p-avatar{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;background:var(--p-soft);color:var(--p-ac);border:1px solid var(--p-line);border-radius:12px;font-size:14px;font-weight:800}.p-type{font-size:11px;color:var(--p-muted);margin-left:10px}.p-link{font-size:13px;color:var(--p-ac);text-decoration:none}.p-layout{display:grid;grid-template-columns:minmax(0,2fr) minmax(230px,1fr);gap:32px;align-items:start;margin-top:32px}.p-panel{border:1px solid var(--p-line);border-radius:14px;padding:24px;margin-bottom:22px}.p-panel h2{margin:0 0 14px;font-size:21px;line-height:1.3}.p-panel p,.p-panel li{font-size:15px;line-height:1.75}.p-panel ul{padding-left:20px}.p-panel a{text-decoration:underline;text-underline-offset:3px}.p-facts{margin:0}.p-facts>div{padding:12px 0;border-top:1px solid var(--p-line)}.p-facts dt{font-size:12px;color:var(--p-muted)}.p-facts dd{font-size:15px;font-weight:600;margin:4px 0 0;overflow-wrap:anywhere}.p-source{font-size:12px!important;color:var(--p-muted);overflow-wrap:anywhere}.p-source li{font-size:13px}.p-scores{overflow:auto}.p-scores table{width:100%;font-size:14px;border-collapse:collapse}.p-scores th,.p-scores td{padding:12px;text-align:left;border-bottom:1px solid var(--p-line);vertical-align:top;min-width:110px}.p-scores td:first-child{width:auto}.p-scores td:last-child{min-width:200px}.p-scores td,.p-scores th{white-space:normal!important}.p-scores small{display:block;white-space:normal;font-size:12px;color:var(--p-muted);max-width:380px}[data-portrait-footer] a{display:inline!important}[data-portrait-footer]{font-size:12px}.p-empty{padding:24px;border:1px dashed var(--p-line);border-radius:12px;color:var(--p-muted)}.p-home{margin:30px auto;padding-top:24px;padding-bottom:24px;border-top:1px solid var(--p-line);border-bottom:1px solid var(--p-line)}.p-home h2{font-size:23px;margin:0 0 8px}.p-home p{font-size:14px;color:var(--p-muted);margin:8px 0}.p-home .p-tabs{margin:16px 0 0}.p-breadcrumb{font-size:12px;color:var(--p-muted)}.p-breadcrumb a{text-decoration:none}.p-stand{font-size:12px;color:var(--p-muted);margin-top:20px}
@media(max-width:900px){.p-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.p-layout{grid-template-columns:minmax(0,1fr);gap:0}}
@media(max-width:540px){.p-grid{grid-template-columns:minmax(0,1fr)}.p-card,.p-panel{padding:20px}.portraits{padding-top:24px}.portraits .p-lead{font-size:17px}.p-filter label{flex:1;min-width:100%}.p-tabs{gap:8px}.p-tabs a{font-size:12px;padding:8px 12px}}
'''
FILTER_JS='''(function(){var q=document.getElementById('pq'),s=document.getElementById('pc'),a=Array.from(document.querySelectorAll('[data-portrait]')),count=document.getElementById('pcount'),empty=document.getElementById('pempty');if(!q)return;function n(t){return t.toLocaleLowerCase('de').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')}function f(){var term=n(q.value),c=s?s.value:'';var hits=0;a.forEach(function(x){var ok=n(x.textContent).includes(term)&&(!c||x.dataset.company===c);x.hidden=!ok;if(ok)hits++});count.textContent=hits+' von '+a.length+' Portraits';empty.hidden=hits!==0}q.addEventListener('input',f);if(s)s.addEventListener('change',f);f()})();'''
KINDS={'companies':('Unternehmen','unternehmen'),'models':('KI-Modelle','ki-modelle'),'benchmarks':('Benchmarks','benchmarks')}
def validate(d):
 assert d['schema_version']==1
 for group in ['companies','models','benchmarks']:
  slugs=[x['slug'] for x in d[group]]; assert len(slugs)==len(set(slugs))
  for x in d[group]:
   assert re.fullmatch('[a-z0-9-]+',x['slug']) and x['name'] and x['summary'] and x['sources']
   assert all(k in d['sources'] for k in x['sources'])
   for f in x.get('facts',[]): assert f['source'] in d['sources'] and f['value']
 for s in d['sources'].values(): assert urlparse(s['url']).scheme=='https' and s['accessed']
 for m in d['models']: assert m['company'] in {c['slug'] for c in d['companies']}
 for s in d['scores']:
  assert s['source'] in d['sources'] and s['model'] in {m['slug'] for m in d['models']} and s['benchmark'] in {b['slug'] for b in d['benchmarks']}
def logo_manifest():
 return json.loads((ROOT/'content/portrait-logos/manifest.json').read_text())
def portrait_mark(x,detail=False):
 logo=x.get('logo');manifest=logo_manifest()
 if not logo or logo['asset'] not in manifest:
  return '<span class="p-avatar" aria-hidden="true">'+E(x['initials'])+'</span>'
 key=logo['asset'];asset=manifest[key]
 cls=' p-logo-dark' if key=='nvidia' else ' p-logo-icon' if key=='openai-blossom' else ''
 return '<span class="p-logo%s"><img src="/assets/portrait-logos/%s" alt="%s" width="160" height="64" decoding="async"></span>'%(cls,E(asset['file']),E(logo['label']))
def logo_note(x):
 logo=x.get('logo')
 if logo and not logo.get('asset'):return '<p class="p-source">'+E(logo.get('label',''))+' Monogramm-Darstellung, kein Logo-Asset übernommen.</p>'
 if not logo:return '<p class="p-source">Monogramm: kein eindeutig zugeordnetes Modelllogo in der geprüften Auswahl.</p>' if x.get('company') else ''
 asset=logo_manifest()[logo['asset']]
 return '<p class="p-source">%s · <a href="%s">Logo-Quelle / Rechtehinweis</a>. Marken gehören ihren jeweiligen Inhabern. Redaktionelle Identifikation, keine Partnerschaft oder Empfehlung durch den Markeninhaber.</p>'%(E(logo['label']),E(asset['source']))
def render(site,out):
 d=json.loads((ROOT/'content/portraits.json').read_text());validate(d)
 from portrait_pdf import export as export_pdf, BUTTON_CSS
 from model_rich import render as rich_model, CSS as MODEL_CSS
 from portrait_snapshots import archive
 archive(d)
 from company_rich import render as rich_company, CSS as COMPANY_CSS, ecosystem
 out=Path(out);technical=site=='kfb';base='https://kifachblatt.de' if technical else 'https://intelligenz-welt.de';brand='KI Fachblatt' if technical else 'Intelligenz Welt';wrap='wrap' if technical else 'w'
 groups=['companies','models']+(['benchmarks'] if technical else [])
 def path(group,slug=''):
  p='/'+KINDS[group][1]+('/'+slug if slug else '')
  return p if technical else p+'/'
 def target(p):return out/(p.strip('/')+'.html' if technical else p.strip('/')+'/index.html')
 template=(out/('halluzinationen.html' if technical else 'impressum/index.html')).read_text()
 if technical:
  shell_top=template[template.index('<body>'):template.index('<main id="main">')];foot=template[template.index('</main>')+7:]
 else:
  i=template.index('</header>')+9
  if template.startswith('<script>',i):i=template.index('</script>',i)+9
  shell_top=template[template.index('<body>'):i];foot=template[template.index('<footer',i):]
 tokens=':root{--p-bg:var(--bg);--p-fg:var(--ink);--p-muted:var(--mute);--p-line:var(--line);--p-ac:var(--amber);--p-soft:var(--bg2)}' if technical else ':root{--p-bg:var(--bg);--p-fg:var(--fg);--p-muted:var(--mut);--p-line:var(--line);--p-ac:var(--ac);--p-soft:var(--soft)}'
 (out/'assets').mkdir(exist_ok=True);shutil.rmtree(out/'assets/portrait-logos',ignore_errors=True);shutil.copytree(ROOT/'content/portrait-logos',out/'assets/portrait-logos',dirs_exist_ok=True)
 css=CSS
 if 'openai-blossom' in logo_manifest():css=css.replace('.p-logo-dark','.p-logo-icon img{width:56px;height:56px;object-fit:contain}.p-logo-dark',1)
 (out/'assets/portraits.css').write_text(tokens+css+COMPANY_CSS+MODEL_CSS+BUTTON_CSS);(out/'assets/portraits.js').write_text(FILTER_JS)
 def tabs(group=''):
  return '<nav class="p-tabs" aria-label="Portrait-Bereiche">'+''.join('<a href="%s"%s>%s</a>'%(path(g),' aria-current="page"' if g==group else '',KINDS[g][0]) for g in groups)+'</nav>'
 def refs(keys):
  return '<section class="p-panel"><h2>Quellen &amp; Stand</h2><ol class="p-source">'+''.join('<li><a href="%s" rel="noopener">%s</a><br>Geprüft: %s</li>'%(E(d['sources'][k]['url']),E(d['sources'][k]['title']),d['sources'][k]['accessed']) for k in dict.fromkeys(keys))+'</ol><p class="p-source">Redaktionelle Zusammenfassung mit KI-Unterstützung, verantwortet von Philipp Paulik. Kein eigener Leistungstest. Änderbare Anbieterangaben gelten für den angegebenen Quellenstand.</p></section>'
 def page(p,title,desc,inner,ld):
  h=template[:template.index('<body>')]
  h=re.sub(r'<title>.*?</title>','<title>'+E(title+' | '+brand)+'</title>',h,flags=re.S)
  h=re.sub(r'<script type="application/ld\+json">.*?</script>','',h,flags=re.S)
  h=re.sub(r'<meta (?:name="description"|property="og:[^"]*"|name="twitter:[^"]*")[^>]*>','',h)
  h=re.sub(r'<link rel="canonical"[^>]*>','',h)
  ldscript=json.dumps(ld,ensure_ascii=False).replace('</','<\\/')
  extra='<meta name="description" content="%s"><link rel="canonical" href="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><link rel="stylesheet" href="/assets/portraits.css"><script type="application/ld+json">%s</script>'%(E(desc),base+p,E(title),E(desc),base+p,ldscript)
  h=h.replace('</head>',extra+'</head>')
  body='<main id="main"><div class="%s portraits">%s</div></main>'%(wrap,inner)
  t=target(p);t.parent.mkdir(parents=True,exist_ok=True);t.write_text(h+shell_top+body+foot)
 def card(g,x):
  co=next((c['name'] for c in d['companies'] if c['slug']==x.get('company')),KINDS[g][0])
  return '<article class="p-card" data-portrait data-company="%s">%s<span class="p-type">%s</span><h2><a href="%s">%s</a></h2><p>%s</p><a class="p-link" href="%s">Portrait lesen →</a></article>'%(E(x.get('company','')),portrait_mark(x),E(co),path(g,x['slug']),E(x['name']),E(x['summary']),path(g,x['slug']))
 docs=[];urls=[]
 for g in groups:
  label=KINDS[g][0];p=path(g);intro={'companies':'Wer entwickelt KI? Unternehmen und Forschungseinheiten, ihre Modelle und ihre Schwerpunkte.','models':'Konkrete KI-Modelle statt bloßer Produktnamen: Aufgaben, Zugang und Grenzen, mit Quellen.','benchmarks':'Was misst ein Benchmark, und was nicht? Methoden und Grenzen verständlich erklärt.'}[g]
  selection='<label>Anbieter<select id="pc"><option value="">Alle Anbieter</option>'+''.join('<option value="%s">%s</option>'%(c['slug'],E(c['name'])) for c in d['companies'])+'</select></label>' if g=='models' else ''
  checks=sorted({(x.get('rich_model') or {}).get('checked') or x.get('checked') or d['reviewed'] for x in d[g]})
  stand='Quellenstand: %s.'%fmt_de(checks[0]) if len(checks)==1 else 'Prüfstand je Portrait unterschiedlich: ältester %s, neuester %s; das jeweilige Datum steht auf der Porträtseite.'%(fmt_de(checks[0]),fmt_de(checks[-1]))
  inner=('<div class="p-topline">Das KI-Verzeichnis · Quellen statt Hype</div><h1>%s</h1><p class="p-lead">%s</p>%s<p class="p-note">'+stand+' Anbieterangaben sind keine unabhängigen Messergebnisse.</p><div class="p-filter"><label>Portraits durchsuchen<input id="pq" type="search" placeholder="Name, Aufgabe oder Begriff …"></label>%s</div><p id="pcount" class="p-count" role="status">%d Portraits</p><div class="p-grid">%s</div><p id="pempty" class="p-empty" hidden>Keine passenden Portraits. Versuche einen anderen Begriff.</p><script src="/assets/portraits.js" defer></script>')%(label,intro,tabs(g),selection,len(d[g]),''.join(card(g,x) for x in d[g]))
  page(p,label+' im Portrait',intro,inner,{'@context':'https://schema.org','@type':'CollectionPage','name':label,'url':base+p,'mainEntity':{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':base+path(g,x['slug']),'name':x['name']} for i,x in enumerate(d[g])]}});urls.append(base+p)
  docs.append({'t':label+' im Portrait','u':p,'k':'Verzeichnis','d':intro,'g':label,'x':intro,'ts':0,'dt':fmt_dot(d['reviewed'])})
  for x in d[g]:
   p=path(g,x['slug']);keys=list(x['sources']);body='<div class="p-topline">%s · Portrait</div><h1>%s</h1><p class="p-lead">%s</p><p class="p-stand">Quellen geprüft am %s · Redaktion: Philipp Paulik</p>'%(label,E(x['name']),E(x['summary']),fmt_de(x.get('checked') or (x.get('rich_model') or {}).get('checked') or d['reviewed']))
   if g=='models':
    co=next(c for c in d['companies'] if c['slug']==x['company']);body+='<p><a class="p-link" href="%s">Entwickler: %s →</a></p>'%(path('companies',co['slug']),E(co['name']))
   body+='<div class="p-layout"><div><section class="p-panel"><h2>%s</h2><p>%s</p></section>'%('Technische Einordnung' if technical else 'Kurz erklärt',E(x['detail'] if technical or g=='models' else x['summary']))
   if g=='models':
    body+='<section class="p-panel"><h2>Zugang &amp; Nutzung</h2><p>%s</p><p>%s</p></section>'%(E(x['access']),E(x['license']))
   if g=='benchmarks':body+='<section class="p-panel"><h2>Messgröße</h2><p>'+E(x['metric'])+'</p></section>'
   body+='<section class="p-panel"><h2>Grenzen &amp; richtig lesen</h2><p>'+E(x['limits'])+'</p></section>'
   results=[s for s in d['scores'] if (g=='models' and s['model']==x['slug']) or (g=='benchmarks' and s['benchmark']==x['slug'])]
   if technical and g in ('models','benchmarks'):
    body+='<section class="p-panel"><h2>Benchmark-Belege</h2>'
    if results:
     body+='<p class="p-source">Herstellerbericht, keine eigene Messung. Die Zahlen sind keine direkt vergleichbare Modellrangliste. Messdatum und vollständige Testkonfiguration sind in den referenzierten Tabellenzeilen nicht ausgewiesen.</p><div class="p-scores"><table><thead><tr><th scope="col">Test / Modell</th><th scope="col">Wert</th><th scope="col">Kontext</th></tr></thead><tbody>'
     for s in results:
      b=next(b for b in d['benchmarks'] if b['slug']==s['benchmark']);m=next(m for m in d['models'] if m['slug']==s['model']);keys.append(s['source'])
      body+='<tr><td><a href="%s">%s</a><small>%s</small></td><td>%s<small>%s</small></td><td>%s<small><a href="%s">Quelle: %s</a> · Abruf %s</small></td></tr>'%(path('benchmarks',b['slug']) if g=='models' else path('models',m['slug']),E(b['name'] if g=='models' else m['name']),E(s['variant']),E(s['value']),E(s['metric']),E(s['setup']),E(d['sources'][s['source']]['url']),E(s['reported_by']),fmt_dot(d['sources'][s['source']]['accessed']) if x.get('checked') else fmt_dot(d['reviewed']))
     body+='</tbody></table></div>'
    else:body+='<p>Für dieses Portrait ist noch kein ausreichend zugeordnetes Ergebnis erfasst. Fehlende Werte sind keine Null. Wir übernehmen keine Werte aus ähnlich benannten Modell- oder Benchmark-Versionen.</p>'
    body+='</section>'
   if g=='companies':
    linked=[m for m in d['models'] if m['company']==x['slug']];body+='<section class="p-panel"><h2>Modelle im Verzeichnis</h2><ul>'+''.join('<li><a href="%s">%s</a> · %s</li>'%(path('models',m['slug']),E(m['name']),E(m['summary'])) for m in linked)+'</ul></section>'
   body+='</div><aside>'
   if g!='benchmarks':
    facts=x['facts'] if technical or g=='models' else x['facts'][:2];body+='<section class="p-panel"><h2>Steckbrief</h2><dl class="p-facts">'
    for f in facts:
     keys.append(f['source']);body+='<div><dt>'+E(f['label'])+'</dt><dd>'+E(f['value'])+'</dd></div>'
    body+='</dl><p class="p-source">Angaben laut den unten verlinkten Primärquellen.</p></section>'
   body+=refs(keys)+'</aside></div>'
   if g=='models' and x.get('rich_model'):body=body.split('<div class="p-layout">')[0]+rich_model(x,d,technical)+refs(keys)
   if g in ('models','companies') and not x.get('rich') and not x.get('rich_model'):body+=ecosystem(x,d)
   if g=='companies' and x.get('rich'):body=body.split('<div class="p-layout">')[0]+rich_company(x,d,technical)+refs(list(dict.fromkeys(keys)))
   if g in ('models','companies'):
    exports=export_pdf(ROOT,out,site,g,x,body,portrait_mark(x,True),logo_note(x),base+p,x.get('checked') or (x.get('rich_model') or {}).get('checked') or d['reviewed'],css+COMPANY_CSS+MODEL_CSS)
    body=body.replace('<div class="p-layout">',exports+'<div class="p-layout">',1) if '<div class="p-layout">' in body else body.replace('<section class="mr">',exports+'<section class="mr">',1) if '<section class="mr">' in body else body.replace('<section class="co-rich">',exports+'<section class="co-rich">',1)
   crumb='<nav class="p-breadcrumb" aria-label="Brotkrumen"><a href="/">Start</a> / <a href="%s">%s</a> / %s</nav>'%(path(g),label,E(x['name']))
   page(p,x['name']+(' erklärt: API, Kontext, Preise & Grenzen' if x.get('rich_model') else ' im Portrait'),x['summary'],crumb+tabs(g)+portrait_mark(x,True)+logo_note(x)+body,{'@context':'https://schema.org','@type':'Article','headline':x['name']+' im Portrait','description':x['summary'],'datePublished':x.get('published','2026-10-19'),'dateModified':x.get('checked') or (x.get('rich_model') or {}).get('checked') or d['reviewed'],'author':{'@type':'Person','name':'Philipp Paulik'},'citation':[d['sources'][k]['url'] for k in dict.fromkeys(keys)],'mainEntityOfPage':base+p});urls.append(base+p)
   docs.append({'t':x['name']+' im Portrait','u':p,'k':label,'d':x['summary'],'g':x.get('company','')+' '+label,'x':' '.join([x['detail'],x['limits']]+([x['rich_model']['answer']]+[q+' '+a for q,a in x['rich_model']['faq']] if x.get('rich_model') else [])+([x['rich']['intro']]+[a[1] for a in x['rich']['sections']]+[a[0]+' '+a[1] for a in x['rich'].get('faq',[])]+[a[0]+' '+a[1] for a in x['rich'].get('offerings',[])]+x['rich'].get('checks',[]) if x.get('rich') else [])+[f['value'] for f in x.get('facts',[])]),'ts':0,'dt':fmt_dot(x.get('checked') or (x.get('rich_model') or {}).get('checked') or d['reviewed'])})
 (out/'portrait-search.json').write_text(json.dumps(docs,ensure_ascii=False))
 # Search is rebuilt earlier in both sites. Merge with deduplication, retaining existing search results.
 sp=out/'search-index.json'
 if sp.exists():
  payload=json.loads(sp.read_text());known={x['u'] for x in docs};payload['docs']=[x for x in payload['docs'] if x['u'] not in known]+docs;sp.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
 # Sitemap regeneration remains idempotent.
 sp=out/'sitemap.xml'
 if sp.exists():
  text=sp.read_text();text=re.sub(r'<url>\s*<loc>'+re.escape(base)+r'/(?:unternehmen|ki-modelle|benchmarks)(?:/|<).*?</url>','',text,flags=re.S)
  text=text.replace('</urlset>',''.join('<url><loc>'+u+'</loc><lastmod>'+d['reviewed']+'</lastmod></url>' for u in urls)+'</urlset>');sp.write_text(text)
 # Portrait link in every header, footer; home teaser uses only static internal links.
 for f in out.rglob('*.html'):
  if any(p in ('content','tools','site','authorpage') for p in f.relative_to(out).parts):continue
  text=f.read_text();old=text
  text=re.sub(r'<a class="(?:l )?p-nav"[^>]*>Portraits</a>', '', text)
  if not re.search(r'<a[^>]+class="[^"]*\bp-nav\b',text):
   marker='<a href="/#themen">Themen</a>' if technical else '<a class="l" href="/news/">KI-News</a>'
   navlink='<a class="p-nav" href="%s">Portraits</a>'%path('models') if technical else '<a class="l p-nav" href="%s">Portraits</a>'%path('models')
   text=text.replace(marker,marker+navlink,1)
  if 'data-portrait-footer' not in text:
   idx=text.find('<footer')
   if idx>=0:
    end=text.find('</footer>',idx);text=text[:end]+'<div class="%s" data-portrait-footer><p><a href="%s">Unternehmens-Portraits</a> · <a href="%s">KI-Modell-Portraits</a>%s</p></div>'%(wrap,path('companies'),path('models'),(' · <a href="'+path('benchmarks')+'">Benchmark-Portraits</a>') if technical else '')+text[end:]
  if f==out/'index.html' and 'id="portrait-verzeichnis"' not in text:
   teaser='<section class="%s p-home" id="portrait-verzeichnis"><div class="p-topline">Neu zum Nachschlagen</div><h2>Wer baut was in der KI?</h2><p>%d Unternehmen, %d Modelle%s. Quellen, Einordnung und Grenzen statt einer pauschalen Bestenliste.</p>%s</section>'%(wrap,len(d['companies']),len(d['models']),', %d Benchmark-Portraits'%len(d['benchmarks']) if technical else '',tabs())
   text=text.replace('</main>',teaser+'</main>',1) if technical else text.replace('<footer',teaser+'<footer',1)
   if '/assets/portraits.css' not in text:text=text.replace('</head>','<link rel="stylesheet" href="/assets/portraits.css"></head>')
  if f==out/'index.html':
   text=re.sub(r'(<section[^>]+id="portrait-verzeichnis".*?<p>)\d+ Unternehmen, \d+ Modelle(, \d+ Benchmark-Portraits)?',lambda m:m.group(1)+str(len(d['companies']))+' Unternehmen, '+str(len(d['models']))+' Modelle'+((', %d Benchmark-Portraits'%len(d['benchmarks'])) if m.group(2) else ''),text,flags=re.S)
  if text!=old:f.write_text(text)
 print('%s portraits: %d pages, %d search documents'%(site,len(urls),len(docs)))
if __name__=='__main__':render(sys.argv[1],sys.argv[2])
