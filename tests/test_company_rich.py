import unittest,sys,json,tempfile,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import company_rich as c,portrait_snapshots as s
class RichTests(unittest.TestCase):
 def test_all_three_profiles(self):
  d=json.loads((ROOT/'content/portraits.json').read_text())
  for x in d['companies'][:3]:
   h=c.render(x,d,ROOT.name=='kfb');self.assertEqual(h.count('class="co-block"'),len(x['rich']['sections'])+len(x['rich'].get('offerings',[])));self.assertIn('role="img"',h);self.assertIn('co-layers-text',h);self.assertIn('Snapshot abgerufen',h)
 def test_all_portraits_archived(self):
  current=json.loads((ROOT/'content/portraits.json').read_text());self.assertTrue(any(json.loads(p.read_text())==current for p in (ROOT/'content/portrait-snapshots/editorial').glob('*.json')))
 def test_append_only(self):
  old=s.ROOT
  with tempfile.TemporaryDirectory() as tmp:
   s.ROOT=Path(tmp);a=s.store('test',{'v':1});data=a.read_bytes();b=s.store('test',{'v':2});self.assertNotEqual(a,b);self.assertEqual(a.read_bytes(),data);self.assertEqual(s.store('test',{'v':1}),a)
  s.ROOT=old
 def test_six_api_snapshots(self):
  for key in s.REPOS:self.assertTrue(list((ROOT/'content/portrait-snapshots'/('github-'+key)).glob('*.json')))
if __name__=='__main__':unittest.main()
