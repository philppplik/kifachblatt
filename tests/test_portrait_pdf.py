import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import portrait_pdf as p
p.logo_inline=lambda *args:'<svg></svg>'
class PortraitPDFTest(unittest.TestCase):
 def test_export_fallback_and_no_stale_download(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'content/branding').mkdir(parents=True);(root/'content/branding/logo.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
   dest=root/'portrait-pdf';dest.mkdir();(dest/'ki-modelle-test.pdf').write_bytes(b'%PDF-'+b'x'*1100)
   with patch.object(p,'to_pdf',return_value=False):
    result=p.export(root,root,'iw','models',{'slug':'test','name':'Test'},'<h1>Test</h1><details><summary>Q</summary><p>A</p></details>','','','https://example.org/ki-modelle/test/','2026-10-19','')
   self.assertNotIn(' download',result);self.assertIn('Druckansicht',result);self.assertFalse((dest/'ki-modelle-test.pdf').exists())
   text=(dest/'ki-modelle-test.html').read_text();self.assertIn('<details open>',text);self.assertIn('noindex,follow',text);self.assertNotIn('<script',text)
 def test_relative_links_and_local_image(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'content/branding').mkdir(parents=True);(root/'content/branding/logo.svg').write_text('<svg></svg>');(root/'assets/portrait-logos').mkdir(parents=True);(root/'assets/portrait-logos/logo.svg').write_text('<svg></svg>')
   with patch.object(p,'to_pdf',return_value=False):p.export(root,root,'iw','companies',{'slug':'test','name':'Test'},'<a href="/ki-modelle/test/">Test</a>','<img src="/assets/portrait-logos/logo.svg">','','https://example.org/unternehmen/test/','2026-10-19','')
   text=(root/'portrait-pdf/unternehmen-test.html').read_text();self.assertIn('data:image/svg+xml;base64,',text);self.assertIn('https://intelligenz-welt.de/ki-modelle/test/',text)
if __name__=='__main__':unittest.main()
