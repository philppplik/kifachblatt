#!/usr/bin/env python3
"""Homepage editorial cards and source-grounded visuals; stdlib, no network."""
import json,re,html,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=lambda x:html.escape(str(x),quote=True)
SOURCE='https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Super-and-Lightning/'
def dec(v):return ('%.3f'%v).rstrip('0').rstrip('.').replace('.',',')
def chart(title,description,labels,series,maxv,unit,anchor):
 colors=['#c4afdF','#7040cd'];W=540;row=72;H=58+len(labels)*row
 svg=['<svg viewBox="0 0 %d %d" role="img" aria-label="%s"><title>%s</title>'%(W,H,E(description),E(title))]
 for i,label in enumerate(labels):
  y=28+i*row;svg.append('<text x="0" y="%d" font-size="12" fill="#64646f">%s</text>'%(y,E(label)))
  for j,(name,values) in enumerate(series):
   yy=y+9+j*20;val=values[i];width=val/maxv*405
   svg.append('<rect x="0" y="%d" width="405" height="13" rx="3" fill="#f3f1f8"/><rect x="0" y="%d" width="%.2f" height="13" rx="3" fill="%s"/><text x="425" y="%d" font-size="12" fill="#151519">%s%s</text>'%(yy,yy,width,colors[j],yy+11,dec(val),E(unit)))
 svg.append('<line x1="0" y1="%d" x2="405" y2="%d" stroke="#dedee4"/><text x="0" y="%d" font-size="10" fill="#64646f">0</text><text x="405" y="%d" text-anchor="end" font-size="10" fill="#64646f">%s%s</text></svg>'%(H-25,H-25,H-8,H-8,dec(maxv),E(unit)))
 legend='<div class="hv-legend">'+''.join('<span><i style="background:%s"></i>%s</span>'%(colors[i],E(n)) for i,(n,_) in enumerate(series))+'</div>'
 table='<details class="hv-data"><summary>Alle Werte als Text</summary><ul>'+''.join('<li>'+E(l)+': '+ '; '.join(E(n)+' '+dec(v[i])+E(unit) for n,v in series)+'</li>' for i,l in enumerate(labels))+'</ul></details>'
 return '<article class="hv-card"><div class="hv-kicker">Herstellerbericht · Nemotron 3.5 Super</div><h3>'+title+'</h3><p>'+description+'</p>'+legend+'<figure>'+''.join(svg)+'</figure>'+table+'<p class="hv-source"><a href="'+SOURCE+'">Quelle: NVIDIA Research</a> · geprüft 19.10.2026. Kein eigener Test. Die Setups gelten nur für diesen Bericht.</p><a class="hv-more" href="/nemotron-3-5-super-lightning-analyse">Analyse mit Methode &amp; Grenzen ↗</a></article>'
def card(a,lead=False):
 image=a.get('image');media='<img src="%s" alt="%s" width="800" height="450" loading="lazy" decoding="async">'%(E(image),E(a.get('alt',''))) if image else '<div class="hc-abstract" aria-hidden="true"><span>'+E(a['topic'])+'</span><b>'+E(a.get('initial','KI'))+'</b></div>'
 return '<article class="hc-card%s" data-topic="%s"><a class="hc-media" href="/%s" tabindex="-1" aria-hidden="true">%s</a><div class="hc-copy"><div class="hc-meta"><span>%s</span><span>%s</span></div><h3><a href="/%s">%s</a></h3><p>%s</p><a class="hc-read" href="/%s">Analyse lesen <span aria-hidden="true">↗</span></a></div></article>'%(' hc-lead' if lead else '',E(a['topic']),a['slug'],media,E(a['topic']),E(a['date']),a['slug'],E(a['title']),E(a['dek']),a['slug'])
