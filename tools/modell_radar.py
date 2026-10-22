#!/usr/bin/env python3
"""KIFB Modell-Radar (Prototyp): Beispielseiten des geplanten Report-PDFs aus dem Modell-Atlas.
Nutzt das bestehende A4-Layout (report_core) und die Atlas-Daten. Stdlib only, keine Netzaufrufe.
Aufruf: python3 tools/modell_radar.py [output-directory] -> berichte/prototyp-modell-radar.html/.pdf
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_core import esc, render, to_pdf, logo_inline, lnk, dom

CSS = '''
.mr-kpis{display:flex;gap:4mm;margin:4mm 0}.mr-kpis div{flex:1;border:1px solid #dfe2ec;border-radius:4px;padding:3mm;text-align:center}
.mr-kpis b{display:block;font-size:16pt;color:#3d2380}.mr-kpis span{font-size:8pt;color:#6b7080}
.mr-priv td,.mr-priv th{white-space:normal!important;font-size:8.4pt}
.mr-badge{display:inline-block;border:1px solid #cfd3de;border-radius:8px;padding:0 6px;font-size:8pt}
.mr-ok{border-color:#166534;color:#166534}
.mr-open{color:#6b7080}
.mr-note{background:#f5f1fc;border:1px solid #dcd0f3;border-radius:4px;padding:3mm 4mm;font-size:9pt;color:#2b3042;margin:3mm 0}
'''

def build(root='.'):
    root = Path(root)
    d = json.loads((root/'content/modell-atlas.json').read_text(encoding='utf-8'))
    providers = {p['slug']: p for p in d['providers']}
    priced = [m for m in d['models'] if m.get('pricing')]
    fmt = lambda v: ('%.2f' % v).rstrip('0').rstrip('.').replace('.', ',')

    rows = ''.join(
        '<tr><td class="l"><b>%s</b><br><span class="mut">%s</span></td><td>%s</td><td>%s</td><td class="l">%s</td><td class="l w">%s</td></tr>' % (
            esc(m['name']), esc(providers[m['provider']]['name']),
            fmt(m['pricing']['input']), fmt(m['pricing']['output']),
            esc(m['pricing']['tier']), esc(m['pricing']['notes']))
        for m in sorted(priced, key=lambda x: x['pricing']['input'] + x['pricing']['output']))
    p1 = ('<style>%s</style>' % CSS +
          '<h2>API-Listenpreise <small>USD je 1 Mio. Token · Stand %s · %d Modelle mit gepflegtem Preis</small></h2>'
          '<table><thead><tr><th class="l">Modell</th><th>Eingabe $</th><th>Ausgabe $</th><th class="l">Tarif</th><th class="l w">Hinweise</th></tr></thead><tbody>%s</tbody></table>'
          '<div class="mr-note"><b>So lesen:</b> Listenpreise der Anbieter, keine Angebote des KI Fachblatts. Tarife unterscheiden sich (Standard, Peak, bezahlte Stufe); die Tabelle nennt den Tarif je Zeile. Cache-, Batch- und Aktionspreise stehen in den Hinweisen und in der Quelle.</div>'
          '<div class="mr-kpis"><div><b>%d</b><span>Modelle im Atlas</span></div><div><b>%d</b><span>mit gepflegtem Preis</span></div><div><b>%d</b><span>Anbieter</span></div><div><b>%d</b><span>Anbieter mit geprüftem Datenschutz-Steckbrief</span></div></div>') % (
          d['reviewed'], len(priced), rows, len(d['models']), len(priced), len(d['providers']),
          sum(1 for p in d['providers'] if p['privacy']['status'] == 'geprueft'))

    priv_rows = ''
    for p in d['providers']:
        pv = p['privacy']
        if pv['status'] == 'geprueft':
            badge = '<span class="mr-badge mr-ok">geprüft</span>'
            txt = '<b>Training:</b> %s<br><b>AVV/DPA:</b> %s' % (esc(pv['training']), esc(pv['dpa']))
        else:
            badge = '<span class="mr-badge mr-open">in Prüfung</span>'
            txt = esc(pv['note'])
        priv_rows += '<tr><td class="l"><b>%s</b></td><td class="l">%s</td><td class="l w">%s</td></tr>' % (esc(p['name']), badge, txt)
    p2 = ('<h2>Datenschutz-Matrix <small>Trainingsnutzung und Auftragsverarbeitung · Eigenangaben der Anbieter</small></h2>'
          '<table class="mr-priv"><thead><tr><th class="l">Anbieter</th><th class="l">Status</th><th class="l">Aussagen (Quellenstand %s)</th></tr></thead><tbody>%s</tbody></table>'
          '<div class="mr-note"><b>Einordnung:</b> Eigenangaben, keine Prüfung durch Dritte. Maßgeblich ist der Vertragstext des jeweiligen AVV/DPA. Keine Rechtsberatung. Anbieter ohne geprüfte Primärquelle führen den Status „in Prüfung" statt einer Aussage.</div>') % (d['reviewed'], priv_rows)

    keys = sorted({(m['pricing'] or {}).get('source') for m in d['models']} - {None})
    sl = ''.join('<li>%s <span class="mut">(%s, geprüft %s)</span></li>' % (lnk(d['sources'][k]['url'], d['sources'][k]['title']), dom(d['sources'][k]['url']), d['sources'][k]['accessed']) for k in keys)
    p3 = '<h2>Quellen der Preisdaten</h2><div class="sl"><ol>%s</ol></div>' % sl

    last = ('<h2>Impressum &amp; Redaktionsschluss</h2>'
            '<p><b>PROTOTYP.</b> Diese Beispielausgabe zeigt Aufbau und Datenlage des geplanten KIFB Modell-Radars. Sie ist nicht zum Verkauf bestimmt und nicht vollständig: Modelle ohne gepflegten Preis fehlen in der Preistabelle.</p>'
            '<h3>Redaktion</h3><p>KI Fachblatt, Redaktion Philipp Paulik · kifachblatt.de</p>'
            '<h3>Hinweis zu KI</h3><p>Erstellt mit KI-Unterstützung, redaktionell verantwortet vom KI Fachblatt. Alle Zahlen tragen Quelle und Prüfdatum; trotz Prüfung können Fehler nicht ausgeschlossen werden. Korrekturen: kifachblatt.de/korrekturen</p>'
            '<h3>Keine Beratung</h3><p>Diese Ausgabe ersetzt keine Rechts-, Steuer- oder Anlageberatung.</p>')

    logo = logo_inline(str(root/'assets/logo.svg'))
    htm = render('KI Fachblatt', 'Modell-Radar', d['reviewed'], '#7040cd', '#3d2380', '#f5f1fc', '#dcd0f3', logo,
                 'Modell-Radar', 'Prototyp · Preise und Datenschutz der Modelle im Vergleich', [p1, p2, p3], last)
    out_html = root/'berichte/prototyp-modell-radar.html'
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(htm, encoding='utf-8')
    pdf = root/'berichte/prototyp-modell-radar.pdf'
    ok = to_pdf(str(out_html), str(pdf))
    print('modell-radar prototyp: %s (PDF: %s)' % (out_html, 'ok' if ok else 'kein Chrome'))

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '.')
