import datetime
from pathlib import Path
import tempfile
import unittest
from daily_archive import sync,valid_pdf,archive_html
PDF=b'%PDF-1.7\n'+b'x'*1500+b'\n%%EOF'
class ArchiveTests(unittest.TestCase):
 def test_one_snapshot_per_berlin_day_and_fallback(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);out=root/'out';out.mkdir();(out/'latest.pdf').write_bytes(PDF)
   utc=datetime.timezone.utc
   day=datetime.datetime(2026,10,18,22,30,tzinfo=utc)
   self.assertEqual(sync(root,out,'latest.pdf','report-',day),['2026-10-19'])
   (out/'latest.pdf').write_bytes(PDF.replace(b'x',b'y'))
   sync(root,out,'latest.pdf','report-',day)
   self.assertEqual((root/'report-archive/2026-10-19.pdf').read_bytes(),PDF)
   (out/'latest.pdf').write_bytes(b'broken')
   sync(root,out,'latest.pdf','report-',day+datetime.timedelta(days=1))
   self.assertEqual((out/'latest.pdf').read_bytes(),PDF)
   self.assertFalse((root/'report-archive/2026-10-20.pdf').exists())
 def test_stale_current_not_archived_as_today_on_failure(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);out=root/'out';out.mkdir();(out/'latest.pdf').write_bytes(PDF)
   sync(root,out,'latest.pdf','report-',datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc),archive_today=False)
   self.assertFalse((root/'report-archive/2026-10-19.pdf').exists())
 def test_restore_after_clean_build_and_no_pruning(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);out=root/'out';out.mkdir();store=root/'report-archive';store.mkdir()
   for date in ['2020-01-01','2026-10-18']:(store/(date+'.pdf')).write_bytes(PDF)
   dates=sync(root,out,'latest.pdf','report-',datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc))
   self.assertEqual(len(dates),2);self.assertTrue((out/'report-2020-01-01.pdf').exists())
   self.assertIn('/berichte/report-2020-01-01.pdf',archive_html(dates,'report-'))
 def test_validation_and_old_dated_seed(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);out=root/'out';out.mkdir();(out/'report-2026-10-18.pdf').write_bytes(PDF)
   self.assertFalse(valid_pdf(out/'missing.pdf'))
   dates=sync(root,out,'latest.pdf','report-',datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc))
   self.assertEqual(dates,['2026-10-18'])
if __name__=='__main__':unittest.main()
