"""Visual blocks for the KI-Tagesbericht PDF: KPI cards, bar charts, donut, age buckets, scatter,
model/benchmark cards from content/portraits.json and article images. Stdlib only, no network.
Only own content, public API counters and monograms (no third-party logos or avatars)."""
import base64, collections, datetime, hashlib, json, math, os
from report_core import esc, lnk

AC, DK = '#7040cd', '#3d2380'
PALETTE = ['#7040cd', '#3f7ae0', '#12a594', '#e08a1e', '#d1457a', '#6b7080', '#8f6be0', '#2fa4d9']
TASKS = {'text-generation': 'Textgenerierung', 'image-text-to-text': 'Bild+Text zu Text', 'any-to-any': 'Multimodal (any-to-any)',
         'text-to-image': 'Text zu Bild', 'text-to-speech': 'Sprachsynthese', 'automatic-speech-recognition': 'Spracherkennung',
         'image-to-image': 'Bild zu Bild', 'text-to-video': 'Text zu Video', 'image-to-text': 'Bild zu Text', 'feature-extraction': 'Embeddings',
         'text-ranking': 'Ranking', 'image-to-video': 'Bild zu Video', 'video-text-to-text': 'Video+Text zu Text', 'robotics': 'Robotik',
         'text-to-audio': 'Text zu Audio', 'fill-mask': 'Fill-Mask', 'translation': 'Übersetzung', 'image-classification': 'Bildklassifikation',
         'audio-text-to-text': 'Audio+Text zu Text', 'unknown': 'Ohne Angabe'}
de = lambda v: '{:,}'.format(int(round(v))).replace(',', '.')


def short(n):
    n = float(n)
    if n >= 1e6: return ('%.1f' % (n / 1e6)).replace('.', ',') + ' Mio.'
    if n >= 1e3: return ('%.1f' % (n / 1e3)).replace('.', ',') + ' Tsd.'
    return str(int(n))


def task_label(t): return TASKS.get(t or 'unknown', t or 'Ohne Angabe')
def org(m): return m['id'].split('/')[0] if '/' in m['id'] else '–'
def name(m): return m['id'].split('/', 1)[-1]


def age_days(m, now):
    try:
        d = datetime.datetime.fromisoformat(m['createdAt'].replace('Z', '+00:00'))
        return max(0, (now.astimezone(datetime.timezone.utc) - d).days)
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


# --- Portrait logos (offline, embedded). Only assets listed in content/portrait-logos/manifest.json, verified by SHA256. ---
LOGOS, USED = {}, set()
# HF organisation -> company asset. Only unambiguous organisation/company pairs; everything else stays a monogram.
HF_ORG_LOGO = {'nvidia': 'nvidia', 'mistralai': 'mistral-ai', 'openai': 'openai', 'anthropic': 'anthropic', 'google': 'google-deepmind', 'facebook': 'meta', 'meta-models': 'meta'}
DARK = {'nvidia'}  # white wordmark, needs the dark plate


