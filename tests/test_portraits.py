"""Run with python3 -m unittest discover -s tests -p 'test_portraits.py'."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('portraits',ROOT/'tools/portraits.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PortraitDataTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ROOT/'content/portraits.json').read_text())
 def test_schema_and_source_references(self):m.validate(self.d)
 def test_first_release_scope(self):
  self.assertEqual([len(self.d[k]) for k in ('companies','models','benchmarks')],[6,8,4])
 def test_no_unattributed_score(self):
  for s in self.d['scores']:
   self.assertTrue(s['reported_by']);self.assertTrue(s['setup']);self.assertTrue(s['variant']);self.assertTrue(s['metric'])
 def test_every_model_has_limits_access_and_license_note(self):
  for x in self.d['models']:
   for k in ('limits','access','license'):self.assertTrue(x[k])
 def test_every_fact_has_direct_source(self):
  for k in ('models','companies'):
   for x in self.d[k]:
    for f in x['facts']:self.assertIn(f['source'],self.d['sources'])
class PortraitLogoTests(unittest.TestCase):
 def test_manifest_files_and_model_mapping(self):
  manifest=json.loads((ROOT/'content/portrait-logos/manifest.json').read_text())
  for key,asset in manifest.items():
   self.assertTrue((ROOT/'content/portrait-logos'/asset['file']).is_file())
   self.assertTrue(asset['source'].startswith('https://'))
   self.assertTrue(asset['license'])
  d=json.loads((ROOT/'content/portraits.json').read_text())
  self.assertEqual(sum('logo' in x for x in d['companies']),6)
  self.assertEqual(sum('logo' in x for x in d['models']),5)
  for x in d['companies']+d['models']:
   if 'logo' in x:self.assertIn(x['logo']['asset'],manifest)
 def test_no_model_logo_means_monogram(self):
  self.assertIn('p-avatar',m.portrait_mark({'initials':'GA'}))
if __name__=='__main__':unittest.main()
