"""QA-Gate für den LLM-Kostenrechner (stdlib unittest).
Prüft Datenmodell (Quellen, Frische, Plausibilität), Rechenlogik an Referenzwerten
und die Seite (Quellen, Disclaimer, kein Drittanbieter-JS, Budget).
Laufenlassen: python3 tests/test_llm_kostenrechner.py"""
import json, re, subprocess, unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/llm-api-preise.json').read_text())
PAGE = (ROOT / 'llm-kostenrechner.html').read_text()
JS = (ROOT / 'assets/tools/llm-kostenrechner.js').read_text()
CSS = (ROOT / 'assets/tools/llm-kostenrechner.css').read_text()
MAX_AGE_DAYS = 14  # K2: Datenstand darf nie älter als 14 Tage sein


class Datenmodell(unittest.TestCase):
    def test_jeder_anbieter_hat_quelle_und_abrufdatum(self):
        for p in DATA['providers']:
            self.assertTrue(p['source']['url'].startswith('https://'), p['id'])
            self.assertRegex(p['source']['retrieved'], r'^\d{4}-\d{2}-\d{2}$', p['id'])
            self.assertGreaterEqual(len(p['models']), 1, p['id'])

    def test_frische(self):
        for p in DATA['providers']:
            y, m, d = map(int, p['source']['retrieved'].split('-'))
            age = (date.today() - date(y, m, d)).days
            self.assertLessEqual(age, MAX_AGE_DAYS, '%s: Preise %d Tage alt' % (p['id'], age))

    def test_preise_plausibel(self):
        for p in DATA['providers']:
            for m in p['models']:
                sets = m.get('tiers') or [m] + ([m['offpeak']] if 'offpeak' in m else [])
                for s in sets:
                    self.assertGreater(s['input'], 0, m['id'])
                    self.assertGreater(s['output'], 0, m['id'])
                    self.assertLessEqual(s['input'], 100, m['id'])
                    self.assertLessEqual(s['output'], 200, m['id'])
                    if s.get('cached_input') is not None:
                        self.assertLess(s['cached_input'], s['input'], m['id'])
                if 'offpeak' in m:
                    self.assertAlmostEqual(m['offpeak']['input'], m['input'] / 2, places=6)
                    self.assertAlmostEqual(m['offpeak']['output'], m['output'] / 2, places=6)

    def test_angekuendigte_aenderungen_datiert(self):
        for p in DATA['providers']:
            for m in p['models']:
                if 'scheduled' in m:
                    self.assertRegex(m['scheduled']['date'], r'^\d{4}-\d{2}-\d{2}$')
                    self.assertIn('note', m['scheduled'])

    def test_fx_vorhanden(self):
        self.assertGreater(DATA['fx']['usd_per_eur'], 0.5)
        self.assertLess(DATA['fx']['usd_per_eur'], 2.5)


class Rechenlogik(unittest.TestCase):
    """Referenzwerte gegen die JS-Logik (per node) prüfen."""

    def _js_cost(self, model_id, inp, out, cache=0, batch=False, offpeak=False):
        harness = """
var DATA = %s;
%s
DATA.providers.forEach(function(p){p.models.forEach(function(m){modelProvider[m.id]=p;});});
var m = null;
DATA.providers.forEach(function(p){p.models.forEach(function(x){if(x.id==='%s')m=x;});});
var s = {input:%d, output:%d, cache:%d, batch:%s, offpeak:%s};
console.log(JSON.stringify(costPerRequest(m, s)));
"""
        # Logikteil extrahieren: priceSet + costPerRequest + currentProvider
        logic = JS[JS.index('function priceSet'):JS.index('/* ---------- Formatierung')]
        full = harness % (json.dumps(DATA), logic, model_id, inp, out, cache,
                          'true' if batch else 'false', 'true' if offpeak else 'false')
        r = subprocess.run(['node', '-e', full], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return float(r.stdout.strip())

    def test_referenz_sonnet5_einfach(self):
        # 1.000 in / 500 out, kein Cache: 1000*2 + 500*10 = 7000 $/1M = 0,007 $
        self.assertAlmostEqual(self._js_cost('claude-sonnet-5', 1000, 500), 0.007)

    def test_referenz_cache(self):
        # GPT-5.6 Terra, 50%% Cache: (500*2.00 + 500*0.20 + 100*12.00)/1e6 = 0.0023
        self.assertAlmostEqual(self._js_cost('gpt-5.6-terra', 1000, 100, cache=50), 0.0023)

    def test_referenz_batch(self):
        # Mistral Small 4 mit Batch: (1000*0.15 + 100*0.60)/1e6 * 0.5 = 0.000105
        self.assertAlmostEqual(self._js_cost('mistral-small-4', 1000, 100, batch=True), 0.000105)

    def test_referenz_offpeak(self):
        # DeepSeek Flash Nebenzeit: (1000*0.15 + 100*0.60)/1e6 = 0.00021
        self.assertAlmostEqual(self._js_cost('deepseek-flash', 1000, 100, offpeak=True), 0.00021)

    def test_referenz_staffelpreis(self):
        # Grok 4.6 über 200K Eingabe: höhere Staffel. 250.000 in / 100 out:
        # (250000*4.00 + 100*12.00)/1e6 = 1.0012
        self.assertAlmostEqual(self._js_cost('grok-4.6', 250000, 100), 1.0012)


class Seite(unittest.TestCase):
    def test_pflichtangaben(self):
        for needle in ['Quellen und Stand', 'ohne Gewähr', 'Keine Verbindung zu den genannten Anbietern',
                       'EZB-Referenzkurs', 'Erstellt mit KI-Unterstützung', 'kifachblatt.de/llm-kostenrechner']:
            self.assertIn(needle, PAGE)

    def test_kein_drittanbieter_code_oder_tracking(self):
        # Kein externes JS/CSS/Fonts außer eigener Domain (GA4 lädt erst nach Consent über consent.js)
        for pat in [r'https?://(?!kifachblatt\.de)[^"\']+\.(js|css|woff2?)', r'googletagmanager', r'cdn\.',
                    r'unpkg', r'jsdelivr']:
            self.assertIsNone(re.search(pat, PAGE), pat)

    def test_datenschutz_versprechen_deckt_umsetzung(self):
        self.assertIn('vollständig in Ihrem Browser', PAGE)
        self.assertNotIn('XMLHttpRequest', JS.replace('fetch(', ''))  # nur der eine fetch der Preis-JSON
        self.assertEqual(JS.count('fetch('), 1)
        self.assertNotIn('localStorage', JS)
        self.assertNotIn('cookie', JS.lower())

    def test_mobil_und_a11y(self):
        self.assertIn('@media(max-width:900px)', CSS)
        self.assertIn('prefers-reduced-motion', CSS)
        self.assertIn('aria-label', PAGE)
        self.assertIn('role="status"', PAGE)

    def test_seo_grundgeruest(self):
        self.assertIn('application/ld+json', PAGE)
        self.assertIn('FAQPage', PAGE)
        self.assertIn('WebApplication', PAGE)
        m = re.search(r'<meta name="description" content="([^"]*)"', PAGE)
        self.assertTrue(m and 60 <= len(m.group(1)) <= 200)


if __name__ == '__main__':
    unittest.main()
