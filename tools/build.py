#!/usr/bin/env python3
"""KI Fachblatt article generator. Format: docs/EDITORIAL.md. Run from repo root: python3 tools/build.py
Reads content/articles/*.json + content/images/*.jpg, writes <slug>.html, thema/<section>.html, redaktion.html,
assets/articles/<slug>.jpg and updates index.html (article table), sitemap.xml, news-sitemap.xml, feed.xml, llms.txt.
Idempotent. Articles with a future "published" are skipped (scheduled). Stdlib only."""
import json, os, re, sys, glob, html, shutil, struct, datetime
BASE = 'https://kifachblatt.de'
PERSON = 'https://philipp-paulik.de/#person'
AUTHOR_URL = BASE + '/redakteur/philipp-paulik'
ORG = BASE + '/#org'
PUB_NAME = 'KI Fachblatt'
SECTIONS = {  # key -> label
    'grundlagen': 'Grundlagen', 'architektur': 'Architektur', 'verlaesslichkeit': 'Verlässlichkeit', 'praxis': 'Praxis',
    'datenschutz': 'Datenschutz', 'methode': 'Methode', 'analyse': 'Analyse', 'modelle': 'Modelle', 'agenten': 'Agenten',
    'forschung': 'Forschung', 'evals': 'Evaluation', 'recht': 'Recht & Regulierung'}
TYPES = {'news': 'NewsArticle', 'analysis': 'NewsArticle', 'explainer': 'Article'}
SITEMAP_NEWS_TYPES = {'news', 'analysis'}
REQ = ['slug', 'title', 'dek', 'section', 'type', 'published', 'modified', 'author', 'tags', 'key_takeaways', 'hero', 'body', 'sources']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from share import share_block, SHARE_CSS
import mdpages
import report as kreport
errors = []
def err(slug, msg): errors.append('%s: %s' % (slug, msg))
esc = lambda s: html.escape(s, quote=True)

CITE = {'n': 0, 'ids': {}, 'seq': 0}

def _cite(m):
    nums = [int(x) for x in re.findall(r'\d+', m.group(0))]
    if not CITE['n'] or any(n < 1 or n > CITE['n'] for n in nums): return m.group(0)
    def link(n):
        CITE['seq'] += 1; cid = 'cr%d-%d' % (n, len(CITE['ids'].setdefault(n, [])) + 1)
        CITE['ids'][n].append(cid)
        return '<a id="%s" href="#q%d" aria-label="Quelle %d im Quellenverzeichnis">%d</a>' % (cid, n, n, n)
    txt = m.group(0)
    if re.search(r'[\u2013-]', txt) and len(nums) == 2: sep = '\u2013'
    else: sep = ', '
    return '<sup class="cr">[' + sep.join(link(n) for n in nums) + ']</sup>'

CITE_RE = r'\[(\d+)(?:\s*(?:,|\u2013|-)\s*\d+)*\]'
def cites(t): return re.sub(CITE_RE, _cite, t)

def inline(t):
    t = esc(t)
    t = cites(t)
    t = re.sub(r'\[\^(\d+)\]', r'<sup><a href="#q\1" aria-label="Quelle \1">[\1]</a></sup>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)', lambda m: '<a href="%s"%s>%s</a>' % (m.group(2), '' if m.group(2).startswith('/') else ' rel="noopener"', m.group(1)), t)
    return t

