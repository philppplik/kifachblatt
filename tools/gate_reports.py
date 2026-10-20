#!/usr/bin/env python3
"""Move generated report PDFs out of the public site into private Vercel Blob storage.
Run after tools/build.py in the daily workflow. Fails closed: if any upload fails, nothing is deleted
and the exit code is non-zero (so the workflow does not publish public PDFs by accident).
Upload goes through the Lead-Wall backend (HMAC-signed, no Blob token in GitHub). Env: LW_SECRET, optional LW_API."""
import os, re, sys, glob, hmac, hashlib, base64
import urllib.request

API = os.environ.get('LW_API', 'https://daily-hob-newsletter.vercel.app/lw')

def auth(secret, date):
    d = hmac.new(secret.encode(), ('upload:' + date).encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(d).decode().rstrip('=')

def upload(f, date, secret):
    req = urllib.request.Request(API + '/api/upload?date=' + date, data=open(f, 'rb').read(), method='POST',
        headers={'x-lw-auth': auth(secret, date), 'content-type': 'application/pdf'})
    return urllib.request.urlopen(req, timeout=90).status

def main(root='.'):
    secret = os.environ.get('LW_SECRET')
    if not secret: sys.exit('gate_reports: LW_SECRET missing, refusing to publish PDFs')
    files = glob.glob(root + '/berichte/*.pdf') + glob.glob(root + '/report-archive/*.pdf')
    dated = {}
    for f in files:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(f))
        if m: dated[m.group(1)] = f  # one file per date is enough, content is identical
    for d, f in sorted(dated.items()):
        try: st = upload(f, d, secret)
        except Exception as e: sys.exit('gate_reports: upload failed %s %s' % (d, e))
        if st != 200: sys.exit('gate_reports: upload failed %s %s' % (d, st))
        print('uploaded', d)
    for f in files: os.remove(f)
    html = root + '/berichte/tagesbericht.html'  # public print view would defeat the gate
    if os.path.exists(html): os.remove(html)
    print('removed %d public PDFs' % len(files))

if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else '.')
