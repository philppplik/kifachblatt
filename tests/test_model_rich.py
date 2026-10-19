import unittest,sys,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import model_rich as m
class ModelRichTests(unittest.TestCase):
 def test_visible_faq_matches_schema(self):
  d=json.loads((ROOT/'content/portraits.json').read_text());a=[x for x in d['models'] if x.get('rich_model')];self.assertEqual(len(a),3)
  for x in a:
   text=m.render(x,d,ROOT.name=='kfb');schemas=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)[1]);self.assertEqual(schemas[0]['@type'],'FAQPage');self.assertEqual(len(schemas[0]['mainEntity']),5)
   for q,a in x['rich_model']['faq']:self.assertIn(m.E(q),text);self.assertIn(m.E(a),text)
 def test_price_caveats(self):
  d=json.loads((ROOT/'content/portraits.json').read_text())
  for x in d['models']:
   if x.get('rich_model'):
    t=m.render(x,d,True);self.assertIn('je 1 Mio. Texttoken',t);self.assertIn('Preisstand 19.10.2026',t);self.assertIn('Batch',t);self.assertIn('Cache',t)
 def test_no_unverified_typo_pages(self):
  d=json.loads((ROOT/'content/portraits.json').read_text());self.assertFalse(any('atsra' in x['slug'] or 'flable' in x['slug'] for x in d['models']))
if __name__=='__main__':unittest.main()