def render(arts=None):
 if arts is None:
  arts=[]
  for p in (ROOT/'content/articles').glob('*.json'):
   a=json.loads(p.read_text());arts.append(a)
 arts=sorted(arts,key=lambda a:a['published'],reverse=True)
 cards=[]
 for a in arts:
  image='/assets/articles/'+a['slug']+'-800.jpg'
  if not (ROOT/image.lstrip('/')).exists():image='/assets/articles/'+a['slug']+'.jpg'
  topic={'modelle':'Modelle','evals':'Evaluation'}.get(a['section'],a['section'].capitalize())
  cards.append(dict(slug=a['slug'],title=a['title'],dek=a['dek'],topic=topic,date=a['published'][:10],image=image,alt=a['hero']['alt']))
 cards+=json.loads((ROOT/'content/home-legacy.json').read_text())
 topics=sorted({x['topic'] for x in cards})
 controls='<div class="hc-controls"><label>Analysen durchsuchen<input id="article-search" type="search" placeholder="Modell, Thema oder Begriff …" autocomplete="off"></label><label>Thema<select id="article-topic"><option value="">Alle Themen</option>'+''.join('<option>'+E(t)+'</option>' for t in topics)+'</select></label><span id="article-count" role="status">'+str(len(cards))+' Beiträge</span></div>'
 editorial='<section class="home-editorial" id="themen"><div class="wrap"><div class="hc-section-head"><div><div class="hv-kicker">Die aktuelle Ausgabe</div><h2>Analysen mit Substanz.</h2></div><p>Modelle einordnen. Zahlen nachrechnen.<br>Grenzen sichtbar machen.</p></div>'+controls+'<div class="hc-grid">'+''.join(card(a,i==0) for i,a in enumerate(cards))+'</div><p id="no-results" hidden>Keine Analyse gefunden. Versuche einen anderen Suchbegriff.</p><p class="hc-method">Quellen, Methode und Grenzen stehen in jeder Analyse. Redaktionell eingeordnete Beiträge, keine ungeprüfte Live-Bestenliste.</p></div></section>'
 visuals='<section class="home-visuals" id="datenblick"><div class="wrap"><div class="hc-section-head"><div><div class="hv-kicker">Datenblick · aus der aktuellen Analyse</div><h2>Was die Zahlen zeigen.</h2></div><p>Originaldaten statt dekorativer Kurven.<br>Mit Quelle, Stand und Grenzen.</p></div><p class="hv-intro">Drei Ausschnitte aus NVIDIAs Bericht zu Nemotron 3.5 Super. Herstellerangaben, keine unabhängigen Messungen und kein Vergleich verschiedener Modelle.</p><div class="hv-grid">'
 visuals+=chart('Mehr parallele Arbeit, höhere Erfolgsquote','Parallele Agentenläufe mit Selbstverifikation gegenüber einem einzelnen Lauf.',['Terminal-Bench 2.1','DeepSWE','BrowseComp'],[('Einzelner Lauf',[62.7,24.6,71.5]),('Parallel + Selbstverifikation',[71.9,34.5,79.8])],100,' %','parallelitaet-und-selbstverifikation')
 visuals+=chart('Langer Kontext muss erlernt werden','RULER-1M vor und nach einer zusätzlichen Erholungsstufe mit 9 Mrd. Token.',['Nach 256K-Mid-Training','Nach 1M-Erholungsstufe'],[('RULER-1M',[33.5,81.0])],100,'','kontext-ist-mehr-als-ein-konfigurationswert')
 visuals+=chart('Mehr akzeptierte Entwurfs-Token','Mittlere Akzeptanzlänge beim spekulativen Dekodieren vor und nach MTP-Boosting.',['Greedy','Probabilistisches Sampling'],[('Vor Boosting',[4.287,3.787]),('Nach Boosting',[4.718,4.612])],5,' Token','mtp-und-spekulatives-dekodieren')
 visuals+='</div><p class="hc-method">Bewusst kein Preis-Leistungs-Scatter und keine Trend-Sparklines: Für vergleichbare Preise, Messkonfigurationen und Zeitreihen liegt hier noch kein geprüfter Datensatz vor.</p></div></section>'
 p=ROOT/'index.html';s=p.read_text()
 # Idempotent exact section replacement, independent of the header/hero/footer.
 s=re.sub(r'<section class="home-visuals".*?</section>','',s,flags=re.S)
 s=re.sub(r'<section class="(?:block|home-editorial)" id="themen">.*?</section>',visuals+editorial,s,count=1,flags=re.S)
 if '/assets/home-editorial.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="/assets/home-editorial.css"></head>')
 p.write_text(s);print('home editorial:',len(cards),'cards, 3 sourced charts')
if __name__=='__main__':render()