def jpeg_size(path):
    with open(path, 'rb') as f:
        d = f.read()
    if d[:2] != b'\xff\xd8': raise ValueError('not a JPEG')
    i = 2
    while i < len(d):
        if d[i] != 0xFF: i += 1; continue
        m = d[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack('>HH', d[i + 5:i + 9]); return w, h
        i += 2 + struct.unpack('>H', d[i + 2:i + 4])[0]
    raise ValueError('no SOF')

def parse_dt(s):
    return datetime.datetime.fromisoformat(s)
MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
def de_date(dt, time=True):
    s = '%d. %s %d' % (dt.day, MONTHS[dt.month - 1], dt.year)
    return s + (', %02d:%02d Uhr' % (dt.hour, dt.minute) if time else '')

def load_articles(now):
    arts = []
    for p in sorted(glob.glob('content/articles/*.json')):
        slug0 = os.path.basename(p)[:-5]
        try: a = json.load(open(p, encoding='utf-8'))
        except Exception as e: err(slug0, 'invalid JSON: %s' % e); continue
        n0 = len(errors)
        for k in REQ:
            if k not in a: err(slug0, 'missing field "%s"' % k)
        if len(errors) > n0: continue
        s = a['slug']
        if s != slug0: err(s, 'slug differs from filename')
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', s): err(s, 'slug must be lowercase ascii kebab-case')
        if os.path.exists(s + '.html') and s not in [x for x in generated_before]: err(s, 'slug collides with an existing hand-written page')
        if a['section'] not in SECTIONS: err(s, 'section must be one of %s' % ', '.join(SECTIONS))
        if a['type'] not in TYPES: err(s, 'type must be news|analysis|explainer')
        if len(a['title']) > 70: err(s, 'title longer than 70 chars (%d)' % len(a['title']))
        if not 100 <= len(a['dek']) <= 160: err(s, 'dek must be 100-160 chars (is %d)' % len(a['dek']))
        if len(a['key_takeaways']) < 3: err(s, 'need >=3 key_takeaways')
        if len(a['sources']) < 3: err(s, 'need >=3 sources')
        for i, so in enumerate(a['sources']):
            for k in ('title', 'publisher', 'url'):
                if not so.get(k): err(s, 'sources[%d] missing %s' % (i, k))
            if not str(so.get('url', '')).startswith('https://'): err(s, 'sources[%d].url must be https' % i)
        if a['author'] != 'philipp-paulik': err(s, 'author must be philipp-paulik')
        try: pub = parse_dt(a['published']); mod = parse_dt(a['modified'])
        except Exception as e: err(s, 'bad date: %s' % e); continue
        if pub.tzinfo is None or mod.tzinfo is None: err(s, 'dates need a time zone offset, e.g. +02:00')
        elif mod < pub: err(s, 'modified before published')
        h = a['hero']
        if not h.get('alt') or not h.get('caption'): err(s, 'hero needs alt and caption')
        ip = 'content/images/%s.jpg' % s
        if not os.path.exists(ip): err(s, 'missing %s' % ip)
        else:
            try:
                w, hh = jpeg_size(ip)
                if (w, hh) != (1600, 900): err(s, 'hero must be 1600x900 (is %dx%d)' % (w, hh))
                if os.path.getsize(ip) > 350 * 1024: err(s, 'hero larger than 350 KB')
            except Exception as e: err(s, 'hero unreadable: %s' % e)
        for b in a['body']:
            if b.get('t') == 'chart':
                if not (b.get('alt') and b.get('caption') and b.get('labels') and b.get('series')): err(s, 'chart needs alt, caption, labels, series')
            elif b.get('t') == 'figure':
                fp = 'content/images/' + b.get('file', '')
                if not os.path.exists(fp): err(s, 'missing figure file ' + fp)
                if not b.get('alt') or not b.get('caption'): err(s, 'figure needs alt and caption')
            elif b.get('t') not in ('p', 'h2', 'h3', 'ul', 'ol', 'quote', 'table', 'callout', 'code', 'chart'): err(s, 'unknown block type %r' % b.get('t'))
        if pub.tzinfo and pub > now: print('skip (scheduled):', s); continue
        a['_pub'], a['_mod'] = pub, mod
        arts.append(a)
    arts.sort(key=lambda a: a['_pub'], reverse=True)
    return arts


PALETTE = ['#7040cd', '#169a86', '#e08a1e', '#3b7dd8', '#c0396b']
def _num(v): return ('%.2f' % v).rstrip('0').rstrip('.').replace('.', ',') if isinstance(v, (int, float)) else str(v)
def chart_html(b, idx, slug):
    kind = b.get('kind', 'bar'); labels = b['labels']; series = b['series']; unit = b.get('unit', '')
    if kind not in ('bar', 'column', 'line'): err(slug, 'chart kind must be bar|column|line')
    for sr in series:
        if len(sr['values']) != len(labels): err(slug, 'chart %d: series "%s" length != labels' % (idx, sr.get('name'))); return ''
    vals = [v for sr in series for v in sr['values'] if v is not None]
    vmax = b.get('max') or (max(vals) if vals else 1)
    if not b.get('max') and vmax > 0:
        import math
        raw = (vmax - min(0, min(vals) if vals else 0)) / 4; mag = 10 ** math.floor(math.log10(raw)); step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
        vmax = math.ceil(vmax / step - 1e-9) * step
    vmin = min(0, min(vals)) if kind != 'line' else b.get('min', min(0, min(vals)))
    if vmax == vmin: vmax = vmin + 1
    leg = ''
    if len(series) > 1: leg = '<ul class="ch-leg">%s</ul>' % ''.join('<li><i style="background:%s"></i>%s</li>' % (PALETTE[i % 5], esc(sr['name'])) for i, sr in enumerate(series))
    if kind == 'bar':
        rows = ''
        for j, lab in enumerate(labels):
            bars = ''
            for i, sr in enumerate(series):
                v = sr['values'][j]
                if v is None: continue
                w = max(0.5, (v - vmin) / (vmax - vmin) * 100)
                bars += '<span class="ch-bar" style="width:%.1f%%;background:%s" title="%s: %s%s"></span><span class="ch-val">%s%s</span>' % (w, PALETTE[i % 5], esc(sr['name']), _num(v), esc(unit), _num(v), esc(unit))
            rows += '<div class="ch-row"><span class="ch-lab">%s</span><span class="ch-trk">%s</span></div>' % (inline(lab), bars)
        body = '<div class="ch-bars" role="img" aria-label="%s">%s</div>' % (esc(b['alt']), rows)
    else:
        W, H, L, R, T, B = 640, 340, 52, 16, 16, 64
        pw, ph = W - L - R, H - T - B
        y = lambda v: T + ph - (v - vmin) / (vmax - vmin) * ph
        n = len(labels)
        g = ''
        for k in range(5):
            v = vmin + (vmax - vmin) * k / 4
            g += '<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="ch-grid"/><text x="%d" y="%.1f" class="ch-t" text-anchor="end">%s</text>' % (L, W - R, y(v), y(v), L - 6, y(v) + 4, _num(round(v, 2)))
        marks = ''
        if kind == 'column':
            gw = pw / n; bw = min(48, gw * 0.7 / len(series))
            for j, lab in enumerate(labels):
                cx = L + gw * (j + .5)
                for i, sr in enumerate(series):
                    v = sr['values'][j]
                    if v is None: continue
                    x0 = cx - bw * len(series) / 2 + i * bw
                    marks += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" class="ch-m" tabindex="0"><title>%s, %s: %s%s</title></rect>' % (x0, min(y(v), y(0)), bw - 2, abs(y(v) - y(0)), PALETTE[i % 5], esc(lab), esc(sr['name']), _num(v), esc(unit))
                marks += '<text x="%.1f" y="%d" class="ch-t" text-anchor="middle">%s</text>' % (cx, H - B + 18, esc(lab if len(lab) < 20 else lab[:19] + '…'))
        else:
            for j, lab in enumerate(labels):
                cx = L + pw * (j + .5) / n
                marks += '<text x="%.1f" y="%d" class="ch-t" text-anchor="middle">%s</text>' % (cx, H - B + 18, esc(lab if len(lab) < 20 else lab[:19] + '…'))
            for i, sr in enumerate(series):
                pts = [(L + pw * (j + .5) / n, y(v), v, labels[j]) for j, v in enumerate(sr['values']) if v is not None]
                marks += '<polyline fill="none" stroke="%s" stroke-width="2.5" points="%s"/>' % (PALETTE[i % 5], ' '.join('%.1f,%.1f' % (px, py) for px, py, _, _ in pts))
                marks += ''.join('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s" class="ch-m" tabindex="0"><title>%s, %s: %s%s</title></circle>' % (px, py, PALETTE[i % 5], esc(l), esc(sr['name']), _num(v), esc(unit)) for px, py, v, l in pts)
        yl = '<text x="%d" y="12" class="ch-t">%s</text>' % (L, esc(b.get('y_label', unit))) if b.get('y_label', unit) else ''
        body = '<svg class="ch-svg" viewBox="0 0 %d %d" role="img" aria-label="%s" preserveAspectRatio="xMidYMid meet">%s%s%s</svg>' % (W, H, esc(b['alt']), g, marks, yl)
    head_ = ''.join('<th scope="col">%s</th>' % esc(x) for x in [b.get('x_label', '')] + [sr['name'] for sr in series])
    trs = ''.join('<tr><th scope="row">%s</th>%s</tr>' % (inline(l), ''.join('<td>%s%s</td>' % (_num(sr['values'][j]) if sr['values'][j] is not None else '–', esc(unit) if sr['values'][j] is not None else '') for sr in series)) for j, l in enumerate(labels))
    tbl = '<details class="ch-data"><summary>Daten als Tabelle</summary><div class="table-scroll"><table class="data"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div></details>' % (head_, trs)
    src = '<p class="ch-src">Quelle: %s</p>' % inline(b['source']) if b.get('source') else ''
    return '<figure class="chart" id="chart-%d"><figcaption class="ch-title">%s</figcaption>%s%s%s%s<p class="ch-cap">%s</p></figure>' % (idx, cites(esc(b.get('title', b['caption']))), leg, body, tbl, src, cites(esc(b['caption'])))

def body_html(a):
    out, toc, n = [], [], 0
    for b in a['body']:
        t = b['t']
        if t == 'p': out.append('<p>%s</p>' % inline(b['x']))
        elif t in ('h2', 'h3'):
            if t == 'h2': n += 1; toc.append((('s%d' % n), b['x'])); out.append('<h2 id="s%d">%s</h2>' % (n, inline(b['x'])))
            else: out.append('<h3>%s</h3>' % inline(b['x']))
        elif t in ('ul', 'ol'): out.append('<%s>%s</%s>' % (t, ''.join('<li>%s</li>' % inline(i) for i in b['items']), t))
        elif t == 'quote':
            c = ''
            if b.get('cite'): c = '<footer>%s</footer>' % (('<a href="%s" rel="noopener">%s</a>' % (esc(b['url']), esc(b['cite']))) if b.get('url') else esc(b['cite']))
            out.append('<blockquote><p>%s</p>%s</blockquote>' % (inline(b['x']), c))
        elif t == 'table':
            cap = '<caption>%s</caption>' % cites(esc(b['caption'])) if b.get('caption') else ''
            th = ''.join('<th scope="col">%s</th>' % inline(c) for c in b['head'])
            rows = ''.join('<tr>%s</tr>' % ''.join('<td%s>%s</td>' % (' class="nw"' if len(str(c)) <= 18 else '', inline(c)) for c in r) for r in b['rows'])
            out.append('<div class="table-scroll"><table class="data">%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cap, th, rows))
        elif t == 'callout': out.append('<aside class="callout"><b>%s</b><p>%s</p></aside>' % (esc(b.get('title', 'Hinweis')), inline(b['x'])))
        elif t == 'code': out.append('<pre><code%s>%s</code></pre>' % (' class="language-%s"' % esc(b['lang']) if b.get('lang') else '', esc(b['x'])))
        elif t == 'chart':
            nch = locals().get('nch', 0) + 1; out.append(chart_html(b, nch, a['slug']))
        elif t == 'figure':
            w, h = jpeg_size('content/images/' + b['file'])
            cap = cites(esc(b['caption'])) + (' · Illustration: KI-generiert' if b.get('ai_generated') and 'KI' not in b['caption'] else '')
            out.append('<figure class="fig"><img src="/assets/articles/%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async"><figcaption>%s</figcaption></figure>' % (esc(b['file']), esc(b['alt']), w, h, cap))
    return '\n'.join(out), toc

def jsonld(a):
    s, h = a['slug'], a['hero']
    url = '%s/%s' % (BASE, s)
    img_url = '%s/assets/articles/%s.jpg' % (BASE, s)
    credit = h.get('credit') or ('Illustration: KI-generiert' if h.get('ai_generated') else '')
    image = {'@type': 'ImageObject', '@id': url + '#image', 'url': img_url, 'contentUrl': img_url, 'width': 1600, 'height': 900,
             'caption': h['caption'], 'description': h['alt'], 'creator': {'@id': PERSON} if not h.get('ai_generated') else {'@id': ORG},
             'creditText': credit, 'copyrightNotice': '© %s KI Fachblatt (Philipp Paulik)' % a['published'][:4], 'license': BASE + '/redaktion#bilder-und-bildrechte', 'acquireLicensePage': BASE + '/redaktion#bilder-und-bildrechte'}
    if h.get('ai_generated'):
        image['digitalSourceType'] = 'http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia'
    body_text = ' '.join(re.sub(r'<[^>]+>', '', x.get('x', '')) for x in a['body'] if x['t'] in ('p',))
    art = {'@type': TYPES[a['type']], '@id': url + '#article', 'mainEntityOfPage': {'@type': 'WebPage', '@id': url}, 'url': url,
           'headline': a['title'], 'description': a['dek'], 'inLanguage': 'de-DE', 'datePublished': a['published'], 'dateModified': a['modified'],
           'author': {'@type': 'Person', '@id': PERSON, 'name': 'Philipp Paulik', 'url': AUTHOR_URL}, 'publisher': {'@id': ORG},
           'image': [image], 'articleSection': SECTIONS[a['section']], 'keywords': ', '.join(a['tags']), 'isAccessibleForFree': True,
           'wordCount': len(body_text.split()), 'citation': [{'@type': 'CreativeWork', 'name': x['title'], 'url': x['url'], 'publisher': {'@type': 'Organization', 'name': x['publisher']}} for x in a['sources']]}
    graph = [{'@type': 'Organization', '@id': ORG, 'name': PUB_NAME, 'url': BASE + '/', 'logo': {'@type': 'ImageObject', 'url': BASE + '/assets/logo-512.png', 'width': 512, 'height': 512}, 'founder': {'@id': PERSON}},
             {'@type': 'WebSite', '@id': BASE + '/#site', 'url': BASE + '/', 'name': PUB_NAME, 'inLanguage': 'de-DE', 'publisher': {'@id': ORG}},
             art, image,
             {'@type': 'BreadcrumbList', '@id': url + '#crumbs', 'itemListElement': [
                 {'@type': 'ListItem', 'position': 1, 'name': 'Start', 'item': BASE + '/'},
                 {'@type': 'ListItem', 'position': 2, 'name': SECTIONS[a['section']], 'item': '%s/thema/%s' % (BASE, a['section'])},
                 {'@type': 'ListItem', 'position': 3, 'name': a['title'], 'item': url}]}]
    if a.get('faq'):
        graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': [{'@type': 'Question', 'name': q['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': q['a']}} for q in a['faq']]})
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)

def head(title, desc, canon, extra='', og_type='website', image=None, ld=None, robots='index,follow,max-image-preview:large,max-snippet:-1'):
    image = image or 'https://kifachblatt.de/assets/kifachblatt-og.png'
    return ('<!doctype html>\n<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<script>document.documentElement.className="js";if(/\\.html$/.test(location.pathname))history.replaceState(null,"",location.pathname.replace(/\\.html$/,"")+location.search+location.hash)</script>\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="%s">\n<meta name="robots" content="%s">\n<meta name="theme-color" content="#100f0d">\n'
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png"><link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16.png"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">\n<link rel="alternate" type="application/rss+xml" title="KI Fachblatt" href="/feed.xml">\n'
            '<meta property="og:type" content="%s"><meta property="og:site_name" content="KI Fachblatt"><meta property="og:locale" content="de_DE">\n'
            '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:image" content="%s">%s\n'
            '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="%s">\n<link rel="stylesheet" href="/style.css">\n%s'
            '<link rel="author" href="%s"></head>') % (esc(title), esc(desc), canon, robots, og_type, esc(title), esc(desc), canon, image, extra, image,
            ('<script type="application/ld+json">%s</script>\n' % ld) if ld else '', AUTHOR_URL)

def article_page(a, shell_top, shell_bottom, arts):
    s, h = a['slug'], a['hero']
    url = '%s/%s' % (BASE, s)
    CITE.update(n=len(a['sources']), ids={}, seq=0)
    _tl = ''.join('<li>%s</li>' % inline(k) for k in a['key_takeaways'])
    body, toc = body_html(a)
    words = len(' '.join(x.get('x', '') for x in a['body']).split()) + sum(len(' '.join(x.get('items', [])).split()) for x in a['body'])
    mins = max(1, round(words / 200))
    pub, mod = a['_pub'], a['_mod']
    img = '/assets/articles/%s.jpg' % s
    extra = ('<meta property="og:image:width" content="1600"><meta property="og:image:height" content="900"><meta property="og:image:alt" content="%s">'
             '<meta property="article:published_time" content="%s"><meta property="article:modified_time" content="%s"><meta property="article:author" content="%s"><meta property="article:section" content="%s">') % (esc(h['alt']), a['published'], a['modified'], AUTHOR_URL, SECTIONS[a['section']])
    extra += ''.join('<meta property="article:tag" content="%s">' % esc(t) for t in a['tags'])
    out = [head(a['title'] + ' | KI Fachblatt', a['dek'], url, extra, 'article', BASE + img, jsonld(a)), shell_top]
    cap = esc(h['caption']) + ((' · ' + esc(h['credit'])) if h.get('credit') else (' · Illustration: KI-generiert' if h.get('ai_generated') else ''))
    modtxt = (' · aktualisiert <time datetime="%s">%s</time>' % (a['modified'], de_date(mod))) if mod != pub else ''
    out.append('<main id="main"><div class="wrap"><nav class="crumbs" aria-label="Brotkrumen"><a href="/">Start</a> › <a href="/thema/%s">%s</a></nav>' % (a['section'], SECTIONS[a['section']]))
    out.append('<article itemscope itemtype="https://schema.org/%s"><div class="art-head"><div class="kicker">%s</div><h1 itemprop="headline">%s</h1><p class="deck">%s</p>' % (TYPES[a['type']], SECTIONS[a['section']], esc(a['title']), esc(a['dek'])))
    out.append('<p class="byline"><a rel="author" href="%s">Philipp Paulik</a>, Redaktion KI Fachblatt · mit KI-Unterstützung erstellt, redaktionell verantwortet (<a href="/transparenz">so arbeiten wir</a>) · <time datetime="%s">%s</time>%s · %d Min. Lesezeit</p></div>' % (AUTHOR_URL, a['published'], de_date(pub), modtxt, mins))
    out.append(share_block(url, a['title'], 'kfb', True))
    out.append('<figure class="hero-fig"><img src="%s" alt="%s" width="1600" height="900" fetchpriority="high" decoding="async"><figcaption>%s</figcaption></figure>' % (img, esc(h['alt']), cap))
    out.append('<div class="tldr"><b>Kurz gesagt</b><ul>%s</ul></div>' % _tl)
    tocs = ''.join('<a href="#%s">%s</a>' % (i, esc(t)) for i, t in toc)
    extra_toc = '<a href="#quellen">Quellen</a>' + ('<a href="#faq">Häufige Fragen</a>' if a.get('faq') else '')
    out.append('<div class="art"><aside class="toc" aria-label="Inhalt"><b>Inhalt</b>%s%s</aside><div class="body" itemprop="articleBody">%s' % (tocs, extra_toc, body))
    if a.get('method') or a.get('limitations'):
        m = ''
        if a.get('method'): m += '<h2 id="methode">Methode</h2>' + ''.join('<p>%s</p>' % inline(x) for x in ([a['method']] if isinstance(a['method'], str) else a['method']))
        lim = a.get('limitations')
        if isinstance(lim, str): lim = [x for x in lim.split('\n') if x.strip()]
        if lim: m += '<h3>Grenzen</h3>' + (('<p>%s</p>' % inline(lim[0])) if isinstance(a.get('limitations'), str) and len(lim) == 1 else '<ul>%s</ul>' % ''.join('<li>%s</li>' % inline(l) for l in lim))
        out.append(m)
    def _bk(i):
        ids = CITE['ids'].get(i + 1, [])
        return ''.join(' <a class="bk" href="#%s" aria-label="Zurück zur Textstelle %d von Quelle %d">\u21a9%s</a>' % (c, k + 1, i + 1, (str(k + 1) if len(ids) > 1 else '')) for k, c in enumerate(ids[:6]))
    out.append('<h2 id="quellen">Quellen</h2><ol class="refs">%s</ol>' % ''.join(
        '<li id="q%d"><a href="%s" rel="noopener">%s</a>, %s%s%s</li>' % (i + 1, esc(x['url']), esc(x['title']), esc(x['publisher']), (' (abgerufen %s)' % esc(x['accessed'])) if x.get('accessed') else '', _bk(i)) for i, x in enumerate(a['sources'])))
    out.append(share_block(url, a['title'], 'kfb'))
    out.append('</div></div></article>')
    if a.get('faq'):
        out.append('<section class="faq" id="faq"><div class="wrap"><div class="sec-h"><h2>Häufige Fragen</h2></div>%s</div></section>' % ''.join('<details><summary>%s</summary><p>%s</p></details>' % (esc(q['q']), inline(q['a'])) for q in a['faq']))
    rel = [x for x in arts if x['slug'] in a.get('related', [])] or [x for x in arts if x['slug'] != s and x['section'] == a['section']][:2]
    if rel:
        out.append('<section class="block"><div class="wrap"><div class="sec-h"><h2>Weiterlesen</h2></div><div class="grid rel-grid">%s</div></div></section>' % ''.join(
            '<article class="card"><div class="kicker">%s</div><h3><a href="/%s">%s</a></h3><p>%s</p><a class="more" href="/%s">Lesen →</a></article>' % (SECTIONS[r['section']], r['slug'], esc(r['title']), esc(r['dek']), r['slug']) for r in rel))
    out.append('</div></main>')
    out.append(shell_bottom)
    return '\n'.join(out)

def simple_page(title, desc, canon, inner, shell_top, shell_bottom, ld=None):
    return '\n'.join([head(title, desc, canon, ld=ld), shell_top, '<main id="main"><div class="wrap">%s</div></main>' % inner, shell_bottom])

def redaktion_html():
    return '''<div class="legal"><div class="kicker">Redaktion</div><h1>Redaktionelle Grundsätze</h1>
<p>Das KI Fachblatt erscheint im Verlag von Philipp Paulik, Neunkirchen-Seelscheid. Verantwortlich im Sinne des § 18 Abs. 2 MStV ist Philipp Paulik (<a href="/impressum">Impressum</a>, <a href="/redakteur/philipp-paulik">Autorenprofil</a>). Kontakt: <a href="mailto:philipp.l.paulik@gmail.com">philipp.l.paulik@gmail.com</a>.</p>
<h2 id="ki-einsatz">Einsatz von KI</h2><p>Beiträge entstehen mit KI-Unterstützung: Recherche, Entwurf und Bildentwurf werden von KI-Werkzeugen unterstützt. Auswahl der Themen, Prüfung der Quellen und die Veröffentlichung verantwortet der Herausgeber. Jeder Beitrag nennt seine Quellen. Wir erfinden keine Zitate, Zahlen oder Studien und kennzeichnen Unsicherheit im Text.</p>
<h2 id="bildrechte">Bilder und Bildrechte</h2><p>Von KI erzeugte Bilder tragen im Bild den Hinweis „KI-generiert“ und in der Bildunterschrift die Angabe „Illustration: KI-generiert“. Alle Bilder haben einen Alternativtext. Eigene Bilder des KI Fachblatts dürfen mit Quellenangabe (KI Fachblatt, kifachblatt.de) verlinkt und zitiert werden; für eine weitergehende Nutzung bitte per E-Mail anfragen.</p>
<h2 id="quellen">Quellen und Belege</h2><p>Wir bevorzugen Primärquellen: Veröffentlichungen, Modellkarten, technische Dokumentation und Messdaten. Eigene Tests werden nur beschrieben, wenn wir sie wirklich durchgeführt haben, mit Methode und Grenzen.</p>
<h2 id="korrekturen">Korrekturen</h2><p>Fehler werden im Beitrag korrigiert. Bei inhaltlichen Änderungen setzen wir das Aktualisierungsdatum und vermerken die Korrektur im Text. Hinweise bitte per E-Mail an die oben genannte Adresse.</p>
<h2 id="werbung">Werbung und Unabhängigkeit</h2><p>Das KI Fachblatt verkauft derzeit keine Anzeigen und nimmt keine bezahlten Beiträge an. Sollte sich das ändern, wird bezahlter Inhalt klar als solcher gekennzeichnet. Wir nehmen keine Stellung zu parteipolitischen Themen.</p></div>'''

def thumb_html(a):
    return ('<a class="thumb" href="/%s" tabindex="-1" aria-hidden="true"><img src="/assets/articles/%s-800.jpg" alt="" width="800" height="450" loading="lazy" decoding="async"></a>' % (a['slug'], a['slug'])) if os.path.exists('assets/articles/%s-800.jpg' % a['slug']) else ''

def section_html(key, arts):
    items = ''.join(('<article class="card">' + thumb_html(a) + '<div class="kicker">%s</div><h3><a href="/%s">%s</a></h3><p>%s</p><span class="meta"><time datetime="%s">%s</time></span><br><a class="more" href="/%s">Lesen →</a></article>') % (
        SECTIONS[key], a['slug'], esc(a['title']), esc(a['dek']), a['published'], de_date(a['_pub'], False), a['slug']) for a in arts if a['section'] == key)
    return '<div class="sec-h"><h1>%s</h1></div><div class="grid rel-grid">%s</div>' % (SECTIONS[key], items)

def replace_block(text, start, end, new):
    i, j = text.find(start), text.find(end)
    if i < 0 or j < 0: return None
    return text[:i + len(start)] + '\n' + new + '\n' + text[j:]

generated_before = []
BURGER_JS = '<script>document.documentElement.classList.add("js");(function(){var b=document.querySelector(".burger"),m=document.getElementById("menu");if(!b||!m)return;function c(){m.classList.remove("open");b.setAttribute("aria-expanded","false");b.setAttribute("aria-label","Menü")}b.addEventListener("click",function(){var o=m.classList.toggle("open");b.setAttribute("aria-expanded",o?"true":"false");b.setAttribute("aria-label",o?"Menü schließen":"Menü")});document.addEventListener("keydown",function(e){if(e.key==="Escape")c()});m.addEventListener("click",function(e){if(e.target.tagName==="A")c()})})()</script>'
BURGER_BTN = '<button type="button" class="burger" aria-label="Menü" aria-expanded="false" aria-controls="menu"><span></span><span></span><span></span></button>'
SEARCH_ICO = ('<a class="search-ico" href="/suche" aria-label="Suche" title="Suche">'
              '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true" focusable="false"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.8-3.8"/></svg></a>')

def patch_footer_and_bylines():
    navre = re.compile(r'<nav(?: aria-label="Hauptnavigation" class="main"| class="main" aria-label="Hauptnavigation")>(.*?)</nav>', re.S)
    old = '<a href="/impressum">Impressum</a><br/><a href="/datenschutz">Datenschutz</a>'
    new = '<a href="/transparenz">KI-Transparenz</a><br/><a href="/redaktion">Redaktion</a><br/><a href="/korrekturen">Korrekturen</a><br/><a href="/quellen">Quellen</a><br/>' + old
    for f in glob.glob('**/*.html', recursive=True):
        t = open(f, encoding='utf-8').read(); o = t
        if '<a href="/glossar">Glossar</a><br/><a href="/ueber">' in t and '/berichte">KI-Tagesbericht' not in t: t = t.replace('<a href="/glossar">Glossar</a><br/><a href="/ueber">', '<a href="/glossar">Glossar</a><br/><a href="/berichte">KI-Tagesbericht (PDF)</a><br/><a href="/ueber">', 1)
        if old in t and '/transparenz">KI-Transparenz' not in t: t = t.replace(old, new, 1)
        if 'class="burger"' not in t:
            t = navre.sub(lambda m: BURGER_BTN + '<nav class="main" id="menu" aria-label="Hauptnavigation">' + m.group(1) + '</nav>' + BURGER_JS, t, count=1)
        t = t.replace('mit KI-Unterstützung erstellt · <time', 'mit KI-Unterstützung erstellt, redaktionell verantwortet (<a href="/transparenz">so arbeiten wir</a>) · <time')
        if 'href="/suche"' not in t:
            t = re.sub(r'(<nav class="main" id="menu" aria-label="Hauptnavigation">(?:(?!</nav>).)*?)(<a href="/ueber")', lambda m: m.group(1) + '<a class="st" href="/suche">Suche</a>' + m.group(2), t, count=1, flags=re.S)
        t = t.replace('<a href="/suche">Suche</a>', '<a class="st" href="/suche">Suche</a>')
        if 'class="search-ico"' not in t and '</nav>' in t:
            t = t.replace('</nav>', '</nav>' + SEARCH_ICO, 1)
        if t != o: open(f, 'w', encoding='utf-8').write(t)

def patch_static_shares():
    for f in sorted(glob.glob('*.html')):
        t = open(f, encoding='utf-8').read()
        if 'class="byline"' not in t or 'class="share' in t: continue
        m = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S); c = re.search(r'<link rel="canonical" href="([^"]+)"', t)
        if not m or not c: continue
        title = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip(); url = c.group(1)
        i = t.find('<div class="tldr"')
        j = t.find('<section class="faq"')
        if j < 0: j = t.find('<section class="block"')
        if i < 0 or j < 0 or j < i: print('WARN share skip', f); continue
        t = t[:i] + share_block(url, title, 'kfb', True) + t[i:j] + share_block(url, title, 'kfb') + t[j:]
        open(f, 'w', encoding='utf-8').write(t)

