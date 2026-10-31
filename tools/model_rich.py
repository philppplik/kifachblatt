"""Sourced model answer pages. Static markup and visible structured data.

Portable patch (2026-10-31):
- Token-Cards/Skala nur bei numerischen Werten; Textwerte (z. B. Videomodelle)
  werden als reine Textkarten ohne Token-Einheiten gezeigt.
- Fehlende Preise/Kontextwerte erzeugen keine Karten und keine erfundenen Einheiten.
- Waehrung/Einheit pro Eintrag: rich_model.price_currency / price_unit (Default USD
  bzw. 'je 1 Mio. Texttoken · Basisrate', reproduziert die bisherige Ausgabe).
- Leere sections/migration/faq werden samt Ueberschrift ausgeblendet; FAQPage-JSON-LD
  nur bei vorhandenen Fragen.
- Pruef-/Preisdatum kommen aus rich_model.checked / rich_model.price_checked,
  Rueckfall auf portraits.json reviewed. Alte Eintraege ohne diese Felder rendern
  unveraendert (IW reviewed 2026-10-19, KIFB reviewed 2026-10-20).
"""
import html,json
E=lambda s:html.escape(str(s),quote=True)
MONTHS=['','Januar','Februar','Maerz','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']
def fmt_dot(iso):
 y,m,dd=str(iso).split('-');return '%d.%d.%s'%(int(dd),int(m),y)
