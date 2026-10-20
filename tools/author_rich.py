#!/usr/bin/env python3
"""Final editorial-directory/profile pass. Stdlib, no network, no invented biographies."""
from pathlib import Path
from html import escape as e
import json,re,sys,datetime,urllib.parse
CONFIG={
 'fa':dict(name='finanz adjust',base='https://finanz-adjust.de',accent='#1975df',bg='var(--bg,#eff1f5)',panel='var(--p,#fff)',fg='var(--fg,#344054)',hd='var(--hd,#111827)',mut='var(--mut,#667085)',border='var(--b,#dce2eb)',themes=['Marktdaten verstehen','Finanzwissen','Rechner und Vergleiche'],intro='Finanzwissen braucht Quellen, verständliche Begriffe und klare Grenzen. Hier findest du die Verantwortung hinter finanz adjust.',focus='Marktdaten, Finanznachrichten und Werkzeuge zum eigenen Nachvollziehen. Keine individuelle Anlageberatung.',about='/ueber-uns/',transparency='/transparenz/',corrections='/korrekturen/'),
 'iw':dict(name='Intelligenz Welt',base='https://intelligenz-welt.de',accent='#2d75ec',bg='#f2f6fc',panel='#fff',fg='#34435a',hd='#132342',mut='#61718c',border='#dbe5f2',themes=['KI-Modelle','Agenten und Werkzeuge','Forschung einordnen'],intro='Modelle, Forschung und Werkzeuge verändern sich schnell. Wir machen sichtbar, wer dieses Angebot verantwortet und worauf die Beiträge beruhen.',focus='Künstliche Intelligenz, Modelle, Agenten und die Einordnung neuer Veröffentlichungen. Quellen statt unbelegter Versprechen.',about='/ueber-uns/',transparency='/transparenz/',corrections='/korrekturen/'),
 'kfb':dict(name='KI Fachblatt',base='https://kifachblatt.de',accent='#8063d3',bg='#f5f2fb',panel='#fff',fg='#423b55',hd='#221a35',mut='#746b85',border='#e3dced',themes=['KI-Grundlagen','Methoden und Evaluation','Modelle in der Praxis'],intro='Ein Fachmagazin braucht nachvollziehbare Methoden und eine erreichbare Redaktion. Lerne den Herausgeber kennen und entdecke die Beiträge.',focus='Grundlagen und Praxis künstlicher Intelligenz: verständlich, quellenbezogen und mit Blick auf die Grenzen einer Aussage.',about='/ueber',transparency='/transparenz',corrections='/korrekturen')}

def walk(node):
 if isinstance(node,list):
  for n in node:yield from walk(n)
 elif isinstance(node,dict):
  yield node
  for key in ['@graph','mainEntity']:
   if key in node:yield from walk(node[key])

def articles(out,c):
 found={}
 for f in out.rglob('*.html'):
  if any(x in f.parts for x in ['redakteur','berichte','assets']):continue
  h=f.read_text(errors='replace')
  for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',h,re.S):
   try:nodes=list(walk(json.loads(raw)))
   except ValueError:continue
   for n in nodes:
    typ=n.get('@type');typ=[typ] if isinstance(typ,str) else (typ or [])
    if not any(t in ['Article','NewsArticle','TechArticle','BlogPosting'] for t in typ):continue
    title=n.get('headline') or n.get('name');date=n.get('datePublished','')
    if not title or not date:continue
    url=n.get('mainEntityOfPage') or n.get('url')
    if isinstance(url,dict):url=url.get('@id') or url.get('url')
    if not url:
     m=re.search(r'<link rel="canonical" href="([^"]+)"',h);url=m.group(1) if m else None
    if not url or not url.startswith(c['base']+'/'):continue
    if date[:10]>datetime.date.today().isoformat():continue
    if url not in found:found[url]=dict(title=title,date=date[:10],url=url)
 return sorted(found.values(),key=lambda a:a['date'],reverse=True)

