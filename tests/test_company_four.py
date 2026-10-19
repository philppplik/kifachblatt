import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import company_rich
class CompanyFourTests(unittest.TestCase):
 def test_verified_profiles_and_references(self):
  d=json.loads((company_rich.ROOT/'content/portraits.json').read_text())
  for slug in ['nvidia','mistral-ai','meta','google-deepmind']:
   x=next(c for c in d['companies'] if c['slug']==slug);p=x['rich'];self.assertGreaterEqual(len(p['sections']),6);self.assertEqual(len(p['faq']),3)
   for _,_,key in p['sections']+p['offerings']+p['faq']+p['milestones']:self.assertIn(key,x['sources']);self.assertIn(key,d['sources'])
   out=company_rich.render(x,d,True);self.assertEqual(out.count('<details>'),3);self.assertIn('Was gehört wohin?',out);self.assertIn('Vor dem Einsatz prüfen',out)
   if not p['milestones']:self.assertNotIn('Wichtige Stationen',out)
 def test_meta_not_blanket_open(self):
  d=json.loads((company_rich.ROOT/'content/portraits.json').read_text());m=next(c for c in d['companies'] if c['slug']=='meta');out=company_rich.render(m,d,False);self.assertIn('700 Millionen',out);self.assertIn('Community License',out);self.assertIn('Muse',out)
if __name__=='__main__':unittest.main()
