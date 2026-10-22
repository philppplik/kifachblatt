#!/usr/bin/env python3
"""KIFB Modell-Atlas (Prototyp): kuratierte Modell-Datenbank mit Preisen, Lizenzen,
Benchmark-Belegen und Datenschutz-Steckbriefen. Stdlib only. Keine Netzaufrufe beim Rendern.
Daten: content/modell-atlas.json. Aufruf: python3 tools/modell_atlas.py [output-directory]
Regeln: jede Zahl mit Quelle und Pruefdatum, keine Fremdlogos (Monogramme), Herstellerangaben
als solche markiert, fehlende Werte sichtbar als "nicht gepflegt" statt erfunden.
"""
import sys, json, re, html
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
E = lambda s: html.escape(str(s), quote=True)
BASE = 'https://kifachblatt.de'

CSS = '''
:root{--ma-bg:var(--bg);--ma-fg:var(--ink);--ma-muted:var(--mute);--ma-line:var(--line);--ma-ac:var(--amber);--ma-soft:var(--bg2)}
.modell-atlas{padding-top:34px;padding-bottom:48px}.modell-atlas h1{font-size:clamp(32px,5vw,56px);line-height:1.1;letter-spacing:-.03em;margin:16px 0}
.modell-atlas .ma-lead{font-size:19px;max-width:780px;color:var(--ma-muted);line-height:1.6}
.ma-topline{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ma-ac)}
.ma-note{border:1px solid rgba(127,127,127,.28);background:var(--ma-soft);padding:15px 18px;font-size:13px;line-height:1.6;margin:24px 0;color:var(--ma-muted)}
.ma-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:26px 0}
.ma-kpi{border:1px solid var(--ma-line);border-radius:12px;padding:16px 18px;background:var(--ma-bg)}
.ma-kpi b{display:block;font-size:26px;letter-spacing:-.02em}.ma-kpi span{font-size:12px;color:var(--ma-muted)}
.ma-filter{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin:26px 0 16px}
.ma-filter label{font-size:12px;display:flex;flex-direction:column;gap:6px}.ma-filter label:first-child{flex:1;min-width:200px}
.ma-filter input,.ma-filter select{font:inherit;font-size:15px;min-height:44px;border:1px solid var(--ma-line);border-radius:8px;padding:9px 12px;background:var(--ma-bg);color:var(--ma-fg);width:100%}
.ma-filter input:focus-visible,.ma-filter select:focus-visible{outline:3px solid var(--ma-ac);outline-offset:2px}
.ma-count{font-size:12px;color:var(--ma-muted)}
.ma-tablewrap{overflow-x:auto;border:1px solid var(--ma-line);border-radius:12px}
.ma-table{width:100%;border-collapse:collapse;font-size:14px;min-width:0}
.ma-table th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--ma-muted);text-align:left;padding:12px 14px;border-bottom:1px solid var(--ma-line);white-space:nowrap}
.ma-table td{padding:12px 14px;border-bottom:1px solid var(--ma-line);vertical-align:top}
.ma-table tbody tr:last-child td{border-bottom:0}
.ma-table td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.ma-table th.num{text-align:right}
.ma-mono{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;background:var(--ma-soft);color:var(--ma-ac);border:1px solid var(--ma-line);border-radius:10px;font-size:12px;font-weight:800;flex:none}
.ma-mname{display:flex;gap:10px;align-items:center;min-width:0}
.ma-mname a{font-weight:700;text-decoration:none}
.ma-sub{display:block;font-size:12px;color:var(--ma-muted);font-weight:400}
.ma-badge{display:inline-block;font-size:11px;border:1px solid var(--ma-line);border-radius:999px;padding:3px 10px;white-space:nowrap}
.ma-badge.open{background:var(--ma-soft)}
.ma-badge.ok{border-color:rgba(22,101,52,.45);color:#166534}
.ma-badge.openq{color:var(--ma-muted)}
.ma-btable{table-layout:fixed}
.ma-btable th:nth-child(2){width:150px}
.ma-table.ma-btable td,.ma-table.ma-btable td.num{white-space:normal;overflow-wrap:break-word}
.ma-missing{color:var(--ma-muted);font-style:italic;font-size:13px}
.ma-empty{padding:24px;border:1px dashed var(--ma-line);border-radius:12px;color:var(--ma-muted)}
.ma-layout{display:grid;grid-template-columns:minmax(0,2fr) minmax(240px,1fr);gap:32px;align-items:start;margin-top:32px}
.ma-panel{border:1px solid var(--ma-line);border-radius:14px;padding:24px;margin-bottom:22px;min-width:0}
.ma-panel h2{margin:0 0 14px;font-size:21px;line-height:1.3}
.ma-panel p,.ma-panel li{font-size:15px;line-height:1.75}
.ma-facts{margin:0}.ma-facts>div{padding:12px 0;border-top:1px solid var(--ma-line)}
.ma-facts dt{font-size:12px;color:var(--ma-muted)}.ma-facts dd{font-size:15px;font-weight:600;margin:4px 0 0;overflow-wrap:anywhere}
.ma-source{font-size:12px;color:var(--ma-muted);overflow-wrap:anywhere}
.ma-source li{font-size:13px;margin-bottom:4px}
.ma-stand{font-size:12px;color:var(--ma-muted);margin-top:20px}
.ma-breadcrumb{font-size:12px;color:var(--ma-muted)}.ma-breadcrumb a{text-decoration:none}
@media(max-width:900px){.ma-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.ma-layout{grid-template-columns:minmax(0,1fr);gap:0}}
@media(max-width:640px){
 .ma-table,.ma-table tbody,.ma-table tr,.ma-table td{display:block;width:100%}
 .ma-table thead{position:absolute;left:-9999px}
 .ma-table tr{border-bottom:1px solid var(--ma-line);padding:10px 0}
 .ma-table tbody tr:last-child{border-bottom:0}
 .ma-table td{border:0;padding:5px 14px;display:flex;justify-content:space-between;gap:14px}
 .ma-table td.num{text-align:right}
 .ma-table td::before{content:attr(data-label);font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--ma-muted);flex:none;padding-top:2px}
 .ma-table td.ma-bench{display:block}
 .ma-table td.ma-bench::before{display:block;margin-bottom:2px}
 .ma-table td:first-child{display:block}
 .ma-table td:first-child::before{content:none}
 .ma-tablewrap{border:0}
 .ma-filter label{flex:1;min-width:100%}
}
'''
FILTER_JS = '''(function(){var q=document.getElementById('maq'),p=document.getElementById('map'),z=document.getElementById('maz'),rows=Array.from(document.querySelectorAll('[data-ma]')),count=document.getElementById('macount'),empty=document.getElementById('maempty');if(!q)return;function n(t){return t.toLocaleLowerCase('de').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')}function f(){var term=n(q.value),pv=p?p.value:'',zv=z?z.value:'';var hits=0;rows.forEach(function(r){var ok=n(r.textContent).includes(term)&&(!pv||r.dataset.provider===pv)&&(!zv||r.dataset.access===zv);r.hidden=!ok;if(ok)hits++});count.textContent=hits+' von '+rows.length+' Modellen';empty.hidden=hits!==0}q.addEventListener('input',f);if(p)p.addEventListener('change',f);if(z)z.addEventListener('change',f);f()})();'''

