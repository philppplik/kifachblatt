import importlib.util,unittest,re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('about',ROOT/'tools/about.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AboutTests(unittest.TestCase):
 def test_counts(self):
  f=m.facts();self.assertEqual(f['glossary'],len(json.loads((ROOT/'content/glossary.json').read_text())))
  for key in ['companies','models','benchmarks']:self.assertEqual(f[key],len(json.loads((ROOT/'content/portraits.json').read_text())[key]))
  self.assertEqual(f['analyses'],f['new']+f['legacy'])
 def test_schedule_evidence(self):self.assertIn("cron: '20 5 * * *'",(ROOT/'.github/workflows/kfb-daily-report.yml').read_text())
 def test_render_idempotent_and_accessible(self):
  m.render();s=(ROOT/'ueber.html').read_text();m.render();self.assertEqual(s,(ROOT/'ueber.html').read_text());self.assertEqual(s.count('class="ab-stat"'),5);self.assertEqual(s.count('role="img"'),2);self.assertNotIn('tel:',s);self.assertIn('mailto:philipp.l.paulik@gmail.com',s)
 def test_local_links_exist(self):
  s=(ROOT/'ueber.html').read_text();main=re.search('<main.*?</main>',s,re.S)[0]
  for href in re.findall('href="(/[^"]*)"',main):
   path=href.split('#')[0]
   if path:self.assertTrue((ROOT/('index.html' if path=='/' else path.strip('/')+'.html')).exists(),href)
if __name__=='__main__':unittest.main()