def load_logos(root):
    LOGOS.clear(); USED.clear()
    d = os.path.join(root, 'content', 'portrait-logos')
    try:
        man = json.load(open(os.path.join(d, 'manifest.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return
    for k, e in man.items():
        try:
            raw = open(os.path.join(d, e['file']), 'rb').read()
        except (OSError, KeyError):
            continue
        if hashlib.sha256(raw).hexdigest() != e.get('sha256'):
            continue
        mime = 'image/svg+xml' if e['file'].endswith('.svg') else 'image/png'
        LOGOS[k] = {'uri': 'data:%s;base64,%s' % (mime, base64.b64encode(raw).decode()), 'source': e.get('source', ''), 'license': e.get('license', ''), 'file': e['file']}


def logo_box(key, w, h):
    L = LOGOS.get(key)
    if not L: return ''
    USED.add(key)
    return '<span class="lgbox%s" style="width:%smm;height:%smm"><img src="%s" alt=""></span>' % (' dk' if key in DARK else '', w, h, L['uri'])


def org_badge(o, color=AC):
    key = HF_ORG_LOGO.get(o.lower())
    inner = logo_box(key, 13, 6) if key in LOGOS else monogram(o, 20, color)
    return '<span class="slot">%s</span>' % inner


def monogram(text, size=22, color=AC):
    t = ''.join(c for c in text if c.isalnum())[:2].upper() or '?'
    return '<span class="mono" style="width:%dpx;height:%dpx;font-size:%.1fpt;background:%s1a;color:%s;border-color:%s55">%s</span>' % (size, size, size / 3.1, color, color, color, esc(t))


def kpis(models, now):
    if not models: return ''
    dl = sum(m.get('downloads') or 0 for m in models)
    top = max(models, key=lambda m: m.get('trendingScore') or 0)
    ages = [(age_days(m, now), m) for m in models if age_days(m, now) is not None]
    new = min(ages, key=lambda x: x[0]) if ages else None
    cards = [('Modelle im Ranking', str(len(models)), 'Top-Auswahl der HF-API'),
             ('Downloads gesamt', short(dl), 'Zähler der API, kein Qualitätsmaß'),
             ('Höchster Trend-Score', de(top.get('trendingScore') or 0), esc(name(top))[:34]),
             ('Jüngstes Modell', ('heute' if new[0] == 0 else 'vor %d Tg.' % new[0]) if new else '–', esc(name(new[1]))[:34] if new else '')]
    return '<div class="kp">%s</div>' % ''.join('<div class="k"><div class="n">%s</div><div class="v">%s</div><div class="s">%s</div></div>' % (esc(a), esc(b), c) for a, b, c in cards)


def trend_bars(models, n=10):
    L = sorted(models, key=lambda m: -(m.get('trendingScore') or 0))[:n]
    if not L: return ''
    mx = max(m.get('trendingScore') or 0 for m in L) or 1
    rows = ''.join('<div class="br"><span class="rk">%d</span>%s<span class="bn">%s<small>%s · %s</small></span><span class="bt"><i style="width:%.1f%%"></i></span><b>%s</b></div>' % (
        i + 1, org_badge(org(m), PALETTE[i % len(PALETTE)]), lnk('https://huggingface.co/' + m['id'], name(m)), esc(org(m)), esc(task_label(m.get('pipeline_tag'))),
        100.0 * (m.get('trendingScore') or 0) / mx, de(m.get('trendingScore') or 0)) for i, m in enumerate(L))
    return '<div class="bars">%s</div>' % rows


def donut(counts, size=120):
    total = sum(counts.values())
    if not total: return ''
    items = counts.most_common(7)
    rest = total - sum(v for _, v in items)
    if rest: items.append(('__rest', rest))
    r, c, sw = 40, 50, 16; circ = 2 * math.pi * r; off = 0; arcs = ''; leg = ''
    for i, (k, v) in enumerate(items):
        col = PALETTE[i % len(PALETTE)] if k != '__rest' else '#c9ccd6'
        ln = circ * v / total
        arcs += '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="%d" stroke-dasharray="%.2f %.2f" stroke-dashoffset="%.2f" transform="rotate(-90 %d %d)"/>' % (c, c, r, col, sw, ln, circ - ln, -off, c, c)
        off += ln
        leg += '<li><i style="background:%s"></i>%s <b>%d</b></li>' % (col, esc('Weitere' if k == '__rest' else task_label(k)), v)
    return ('<div class="dn"><svg viewBox="0 0 100 100" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">%s<text x="50" y="52" text-anchor="middle" font-size="15" font-weight="700" fill="%s" font-family="Helvetica,Arial,sans-serif">%d</text>'
            '<text x="50" y="63" text-anchor="middle" font-size="6" fill="#6b7080" font-family="Helvetica,Arial,sans-serif">Modelle</text></svg><ul>%s</ul></div>') % (size, size, arcs, DK, total, leg)


def org_bars(models, n=5):
    c = collections.Counter(org(m) for m in models)
    L = c.most_common(n)
    if not L: return ''
    mx = L[0][1]
    return '<div class="bars sm">%s</div>' % ''.join('<div class="br">%s<span class="bn">%s</span><span class="bt"><i style="width:%.0f%%;background:%s"></i></span><b>%d</b></div>' % (
        org_badge(o, PALETTE[i % len(PALETTE)]), esc(o), 100.0 * v / mx, PALETTE[i % len(PALETTE)], v) for i, (o, v) in enumerate(L))


def age_buckets(models, now):
    B = [('bis 7 Tage', 0, 7), ('8 bis 30 Tage', 8, 30), ('31 bis 180 Tage', 31, 180), ('älter', 181, 10 ** 6)]
    counts = [0] * len(B)
    for m in models:
        a = age_days(m, now)
        if a is None: continue
        for i, (_, lo, hi) in enumerate(B):
            if lo <= a <= hi: counts[i] += 1; break
    tot = sum(counts)
    if not tot: return ''
    seg = ''.join('<i style="width:%.1f%%;background:%s" title="%s"></i>' % (100.0 * c / tot, PALETTE[i], B[i][0]) for i, c in enumerate(counts) if c)
    leg = ''.join('<li><i style="background:%s"></i>%s <b>%d</b></li>' % (PALETTE[i], B[i][0], c) for i, c in enumerate(counts))
    return '<div class="ab"><div class="stk">%s</div><ul class="lg">%s</ul></div>' % (seg, leg)


def scatter(models, w=560, h=190):
    P = [m for m in models if (m.get('likes') or 0) > 0 and (m.get('downloads') or 0) > 0]
    if len(P) < 3: return ''
    lx = [math.log10(m['downloads']) for m in P]; ly = [math.log10(m['likes']) for m in P]
    x0, x1 = math.floor(min(lx)), math.ceil(max(lx)); y0, y1 = math.floor(min(ly)), math.ceil(max(ly))
    x1 = max(x1, x0 + 1); y1 = max(y1, y0 + 1)
    px = lambda v: 34 + (v - x0) / (x1 - x0) * (w - 44); py = lambda v: h - 22 - (v - y0) / (y1 - y0) * (h - 34)
    g = ''
    for v in range(x0, x1 + 1):
        g += '<line x1="%.1f" y1="8" x2="%.1f" y2="%d" stroke="#e6e8f0"/><text x="%.1f" y="%d" font-size="6.5" text-anchor="middle" fill="#6b7080">%s</text>' % (px(v), px(v), h - 22, px(v), h - 11, short(10 ** v))
    for v in range(y0, y1 + 1):
        g += '<line x1="34" y1="%.1f" x2="%d" y2="%.1f" stroke="#e6e8f0"/><text x="30" y="%.1f" font-size="6.5" text-anchor="end" fill="#6b7080">%s</text>' % (py(v), w - 10, py(v), py(v) + 2, short(10 ** v))
    top = set(id(m) for m in sorted(P, key=lambda m: -(m.get('trendingScore') or 0))[:4])
    dots = ''
    for m in P:
        x, y = px(math.log10(m['downloads'])), py(math.log10(m['likes']))
        dots += '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity=".55" stroke="%s"/>' % (x, y, 3 + 5 * min(1, (m.get('trendingScore') or 0) / 1500), AC, DK)
        if id(m) in top:
            dots += '<text x="%.1f" y="%.1f" font-size="6.5" fill="%s">%s</text>' % (min(x + 5, w - 70), y - 5, DK, esc(name(m)[:18]))
    return ('<svg viewBox="0 0 %d %d" width="100%%" style="max-height:62mm" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica,Arial,sans-serif">%s%s'
            '<text x="%d" y="%d" font-size="6.5" text-anchor="middle" fill="#3a3e4c">Downloads (log)</text></svg>') % (w, h, g, dots, (34 + w - 10) // 2, h - 1)


def table(models, now, nf):
    mx = max((m.get('trendingScore') or 0) for m in models) or 1
    rows = ''.join('<tr><td class="l">%d</td><td class="l w"><b>%s</b><small class="mut"> %s</small>%s</td><td class="l">%s</td><td>%s</td><td>%s</td><td class="tb"><span><i style="width:%.0f%%"></i></span>%s</td><td class="l">%s</td></tr>' % (
        i + 1, lnk('https://huggingface.co/' + m['id'], name(m)), esc(org(m)), (' ' + logo_box(HF_ORG_LOGO.get(org(m).lower()), 10, 4)) if HF_ORG_LOGO.get(org(m).lower()) in LOGOS else '', esc(task_label(m.get('pipeline_tag'))), nf(m.get('likes')), nf(m.get('downloads')),
        100.0 * (m.get('trendingScore') or 0) / mx, nf(m.get('trendingScore')), esc((m.get('createdAt') or '')[:10])) for i, m in enumerate(models))
    return ('<table><thead><tr><th class="l">#</th><th class="l">Modell</th><th class="l">Aufgabe</th><th>Likes</th><th>Downloads</th><th class="l">Trend-Score</th><th class="l">Erstellt</th></tr></thead><tbody>%s</tbody></table>' % rows)


def logo_credits():
    if not USED: return ''
    li = ''.join('<li><b>%s</b>: <a href="%s">%s</a> · %s</li>' % (esc(k), esc(LOGOS[k]['source']), esc(LOGOS[k]['source']), esc(LOGOS[k]['license'])) for k in sorted(USED))
    return ('<h3>Logos und Marken</h3><p>Logos stammen aus dem lokalen Bestand des KI Fachblatts (content/portrait-logos), unverändert und eingebettet, mit Quelle und Rechtehinweis je Datei. Marken gehören ihren jeweiligen Inhabern. '
            'Die Logos dienen der redaktionellen Identifikation und deuten keine Partnerschaft, Freigabe oder Empfehlung durch die Markeninhaber an. Wo kein eindeutig zugeordnetes Logo vorliegt, steht ein Kürzel. Modelllogos und Unternehmenslogos werden nicht vermischt.</p><ul class="lc">%s</ul>' % li)


def _fact(m, *labels):
    for f in m.get('facts', []):
        if f['label'] in labels: return f['value']
    return ''


def portrait_cards(portraits, limit=8):
    comps = {c['slug']: c for c in portraits.get('companies', [])}
    out = ''
    for i, m in enumerate(portraits.get('models', [])[:limit]):
        c = comps.get(m['company'], {})
        io = _fact(m, 'Eingabe → Ausgabe')
        chips = ''
        if io:
            ins, _, outs = io.partition('→')
            mk = lambda s: ''.join('<span class="ch">%s</span>' % esc(x.strip()) for x in s.split(',') if x.strip())
            chips = '<span class="mut" style="font-size:7.4pt">Ein</span>' + mk(ins) + ('<span class="mut" style="font-size:7.4pt">→ Aus</span>' + mk(outs) if outs.strip() else '')
        when = _fact(m, 'Veröffentlicht', 'Veröffentlichung der Quelle', 'Stand der Modellkarte')
        mk = m.get('logo', {}).get('asset')
        lead = ('<span class="mlg">%s</span>' % logo_box(mk, 24, 11)) if mk in LOGOS else monogram(m.get('initials') or m['name'], 30, PALETTE[i % len(PALETTE)])
        out += '<div class="mc">%s<div class="mb"><b>%s</b><small>%s</small><p>%s</p><div class="chs">%s</div>%s</div></div>' % (
            lead, esc(m['name']), esc(c.get('name', m['company'])), esc(m.get('summary', '')), chips,
            ('<small class="mut">%s</small>' % esc(when)) if when else '')
    return '<div class="mcs">%s</div>' % out


def score_cards(portraits):
    bm = {b['slug']: b for b in portraits.get('benchmarks', [])}
    mo = {m['slug']: m for m in portraits.get('models', [])}
    rows = ''
    for s in portraits.get('scores', []):
        try: v = float(s['value'].replace(',', '.'))
        except (ValueError, KeyError): continue
        b = bm.get(s['benchmark'], {}); m = mo.get(s['model'], {})
        rows += '<div class="sg"><div class="sl2"><b>%s</b> <span class="mut">%s · %s</span></div><div class="gv">%s <small>%%</small></div><div class="gb"><i style="width:%.1f%%"></i></div><small class="mut">%s, laut %s</small></div>' % (
            esc(b.get('name', s['benchmark'])), esc(s.get('variant', '')), esc(m.get('name', s['model'])), esc(s['value']), max(0, min(100, v)), esc(s.get('metric', '').replace('% laut Herstellertabelle', 'Herstellertabelle')), esc(s.get('reported_by', 'Hersteller')))
    if not rows: return ''
    return '<div class="sgs">%s</div><div class="note"><b>Einordnen:</b> Diese Werte sind Herstellerangaben aus einer Modellkarte. Setup, Prompt und Budget sind nicht vollständig angegeben, die Zahlen eignen sich nicht für Ranglisten oder den Vergleich zwischen Modellen.</div>' % rows


CSS = '''
.slot{display:inline-flex;width:13mm;justify-content:center;flex:none}.lgbox{display:inline-flex;align-items:center;justify-content:center;background:#fff;border:1px solid #e3e5ee;border-radius:2mm;padding:.8mm 1.2mm;flex:none}.lgbox.dk{background:#161616;border-color:#161616}.lgbox img{max-width:100%;max-height:100%;object-fit:contain;display:block}.mlg{flex:none;width:26mm}.lc{margin:1mm 0;padding-left:4mm;font-size:8pt;overflow-wrap:anywhere}
.kp{display:flex;gap:3.5mm;margin:0 0 5mm}.k{flex:1;border:1px solid #dcd0f3;border-top:3px solid #7040cd;border-radius:4px;padding:3mm 3.5mm;background:#f5f1fc}
.k .n{font-size:7.6pt;color:#6b7080;text-transform:uppercase;letter-spacing:.05em}.k .v{font-size:17pt;font-weight:800;color:#3d2380;margin:1px 0}.k .s{font-size:7.8pt;color:#4a4e5c;overflow-wrap:anywhere}
.mono{display:inline-flex;align-items:center;justify-content:center;border-radius:50%;border:1px solid;font-weight:800;flex:none;letter-spacing:-.03em}
.bars .br{display:flex;align-items:center;gap:2.6mm;margin:1.1mm 0;font-size:8.8pt}.bars .rk{width:4mm;color:#6b7080;font-weight:700;text-align:right}
.bars .bn{width:62mm;min-width:0;overflow:hidden}.bars .bn a{font-weight:700;color:#14151b;text-decoration:none;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.bars .bn small{display:block;color:#6b7080;font-size:7.4pt;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bars.sm .bn{width:40mm;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600}
.bars .bt{flex:1;height:3.2mm;background:#eee9f8;border-radius:2mm;overflow:hidden}.bars .bt i{display:block;height:100%;background:linear-gradient(90deg,#7040cd,#8f6be0)}
.bars b{width:13mm;text-align:right;font-variant-numeric:tabular-nums}
.two{display:flex;gap:6mm}.two>div{flex:1;min-width:0}
.dn{display:flex;gap:4mm;align-items:center}.dn ul,.lg{list-style:none;margin:0;padding:0;font-size:8.4pt}.dn li,.lg li{margin:.9mm 0;display:flex;align-items:center;gap:1.6mm}.dn li i,.lg li i{display:inline-block;width:2.6mm;height:2.6mm;border-radius:50%;flex:none}.dn li b,.lg li b{margin-left:auto;padding-left:3mm}
.stk{display:flex;height:6mm;border-radius:3mm;overflow:hidden}.stk i{display:block}.ab .lg{margin-top:2.5mm}
.tb{white-space:nowrap}.tb span{display:inline-block;width:14mm;height:2mm;background:#eee9f8;border-radius:1mm;vertical-align:middle;margin-right:1.6mm;overflow:hidden}.tb span i{display:block;height:100%;background:#7040cd}
.mcs{display:grid;grid-template-columns:1fr 1fr;gap:3mm}.mc{display:flex;gap:3mm;border:1px solid #dfe2ec;border-radius:5px;padding:3mm;break-inside:avoid;background:#fff}
.mc b{font-size:10pt;color:#14151b}.mc small{display:block;color:#6b7080;font-size:7.8pt}.mc p{margin:1mm 0 1.5mm;font-size:8.4pt;color:#3a3e4c}.chs{display:flex;flex-wrap:wrap;gap:1mm;margin-bottom:1mm}
.ch{border:1px solid #dcd0f3;background:#f5f1fc;color:#3d2380;border-radius:10px;padding:0 6px;font-size:7.4pt}
.sgs{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm}.sg{border:1px solid #dfe2ec;border-radius:5px;padding:3mm}.sg .sl2{font-size:8.8pt;margin-bottom:1.5mm}
.gb{position:relative;height:5mm;background:#eee9f8;border-radius:3mm;overflow:hidden;margin-bottom:1mm}.gb i{display:block;height:100%;background:linear-gradient(90deg,#7040cd,#3f7ae0)}.gv{font-size:15pt;font-weight:800;color:#3d2380}.gv small{font-size:9pt;color:#6b7080;font-weight:600;display:inline}.gb em{position:absolute;right:2mm;top:0;line-height:5mm;font-size:8pt;font-style:normal;font-weight:700;color:#14151b}
.chs .mut{align-self:center}
'''