def slugify(t):
    t = t.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

def glossary_page(shell_top, shell_bottom, now):
    CITE['n'] = 0
    terms = sorted(json.load(open('content/glossary.json', encoding='utf-8')), key=lambda x: x['term'].lower())
    ids = {x['term']: slugify(x['term']) for x in terms}
    def art_title(path):
        f = path.strip('/') + '.html'
        try: m = re.search(r'<h1[^>]*>(.*?)</h1>', open(f, encoding='utf-8').read(), re.S); return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        except Exception: return None
    letters = sorted({slugify(x['term'])[0].upper() for x in terms})
    nav = '<nav class="az" aria-label="Glossar A bis Z">' + ''.join('<a href="#buchstabe-%s">%s</a>' % (l, l) for l in letters) + '</nav>'
    body, cur = '', None
    for x in terms:
        l = slugify(x['term'])[0].upper()
        if l != cur:
            if cur: body += '</dl></section>'
            body += '<section class="gl-sec" id="buchstabe-%s"><h2 class="gl-letter">%s</h2><dl class="gl-list">' % (l, l); cur = l
        aka = ('<span class="gl-aka">auch: %s</span>' % esc(', '.join(x['aka']))) if x.get('aka') else ''
        dd = '<p>%s</p>' % inline(x['definition'])
        if x.get('usage'): dd += '<p class="gl-use"><b>In der Praxis:</b> %s</p>' % inline(x['usage'])
        rel = [(r, art_title(r)) for r in x.get('related', [])]
        links = ''.join('<a href="%s">%s</a>' % (r, esc(t)) for r, t in rel if t)
        sa = ''.join('<a href="#%s">%s</a>' % (ids[t], esc(t)) for t in x.get('see_also', []) if t in ids)
        if links: dd += '<p class="gl-more"><b>Artikel:</b> %s</p>' % links
        if sa: dd += '<p class="gl-more"><b>Siehe auch:</b> %s</p>' % sa
        if x.get('sources'): dd += '<p class="gl-src"><b>Quellen:</b> %s</p>' % ' · '.join('<a href="%s" rel="noopener">%s</a>' % (esc(sr['url']), esc(sr['title'])) for sr in x['sources'])
        body += '<dt id="%s">%s%s</dt><dd>%s</dd>' % (ids[x['term']], esc(x['term']), aka, dd)
    body += '</dl></section>'
    setld = {'@context': 'https://schema.org', '@type': 'DefinedTermSet', '@id': BASE + '/glossar#set', 'name': 'KI-Glossar des KI Fachblatts', 'url': BASE + '/glossar', 'inLanguage': 'de',
             'hasDefinedTerm': [dict({'@type': 'DefinedTerm', '@id': '%s/glossar#%s' % (BASE, ids[x['term']]), 'name': x['term'], 'description': x['definition'], 'url': '%s/glossar#%s' % (BASE, ids[x['term']]), 'inDefinedTermSet': BASE + '/glossar#set'}, **({'alternateName': x['aka']} if x.get('aka') else {})) for x in terms]}
    inner = ('<div class="art-head"><div class="kicker">Nachschlagen</div><h1>Glossar: KI-Begriffe, kurz erklärt</h1><p class="deck">%d Begriffe rund um Sprachmodelle, Agenten und Werkzeuge: mit Definition, Praxishinweis und Quellen. Beispielrechnungen sind als „eigene Rechnung“ gekennzeichnet.</p></div>%s<div class="gl-wrap">%s</div>' % (len(terms), nav, body))
    title = 'KI-Glossar: %d Begriffe von Adapter bis Zero-Shot erklärt | KI Fachblatt' % len(terms)
    desc = 'Das KI-Glossar des KI Fachblatts erklärt %d Begriffe zu Sprachmodellen, Agenten, RAG und Evaluation: mit Definition, Praxishinweis, Quellen und Links zu Artikeln.' % len(terms)
    return simple_page(title, desc, BASE + '/glossar', inner, shell_top, shell_bottom, ld=json.dumps(setld, ensure_ascii=False).replace('</', '<\\/'))


