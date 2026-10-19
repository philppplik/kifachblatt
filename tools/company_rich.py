"""Local company portrait components, no remote requests during builds."""
from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parents[1]
E=lambda s:html.escape(str(s),quote=True)
CSS='''
.co-rich{margin:30px 0}.co-rich h2{font-size:clamp(28px,4vw,44px);line-height:1.15;letter-spacing:-.03em;margin:12px 0 20px}.co-eyebrow{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--p-ac);font-weight:700}.co-intro{font-size:18px;line-height:1.75;max-width:850px}.co-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:28px 0}.co-block{border:1px solid var(--p-line);border-radius:14px;padding:26px;min-width:0}.co-block h3{font-size:20px;line-height:1.3;margin:0 0 12px}.co-block p{font-size:15px;line-height:1.8;color:var(--p-muted)}.co-ref{font-size:12px;overflow-wrap:anywhere}.co-stack{background:var(--p-soft);border-radius:14px;padding:28px;margin:28px 0}.co-stack svg{display:block;width:100%;height:auto;max-width:760px;margin:auto}.co-layers-text{display:none}.co-stack>p{font-size:12px;color:var(--p-muted)}.co-timeline{list-style:none;padding:0;display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin:25px 0 35px}.co-timeline li{padding:18px;border-top:3px solid var(--p-ac);background:var(--p-soft);font-size:14px;line-height:1.7}.co-timeline b{display:block;font-size:23px;margin-bottom:12px}.co-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.co-stat{border:1px solid var(--p-line);border-radius:10px;padding:20px}.co-stat strong{display:block;font-size:30px;line-height:1.2;overflow-wrap:anywhere}.co-stat span{font-size:12px;color:var(--p-muted)}.co-rich a{color:var(--p-ac);text-underline-offset:3px}.co-repo{font-size:14px;line-height:1.8;overflow-wrap:anywhere}.co-models{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.co-models a{border:1px solid var(--p-line);padding:14px;border-radius:10px;font-size:14px}.co-foot{font-size:12px;color:var(--p-muted);line-height:1.7;overflow-wrap:anywhere}@media(max-width:650px){.co-grid,.co-timeline,.co-stats,.co-models{grid-template-columns:minmax(0,1fr)}.co-block{padding:22px}.co-stack{padding:18px}.co-stack svg{display:none}.co-layers-text{display:grid;gap:12px}.co-layers-text>div{border:1px solid var(--p-line);border-radius:10px;background:white;padding:16px}.co-layers-text b{display:block;font-size:17px}.co-layers-text span{font-size:14px;color:var(--p-muted)}.co-stat strong{font-size:28px}}
'''
def render(c,d,technical):
 p=c['rich'];sources=d['sources']
 def ref(key):
  src=sources[key];return '<a class="co-ref" href="'+E(src['url'])+'">Quelle: '+E(src['title'])+'</a>'
 out='<section class="co-rich"><div class="co-eyebrow">'+E(p['eyebrow'])+'</div><h2>'+E(p['headline'])+'</h2><p class="co-intro">'+E(p['intro'])+'</p>'
 svg='<svg viewBox="0 0 650 285" role="img" aria-label="'+E('; '.join(a+': '+b for a,b in p['layers']))+'"><title>Organisation, Entwicklung und Anwendung</title>'
 for i,(a,b) in enumerate(p['layers']):
  y=i*96;svg+='<rect x="1" y="%d" width="648" height="76" rx="12" fill="white" stroke="#d8d8e0"/><text x="24" y="%d" fill="#151519" font-size="23">%s</text><text x="24" y="%d" fill="#64646f" font-size="16">%s</text>'%(y+1,y+32,E(a),y+58,E(b))
 svg+='</svg><div class="co-layers-text">'+''.join('<div><b>'+E(a)+'</b><span>'+E(b)+'</span></div>' for a,b in p['layers'])+'</div>';out+='<div class="co-stack">'+svg+'<p>Redaktionelles Orientierungsbild, keine rechtliche Organigramm-Gesamtdarstellung. '+ref(p['primary'])+'</p></div><div class="co-grid">'
 for title,text,key in p['sections']:out+='<article class="co-block"><h3>'+E(title)+'</h3><p>'+E(text)+'</p>'+ref(key)+'</article>'
 out+='</div><h2>Wichtige Stationen</h2><ol class="co-timeline">'
 for date,text,key in p['milestones']:out+='<li><b>'+E(date)+'</b>'+E(text)+'<br>'+ref(key)+'</li>'
 out+='</ol>'
 files=sorted((ROOT/'content/portrait-snapshots'/('github-'+p['repo'])).glob('*.json'))
 if files:
  snap=max((json.loads(f.read_text()) for f in files),key=lambda a:a['retrieved_at']);r=snap['data'];n=lambda v:f'{v:,}'.replace(',','.')
  out+='<h2>Entwickler-Ökosystem: ein konkreter Ausschnitt</h2><p class="co-repo">Offizielles öffentliches Repository: <a href="'+E(r['html_url'])+'">'+E(r['full_name'])+'</a>. Die Werte beschreiben dieses Repository, nicht die Größe des Unternehmens, zahlende Nutzer oder Modellqualität.</p><div class="co-stats">'
  for value,label in [(n(r['stargazers_count']),'GitHub-Stars'),(n(r['forks_count']),'Forks'),(r['license']['spdx_id'] if r['license'] else 'Nicht erkannt','Repository-Lizenz laut API')]:out+='<div class="co-stat"><strong>'+E(value)+'</strong><span>'+E(label)+'</span></div>'
  out+='</div><p class="co-foot">Letzter Push laut API: '+E(r['pushed_at'])+' · Snapshot abgerufen: '+E(snap['retrieved_at'])+'. Kein Aktualisierungsversprechen und keine Aussage über ein Release. <a href="'+E(snap['source'])+'">GitHub-API-Primärquelle</a>. Lokal versionierter Datenstand; kein externer Abruf beim Lesen. Die Repository-Lizenz ist keine Lizenz für Modelle oder den GitHub-Dienst.</p>'
 models=[m for m in d['models'] if m['company']==c['slug']]
 out+='<h2>Modelle im lokalen Verzeichnis</h2><div class="co-models">'+''.join('<a href="/ki-modelle/'+m['slug']+('' if technical else '/')+'">'+E(m['name'])+' ↗</a>' for m in models)+'</div><p class="co-foot">Kuratierter Bestand dieser Website. Anzahl und Auswahl sind keine vollständige Produktliste des Anbieters. Unternehmensangaben sind Primärquellen-Selbstauskünfte, keine unabhängigen Audits. Quellenstand: 19.10.2026.</p></section>'
 return out