def styles(c):
 return '''<style>
.er{--ea:ACCENT;--eb:BG;--ep:PANEL;--ef:FG;--eh:HD;--em:MUT;--el:BORDER;max-width:1180px;margin:0 auto;padding:42px 28px 70px;color:var(--ef);font:15px/1.7 system-ui,-apple-system,Segoe UI,sans-serif}.er *{box-sizing:border-box}.er h1,.er h2,.er h3{font-family:inherit;color:var(--eh);letter-spacing:-.035em;line-height:1.12}.er h1{font-size:clamp(40px,5.7vw,70px);margin:12px 0 24px}.er h2{font-size:clamp(27px,3.2vw,40px);margin:12px 0 24px}.er h3{font-size:20px;margin:0 0 12px}.er p{margin:0 0 18px}.er a{color:var(--ea);text-decoration:underline;text-underline-offset:4px}.er .er-k{font-size:11px;letter-spacing:.16em;font-weight:800;color:var(--ea);margin-bottom:12px}.er-lead{font-size:20px;line-height:1.6;color:var(--eh)}.er-hero{display:grid;grid-template-columns:1.2fr 1fr;align-items:center;gap:64px;padding:24px 0 42px}.er-art{position:relative;min-height:330px;border:1px solid var(--el);border-radius:24px;background:var(--ep);overflow:hidden;box-shadow:0 20px 65px -45px #203e78}.er-art svg{width:100%;height:300px;stroke:var(--ea);fill:none;stroke-width:2;opacity:.65}.er-art p{position:absolute;bottom:4px;left:24px;color:var(--em);font-size:11px}.er-art .er-tag{position:absolute;padding:12px 16px;background:var(--ep);border:1px solid var(--el);border-radius:12px;color:var(--eh);font-size:12px;font-weight:700;box-shadow:0 6px 24px -16px #203e78}.er-tag.t1{top:32px;left:24px}.er-tag.t2{top:130px;right:24px}.er-tag.t3{bottom:58px;left:45px}.er-buttons{display:flex;flex-wrap:wrap;gap:18px;align-items:center;margin-top:24px}.er .er-button{display:inline-flex;padding:13px 20px;border-radius:10px;color:#fff;background:var(--ea);text-decoration:none;font-weight:750;border:1px solid transparent}.er .er-button:hover{filter:brightness(.94);color:#fff}.er .er-card{padding:28px;border:1px solid var(--el);border-radius:18px;background:var(--ep);min-width:0}.er-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:0 0 12px}.er-stats strong{font-size:36px;line-height:1.1;display:block;color:var(--ea);margin-bottom:13px;letter-spacing:-.04em}.er-stats p{font-size:12px;color:var(--em);margin:0}.er-stats h3{font-size:15px;margin-bottom:8px}.er-note{font-size:12px;color:var(--em)}.er-section{padding:46px 0;border-top:1px solid var(--el);scroll-margin-top:80px}.er-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.er-profile-card{display:grid;grid-template-columns:180px 1fr;gap:28px;align-items:center}.er img{max-width:100%;display:block}.er .er-portrait{display:block;width:100%;height:auto;border-radius:18px;aspect-ratio:1;object-fit:cover}.er figcaption{font-size:11px;color:var(--em);margin-top:8px}.er figure{margin:0}.er-profile-hero{grid-template-columns:1.35fr .8fr}.er-profile-hero figure{max-width:350px;justify-self:end}.er-chips{display:flex;flex-wrap:wrap;gap:8px}.er-chips span{font-size:12px;border:1px solid var(--el);border-radius:999px;padding:6px 12px;color:var(--em)}.er-recent{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.er-recent a{display:block;text-decoration:none;padding:24px;background:var(--ep);border:1px solid var(--el);border-radius:14px}.er-recent a h3{font-size:18px;line-height:1.4}.er-recent time{font-size:11px;color:var(--em);display:block;margin-bottom:12px}.er-recent a:hover{border-color:var(--ea)}.er-callout{display:grid;grid-template-columns:1.3fr 1fr;gap:40px;padding:36px;border:1px solid var(--el);background:var(--ep);border-radius:20px}.er-callout p{font-size:14px}.er a:focus-visible{outline:3px solid var(--ea);outline-offset:5px}.er-crumb{font-size:12px;color:var(--em);margin-bottom:24px}.er-contact{overflow-wrap:anywhere}.er-split{display:grid;grid-template-columns:.8fr 1.4fr;gap:60px}.er ul{padding-left:20px}.er li{margin-bottom:12px}@media(max-width:800px){.er-hero,.er-callout,.er-split{grid-template-columns:1fr;gap:26px}.er-profile-hero figure{justify-self:start;max-width:300px}.er-hero{padding-top:10px}.er-art{max-width:540px}.er-profile-card{grid-template-columns:130px 1fr;gap:20px}}@media(max-width:520px){.er{padding:24px 18px 44px}.er h1{font-size:36px;overflow-wrap:anywhere}.er-hero>*{min-width:0}.er-art{width:100%}.er-lead{font-size:18px}.er-stats,.er-grid,.er-recent{grid-template-columns:1fr}.er-stats .er-card{padding:20px}.er-stats strong{font-size:30px}.er-profile-card{grid-template-columns:1fr}.er-profile-card figure{max-width:190px}.er-callout{padding:24px}.er-section{padding:34px 0}.er-hero{gap:25px}.er-art{min-height:290px}.er-art svg{height:260px}}
</style>'''.replace('ACCENT',c['accent']).replace('BG',c['bg']).replace('PANEL',c['panel']).replace('FG',c['fg']).replace('HD',c['hd']).replace('MUT',c['mut']).replace('BORDER',c['border'])

