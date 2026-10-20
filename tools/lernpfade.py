"""Builds /lernpfade.html from content/lernpfade.json (three guided paths).
Steps point at article slugs or static pages; titles are read from the built pages, glossary terms are validated against content/glossary.json."""
import html, json, os, re

BASE = 'https://kifachblatt.de'

def _slugify(t):
    t = t.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

def _page_title(slug):
    t = open(slug + '.html', encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S) or re.search(r'<title>(.*?)</title>', t, re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).replace(' | KI Fachblatt', '').strip()

def build(simple_page, shell_top, shell_bottom, errors):
    cfg = json.load(open('content/lernpfade.json', encoding='utf-8'))
    terms = {_slugify(x['term']): x['term'] for x in json.load(open('content/glossary.json', encoding='utf-8'))}
    esc = lambda s: html.escape(s, quote=True)
    nav = ''.join('<a class="lp-jump" href="#%s"><strong>%s</strong><span>%s</span></a>' % (p['id'], esc(p['name']), esc(p['frage'])) for p in cfg['paths'])
    secs, items, n = [], [], 0
    for p in cfg['paths']:
        lis = []
        for i, st in enumerate(p['steps'], 1):
            slug = st['slug']
            if not os.path.exists(slug + '.html'):
                errors.append('lernpfade: page %s.html does not exist' % slug); continue
            title = _page_title(slug)
            n += 1; items.append({'@type': 'ListItem', 'position': n, 'name': p['name'] + ': ' + title, 'url': '%s/%s' % (BASE, slug)})
            lis.append('<li class="lp-step"><span class="lp-num" aria-hidden="true">%d</span><div><h3><a href="/%s">%s</a></h3><p>%s</p></div></li>' % (i, slug, esc(title), esc(st['warum'])))
        chips = []
        for t in p.get('terms', []):
            s = _slugify(t)
            if s not in terms: errors.append('lernpfade: glossary term %r not found' % t); continue
            chips.append('<a class="lp-chip" href="/glossar#%s">%s</a>' % (s, esc(terms[s])))
        secs.append('<section class="lp-path" id="%s" aria-labelledby="%s-h"><h2 id="%s-h">%s</h2><p class="lp-q">%s</p><p>%s</p><ol class="lp-steps">%s</ol><p class="lp-terms-h"><strong>Begriffe auf diesem Weg</strong></p><p class="lp-terms">%s</p></section>'
                    % (p['id'], p['id'], p['id'], esc(p['name']), esc(p['frage']), esc(p['intro']), ''.join(lis), ''.join(chips)))
    inner = ('<div class="legal lp"><div class="kicker">Lernpfade</div><h1>%s</h1><p>%s</p><nav class="lp-nav" aria-label="Pfade">%s</nav>%s'
             '<p class="mut">Alle Seiten sind mit Quellen belegt und entstehen mit KI-Unterstützung, redaktionell verantwortet (<a href="/transparenz">so arbeiten wir</a>). Nachschlagen kannst du jederzeit im <a href="/glossar">Glossar</a>.</p></div>') % (esc(cfg['title'].split(':')[0]) if False else esc(cfg['title']), esc(cfg['intro']), nav, ''.join(secs))
    ld = json.dumps({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': BASE + '/lernpfade#page', 'url': BASE + '/lernpfade', 'name': cfg['title'], 'inLanguage': 'de-DE', 'description': cfg['intro'], 'isPartOf': {'@id': BASE + '/#site'}, 'mainEntity': {'@id': BASE + '/lernpfade#list'}},
        {'@type': 'ItemList', '@id': BASE + '/lernpfade#list', 'name': cfg['title'], 'itemListElement': items},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Start', 'item': BASE + '/'}, {'@type': 'ListItem', 'position': 2, 'name': 'Lernpfade', 'item': BASE + '/lernpfade'}]}]},
        ensure_ascii=False).replace('</', '<\\/')
    desc = 'Drei Lernpfade durch das KI Fachblatt für Einsteiger, Praktiker und Entscheider: Seiten in sinnvoller Reihenfolge, mit Glossar-Begriffen.'
    open('lernpfade.html', 'w', encoding='utf-8').write(simple_page(cfg['title'] + ' | KI Fachblatt', desc, BASE + '/lernpfade', inner, shell_top, shell_bottom, ld=ld))
    return n