def ecosystem(x,d):
 """A company repository is context for a model, never its own repository claim."""
 company=x.get('company',x['slug']);key={'openai':'openai','anthropic':'anthropics','google-deepmind':'googleapis','mistral-ai':'mistralai','nvidia':'nvidia','meta':'meta-llama'}.get(company)
 if not key:return ''
 files=sorted((ROOT/'content/portrait-snapshots'/('github-'+key)).glob('*.json'))
 if not files:return ''
 snap=max((json.loads(f.read_text()) for f in files),key=lambda a:a['retrieved_at']);a=snap['data'];lic=a['license']['spdx_id'] if a['license'] else 'nicht erkannt'
 return '<section class="p-panel"><h2>Entwickler-Kontext des Anbieters</h2><p>Ein öffentliches Entwicklerprojekt des Anbieters: <a href="'+E(a['html_url'])+'">'+E(a['full_name'])+'</a>. Das ist kein Nachweis, dass dieses Repository die Gewichte oder den Quellcode des hier porträtierten Modells enthält.</p><p>'+str(a['stargazers_count'])+' GitHub-Stars · '+str(a['forks_count'])+' Forks · Repository-Lizenz laut API: '+E(lic)+'.</p><p class="p-source">Snapshot: '+E(snap['retrieved_at'])+' · letzter Push: '+E(a['pushed_at'])+'. Beachtung und Repository-Aktivität, keine Modellqualität oder Unternehmensgröße. <a href="'+E(snap['source'])+'">API-Quelle</a>. Lokal gespeichert; kein Live-Abruf beim Lesen. SDK-/Code-Lizenzen gelten nicht automatisch für Modelle oder APIs.</p></section>'
