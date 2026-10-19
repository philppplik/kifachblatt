import datetime, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
import report_visuals as V

NOW = datetime.datetime(2026, 10, 19, 12, 0, tzinfo=datetime.timezone.utc)
M = [{'id': 'acme/model-a', 'likes': 100, 'downloads': 5000, 'trendingScore': 90, 'pipeline_tag': 'text-generation', 'createdAt': '2026-10-17T00:00:00.000Z'},
     {'id': 'acme/model-b', 'likes': 10, 'downloads': 200, 'trendingScore': 30, 'pipeline_tag': 'text-to-image', 'createdAt': '2025-01-01T00:00:00.000Z'},
     {'id': 'solo', 'likes': 0, 'downloads': 0, 'trendingScore': 0, 'createdAt': 'kaputt'}]


class ReportVisualsTest(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(V.org(M[0]), 'acme'); self.assertEqual(V.name(M[0]), 'model-a'); self.assertEqual(V.org(M[2]), '–')
        self.assertEqual(V.age_days(M[0], NOW), 2); self.assertIsNone(V.age_days(M[2], NOW))
        self.assertEqual(V.short(16800000), '16,8 Mio.')

    def test_blocks_render_and_escape(self):
        bad = dict(M[0], id='x<script>/y')
        out = V.trend_bars([bad] + M[1:]) + V.kpis([bad] + M[1:], NOW) + V.org_bars([bad] + M[1:])
        self.assertNotIn('<script>', out)
        self.assertIn('Textgenerierung', V.donut(__import__('collections').Counter(m.get('pipeline_tag') or 'unknown' for m in M)))
        self.assertIn('bis 7 Tage', V.age_buckets(M, NOW))

    def test_empty_inputs_do_not_crash(self):
        self.assertEqual(V.kpis([], NOW), ''); self.assertEqual(V.trend_bars([]), ''); self.assertEqual(V.scatter(M[:2]), '')
        self.assertEqual(V.score_cards({}), '')

    def test_scores_are_labelled_as_vendor_claims(self):
        p = {'benchmarks': [{'slug': 'b', 'name': 'B'}], 'models': [{'slug': 'm', 'name': 'M'}],
             'scores': [{'model': 'm', 'benchmark': 'b', 'value': '71,07', 'metric': '% laut Herstellertabelle', 'reported_by': 'X'}]}
        out = V.score_cards(p)
        self.assertIn('71,07', out); self.assertIn('nicht für Ranglisten', out)


class LogoTest(unittest.TestCase):
    ROOT = os.path.join(os.path.dirname(__file__), '..')

    def test_only_verified_manifest_assets_load(self):
        V.load_logos(self.ROOT)
        self.assertIn('claude', V.LOGOS); self.assertIn('nvidia', V.LOGOS)
        self.assertTrue(V.LOGOS['claude']['uri'].startswith('data:image/svg+xml;base64,'))
        self.assertIn('dk', V.logo_box('nvidia', 10, 4))

    def test_tampered_or_missing_manifest_gives_no_logos(self):
        import tempfile, json, shutil
        d = tempfile.mkdtemp(); os.makedirs(d + '/content/portrait-logos')
        open(d + '/content/portrait-logos/a.svg', 'w').write('<svg/>')
        json.dump({'a': {'file': 'a.svg', 'sha256': '0' * 64}}, open(d + '/content/portrait-logos/manifest.json', 'w'))
        V.load_logos(d); self.assertEqual(V.LOGOS, {})
        V.load_logos('/nonexistent'); self.assertEqual(V.LOGOS, {})
        shutil.rmtree(d)

    def test_org_badge_allowlist_and_model_vs_company(self):
        V.load_logos(self.ROOT)
        self.assertIn('<img', V.org_badge('nvidia')); self.assertIn('<img', V.org_badge('google')); self.assertIn('<img', V.org_badge('meta-models'))
        p = {'models': [{'slug': 'x', 'name': 'GPT-6 Astra', 'company': 'openai', 'initials': 'GA'}], 'companies': [{'slug': 'openai', 'name': 'OpenAI'}]}
        self.assertNotIn('<img', V.portrait_cards(p))  # company logo is never used as a model logo
        self.assertEqual(V.logo_credits() == '' or 'Marken' in V.logo_credits(), True)


if __name__ == '__main__':
    unittest.main()
