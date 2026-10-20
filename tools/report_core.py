"""Shared A4 print layout for the daily PDF editions (stdlib only). Chrome prints the HTML to PDF."""
import html, os, re, shutil, subprocess

DAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
esc = lambda s: html.escape(str(s), quote=True)

def lnk(url, label=None):
    return '<a href="%s">%s</a>' % (esc(url), esc(label if label is not None else url))

def dom(u):
    m = re.match(r'https?://(?:www\.)?([^/]+)', u or ''); return m.group(1) if m else (u or '')

def srclist(sources, limit=12):
    out = ''.join('<li>%s <span class="mut">(%s)</span></li>' % (lnk(x['url'], x.get('title') or dom(x['url'])), esc(dom(x['url']))) for x in sources[:limit] if x.get('url'))
    return ('<div class="sl"><b>Quellen</b><ol>%s</ol></div>' % out) if out else ''

CSS = '''
@page{size:A4;margin:16mm 15mm 18mm 15mm;
 @bottom-left{content:"%(brand)s · %(kind)s %(date)s";font:8pt Helvetica,Arial,sans-serif;color:#8a8f9c}
 @bottom-right{content:"Seite " counter(page) " von " counter(pages);font:8pt Helvetica,Arial,sans-serif;color:#8a8f9c}}
@page:first{margin-top:0;margin-left:0;margin-right:0;
 @bottom-left{content:"%(brand)s · %(kind)s %(date)s";font:8pt Helvetica,Arial,sans-serif;color:#8a8f9c;margin-left:15mm}
 @bottom-right{content:"Seite " counter(page) " von " counter(pages);font:8pt Helvetica,Arial,sans-serif;color:#8a8f9c;margin-right:15mm}}
*{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;font:9.6pt/1.5 Helvetica,Arial,"Liberation Sans",sans-serif;color:#1a1c24;background:#fff}
a{color:%(ac)s;text-decoration:underline;text-decoration-color:rgba(0,0,0,.25)}
.sl{margin-top:2mm;font-size:8pt;color:#3a3e4c}.sl ol{margin:1mm 0 0;padding-left:5mm}.sl li{margin:0 0 .6mm;overflow-wrap:anywhere}
.sl ol{columns:2;column-gap:6mm}.sl li{break-inside:avoid}
.art .t a{color:#14151b;text-decoration:none}
.pg{break-after:page}.pg:last-of-type{break-after:auto}
.cover{border:1px solid rgba(127,127,127,.28);background:%(soft)s;padding:12mm 15mm 9mm;margin-bottom:7mm;border-bottom:1px solid %(line)s}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:15pt;letter-spacing:-.01em;color:%(dk)s}
.brand svg,.brand img{height:30px;width:30px}
.cover h1{margin:9mm 0 2mm;font-size:26pt;line-height:1.1;letter-spacing:-.02em;color:#14151b}
.cover p{margin:0;font-size:10.5pt;color:#4a4e5c}
.wrap{padding:0}.pg:first-of-type .wrap{padding:0 15mm}.pg td,.pg th{white-space:nowrap}.pg td.w{white-space:normal}.pg table{font-size:8.6pt}
h2{font-size:12.5pt;margin:5mm 0 2.5mm;padding-bottom:1.5mm;border-bottom:2px solid %(ac)s;color:%(dk)s;break-after:avoid}
h2 small{font-size:8.5pt;font-weight:400;color:#6b7080;margin-left:6px}
table{width:100%%;border-collapse:collapse}tr{break-inside:avoid}
th{font-size:7.8pt;color:#6b7080;font-weight:600;text-transform:uppercase;letter-spacing:.04em;padding:4px 6px;text-align:right;border-bottom:1px solid #cfd3de}
td{padding:3px 6px;text-align:right;border-bottom:1px solid #eceef4;font-variant-numeric:tabular-nums}
th:first-child,td:first-child{text-align:left}th.l,td.l{text-align:left}
tbody tr:nth-child(even) td{background:#f8f9fc}
.mut{color:#6b7080}
.art{border:1px solid #dfe2ec;border-radius:4px;padding:3.2mm 4mm;margin-bottom:3.2mm;break-inside:avoid}
.art.lead{background:%(soft)s;padding:5mm}
.art .m{font-size:8pt;color:#6b7080;text-transform:uppercase;letter-spacing:.05em}
.art .t{font-size:11.5pt;font-weight:700;color:#14151b;margin:1px 0 2px;line-height:1.3}
.art.lead .t{font-size:15pt}
.art .d{font-size:9.3pt;color:#3a3e4c}
.art ul{margin:2mm 0 0;padding-left:5mm;font-size:9pt;color:#3a3e4c}
.art .u{font-size:8pt;color:%(ac)s;margin-top:2px;word-break:break-all}
.note{background:%(soft)s;border:1px solid %(line)s;border-radius:4px;padding:3mm 4mm;font-size:9pt;color:#2b3042;margin:3mm 0}
.last h3{font-size:10pt;margin:4.5mm 0 1mm;color:%(dk)s}
.last p{margin:0 0 1.5mm;font-size:9.2pt}
.imp{display:flex;gap:6mm}.imp>div{flex:1}
.foot{margin-top:5mm;font-size:8pt;color:#6b7080}
.print-btn{position:fixed;right:12px;top:12px;background:%(ac)s;color:#fff;border:0;border-radius:8px;padding:10px 16px;font:600 14px Arial,sans-serif;cursor:pointer}
@media print{.print-btn{display:none}}
'''

def render(brand, kind, date_label, ac, dk, soft, line, logo_svg, title, subtitle, pages, last):
    css = CSS % {'brand': brand, 'kind': kind, 'date': date_label, 'ac': ac, 'dk': dk, 'soft': soft, 'line': line}
    cover = '<div class="cover"><div class="brand">%s<span>%s</span></div><h1>%s</h1><p>%s</p></div>' % (logo_svg, esc(brand), esc(title), esc(subtitle))
    body = ''
    for i, p in enumerate(pages):
        body += '<div class="pg">%s<div class="wrap">%s</div></div>' % (cover if i == 0 else '', p)
    body += '<div class="pg last"><div class="wrap">%s</div></div>' % last
    return '<!doctype html><html lang="de"><head><meta charset="utf-8"><title>%s</title><style>%s</style></head><body><button class="print-btn" onclick="window.print()">Als PDF speichern / drucken</button>%s</body></html>' % (esc(title + ' ' + date_label), css, body)

def to_pdf(html_path, pdf_path):
    chrome = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
    if not chrome: return False
    if os.path.exists(pdf_path + '.tmp'): os.remove(pdf_path + '.tmp')
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', '--print-to-pdf=' + os.path.abspath(pdf_path + '.tmp'), 'file://' + os.path.abspath(html_path)], capture_output=True)
    from daily_archive import valid_pdf
    if not valid_pdf(pdf_path + '.tmp'): return False
    os.replace(pdf_path + '.tmp', pdf_path)
    return True

def logo_inline(path):
    s = open(path, encoding='utf-8').read()
    s = re.sub(r'<svg[^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="254 254 1540 1540" width="30" height="30">', s, count=1)
    return s
