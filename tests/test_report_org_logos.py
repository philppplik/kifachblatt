import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import report_visuals as v
class OrgMappingTests(unittest.TestCase):
 def test_approved_handles(self):
  v.load_logos(str(Path(__file__).resolve().parents[1]))
  for key,asset in [('google','google-deepmind'),('facebook','meta'),('meta-models','meta')]:
   self.assertEqual(v.HF_ORG_LOGO[key],asset);self.assertIn('data:image',v.org_badge(key))
  self.assertNotIn('data:image',v.org_badge('google-unverified'))
if __name__=='__main__':unittest.main()