ACCESS = {'api':'API','open_weights':'Offene Gewichte','api_und_gewichte':'API + Gewichte','unklar':'Zugang unklar'}
BENCH_NAMES = {'gpqa':'GPQA','swe-bench-verified':'SWE-bench Verified','terminal-bench-2-1':'Terminal-Bench 2.1','mmlu-pro':'MMLU-Pro',
    'humanitys-last-exam':"Humanity's Last Exam",'browsecomp':'BrowseComp','osworld':'OSWorld','tau2-bench':'τ²-Bench','cybergym':'CyberGym','mle-bench':'MLE-bench'}

def load(root='.'):
    return json.loads((Path(root)/'content/modell-atlas.json').read_text(encoding='utf-8'))

def validate(d):
    assert d['schema_version'] == 1, 'schema_version'
    providers = {p['slug'] for p in d['providers']}
    for p in d['providers']:
        assert re.fullmatch('[a-z0-9-]+', p['slug']) and p['name']
        assert p['privacy']['status'] in ('geprueft','in_pruefung')
        if p['privacy']['status'] == 'geprueft':
            assert p['privacy']['training'] and p['privacy']['sources'], 'gepruefter Datenschutz-Steckbrief braucht Aussagen und Quellen'
        for k in p['privacy']['sources']: assert k in d['sources'], k
    slugs = [m['slug'] for m in d['models']]
    assert len(slugs) == len(set(slugs))
    for m in d['models']:
        assert re.fullmatch('[a-z0-9-]+', m['slug']) and m['name'] and m['summary'] and m.get('initials')
        assert m['provider'] in providers, m['slug']
        assert m['access'] in ACCESS, m['slug']
        assert m['license']['text'] and m['license']['source'] in d['sources'], m['slug']
        for k in m['sources']: assert k in d['sources'], (m['slug'], k)
        pr = m.get('pricing')
        if pr:
            assert isinstance(pr['input'], (int, float)) and isinstance(pr['output'], (int, float)), m['slug']
            assert pr['currency'] == 'USD' and pr['unit'] and pr['tier'] and pr['notes'], m['slug']
            assert pr['source'] in d['sources'], m['slug']
        for b in m.get('benchmarks', []):
            assert b['value'] and b['metric'] and b['reported_by'] and b['source'] in d['sources'], m['slug']
    for key, s in d['sources'].items():
        assert urlparse(s['url']).scheme == 'https' and re.fullmatch(r'\d{4}-\d{2}-\d{2}', s['accessed']), key

