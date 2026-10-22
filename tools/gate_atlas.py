#!/usr/bin/env python3
"""Upload des Modell-Atlas-Datenpakets in den privaten Blob ueber das Lead-Wall-Backend.
Fail closed: bei Fehler wird nichts geloescht und Exit-Code != 0. Env: LW_SECRET, optional LW_API.
Aufruf nach tools/modell_atlas_pack.py. Entfernt das lokale ZIP nur nach erfolgreichem Upload."""
import base64, hashlib, hmac, os, sys
import urllib.request

API = os.environ.get('LW_API', 'https://daily-hob-newsletter.vercel.app/lw')
VERSION = '1.0'

def main(root='.'):
    secret = os.environ.get('LW_SECRET')
    if not secret:
        sys.exit('gate_atlas: LW_SECRET missing, refusing to publish')
    z = os.path.join(root, 'build-artifacts', 'modell-atlas-datenpaket-v%s.zip' % VERSION)
    if not os.path.exists(z):
        sys.exit('gate_atlas: %s fehlt - erst tools/modell_atlas_pack.py laufen lassen' % z)
    auth = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), ('upload:atlas:' + VERSION).encode(), hashlib.sha256).digest()).decode().rstrip('=')
    req = urllib.request.Request(API + '/api/atlasupload?v=' + VERSION, data=open(z, 'rb').read(), method='POST',
        headers={'x-lw-auth': auth, 'content-type': 'application/zip'})
    st = urllib.request.urlopen(req, timeout=90).status
    if st != 200:
        sys.exit('gate_atlas: upload failed %s' % st)
    os.remove(z)
    print('gate_atlas: uploaded atlas package v%s' % VERSION)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
