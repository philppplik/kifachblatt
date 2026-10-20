#!/usr/bin/env python3
"""Move generated report PDFs out of the public site into private Vercel Blob storage.
Run after tools/build.py in the daily workflow. Fails closed: if any upload fails, nothing is deleted
and the exit code is non-zero (so the workflow does not publish public PDFs by accident).
Env: BLOB_READ_WRITE_TOKEN, LW_SECRET."""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(__file__))
from publish_report_blob import path
import urllib.request

def upload(f, date, secret, token):
    req = urllib.request.Request('https://blob.vercel-storage.com/' + path(date, secret), data=open(f, 'rb').read(), method='PUT',
        headers={'authorization': 'Bearer ' + token, 'x-api-version': '7', 'x-add-random-suffix': '0', 'x-allow-overwrite': '1', 'x-content-type': 'application/pdf'})
    return urllib.request.urlopen(req, timeout=60).status

def main(root='.'):
    secret, token = os.environ.get('LW_SECRET'), os.environ.get('BLOB_READ_WRITE_TOKEN')
    if not secret or not token: sys.exit('gate_reports: LW_SECRET / BLOB_READ_WRITE_TOKEN missing, refusing to publish PDFs')
    files = glob.glob(root + '/berichte/*.pdf') + glob.glob(root + '/report-archive/*.pdf')
    dated = {}
    for f in files:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(f))
        if m: dated[m.group(1)] = f  # one file per date is enough, content is identical
    for d, f in sorted(dated.items()):
        st = upload(f, d, secret, token)
        if st not in (200, 201): sys.exit('gate_reports: upload failed %s %s' % (d, st))
        print('uploaded', d)
    for f in files: os.remove(f)
    html = root + '/berichte/tagesbericht.html'  # public print view would defeat the gate
    if os.path.exists(html): os.remove(html)
    print('removed %d public PDFs' % len(files))

if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else '.')