def is_num(v):return isinstance(v,(int,float)) and not isinstance(v,bool)
CSS='''.mr{margin:30px 0}.mr h2{font-size:clamp(26px,3.7vw,38px);line-height:1.2;letter-spacing:-.025em;margin:35px 0 20px}.mr h3{font-size:20px;line-height:1.35;margin:0 0 14px}.mr p,.mr li{font-size:15px;line-height:1.85;color:var(--p-muted)}.mr-answer{padding:30px;border:1px solid var(--p-line);border-radius:12px;background:var(--p-soft)}.mr-answer p{font-size:18px;color:var(--p-fg)}.mr-kicker{font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--p-ac)}.mr-nav{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.mr-nav a{font-size:13px;padding:10px 14px;border:1px solid var(--p-line);border-radius:7px;text-decoration:none}.mr-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:24px 0}.mr-card{border:1px solid var(--p-line);border-radius:12px;padding:26px;min-width:0}.mr a{color:var(--p-ac);overflow-wrap:anywhere}.mr-stat{display:block;font-size:32px;font-weight:700;line-height:1.2;margin:12px 0}.mr-unit{font-size:12px;color:var(--p-muted)}.mr-visual svg{width:100%;height:auto;display:block}.mr-visual{padding:24px;background:var(--p-soft);border-radius:12px}.mr-visual p{font-size:12px}.mr-faq details{border:1px solid var(--p-line);border-radius:10px;margin:12px 0;padding:0 20px}.mr-faq summary{font-size:17px;font-weight:700;cursor:pointer;padding:18px 0}.mr-faq p{margin:0 0 20px}.mr-note{font-size:12px!important}.mr-checklist{padding-left:22px}.mr-related{display:flex;flex-wrap:wrap;gap:15px}.mr-related a{padding:14px;border:1px solid var(--p-line);border-radius:8px;font-size:14px}@media(max-width:650px){.mr-grid{grid-template-columns:minmax(0,1fr)}.mr-card,.mr-answer{padding:22px}.mr-nav a{flex:1 1 calc(50% - 12px);text-align:center;min-width:0;box-sizing:border-box}.mr-visual{padding:15px}.mr-visual svg{display:none}.mr-visual .mr-textchart{display:block}}.mr-textchart{display:none}'''
def render(m,d,technical):
 p=m['rich_model'];name=p['name'];source='<a href="'+E(p['url'])+'">Offizielle Dokumentation: '+E(name)+'</a>';base='https://kifachblatt.de' if technical else 'https://intelligenz-welt.de';path='/ki-modelle/'+m['slug']+('' if technical else '/')
 checked=fmt_dot(p.get('checked') or m.get('checked') or d['reviewed']);price_checked=fmt_dot(p.get('price_checked') or p.get('checked') or m.get('checked') or d['reviewed'])
 num_ctx=is_num(p.get('context')) and is_num(p.get('maxout'))
 num_price=is_num(p.get('input')) and is_num(p.get('output'))
 ctx_partial=not num_ctx and (is_num(p.get('context')) or is_num(p.get('maxout')))
 text_spec=any(isinstance(p.get(k),str) and p.get(k) for k in ('input','output','context','maxout'))
 has_daten=num_ctx or ctx_partial or text_spec
 has_preise=num_price or bool(p.get('pricing_note'))
 has_migration=bool(p.get('migration'))
 has_faq=bool(p.get('faq'))
 nav=[('einsatz','Einsatz & Grenzen')]
 if has_daten:nav.append(('daten','Kontext & Ausgabe' if (num_ctx or ctx_partial) and not text_spec else 'Ein- & Ausgaben'))
 if has_preise:nav.append(('preise','API-Preise'))
 if has_faq:nav.append(('faq','Fragen & Antworten'))
 out='<section class="mr"><div class="mr-answer"><div class="mr-kicker">'+('Technisches Modellportrait' if technical else 'Das Modell einfach erklärt')+'</div><h2>'+E(p['headline'])+'</h2><p>'+E(p['answer'])+'</p>'+source+'<p class="mr-note">Quellen geprüft: '+checked+'. Herstellerangaben, kein eigener Modelltest.</p></div><nav class="mr-nav" aria-label="Auf dieser Modellseite">'+''.join('<a href="#'+i+'">'+t+'</a>' for i,t in nav)+'</nav><h2 id="einsatz">Wofür eignet sich '+E(name)+'?</h2><p>'+E(p['technical'] if technical else p['practical'])+'</p>'
 if p.get('sections'):
  out+='<div class="mr-grid">'
  for title,text in p['sections']:out+='<article class="mr-card"><h3>'+E(title)+'</h3><p>'+E(text)+'</p>'+source+'</article>'
  out+='</div>'
 if has_daten:
  out+='<h2 id="daten">'+('Kontextfenster ist nicht Ausgabelimit.' if num_ctx else 'Kontext und Ausgabe.' if ctx_partial and not text_spec else 'Ein- und Ausgaben im Überblick.')+'</h2>'
  if num_ctx:
   out+='<div class="mr-grid">'
   for value,label in [(f"{p['context']:,}".replace(',','.'),'Token Kontextfenster'),(f"{p['maxout']:,}".replace(',','.'),'maximale Ausgabe-Token, synchron')]:out+='<div class="mr-card"><span class="mr-stat">'+value+'</span><span class="mr-unit">'+label+'</span></div>'
   out+='</div><div class="mr-visual"><svg viewBox="0 0 650 180" role="img" aria-label="'+E(name)+' hat '+str(p['context'])+' Token Kontext und '+str(p['maxout'])+' maximale Ausgabe-Token. Gemeinsame Skala, nicht addieren."><title>Kontext und maximale Ausgabe, in Token</title><text x="0" y="22" font-size="17">Kontext</text><rect x="0" y="35" width="550" height="20" rx="4" fill="#7040cd"/><text x="0" y="90" font-size="17">Maximale Ausgabe (synchron)</text><rect x="0" y="105" width="'+str(p['maxout']/p['context']*550)+'" height="20" rx="4" fill="#ac97ce"/><text x="0" y="165" font-size="14">0</text><text x="550" y="165" text-anchor="end" font-size="14">'+str(p['context'])+' Token</text></svg><div class="mr-textchart"><b>Kontext: '+str(p['context'])+' Token</b><p>Maximale Ausgabe synchron: '+str(p['maxout'])+' Token</p></div><p>Zwei unterschiedliche Grenzen auf gemeinsamer Nullskala, nicht addieren. '+source+'</p></div>'
  else:
   out+='<div class="mr-grid">'
   if is_num(p.get('context')):out+='<div class="mr-card"><span class="mr-stat">'+f"{p['context']:,}".replace(',','.')+'</span><span class="mr-unit">Token Kontextfenster</span></div>'
   if is_num(p.get('maxout')):out+='<div class="mr-card"><span class="mr-stat">'+f"{p['maxout']:,}".replace(',','.')+'</span><span class="mr-unit">maximale Ausgabe-Token, synchron</span></div>'
   for value,label in [(p.get('input'),'Eingabe'),(p.get('output'),'Ausgabe'),(p.get('context') if not is_num(p.get('context')) else None,'Kontext / Grenzen'),(p.get('maxout') if not is_num(p.get('maxout')) else None,'Maximale Ausgabe')]:
    if isinstance(value,str) and value:out+='<div class="mr-card"><h3>'+label+'</h3><p>'+E(value)+'</p></div>'
   out+='</div>'
 if has_preise:
  out+='<h2 id="preise">Was kostet '+E(name)+' über die API?</h2>'
  if num_price:
   currency=str(p.get('price_currency') or 'USD');unit=str(p.get('price_unit') or 'je 1 Mio. Texttoken · Basisrate')
   out+='<div class="mr-grid">'
   for price,label in [(p['input'],'Standard-Eingabe'),(p['output'],'Standard-Ausgabe')]:out+='<div class="mr-card"><h3>'+label+'</h3><span class="mr-stat">'+str(price)+' '+E(currency)+'</span><span class="mr-unit">'+E(unit)+'</span></div>'
   out+='</div>'
  if p.get('pricing_note'):out+='<p>'+E(p['pricing_note'])+'</p>'
  if num_price:out+='<p class="mr-note">Preisstand '+price_checked+'. '+source+'</p>'
 if has_migration:
  out+='<h2>'+('Technische Prüfliste vor der Migration' if technical else 'Vor dem Einsatz prüfen')+'</h2><ul class="mr-checklist">'+''.join('<li>'+E(t)+'</li>' for t in p['migration'])+'</ul>'
 if has_faq:
  out+='<h2 id="faq">Häufige Fragen zu '+E(name)+'</h2><div class="mr-faq">'
  for q,a in p['faq']:out+='<details><summary>'+E(q)+'</summary><p>'+E(a)+'</p></details>'
  out+='</div><p class="mr-note">Alle Antworten beziehen sich auf die verlinkte Herstellerdokumentation und den angegebenen Stand. Kein unabhängiger Benchmark, keine Garantie für Verfügbarkeit oder Ergebnisqualität.</p>'
 out+='<h2>Weiterlesen und vergleichen</h2><div class="mr-related">'
 for x in d['models']:
  if x.get('rich_model') and x['slug']!=m['slug']:out+='<a href="/ki-modelle/'+x['slug']+('' if technical else '/')+'">'+E(x['name'])+' im Portrait ↗</a>'
 out+='</div></section>'
 lds=[]
 if has_faq:lds.append({'@context':'https://schema.org','@type':'FAQPage','@id':base+path+'#faq','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in p['faq']]})
 lds.append({'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Start','item':base+'/'},{'@type':'ListItem','position':2,'name':'KI-Modelle','item':base+'/ki-modelle'+('' if technical else '/')},{'@type':'ListItem','position':3,'name':name,'item':base+path}]})
 return out+'<script type="application/ld+json">'+json.dumps(lds,ensure_ascii=False).replace('</','<\/')+'</script>'