def initials(name):
    return ''.join(w[0] for w in re.split(r'[\s-]+', name) if w and w[0].isalnum())[:2].upper()

def fmt_price(v):
    return ('%.2f' % v).rstrip('0').rstrip('.').replace('.', ',')

def kpis(d):
    priced = sum(1 for m in d['models'] if m.get('pricing'))
    weights = sum(1 for m in d['models'] if m['access'] in ('open_weights','api_und_gewichte'))
    priv = sum(1 for p in d['providers'] if p['privacy']['status'] == 'geprueft')
    return len(d['models']), priced, weights, priv

def privacy_badge(p):
    if p['privacy']['status'] == 'geprueft':
        return '<span class="ma-badge ok">Steckbrief geprüft</span>'
    return '<span class="ma-badge openq">in Prüfung</span>'

def price_cell(m):
    pr = m.get('pricing')
    if not pr:
        return '<span class="ma-missing">nicht gepflegt</span>'
    return '%s / %s $<span class="ma-sub"> pro 1 Mio. Token (Ein-/Ausgabe), %s</span>' % (fmt_price(pr['input']), fmt_price(pr['output']), E(pr['tier']))

def bench_cell(m, d):
    if not m.get('benchmarks'):
        return '<span class="ma-missing">kein Beleg erfasst</span>'
    out = []
    for b in m['benchmarks'][:2]:
        out.append('%s %s: <b>%s</b><span class="ma-sub">%s, Herstellerangabe</span>' % (E(BENCH_NAMES.get(b['benchmark'], b['benchmark'])), E(b['variant']), E(b['value']), E(b['reported_by'])))
    return '<br>'.join(out)

