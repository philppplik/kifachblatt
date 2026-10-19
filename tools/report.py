"""KI-Tagesbericht (A4 PDF + print page). Called from build.py. Data: Hugging Face public API (no key), own articles."""
import json, os, re, sys, urllib.request, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_core import esc, DAYS, render, to_pdf, logo_inline, lnk, dom, srclist
import report_visuals as V

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
    try:
        portraits = json.load(open(os.path.join(root, 'content', 'portraits.json'), encoding='utf-8'))
    except (OSError, ValueError):
        portraits = {}
    if models:
        tbl = V.table(models, now, nf)
        note = '<div class="note"><b>So lesen:</b> Reihenfolge nach dem Feld <i>trendingScore</i> der Hugging-Face-API, Stand %s. Likes, Downloads und Trend-Score sind Zähler der API, keine Qualitätsbewertung und kein Benchmark-Ergebnis. Die Diagramme zeigen nur diese Zähler.</div>' % esc(stamp)
        tasks = __import__('collections').Counter(m.get('pipeline_tag') or 'unknown' for m in models)
        p1 = ('<style>%s</style>%s<h2>Trend-Ranking <small>Top 10 nach Trend-Score · Stand %s</small></h2>%s'
              '<div class="two"><div><h2>Aufgaben im Ranking</h2>%s</div><div><h2>Alter der Modelle</h2>%s<h2>Wer vorn liegt</h2>%s</div></div>') % (
            V.CSS, V.kpis(models, now), esc(stamp), V.trend_bars(models), V.donut(tasks), V.age_buckets(models, now), V.org_bars(models))
        p1b = '<h2>Beachtung und Nutzung <small>Likes gegen Downloads, logarithmisch</small></h2>%s<p class="foot">Jeder Punkt ist ein Modell, die Größe zeigt den Trend-Score. Hohe Downloads bei wenigen Likes und umgekehrt sind normal und sagen nichts über Qualität.</p><h2>Alle 20 Modelle <small>Top 20 laut Hugging-Face-API · Stand %s</small></h2>%s%s' % (V.scatter(models), esc(stamp), tbl, note)
    else:
        p1 = '<style>%s</style><h2>Trending-Modelle</h2><p class="mut">Die Hugging-Face-API war zum Erstellungszeitpunkt nicht erreichbar. Die Modellliste fehlt in dieser Ausgabe.</p>' % V.CSS
        p1b = ''
    p3 = ''
    if portraits.get('models'):
        p3 = ('<h2>Aus dem KI-Verzeichnis <small>Modelle mit Quellen auf kifachblatt.de/ki-modelle</small></h2>%s'
              '<h2>Benchmark-Angaben der Hersteller</h2>%s<p class="foot">Quellen und Prüfdatum (%s) je Eintrag unter <a href="%s/ki-modelle">kifachblatt.de/ki-modelle</a> und <a href="%s/benchmarks">kifachblatt.de/benchmarks</a>.</p>') % (
            V.portrait_cards(portraits), V.score_cards(portraits), esc(portraits.get('reviewed', '')), base, base)
    two = sorted(arts, key=lambda a: a['_pub'], reverse=True)[:2]
    cl = lambda t: re.sub(r'\s*\[\d+(?:[,–-]\s*\d+)*\]', '', t)
    ablk = ''
    for a in two:
        pts = ''.join('<li>%s</li>' % esc(cl(t)) for t in a.get('key_takeaways', [])[:3])
        ablk += '<div class="art"><div class="m">%s · %s · %d Quellen</div><div class="t">%s</div><div class="d">%s</div><ul>%s</ul><div class="u">%s</div>%s</div>' % (
            esc(a['section'].capitalize()), a['_pub'].strftime('%d.%m.%Y'), len(a.get('sources', [])), lnk(base + '/' + a['slug'], a['title']), esc(a['dek']), pts, lnk(base + '/' + a['slug']), srclist(a.get('sources', [])))
    p2 = '<h2>Die zwei Analysen des Tages</h2>%s<p class="foot">Vollständige Texte mit Quellen, Methode und Grenzen auf kifachblatt.de. „Eigene Rechnung“ kennzeichnet Berechnungen der Redaktion auf Basis der genannten Quellen.</p>' % (ablk or '<p class="mut">Noch keine Analysen.</p>')
    last = '''<h2>Impressum &amp; Redaktionsschluss</h2>
<div class="imp"><div><h3>Anbieter nach § 5 DDG</h3><p>Philipp Paulik<br>Mozartstraße 1<br>53819 Neunkirchen-Seelscheid<br>Nordrhein-Westfalen</p><h3>Kontakt</h3><p>E-Mail: philipp.l.paulik@gmail.com<br>Web: kifachblatt.de</p></div>
<div><h3>Verantwortlich nach § 18 Abs. 2 MStV</h3><p>Philipp Paulik, Anschrift wie links</p><h3>Redaktion</h3><p>KI Fachblatt, Redaktion Philipp Paulik</p></div></div>
<h3>Redaktionsschluss</h3><p>Diese Ausgabe wurde am %s automatisch erstellt. Später veröffentlichte Beiträge und Zählerstände sind nicht berücksichtigt.</p>
<h3>Hinweis zu KI</h3><p>Die Inhalte des KI Fachblatts werden mit Unterstützung von KI erstellt und redaktionell geprüft (siehe kifachblatt.de/transparenz). Dieser Bericht wird automatisch aus öffentlichen Daten und den veröffentlichten Beiträgen zusammengestellt. Trotz Prüfung können Fehler nicht ausgeschlossen werden.</p>
<h3>Datenquellen</h3><p>Modellliste: Hugging Face, öffentliche API (huggingface.co/api/models, Sortierung trendingScore), Stand %s. Analysen und KI-Verzeichnis: eigene Beiträge und Quellenprüfung des KI Fachblatts. Diagramme: eigene Darstellung der API-Zähler. Es werden keine fremden Logos oder Profilbilder verwendet, Organisationen erscheinen als Kürzel. Beitragsbilder sind KI-generiert und gekennzeichnet.</p>
<p class="foot">© %d KI Fachblatt · Philipp Paulik · Stand %s</p>''' % (esc(stamp), esc(stamp), now.year, esc(stamp))
    logo = logo_inline(os.path.join(root, 'assets', 'logo.svg'))
    htm = render('KI Fachblatt', 'KI-Tagesbericht', now.strftime('%d.%m.%Y'), '#7040cd', '#3d2380', '#f5f1fc', '#dcd0f3', logo,
                 'KI-Tagesbericht', day + ' · Trending-Modelle und die Analysen des Tages', [x for x in (p1, p1b, p3, p2) if x], last)
    os.makedirs(os.path.join(root, 'berichte'), exist_ok=True)
    open(os.path.join(root, 'berichte', 'tagesbericht.html'), 'w', encoding='utf-8').write(htm)
    dated = os.path.join(root, 'berichte', 'ki-tagesbericht-%s.pdf' % now.strftime('%Y-%m-%d'))
    ok = to_pdf(os.path.join(root, 'berichte', 'tagesbericht.html'), dated)
    if ok:
        import shutil; shutil.copy(dated, os.path.join(root, 'berichte', 'ki-tagesbericht.pdf'))
    return ok, bool(models)
