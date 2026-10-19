from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import report_landing as r
class LandingTests(unittest.TestCase):
 def test_brands_ctas_faq_and_archive(self):
  for key in ['fa','iw','kfb']:
   with tempfile.TemporaryDirectory() as t,patch.object(r.shutil,'which',return_value=None):
    s=r.build(t,t,key,['2026-10-19'],'current.pdf','report-')
    self.assertIn('data-brand="'+key+'"',s)
    self.assertEqual(s.count('class="rl-button"'),2)
    self.assertIn('/berichte/report-2026-10-19.pdf',s)
    self.assertEqual(s.count('<details>'),6)
    self.assertNotIn('<form',s);self.assertNotIn('<script',s);self.assertNotIn('<iframe',s)
    self.assertIn('Ohne Anmeldung',s);self.assertIn('Ohne E-Mail',s)
    self.assertTrue((Path(t)/'assets/report-preview/landing.css').is_file())
 def test_real_pdf_conversion_when_present(self):
  if not r.shutil.which('pdftoppm'):self.skipTest('system renderer unavailable')
  # Integration proof checks the generated build assets rather than faking images.
  roots=[Path('site/out'),Path('.')]
  if not any((x/'assets/report-preview/page-1.jpg').is_file() for x in roots):self.skipTest('Build first')
  self.assertTrue(any((x/'assets/report-preview/page-2.jpg').is_file() for x in roots))
if __name__=='__main__':unittest.main()
