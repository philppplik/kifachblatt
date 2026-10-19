import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import licensed_news as n
class LicensedTests(unittest.TestCase):
 def sample(self,key='heise'):
  return dict(title='KI <Test> & Datenschutz',url={'heise':'https://www.heise.de/news/ki-test-123.html','destatis':'https://www.destatis.de/DE/Presse/Pressemitteilungen/2026/10/PD26_371_421.html','ecb':'https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261007~6447350434.en.html'}[key],ts=1792400790,teaser='Ein erlaubter Anriss.',license_key=key,captured_at='2026-10-19T12:00:00+00:00')
 def test_strict_hosts_and_paths(self):
  for key in ('heise','destatis','ecb'):
   i=self.sample(key);self.assertTrue(n.matches(key,i['url']))
   for url in ['javascript:alert(1)','https://heise.de.evil.test/news/a.html','https://www.cnn.com/news/a.html','http://www.heise.de/news/a.html']:
    self.assertFalse(n.matches(key,url))
  for path in ['/press/key/date/2026/html/a.html','/pub/pdf/scpwps/a.pdf','/press/blog/date/2026/html/a.html']:
   self.assertFalse(n.matches('ecb','https://www.ecb.europa.eu'+path))
 def test_escape_and_no_remote_images(self):
  s=n.body(self.sample(),'Intelligenz Welt');self.assertIn('&lt;Test&gt;',s);self.assertNotIn('<Test>',s)
  self.assertEqual(s.count('class="ln-original"'),2);self.assertIn('noopener noreferrer nofollow',s);self.assertIn('ln-leaving',s)
  self.assertNotIn('<img',s);self.assertNotIn('<iframe',s);self.assertNotIn('<script',s)
 def test_immutable_and_failure_retention(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data';p.mkdir();i=self.sample();(p/'news-pages.json').write_text(json.dumps([i]));old=n.detail_path(i)
   with patch('urllib.request.urlopen',side_effect=OSError('offline')):self.assertEqual(n.collect(t,'iw'),[i])
   self.assertEqual(n.detail_path(n.collect(t,'iw',fetch=False)[0]),old)
 def test_no_cached_foreign_teasers(self):
  with tempfile.TemporaryDirectory() as t:
   i=dict(self.sample(),url='https://www.finanznachrichten.de/nachrichten/a.htm',sum='UNAPPROVED',teaser='UNAPPROVED')
   rows=n.collect(t,'fa',[i],fetch=False);self.assertEqual(rows[0]['teaser'],'');self.assertEqual(rows[0]['sum'],'')
 def test_corrupt_archive_stops_without_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data';p.mkdir();f=p/'news-pages.json';f.write_text('{bad')
   with self.assertRaises(ValueError):n.collect(t,'iw',fetch=False)
   self.assertEqual(f.read_text(),'{bad')
 def test_feed_filters_and_no_injected_html(self):
  rss=b'<rss><channel><item><title>Bad speech</title><link>https://www.ecb.europa.eu/press/key/date/2026/html/a.html</link><pubDate>Mon, 19 Oct 2026 10:00:00 +0200</pubDate></item></channel></rss>'
  self.assertEqual(n.parse_feed(rss,'ecb'),[])
  self.assertEqual(n.text('<p>Hallo <b>Welt</b><img src="x"><script>attack</script></p>'),'Hallo Welt')
 def test_noindex_removes_canonical(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'index.html';p.write_text('<meta name="robots" content="index,follow"><link rel="canonical" href="x">');n.noindex(p);self.assertIn('noindex,follow',p.read_text());self.assertNotIn('canonical',p.read_text())
if __name__=='__main__':unittest.main()
