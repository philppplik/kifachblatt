#!/usr/bin/env python3
"""Upload a daily report PDF to Vercel Blob under the unguessable path the lead-wall function expects.
Usage: BLOB_READ_WRITE_TOKEN=... LW_SECRET=... python3 tools/publish_report_blob.py berichte/ki-tagesbericht-2026-10-20.pdf
The PDF must then NOT be committed to the public repo / Pages."""
import os, sys, re, hmac, hashlib, base64, urllib.request
def path(date, secret):
    sig = base64.urlsafe_b64encode(hmac.new(secret.encode(), ('report:'+date).encode(), hashlib.sha256).digest()).decode().rstrip('=')
    return f'reports/ki-tagesbericht-{date}-{sig[:24]}.pdf'
if __name__ == '__main__':
    f = sys.argv[1]; date = re.search(r'(\d{4}-\d{2}-\d{2})', f).group(1)
    req = urllib.request.Request('https://blob.vercel-storage.com/'+path(date, os.environ['LW_SECRET']), data=open(f,'rb').read(), method='PUT',
        headers={'authorization':'Bearer '+os.environ['BLOB_READ_WRITE_TOKEN'],'x-api-version':'7','x-vercel-blob-access':'private','x-add-random-suffix':'0','x-allow-overwrite':'1','x-content-type':'application/pdf'})
    print(urllib.request.urlopen(req, timeout=60).status, date)
