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


if __name__ == '__main__':
    unittest.main()