def main(key,out):
 c=CONFIG[key];out=Path(out);base=c['base'];profile=base+'/redakteur/philipp-paulik'+('' if key=='kfb' else '/');directory=base+'/redakteur/'
 pf=out/('redakteur/philipp-paulik.html' if key=='kfb' else 'redakteur/philipp-paulik/index.html')
 template=pf.read_text();start=template.find('</header>')+len('</header>');foot=template.rfind('<footer')
 # Keep full site header and legal/consent/footer shell; replace only the page body area.
 head=template[:start];tail=template[foot:];items=articles(out,c);topics=c['themes'];portrait='/assets/philipp-paulik-portrait-bibliothek-gruene-lampen-800.jpg'
 if key=='iw' and 'querySelector(".burger")' not in head:
  home=(out/'index.html').read_text()
  menu=next((v for v in re.findall(r'<script>.*?</script>',home,re.S) if 'querySelector(".burger")' in v),'')
  head+=menu
 fig='<figure><img class="er-portrait" src="'+portrait+'" width="800" height="800" alt="Philipp Paulik, vorhandenes Profilbild" decoding="async"><figcaption>Philipp Paulik · Profilbild aus dem bestehenden Autorenprofil</figcaption></figure>'
 chips='<div class="er-chips">'+''.join('<span>'+e(t)+'</span>' for t in topics)+'</div>'
 mail='mailto:philipp.l.paulik@gmail.com?subject='+urllib.parse.quote('Als Redakteur bewerben - '+c['name'])
 invite='<section class="er-callout"><div><p class="er-k">MITWIRKEN</p><h2>Gute Fragen.<br>Saubere Quellen.<br>Dein Beitrag?</h2><p>Du möchtest für '+e(c['name'])+' schreiben oder eine Themenidee vorstellen? Schick eine kurze Vorstellung, deine Interessengebiete und gern eine Arbeitsprobe oder einen Quellenhinweis.</p></div><div><h3>Direkt zur Redaktion</h3><p>Die Einladung ist kein Stellenangebot mit zugesagten Konditionen. Ob und wie eine Zusammenarbeit passt, wird persönlich besprochen.</p><a class="er-button" href="'+mail+'">Als Redakteur bewerben</a><p class="er-note er-contact" style="margin-top:16px">philipp.l.paulik@gmail.com</p></div></section>'
 stats='<div class="er-stats">'+''.join('<div class="er-card"><strong>'+str(n)+'</strong><h3>'+e(label)+'</h3><p>'+e(note)+'</p></div>' for n,label,note in [(len(items),'Beiträge im Angebot','Aus veröffentlichten Artikel-Metadaten gezählt; keine externen Schlagzeilen.'),(1,'Vorgestelltes Profil','Aktuell ist Philipp Paulik in dieser Übersicht vertreten.'),(len(topics),'Thematische Zugänge','Redaktionelle Orientierung, keine individuellen Fachzertifikate.')])+'</div><p class="er-note">Bestand dieses Seitenaufbaus. Die Beitragszahl ist keine Behauptung, dass jeder Text ohne KI-Unterstützung oder persönlich allein verfasst wurde.</p>'
 art='<div class="er-art" aria-label="Redaktionelles Prinzip: Quelle, Kontext, Verantwortung"><svg viewBox="0 0 400 300" aria-hidden="true"><circle cx="200" cy="145" r="105"/><path d="M55 215L125 180L190 193L255 99L345 60"/><circle cx="255" cy="99" r="6"/></svg><span class="er-tag t1">QUELLE</span><span class="er-tag t2">KONTEXT</span><span class="er-tag t3">VERANTWORTUNG</span><p>Einblick in das Angebot, kein Gütesiegel.</p></div>'
 recent='<div class="er-recent">'+''.join('<a href="'+e(a['url'],quote=True)+'"><time datetime="'+a['date']+'">'+'.'.join(reversed(a['date'].split('-')) )+'</time><h3>'+e(a['title'])+'</h3><span>Beitrag lesen ↗</span></a>' for a in items[:6])+'</div>' if items else '<p>Aktuelle Beiträge findest du auf der Startseite.</p>'
 common='<section class="er-section er-split"><div><p class="er-k">VERANTWORTUNG &amp; KI</p><h2>Erreichbar statt anonym.</h2></div><div><p>Philipp Paulik ist laut Impressum Herausgeber beziehungsweise Betreiber dieses Angebots. Die redaktionelle Verantwortung bleibt bei ihm. KI-Werkzeuge können Recherche, Entwürfe und Gestaltung unterstützen; automatisierte Nachrichtenelemente sind von eigenen Beiträgen zu unterscheiden.</p><p>Ein Profil ist keine Garantie für Fehlerfreiheit. Für eine Aussage zählen die konkrete Quelle, das Datum und die ausgewiesenen Grenzen. Eine besondere persönliche Prüfung oder Freigabe sollte nur angenommen werden, wenn sie am Inhalt belegt ist.</p><p><a href="'+c['transparency']+'">KI-Transparenz</a> · <a href="'+c['corrections']+'">Korrekturen</a> · <a href="'+c['about']+'">Über '+e(c['name'])+'</a></p></div></section>'
 index='<main class="er"><section class="er-hero"><div><p class="er-k">DIE REDAKTION · '+e(c['name']).upper()+'</p><h1>Die Redaktion.<br>Die Verantwortung.</h1><p class="er-lead">'+e(c['intro'])+'</p><div class="er-buttons"><a class="er-button" href="#profile">Redaktion kennenlernen</a><a href="'+mail+'">Als Redakteur bewerben ↗</a></div></div>'+art+'</section>'+stats+'<section class="er-section" id="profile"><p class="er-k">AKTUELL VORGESTELLT</p><h2>Eine klare Ansprechperson.</h2><div class="er-card er-profile-card">'+fig+'<div><h3>Philipp Paulik</h3><p>Herausgeber / Betreiber · redaktionelle Verantwortung</p><p>'+e(c['focus'])+'</p>'+chips+'<div class="er-buttons"><a class="er-button" href="'+profile+'">Zum Redakteursprofil</a><a href="mailto:philipp.l.paulik@gmail.com">Kontakt per E-Mail</a></div></div></div></section>'+common+invite+'</main>'
 prof='<main class="er"><nav class="er-crumb" aria-label="Breadcrumb"><a href="/redakteur/">Redaktion</a> / Philipp Paulik</nav><section class="er-hero er-profile-hero"><div><p class="er-k">REDAKTEURSPROFIL · '+e(c['name']).upper()+'</p><h1>Philipp Paulik.</h1><p class="er-lead">Herausgeber. Betreiber.<br>Für dieses Angebot erreichbar.</p><p>'+e(c['focus'])+'</p>'+chips+'<div class="er-buttons"><a class="er-button" href="mailto:philipp.l.paulik@gmail.com">Kontakt aufnehmen</a><a href="#beitraege">Letzte Beiträge ↓</a></div></div>'+fig+'</section>'+stats+'<section class="er-section er-split"><div><p class="er-k">PROFIL</p><h2>Die Verantwortung<br>hat einen Namen.</h2></div><div><p>Philipp Paulik betreibt '+e(c['name'])+'. Name und Kontakt sind im <a href="'+('/impressum' if key=='kfb' else '/impressum/')+'">Impressum</a> dokumentiert. Das Profil stellt seine Rolle auf dieser Website vor, keine extern geprüften Berufsabschlüsse oder Auszeichnungen.</p><p>Das bestehende Autorenprofil verknüpft außerdem seine persönliche Website und weitere Projekte. Hier steht die Arbeit für dieses Angebot im Mittelpunkt.</p><p><a href="https://philipp-paulik.de/" rel="me noopener">Persönliche Website: philipp-paulik.de ↗</a></p></div></section>'+common+'<section class="er-section" id="beitraege"><p class="er-k">AUS DEM ANGEBOT</p><h2>Zuletzt veröffentlicht.</h2><p class="er-note">Aktuelle Artikel dieses Angebots, mit ihrem Veröffentlichungsdatum. Keine Behauptung einer ausschließlich manuellen Verfasserschaft.</p>'+recent+'</section>'+invite+'</main>'
 def publish(dest,url,title,description,body,typ):
  h=re.sub(r'<style>\s*\.er\{.*?</style>', '', head, flags=re.S)
  h=re.sub(r'<title>.*?</title>','<title>'+e(title)+'</title>',h,flags=re.S)
  h=re.sub(r'<meta name="description"[^>]*>','<meta name="description" content="'+e(description,quote=True)+'">',h)
  h=re.sub(r'<link rel="canonical"[^>]*>','<link rel="canonical" href="'+url+'">',h)
  h=re.sub(r'<script type="application/ld\+json">.*?</script>','',h,flags=re.S)
  for prop,value in [('og:title',title),('og:description',description),('og:url',url),('og:type','profile' if typ=='ProfilePage' else 'website')]:h=re.sub(r'<meta property="'+prop+'"[^>]*>','<meta property="'+prop+'" content="'+e(value,quote=True)+'">',h)
  for prop,value in [('twitter:title',title),('twitter:description',description)]:h=re.sub(r'<meta name="'+prop+'"[^>]*>','<meta name="'+prop+'" content="'+e(value,quote=True)+'">',h)
  if typ=='CollectionPage':h=re.sub(r'<meta property="profile:[^>]*>','',h)
  ld={'@context':'https://schema.org','@type':typ,'name':title,'url':url,'inLanguage':'de-DE','mainEntity':{'@type':'Person','@id':'https://philipp-paulik.de/#person','name':'Philipp Paulik','url':profile} if typ=='ProfilePage' else {'@type':'ItemList','numberOfItems':1,'itemListElement':[{'@type':'ListItem','position':1,'url':profile,'name':'Philipp Paulik'}]}}
  h=h.replace('</head>',styles(c)+'<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False)+'</script></head>')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(h+body+tail)
 publish(pf,profile,'Philipp Paulik: Redakteursprofil | '+c['name'],'Rolle, Themen, aktuelle Beiträge und Kontakt von Philipp Paulik bei '+c['name']+'.',prof,'ProfilePage')
 publish(out/'redakteur/index.html',directory,'Redaktion & Redakteure | '+c['name'],'Die Redaktion von '+c['name']+': Profile, Verantwortung und Kontakt. Als Redakteur bewerben.',index,'CollectionPage')
 # Static hosts differ: KFB serves extensionless files, so provide a directory route as requested too.
 if key=='kfb':(out/'redakteur.html').write_text((out/'redakteur/index.html').read_text())
 sm=out/'sitemap.xml'
 if sm.exists():
  x=sm.read_text()
  for url in [profile,directory]:
   if '<loc>'+url+'</loc>' not in x:x=x.replace('</urlset>','<url><loc>'+url+'</loc></url></urlset>')
  sm.write_text(x)
 # Make the directory reachable through the shared footer, without replacing other editor links.
 for f in out.rglob('*.html'):
  if 'assets' in f.parts:continue
  h=f.read_text(errors='replace');idx=h.rfind('<footer')
  if idx<0:continue
  foot=h[idx:]
  if 'href="/redakteur/"' in foot:continue
  link='<a href="/redakteur/">Redakteure &amp; Mitwirken</a>'
  m=re.search(r'<a href="/redaktion/?">Redaktion</a>',foot)
  # Put it in the footer's Redaktion column, next to the Redaktion link. Fallback keeps the old single line.
  foot=foot[:m.end()]+link+foot[m.end():] if m else foot.replace('</footer>','<p class="er-directory-link" style="margin:16px 0">'+link+'</p></footer>',1)
  h=h[:idx]+foot
  f.write_text(h)
 print('rich editorial pages:',key,'articles',len(items),'profile',pf)
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