def render(out='.'):
    out = Path(out)
    d = load(out)
    validate(d)
    template = (out/'halluzinationen.html').read_text(encoding='utf-8')
    shell_top = template[template.index('<body>'):template.index('<main id="main">')]
    foot = template[template.index('</main>')+7:]
    (out/'assets').mkdir(exist_ok=True)
    (out/'assets/modell-atlas.css').write_text(CSS, encoding='utf-8')
    (out/'assets/modell-atlas.js').write_text(FILTER_JS, encoding='utf-8')
    providers = {p['slug']: p for p in d['providers']}

    def page(path, title, desc, inner, ld):
        h = template[:template.index('<body>')]
        h = re.sub(r'<title>.*?</title>', '<title>' + E(title + ' | KI Fachblatt') + '</title>', h, flags=re.S)
        h = re.sub(r'<script type="application/ld\+json">.*?</script>', '', h, flags=re.S)
        h = re.sub(r'<meta (?:name="description"|property="og:[^"]*"|name="twitter:[^"]*")[^>]*>', '', h)
        h = re.sub(r'<link rel="canonical"[^>]*>', '', h)
        ldscript = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
        extra = '<meta name="description" content="%s"><link rel="canonical" href="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><link rel="stylesheet" href="/assets/modell-atlas.css"><script type="application/ld+json">%s</script>' % (E(desc), BASE+path, E(title), E(desc), BASE+path, ldscript)
        h = h.replace('</head>', extra + '</head>')
        body = '<main id="main"><div class="wrap modell-atlas">%s</div></main>' % inner
        t = out/(path.strip('/') + '.html')
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(h + shell_top + body + foot, encoding='utf-8')

    def refs(keys):
        keys = list(dict.fromkeys(keys))
        items = ''.join('<li><a href="%s" rel="noopener">%s</a><br>Geprüft: %s</li>' % (E(d['sources'][k]['url']), E(d['sources'][k]['title']), d['sources'][k]['accessed']) for k in keys)
        return ('<section class="ma-panel"><h2>Quellen &amp; Stand</h2><ol class="ma-source">%s</ol>'
                '<p class="ma-source">Redaktionelle Zusammenstellung mit KI-Unterstützung, verantwortet von Philipp Paulik. '
                'Keine eigenen Leistungstests. Anbieterangaben gelten für den angegebenen Quellenstand und können sich ändern.</p></section>') % items

    # --- Index ---
    n_models, n_priced, n_weights, n_priv = kpis(d)
    rows = ''
    for m in d['models']:
        p = providers[m['provider']]
        rows += ('<tr data-ma data-provider="%s" data-access="%s">'
                 '<td><span class="ma-mname"><span class="ma-mono" aria-hidden="true">%s</span><span><a href="/modell-atlas/%s">%s</a><span class="ma-sub">%s</span></span></span></td>'
                 '<td data-label="Zugang"><span class="ma-badge%s">%s</span></td>'
                 '<td data-label="Kontext" class="num">%s</td>'
                 '<td data-label="Preis" class="num">%s</td>'
                 '<td data-label="Benchmarks" class="ma-bench">%s</td>'
                 '<td data-label="Datenschutz">%s</td></tr>') % (
            E(m['provider']), E(m['access']),
            E(m.get('initials') or initials(m['name'])), E(m['slug']), E(m['name']), E(p['name']),
            ' open' if m['access'] in ('open_weights','api_und_gewichte') else '', E(ACCESS[m['access']]),
            ('{:,}'.format(m['context_tokens']).replace(',', '.')) if m.get('context_tokens') else '<span class="ma-missing">–</span>',
            price_cell(m), bench_cell(m, d), privacy_badge(p))
    intro = ('Preise, Kontextfenster, Lizenzen, Benchmark-Belege und Datenschutz-Steckbriefe der Modelle, über die das KI Fachblatt berichtet - eine Datenbank zum Vergleichen statt einer Bestenliste.')
    inner = ('<div class="ma-topline">Modell-Atlas · Prototyp</div><h1>Modell-Atlas</h1><p class="ma-lead">%s</p>'
             '<div class="ma-kpis"><div class="ma-kpi"><b>%d</b><span>Modelle im Atlas</span></div><div class="ma-kpi"><b>%d</b><span>mit gepflegtem Preis</span></div><div class="ma-kpi"><b>%d</b><span>mit offenen Gewichten</span></div><div class="ma-kpi"><b>%d</b><span>Anbieter mit geprüftem Datenschutz-Steckbrief</span></div></div>'
             '<p class="ma-note">Quellenstand: 22. Oktober 2026. Preise sind Listenpreise der Anbieter in US-Dollar je 1 Mio. Token im genannten Tarif, keine Angebote des KI Fachblatts. Benchmark-Werte sind Herstellerangaben, keine eigenen Messungen. Fehlende Angaben werden als „nicht gepflegt“ gezeigt statt geschätzt. Keine Rechts- oder Anlageberatung.</p>'
             '<div class="ma-filter"><label>Modelle durchsuchen<input id="maq" type="search" placeholder="Name, Anbieter oder Eigenschaft …"></label>'
             '<label>Anbieter<select id="map"><option value="">Alle Anbieter</option>%s</select></label>'
             '<label>Zugang<select id="maz"><option value="">Jeder Zugang</option>%s</select></label></div>'
             '<p id="macount" class="ma-count" role="status">%d Modelle</p>'
             '<div class="ma-tablewrap"><table class="ma-table"><thead><tr><th scope="col">Modell</th><th scope="col">Zugang</th><th scope="col" class="num">Kontext (Token)</th><th scope="col" class="num">Preis Ein-/Ausgabe</th><th scope="col">Benchmark-Belege</th><th scope="col">Datenschutz</th></tr></thead><tbody>%s</tbody></table></div>'
             '<p id="maempty" class="ma-empty" hidden>Keine passenden Modelle. Versuche einen anderen Begriff.</p>'
             '<p class="ma-note"><b>Als Datenpaket mitnehmen:</b> Die komplette Auswertung als PDF, dazu alle Werte als CSV und JSON - <a href="/atlas-daten-anmelden">Modell-Atlas-Datenpaket gratis per E-Mail-Bestätigung laden</a>. Kein Kauf, kein Preis.</p>'
             '<p class="ma-stand">Ausführliche Porträts der Modelle stehen im <a href="/ki-modelle">KI-Verzeichnis</a>. Methodik und Pflegeprozess: jede Zahl trägt Quelle und Prüfdatum; Details auf den Modellseiten.</p>'
             '<script src="/assets/modell-atlas.js" defer></script>') % (
        intro, n_models, n_priced, n_weights, n_priv,
        ''.join('<option value="%s">%s</option>' % (E(p['slug']), E(p['name'])) for p in d['providers']),
        ''.join('<option value="%s">%s</option>' % (k, E(v)) for k, v in ACCESS.items()),
        n_models, rows)
    page('/modell-atlas', 'Modell-Atlas: Preise, Lizenzen, Benchmarks und Datenschutz im Vergleich', intro, inner,
         {'@context':'https://schema.org','@type':'CollectionPage','name':'Modell-Atlas','url':BASE+'/modell-atlas',
          'dateModified': d['reviewed'],
          'mainEntity':{'@type':'ItemList','numberOfItems':n_models,'itemListElement':[{'@type':'ListItem','position':i+1,'url':BASE+'/modell-atlas/'+m['slug'],'name':m['name']} for i,m in enumerate(d['models'])]}})

    # --- Detail pages ---
    for m in d['models']:
        p = providers[m['provider']]
        keys = list(m['sources'])
        facts = []
        if m.get('api_id'): facts.append(('API-ID', m['api_id']))
        facts.append(('Zugang', ACCESS[m['access']]))
        if m.get('context_tokens'): facts.append(('Kontextfenster', '{:,} Token'.format(m['context_tokens']).replace(',', '.')))
        if m.get('max_output_tokens'): facts.append(('Maximale Ausgabe', '{:,} Token'.format(m['max_output_tokens']).replace(',', '.')))
        facts_html = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (E(k), E(v)) for k, v in facts)

        if m.get('pricing'):
            pr = m['pricing']; keys.append(pr['source'])
            price_html = ('<section class="ma-panel"><h2>Preis</h2><p><b>%s&nbsp;$</b> Eingabe · <b>%s&nbsp;$</b> Ausgabe, jeweils pro 1 Mio. Token (%s, %s).</p><p>%s</p>'
                          '<p class="ma-source">Listenpreis des Anbieters, Stand %s. Eigene Rechnung: 1 Mio. Eingabe- und 1 Mio. Ausgabe-Token kosten zusammen %s&nbsp;$.</p></section>') % (
                fmt_price(pr['input']), fmt_price(pr['output']), E(pr['currency']), E(pr['tier']), E(pr['notes']),
                d['sources'][pr['source']]['accessed'], fmt_price(round(pr['input']+pr['output'], 2)))
        else:
            price_html = ('<section class="ma-panel"><h2>Preis</h2><p class="ma-missing">Für dieses Modell ist noch kein Preis gepflegt.</p>'
                          '<p class="ma-source">Wir zeigen keine geschätzten oder veralteten Preise. Der nächste Pflegedurchlauf prüft die Preisseite des Anbieters und ergänzt Quelle und Datum.</p></section>')

        lic = m['license']; keys.append(lic['source'])
        license_html = ('<section class="ma-panel"><h2>Lizenz</h2><p>%s</p>'
                        '<p class="ma-source">Lizenzhinweis laut %s (geprüft: %s). Lizenztexte ändern sich; vor produktiver Nutzung den aktuellen Text beim Anbieter prüfen. Keine Rechtsberatung.</p></section>') % (
            E(lic['text']), E(d['sources'][lic['source']]['title']), d['sources'][lic['source']]['accessed'])

        pv = p['privacy']
        for k in pv['sources']: keys.append(k)
        if pv['status'] == 'geprueft':
            rows_priv = ''
            if pv['training']: rows_priv += '<div><dt>Trainingsnutzung</dt><dd>%s</dd></div>' % E(pv['training'])
            if pv['dpa']: rows_priv += '<div><dt>Auftragsverarbeitung</dt><dd>%s</dd></div>' % E(pv['dpa'])
            if pv['retention']: rows_priv += '<div><dt>Aufbewahrung</dt><dd>%s</dd></div>' % E(pv['retention'])
            priv_html = ('<section class="ma-panel"><h2>Datenschutz-Steckbrief: %s</h2><dl class="ma-facts">%s</dl>'
                         '<p class="ma-source">%s Stand: %s. Eigenangaben des Anbieters; der AVV-/DPA-Text im Vertrag ist maßgeblich. Keine Rechtsberatung.</p></section>') % (
                E(p['name']), rows_priv, E(pv['note'] + ' '), max(d['sources'][k]['accessed'] for k in pv['sources']))
        else:
            priv_html = ('<section class="ma-panel"><h2>Datenschutz-Steckbrief: %s</h2><p class="ma-missing">In Prüfung.</p><p>%s</p>'
                         '<p class="ma-source">Wir veröffentlichen keine Datenschutz-Aussagen ohne geprüfte Primärquelle.</p></section>') % (E(p['name']), E(pv['note']))

        bench_html = '<section class="ma-panel"><h2>Benchmark-Belege</h2>'
        if m.get('benchmarks'):
            bench_html += '<p class="ma-source">Herstellerbericht, keine eigene Messung. Keine direkt vergleichbare Rangliste: Testkonfigurationen unterscheiden sich.</p><div class="ma-tablewrap"><table class="ma-table ma-btable"><thead><tr><th scope="col">Benchmark</th><th scope="col" class="num">Wert</th><th scope="col">Kontext</th></tr></thead><tbody>'
            for b in m['benchmarks']:
                keys.append(b['source'])
                bench_html += '<tr><td>%s <span class="ma-sub">%s</span></td><td class="num"><b>%s</b> <span class="ma-sub">%s</span></td><td class="ma-sub">%s · Quelle: %s, Abruf %s</td></tr>' % (
                    E(BENCH_NAMES.get(b['benchmark'], b['benchmark'])), E(b['variant']), E(b['value']), E(b['metric']),
                    E(b['reported_by']), E(d['sources'][b['source']]['title']), d['sources'][b['source']]['accessed'])
            bench_html += '</tbody></table></div>'
        else:
            bench_html += '<p class="ma-missing">Noch kein ausreichend zugeordneter Beleg erfasst.</p><p class="ma-source">Fehlende Werte sind keine Null. Wir übernehmen keine Werte aus ähnlich benannten Modell- oder Benchmark-Versionen.</p>'
        bench_html += '</section>'

        crumb = '<nav class="ma-breadcrumb" aria-label="Brotkrumen"><a href="/">Start</a> / <a href="/modell-atlas">Modell-Atlas</a> / %s</nav>' % E(m['name'])
        body = (crumb + '<div class="ma-topline">Modell-Atlas · %s</div><h1>%s</h1><p class="ma-lead">%s</p>'
                '<p class="ma-stand">Anbieter: %s · Quellenstand: %s · <a href="%s">Ausführliches Porträt im KI-Verzeichnis</a></p>'
                '<div class="ma-layout"><div>%s%s%s%s</div><aside><section class="ma-panel"><h2>Steckbrief</h2><dl class="ma-facts">%s</dl></section>%s</aside></div>') % (
            E(ACCESS[m['access']]), E(m['name']), E(m['summary']),
            E(p['name']), d['reviewed'], E(m['portrait']),
            price_html, license_html, priv_html, bench_html, facts_html, refs(keys))
        page('/modell-atlas/' + m['slug'], m['name'] + ': Preis, Lizenz, Benchmarks und Datenschutz', m['summary'], body,
             {'@context':'https://schema.org','@type':'Article','headline':m['name']+' im Modell-Atlas','description':m['summary'],
              'dateModified': d['reviewed'],'author':{'@type':'Person','name':'Philipp Paulik'},
              'citation':[d['sources'][k]['url'] for k in dict.fromkeys(keys)],'mainEntityOfPage':BASE+'/modell-atlas/'+m['slug']})

    # Sitemap idempotent ergänzen
    sp = out/'sitemap.xml'
    if sp.exists():
        text = sp.read_text(encoding='utf-8')
        text = re.sub(r'<url>\s*<loc>' + re.escape(BASE) + r'/modell-atlas(?:/[^<]*)?</loc>.*?</url>', '', text, flags=re.S)
        urls = [BASE+'/modell-atlas'] + [BASE+'/modell-atlas/'+m['slug'] for m in d['models']]
        text = text.replace('</urlset>', ''.join('<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (u, d['reviewed']) for u in urls) + '</urlset>')
        sp.write_text(text, encoding='utf-8')

    # Suchindex idempotent ergänzen
    si = out/'search-index.json'
    if si.exists():
        payload = json.loads(si.read_text(encoding='utf-8'))
        urls = {'/modell-atlas'} | {'/modell-atlas/'+m['slug'] for m in d['models']}
        payload['docs'] = [x for x in payload['docs'] if x['u'] not in urls]
        payload['docs'].append({'t':'Modell-Atlas','u':'/modell-atlas','k':'Datenbank','d':intro,'g':'Modell-Atlas','x':intro,'ts':0,'dt':'20.10.2026'})
        for m in d['models']:
            payload['docs'].append({'t':m['name']+' im Modell-Atlas','u':'/modell-atlas/'+m['slug'],'k':'Modell-Atlas','d':m['summary'],'g':m['provider'],'x':m['summary']+' '+m['license']['text'],'ts':0,'dt':'20.10.2026'})
        si.write_text(json.dumps(payload, ensure_ascii=False, separators=(',',':')), encoding='utf-8')

    # Navigations- und Footer-Link idempotent
    for f in out.rglob('*.html'):
        if any(part in ('content','tools','modell-atlas') for part in f.relative_to(out).parts):
            continue
        text = f.read_text(encoding='utf-8'); old = text
        if 'href="/modell-atlas"' not in text and 'class="p-nav"' in text:
            text = re.sub(r'(<a class="p-nav" href="/ki-modelle">Portraits</a>)', r'\1<a class="p-nav" href="/modell-atlas">Atlas</a>', text, count=1)
        if '<a href="/modell-atlas">Modell-Atlas</a>' not in text and 'data-portrait-footer' in text:
            text = text.replace('<a href="/ki-modelle">KI-Modell-Portraits</a>', '<a href="/ki-modelle">KI-Modell-Portraits</a> · <a href="/modell-atlas">Modell-Atlas</a>', 1)
        if text != old:
            f.write_text(text, encoding='utf-8')

    print('modell-atlas: %d Modelle, %d Detailseiten, %d mit Preis' % (n_models, len(d['models']), n_priced))

if __name__ == '__main__':
    render(sys.argv[1] if len(sys.argv) > 1 else '.')
