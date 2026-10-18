"""KI-Tagesbericht (A4 PDF + print page). Called from build.py. Data: Hugging Face public API (no key), own articles."""
import json, os, re, sys, urllib.request, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_core import esc, DAYS, render, to_pdf, logo_inline

HF = 'https://huggingface.co/api/models?sort=trendingScore&limit=20&expand[]=likes&expand[]=downloads&expand[]=pipeline_tag&expand[]=createdAt&expand[]=trendingScore&expand[]=library_name'
HF_PUBLIC = 'https://huggingface.co/models?sort=trending'
nf = lambda v: '{:,}'.format(int(v)).replace(',', '.') if isinstance(v, (int, float)) else '–'

def fetch_models():
    try:
        req = urllib.request.Request(HF, headers={'User-Agent': 'kifachblatt-report/1.0 (+https://kifachblatt.de)'})
        return json.load(urllib.request.urlopen(req, timeout=25))
    except Exception as e:
        print('HF API failed:', e); return None

def build(arts, now, base, root='.'):
    day = DAYS[now.weekday()] + ', ' + now.strftime('%d.%m.%Y'); stamp = now.strftime('%d.%m.%Y, %H:%M') + ' Uhr'
    models = fetch_models()
    if models:
        rows = ''.join('<tr><td class="l">%d</td><td class="l w"><b>%s</b></td><td class="l">%s</td><td>%s</td><td>%s</td><td>%s</td><td class="l">%s</td></tr>' % (
            i + 1, esc(m['id']), esc(m.get('pipeline_tag') or '–'), nf(m.get('likes')), nf(m.get('downloads')), nf(m.get('trendingScore')), esc((m.get('createdAt') or '')[:10])) for i, m in enumerate(models))
        tbl = '<table><thead><tr><th class="l">#</th><th class="l">Modell</th><th class="l">Aufgabe</th><th>Likes</th><th>Downloads</th><th>Trend-Score</th><th class="l">Erstellt</th></tr></thead><tbody>%s</tbody></table>' % rows
        note = '<div class="note"><b>So lesen:</b> Reihenfolge nach dem Feld <i>trendingScore</i> der Hugging-Face-API, Stand %s. Likes, Downloads und Trend-Score sind Zähler der API, keine Qualitätsbewertung und kein Benchmark-Ergebnis. „Aufgabe“ ist das Feld <i>pipeline_tag</i>. Quelle: huggingface.co (öffentliche API, ohne Schlüssel).</div>' % esc(stamp)
    else:
        tbl = '<p class="mut">Die Hugging-Face-API war zum Erstellungszeitpunkt nicht erreichbar. Die Modellliste fehlt in dieser Ausgabe.</p>'; note = ''
    p1 = '<h2>Trending-Modelle <small>Top 20 laut Hugging-Face-API · Stand %s</small></h2>%s%s' % (esc(stamp), tbl, note)
    two = sorted(arts, key=lambda a: a['_pub'], reverse=True)[:2]
    cl = lambda t: re.sub(r'\s*\[\d+(?:[,–-]\s*\d+)*\]', '', t)
    ablk = ''
    for a in two:
        pts = ''.join('<li>%s</li>' % esc(cl(t)) for t in a.get('key_takeaways', [])[:3])
        ablk += '<div class="art"><div class="m">%s · %s · %d Quellen</div><div class="t">%s</div><div class="d">%s</div><ul>%s</ul><div class="u">kifachblatt.de/%s</div></div>' % (
            esc(a['section'].capitalize()), a['_pub'].strftime('%d.%m.%Y'), len(a.get('sources', [])), esc(a['title']), esc(a['dek']), pts, esc(a['slug']))
    p2 = '<h2>Die zwei Analysen des Tages</h2>%s<p class="foot">Vollständige Texte mit Quellen, Methode und Grenzen auf kifachblatt.de. „Eigene Rechnung“ kennzeichnet Berechnungen der Redaktion auf Basis der genannten Quellen.</p>' % (ablk or '<p class="mut">Noch keine Analysen.</p>')
    last = '''<h2>Impressum &amp; Redaktionsschluss</h2>
<div class="imp"><div><h3>Anbieter nach § 5 DDG</h3><p>Philipp Paulik<br>Mozartstraße 1<br>53819 Neunkirchen-Seelscheid<br>Nordrhein-Westfalen</p><h3>Kontakt</h3><p>E-Mail: philipp.l.paulik@gmail.com<br>Web: kifachblatt.de</p></div>
<div><h3>Verantwortlich nach § 18 Abs. 2 MStV</h3><p>Philipp Paulik, Anschrift wie links</p><h3>Redaktion</h3><p>KI Fachblatt, Redaktion Philipp Paulik</p></div></div>
<h3>Redaktionsschluss</h3><p>Diese Ausgabe wurde am %s automatisch erstellt. Später veröffentlichte Beiträge und Zählerstände sind nicht berücksichtigt.</p>
<h3>Hinweis zu KI</h3><p>Die Inhalte des KI Fachblatts werden mit Unterstützung von KI erstellt und redaktionell geprüft (siehe kifachblatt.de/transparenz). Dieser Bericht wird automatisch aus öffentlichen Daten und den veröffentlichten Beiträgen zusammengestellt. Trotz Prüfung können Fehler nicht ausgeschlossen werden.</p>
<h3>Datenquellen</h3><p>Modellliste: Hugging Face, öffentliche API (huggingface.co/api/models, Sortierung trendingScore), Stand %s. Analysen: eigene Beiträge des KI Fachblatts.</p>
<p class="foot">© %d KI Fachblatt · Philipp Paulik · Stand %s</p>''' % (esc(stamp), esc(stamp), now.year, esc(stamp))
    logo = logo_inline(os.path.join(root, 'assets', 'logo.svg'))
    htm = render('KI Fachblatt', 'KI-Tagesbericht', now.strftime('%d.%m.%Y'), '#7040cd', '#3d2380', '#f5f1fc', '#dcd0f3', logo,
                 'KI-Tagesbericht', day + ' · Trending-Modelle und die Analysen des Tages', [p1, p2], last)
    os.makedirs(os.path.join(root, 'berichte'), exist_ok=True)
    open(os.path.join(root, 'berichte', 'tagesbericht.html'), 'w', encoding='utf-8').write(htm)
    dated = os.path.join(root, 'berichte', 'ki-tagesbericht-%s.pdf' % now.strftime('%Y-%m-%d'))
    ok = to_pdf(os.path.join(root, 'berichte', 'tagesbericht.html'), dated)
    if ok:
        import shutil; shutil.copy(dated, os.path.join(root, 'berichte', 'ki-tagesbericht.pdf'))
    return ok, bool(models)