SEARCH_PAGES = [
    ('Glossar: KI-Begriffe, kurz erklärt', '/glossar', 'Seite', 'Das KI-Glossar erklärt Begriffe zu Sprachmodellen, Agenten, RAG und Evaluation.'),
    ('KI-Tagesbericht als PDF', '/berichte', 'Seite', 'Tägliche Ausgabe als PDF: Trending-Modelle, die Analysen des Tages, Impressum.'),
    ('Über das Magazin', '/ueber', 'Seite', 'Das KI Fachblatt ist ein deutschsprachiges Fachmagazin über künstliche Intelligenz von Philipp Paulik.'),
]

def legacy_article_docs(gen_slugs):
    docs = []
    for f in sorted(glob.glob('*.html')):
        slug = f[:-5]
        if slug in gen_slugs or slug in ('index', 'suche', '404'):
            continue
        t = open(f, encoding='utf-8').read()
        if '<div class="body"' not in t or '<div class="art-head">' not in t:
            continue
        m = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
        if not m:
            continue
        title = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        k = re.search(r'<div class="kicker">([^<]*)</div>', t)
        d = re.search(r'<meta name="description" content="([^"]*)"', t)
        tm = re.search(r'<time datetime="([^"]+)"', t)
        i = t.find('<div class="body"'); j = t.find('</article>', i)
        text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t[i:j if j > 0 else i + 30000]))).strip()
        dt = tm.group(1) if tm else ''
        try:
            pub = parse_dt(dt); ts = int(pub.timestamp()); ds = de_date(pub, False)
        except Exception:
            ts, ds = 0, ''
        docs.append({'t': title, 'u': '/' + slug, 'k': k.group(1).strip() if k else 'Beitrag',
                     'd': html.unescape(d.group(1)) if d else '', 'g': '', 'x': text[:6000], 'ts': ts, 'dt': ds})
    return docs

