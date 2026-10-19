import importlib.util,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('home',ROOT/'tools/home_editorial.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class EditorialTests(unittest.TestCase):
 def test_chart_text_alternative_and_source(self):
  text=m.chart('Test','Beschreibung',['A'],[('Vor',[1]),('Nach',[2])],5,' %','x')
  self.assertIn('role="img"',text);self.assertIn('Alle Werte als Text',text);self.assertIn(m.SOURCE,text);self.assertIn('Vor 1 %',text);self.assertIn('Nach 2 %',text)
 def test_legacy_records(self):
  d=json.loads((ROOT/'content/home-legacy.json').read_text());self.assertEqual(len(d),6);self.assertEqual(len({x['slug'] for x in d}),6)
 def test_home_has_no_analysis_table(self):
  text=(ROOT/'index.html').read_text();self.assertNotIn('id="articles"',text);self.assertEqual(text.count('class="hv-card"'),3);self.assertEqual(text.count('data-topic='),10)
if __name__=='__main__':unittest.main()
