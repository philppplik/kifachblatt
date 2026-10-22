"""Run with python3 -m unittest discover -s tests -p 'test_modell_atlas.py'."""
import importlib.util, json, re, unittest, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modell_atlas', ROOT/'tools/modell_atlas.py')
ma = importlib.util.module_from_spec(spec); spec.loader.exec_module(ma)

class AtlasDataTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((ROOT/'content/modell-atlas.json').read_text())

    def test_schema_and_source_references(self):
        ma.validate(self.d)

    def test_no_price_without_source_tier_and_unit(self):
        for m in self.d['models']:
            pr = m.get('pricing')
            if pr:
                self.assertIn(pr['source'], self.d['sources'])
                self.assertTrue(pr['tier'] and pr['unit'] and pr['notes'])
                self.assertEqual(pr['currency'], 'USD')
                self.assertGreater(pr['input'], 0)
                self.assertGreater(pr['output'], 0)

    def test_no_benchmark_without_attribution(self):
        for m in self.d['models']:
            for b in m['benchmarks']:
                self.assertTrue(b['reported_by'])
                self.assertTrue(b['metric'])
                self.assertTrue(b['variant'])
                self.assertIn(b['source'], self.d['sources'])

    def test_every_source_https_with_check_date(self):
        for key, s in self.d['sources'].items():
            self.assertTrue(s['url'].startswith('https://'), key)
            datetime.date.fromisoformat(s['accessed'])

    def test_gepruefte_privacy_hat_aussagen_und_quellen(self):
        for p in self.d['providers']:
            if p['privacy']['status'] == 'geprueft':
                self.assertTrue(p['privacy']['training'])
                self.assertTrue(p['privacy']['dpa'])
                self.assertTrue(p['privacy']['sources'])
            for k in p['privacy']['sources']:
                self.assertIn(k, self.d['sources'])

    def test_known_seed_scope(self):
        self.assertEqual(len(self.d['models']), 18)
        self.assertGreaterEqual(sum(1 for m in self.d['models'] if m.get('pricing')), 8)

    def test_no_invented_price_placeholder(self):
        for m in self.d['models']:
            pr = m.get('pricing')
            if pr:
                self.assertIsNotNone(pr['input'])
                self.assertIsNotNone(pr['output'])
                self.assertNotEqual(pr['input'], 0)

class AtlasRenderTests(unittest.TestCase):
    def test_render_smoke(self):
        import tempfile, shutil, subprocess
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT/'content', tmp/'content')
            shutil.copy(ROOT/'halluzinationen.html', tmp/'halluzinationen.html')
            subprocess.check_call(['python3', str(ROOT/'tools/modell_atlas.py'), str(tmp)])
            index = (tmp/'modell-atlas.html').read_text(encoding='utf-8')
            self.assertIn('Modell-Atlas', index)
            self.assertIn('nicht gepflegt', index)  # fehlende Preise sichtbar statt erfunden
            detail = (tmp/'modell-atlas/claude-sonnet-5.html').read_text(encoding='utf-8')
            self.assertIn('2', detail)
            self.assertIn('Quellen', detail)
            self.assertIn('Trainingsnutzung', detail)
            data = json.load(open(ROOT/'content/modell-atlas.json'))
            unpriced_slug = next(m['slug'] for m in data['models'] if not m.get('pricing'))
            unpriced = (tmp/('modell-atlas/%s.html' % unpriced_slug)).read_text(encoding='utf-8')
            self.assertIn('kein Preis gepflegt', unpriced)
            self.assertNotIn('0 $', unpriced)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