def article_doc(a):
    parts = list(a.get('key_takeaways', []))
    for b in a['body']:
        if b.get('x'): parts.append(b['x'])
        parts.extend(b.get('items', []) or [])
        for r in b.get('rows', []) or []: parts.extend(str(c) for c in r)
    for q in a.get('faq', []) or []: parts += [q.get('q', ''), q.get('a', '')]
    text = re.sub(r'[*_`]', '', re.sub(r'\[\^(\d+)\]', r'[\1]', re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)', r'\1', ' '.join(parts))))
    return {'t': a['title'], 'u': '/' + a['slug'], 'k': SECTIONS[a['section']], 'd': a['dek'],
            'g': ' '.join(a.get('tags', [])), 'x': text[:6000], 'ts': int(a['_pub'].timestamp()), 'dt': de_date(a['_pub'], False)}

def glossary_docs():
    try:
        terms = json.load(open('content/glossary.json', encoding='utf-8'))
    except Exception:
        return []
    return [{'t': x['term'], 'u': '/glossar#' + slugify(x['term']), 'k': 'Glossar',
             'd': re.sub(r'[*_`]', '', x.get('definition', '')), 'g': ' '.join(x.get('aka', [])),
             'x': re.sub(r'[*_`]', '', x.get('usage', '')), 'ts': 0, 'dt': ''} for x in terms]

def build_search(arts, shell_top, shell_bottom, now):
    docs = [article_doc(a) for a in arts] + legacy_article_docs({a['slug'] for a in arts}) + glossary_docs()
    docs += [{'t': t, 'u': u, 'k': k, 'd': d, 'g': '', 'x': '', 'ts': 0, 'dt': ''} for t, u, k, d in SEARCH_PAGES]
    json.dump({'generated': now.isoformat(timespec='seconds'), 'docs': docs}, open('search-index.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    js = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search.js'), encoding='utf-8').read()
    inner = ('<div class="legal"><div class="kicker">Suche</div><h1>Beiträge durchsuchen</h1>'
             '<p>Alle Beiträge und Glossar-Begriffe des KI Fachblatts. Die Suche läuft lokal in deinem Browser, ohne Tracking. Umlaute und kleine Tippfehler sind egal.</p>'
             '<form class="searchbox" role="search" action="/suche" method="get"><label for="sq">Suchbegriff</label><div class="searchrow"><input id="sq" name="q" type="search" placeholder="Agenten, Kosten, RAG …" autocomplete="off"><button class="btn" type="submit">Suchen</button></div></form>'
             '<p id="sstatus" class="searchstatus" role="status"></p><ul id="sresults" class="searchresults"></ul>'
             '<noscript><p>Für die Suche wird JavaScript benötigt. Alle Beiträge stehen in der <a href="/#themen">Artikelübersicht der Startseite</a>.</p></noscript></div>'
             '<script>' + js + '</script>')
    open('suche.html', 'w', encoding='utf-8').write(simple_page('Suche | KI Fachblatt', 'Alle Beiträge und Glossar-Begriffe des KI Fachblatts durchsuchen: lokal im Browser, ohne Tracking.', BASE + '/suche', inner, shell_top, shell_bottom))
    return len(docs)

def main():
    global generated_before
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from zoneinfo import ZoneInfo
    now = datetime.datetime.now(ZoneInfo('Europe/Berlin'))
    if os.path.exists('.generated.json'): generated_before = json.load(open('.generated.json'))
    arts = load_articles(now)
    if errors:
        print('BUILD FAILED:'); [print(' -', e) for e in errors]; sys.exit(1)
    shell = open('halluzinationen.html', encoding='utf-8').read()
    shell_top = shell[shell.index('<body>'):shell.index('<main id="main">')]
    shell_bottom = shell[shell.index('</main>') + len('</main>'):]
    os.makedirs('assets/articles', exist_ok=True); os.makedirs('thema', exist_ok=True)
    for a in arts:
        shutil.copyfile('content/images/%s.jpg' % a['slug'], 'assets/articles/%s.jpg' % a['slug'])
        tp = 'assets/articles/%s-800.jpg' % a['slug']
        if not os.path.exists(tp):
            try:
                from PIL import Image
                Image.open('content/images/%s.jpg' % a['slug']).convert('RGB').resize((800, 450), Image.LANCZOS).save(tp, quality=82, optimize=True, progressive=True)
            except ImportError: pass
        for b in a['body']:
            if b['t'] == 'figure': shutil.copyfile('content/images/' + b['file'], 'assets/articles/' + b['file'])
        open(a['slug'] + '.html', 'w', encoding='utf-8').write(article_page(a, shell_top, shell_bottom, arts))
    sections = sorted({a['section'] for a in arts})
    for k in sections:
        open('thema/%s.html' % k, 'w', encoding='utf-8').write(simple_page('%s | KI Fachblatt' % SECTIONS[k], 'Alle Beiträge des KI Fachblatts zum Thema %s.' % SECTIONS[k], '%s/thema/%s' % (BASE, k), section_html(k, arts), shell_top, shell_bottom))
    open('glossar.html', 'w', encoding='utf-8').write(glossary_page(shell_top, shell_bottom, now))
    n_search = build_search(arts, shell_top, shell_bottom, now)

    from daily_archive import sync, archive_html
    sync('.', 'berichte', 'ki-tagesbericht.pdf', 'ki-tagesbericht-', now, seed_only=True)
    ok, hf = kreport.build(arts, now, BASE)
    archive_dates = sync('.', 'berichte', 'ki-tagesbericht.pdf', 'ki-tagesbericht-', now, archive_today=ok)
    stand = now.strftime('%d.%m.%Y, %H:%M') + ' Uhr'
    hfx = ('<div class="hfx" id="hfx" hidden><h2>Live-Auswahl</h2><p>Eigene Sortierung und Aufgabe wählen. Die Daten kommen live im Browser von der öffentlichen Hugging-Face-API (kein Schlüssel, kein Tracking durch uns) und werden zehn Minuten zwischengespeichert.</p>'
           '<div class="ctl"><label>Sortierung<select id="hf-sort"><option value="trend">Trend</option><option value="likes">Likes</option><option value="downloads">Downloads</option><option value="new">Neueste (unter den 100 Trendigsten)</option></select></label>'
           '<label>Aufgabe<select id="hf-tag"><option value="">Alle</option><option>text-generation</option><option>image-text-to-text</option><option>any-to-any</option><option>text-to-image</option><option>text-to-video</option><option>image-to-video</option><option>automatic-speech-recognition</option><option>text-to-speech</option><option>feature-extraction</option><option>image-classification</option><option>translation</option></select></label></div>'
           '<p class="ts-print" id="hf-ts"></p><div class="bar nopr"><span id="hf-stand"></span><button type="button" class="btn" id="hf-reload">Neu laden</button><button type="button" class="btn" id="hf-print" disabled>Auswahl als PDF drucken / speichern</button></div>'
           '<div id="hf-out" class="table-scroll"></div><p class="method-note">Likes, Downloads und Trend-Score sind Zähler der API, keine Qualitätsbewertung und kein Benchmark-Ergebnis. „Neueste“ sortiert die 100 aktuell trendigsten Modelle nach Erstellungsdatum, weil die reine Neu-Liste fast nur leere Uploads enthält. Zum Speichern als PDF im Druckdialog „Als PDF speichern“ wählen.</p><hr class="nopr"><h2 class="nopr">Tägliches PDF</h2></div>'
           '<p id="hf-nojs" class="mut">Für die Live-Auswahl wird JavaScript benötigt. Das tägliche PDF funktioniert ohne.</p>'
           '<link rel="stylesheet" href="/assets/berichte.css"><script src="/assets/berichte.js" defer></script>')
    inner = ('<div class="legal"><div class="kicker">Berichte</div><h1>KI-Tagesbericht</h1>'
             '<p>Die Tagesausgabe fasst die 20 aktuell meistbeachteten Modelle auf Hugging Face (Sortierung nach dem Trend-Score der öffentlichen API), die zwei neuesten Analysen des KI Fachblatts und das Impressum mit Redaktionsschluss auf vier A4-Seiten zusammen. Hell, druckfreundlich, ohne Tracking.</p>'
             + hfx + '<p><a class="btn" href="/berichte/ki-tagesbericht.pdf" download>PDF herunterladen</a> &nbsp; <a href="/berichte/tagesbericht">Druckansicht im Browser</a></p>'
             '<p class="mut">Stand der aktuellen Ausgabe: %s. Modelldaten: Hugging Face (öffentliche API). Likes, Downloads und Trend-Score sind Zähler der API, keine Qualitätsbewertung. Die Ausgabe wird automatisch erstellt; Inhalte entstehen mit KI-Unterstützung und werden redaktionell geprüft (<a href="/transparenz">so arbeiten wir</a>).</p></div>') % stand
    from report_landing import build as report_landing
    inner = report_landing('.', '.', 'kfb', archive_dates, 'ki-tagesbericht.pdf', 'ki-tagesbericht-')
    open('berichte.html', 'w', encoding='utf-8').write(simple_page('KI-Tagesbericht als PDF | KI Fachblatt', 'Täglicher KI-Tagesbericht als PDF: Trending-Modelle von Hugging Face, die Analysen des Tages, Impressum. Kostenlos, druckfreundlich.', BASE + '/berichte', inner, shell_top, shell_bottom))
    pages = mdpages.load('content/pages')
    for k, pg in pages.items():
        inner = '<div class="legal"><div class="kicker">Redaktion</div><h1>%s</h1>%s</div>' % (esc(pg['title']), pg['html'])
        open(k + '.html', 'w', encoding='utf-8').write(simple_page(pg['title'] + ' | KI Fachblatt', pg['desc'] or pg['title'], BASE + '/' + k, inner, shell_top, shell_bottom))
    patch_static_shares(); patch_footer_and_bylines()
    json.dump([a['slug'] for a in arts], open('.generated.json', 'w'))
    # index table
    idx = open('index.html', encoding='utf-8').read()
    rows = ''.join(('<tr data-topic="%s"><td>' + thumb_html(a) + '<a href="/%s">%s</a><p>%s</p></td><td><span class="topic">%s</span></td><td>%s</td><td><a aria-label="%s lesen" class="read" href="/%s">Lesen ↗</a></td></tr>') % (
        SECTIONS[a['section']], a['slug'], esc(a['title']), esc(a['dek']), SECTIONS[a['section']], de_date(a['_pub'], False), esc(a['title']), a['slug']) for a in arts)
    new = replace_block(idx, '<!--GEN-ARTICLES:START-->', '<!--GEN-ARTICLES:END-->', rows)
    if new is None: print('WARN: index.html has no <!--GEN-ARTICLES--> markers; run PR setup first')
    else: open('index.html', 'w', encoding='utf-8').write(new)
    # sitemap
    sm = open('sitemap.xml', encoding='utf-8').read()
    static = [m for m in re.findall(r'<url>.*?</url>', sm, re.S) if not any('<loc>%s/%s</loc>' % (BASE, x) in m for x in [a['slug'] for a in arts] + ['thema/' + k for k in sections] + list(pages) + ['berichte', 'suche'])]
    gen = []
    for a in arts:
        gen.append('<url><loc>%s/%s</loc><lastmod>%s</lastmod><image:image><image:loc>%s/assets/articles/%s.jpg</image:loc><image:title>%s</image:title><image:caption>%s</image:caption></image:image></url>' % (BASE, a['slug'], a['modified'], BASE, a['slug'], esc(a['title']), esc(a['hero']['alt'])))
    for k in sections: gen.append('<url><loc>%s/thema/%s</loc><lastmod>%s</lastmod></url>' % (BASE, k, max(a['modified'] for a in arts if a['section'] == k)))
    gen.append('<url><loc>%s/berichte</loc><lastmod>%s</lastmod></url>' % (BASE, now.date().isoformat()))
    gen.append('<url><loc>%s/suche</loc><lastmod>%s</lastmod></url>' % (BASE, now.date().isoformat()))
    for k in pages: gen.append('<url><loc>%s/%s</loc><lastmod>%s</lastmod></url>' % (BASE, k, now.date().isoformat()))
    open('sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(static + gen) + '</urlset>\n')
    # news sitemap (last 2 days)
    recent = [a for a in arts if a['type'] in SITEMAP_NEWS_TYPES and now - a['_pub'] <= datetime.timedelta(hours=48)][:1000]
    ns = ''.join('<url><loc>%s/%s</loc><news:news><news:publication><news:name>%s</news:name><news:language>de</news:language></news:publication><news:publication_date>%s</news:publication_date><news:title>%s</news:title></news:news></url>\n' % (BASE, a['slug'], PUB_NAME, a['published'], esc(a['title'])) for a in recent)
    open('news-sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' + ns + '</urlset>\n')
    # robots
    rb = open('robots.txt').read()
    if 'news-sitemap.xml' not in rb: open('robots.txt', 'w').write(rb.rstrip('\n') + '\nSitemap: %s/news-sitemap.xml\n' % BASE)
    # feed
    fd = open('feed.xml', encoding='utf-8').read()
    old = [m for m in re.findall(r'<item>.*?</item>', fd, re.S) if not any('<guid>%s/%s</guid>' % (BASE, a['slug']) in m for a in arts)]
    items = ''.join('<item><title>%s</title><link>%s/%s</link><guid>%s/%s</guid><pubDate>%s</pubDate><category>%s</category><dc:creator>Philipp Paulik</dc:creator><description>%s</description></item>' % (
        esc(a['title']), BASE, a['slug'], BASE, a['slug'], a['_pub'].strftime('%a, %d %b %Y %H:%M:%S %z'), SECTIONS[a['section']], esc(a['dek'])) for a in arts)
    head_ = fd[:fd.index('<item>')] if '<item>' in fd else fd[:fd.index('</channel>')]
    head_ = head_.replace('<rss version="2.0">', '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">')
    open('feed.xml', 'w', encoding='utf-8').write(head_ + items + ''.join(old) + '</channel></rss>\n')
    # llms.txt
    ll = open('llms.txt', encoding='utf-8').read()
    lines = ''.join('- [%s](%s/%s): %s\n' % (a['title'], BASE, a['slug'], a['dek']) for a in arts)
    if '<!--GEN-->' in ll: ll = re.sub(r'<!--GEN-->.*?<!--/GEN-->', lambda m: '<!--GEN-->\n' + lines + '<!--/GEN-->', ll, flags=re.S)
    else: ll = ll.replace('## Beiträge\n\n', '## Beiträge\n\n<!--GEN-->\n' + lines + '<!--/GEN-->\n', 1)
    open('llms.txt', 'w', encoding='utf-8').write(ll)
    print('built %d article(s), %d section page(s); news-sitemap: %d; search-index: %d' % (len(arts), len(sections), len(recent), n_search))

if __name__ == '__main__':
    main()
    from portraits import render
    render('kfb', '.')
    import footer; footer.main('.')
    # Final isolated pass: advertising pages, consent UI and activation gates (no third-party code by default).
    import subprocess, sys
    subprocess.check_call([sys.executable, str(__import__('pathlib').Path(__file__).with_name('monetization.py')), '.'])

if __name__ == "__main__":
    from share_iconify import patch
    patch(".")

# Static in-article daily-report CTA, after all article renderers and consent passes.
if __name__ == '__main__':
    from report_breaker import main as add_report_breakers
    add_report_breakers('.')
