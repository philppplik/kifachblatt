import unittest
import report_breaker as m
class BreakerTests(unittest.TestCase):
 def test_midpoint_and_idempotent(self):
  h='<html><head></head><body><div class="body"><h2>One</h2><p>Alpha</p><h2>Two</h2><p>Beta</p><h2>Three</h2><p>Gamma</p></div></body></html>'
  r=m.patch(h)
  self.assertEqual(r.count('class="report-breaker"'),1)
  self.assertEqual(m.patch(r),r)
  self.assertIn('href="'+m.PDF+'"',r)
  self.assertIn('</p><aside class="report-breaker"',r)
 def test_does_not_split_nested_structure(self):
  s='<p>A</p><div><table><tr><td><p>B</p></td></tr></table></div><h2>C</h2><p>D</p>'
  r=m.inject_body(s)
  self.assertIn('<td><p>B</p></td>',r)
  self.assertNotIn('<td><p>B</p><aside',r)
 def test_no_script_or_storage(self):
  for x in ['<script','sessionStorage','localStorage','https://','<form']:
   self.assertNotIn(x,m.box()+m.CSS)
 def test_mockup_image_lazy_with_alt(self):
  b=m.box()
  self.assertIn('class="rb-mock rb-mocks"',b)
  self.assertIn('loading="lazy"',b)
  self.assertIn('decoding="async"',b)
  self.assertIn('alt="',b)
  self.assertIn('/assets/report-preview/page-1.jpg',b)
  self.assertIn('width="707" height="1000"',b)
 def test_upgrade_replaces_previous_generation(self):
  old='<html><head><style id="report-breaker-style">.old{color:red}</style></head><body><div class="body"><p>A</p><aside class="report-breaker"><span class="rb-label">alt</span></aside><p>B</p></div></body></html>'
  r=m.patch(old)
  self.assertIn('rb-mock',r)
  self.assertNotIn('.old{color:red}',r)
  self.assertNotIn('>alt<',r)
  self.assertEqual(r.count('class="report-breaker"'),1)
  self.assertEqual(m.patch(r),r)
 def test_non_article_unchanged(self):
  s='<html><head></head><body><p>Home</p></body></html>'
  self.assertEqual(m.patch(s),s)
 def test_complete_heading_paragraph(self):
  s='<h2>Head</h2><p>A</p><p>B</p><p>C</p>'
  r=m.inject_body(s)
  self.assertIn('<h2>Head</h2><p>A</p>',r)
if __name__=='__main__':unittest.main()
