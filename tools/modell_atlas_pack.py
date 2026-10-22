#!/usr/bin/env python3
"""Modell-Atlas-Datenpaket (ZIP) fuer den Leadwall-Download bauen.
Inhalt: prototyp-modell-radar.pdf (Beispielauswertung), modell-atlas.csv, modell-atlas.json, LIESMICH.txt.
Schreibt nach build-artifacts/ (nicht committed). Aufruf: python3 tools/modell_atlas_pack.py
"""
import csv, io, json, os, sys, zipfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = '1.0'

def build_zip(root='.'):
    root = Path(root)
    d = json.loads((root/'content/modell-atlas.json').read_text(encoding='utf-8'))
    providers = {p['slug']: p for p in d['providers']}

    # 1) Radar-PDF erzeugen (schreibt berichte/prototyp-modell-radar.{html,pdf})
    import modell_radar
    modell_radar.build(str(root))
    pdf_path = root/'berichte/prototyp-modell-radar.pdf'
    if not pdf_path.exists():
        raise SystemExit('modell_atlas_pack: Radar-PDF wurde nicht erzeugt (Chrome fehlt?)')

    # 2) CSV aus den kuratierten Daten
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['Modell', 'Anbieter', 'Zugang', 'API-ID', 'Kontextfenster (Token)', 'Max. Ausgabe (Token)',
                'Preis Eingabe (USD/1 Mio.)', 'Preis Ausgabe (USD/1 Mio.)', 'Tarif', 'Preis-Hinweise',
                'Lizenz', 'Datenschutz-Status Anbieter', 'Benchmark-Belege (Anzahl)', 'Quellenstand'])
    for m in d['models']:
        p = providers[m['provider']]
        pr = m.get('pricing') or {}
        w.writerow([m['name'], p['name'], m['access'], m.get('api_id') or '',
                    m.get('context_tokens') or '', m.get('max_output_tokens') or '',
                    pr.get('input', ''), pr.get('output', ''), pr.get('tier', ''), pr.get('notes', ''),
                    m['license']['text'], p['privacy']['status'], len(m.get('benchmarks', [])), d['reviewed']])

    # 3) LIESMICH
    liesmich = (
        'Modell-Atlas-Datenpaket des KI Fachblatts - Version %s, Quellenstand %s\n'
        '========================================================================\n\n'
        'INHALT\n'
        '- prototyp-modell-radar.pdf  Beispielauswertung: API-Listenpreise und Datenschutz-Matrix\n'
        '  der Modelle im Atlas (Prototyp-Markierung, nicht zum Verkauf bestimmt).\n'
        '- modell-atlas.csv           Alle %d Modelle mit Preis, Kontextfenster, Lizenz, Datenschutz-Status.\n'
        '- modell-atlas.json          Die kuratierten Originaldaten inkl. Benchmark-Belegen und Quellen-URLs.\n\n'
        'EINORDNUNG\n'
        'Redaktionelle Zusammenstellung mit KI-Unterstuetzung, verantwortet von Philipp Paulik (KI Fachblatt).\n'
        'Preise sind Listenpreise der Anbieter, Benchmark-Werte Herstellerangaben - keine eigenen Messungen,\n'
        'keine Angebote des KI Fachblatts. Jeder Wert traegt Quelle und Pruefdatum (siehe JSON, Feld sources).\n'
        'Keine Rechts-, Steuer- oder Anlageberatung. Anbieterangaben koennen sich geaendert haben;\n'
        'massgeblich sind die verlinkten Primaerquellen.\n\n'
        'KI Fachblatt - kifachblatt.de/modell-atlas - redaktion@kifachblatt.de\n'
    ) % (VERSION, d['reviewed'], len(d['models']))

    out = root/'build-artifacts'
    out.mkdir(exist_ok=True)
    z = out/('modell-atlas-datenpaket-v%s.zip' % VERSION)
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(pdf_path, 'prototyp-modell-radar.pdf')
        zipf.writestr('modell-atlas.csv', buf.getvalue())
        zipf.writestr('modell-atlas.json', json.dumps(d, ensure_ascii=False, indent=1))
        zipf.writestr('LIESMICH.txt', liesmich)
    print('modell_atlas_pack: %s (%d bytes)' % (z, z.stat().st_size))
    return z

if __name__ == '__main__':
    build_zip(sys.argv[1] if len(sys.argv) > 1 else '.')
