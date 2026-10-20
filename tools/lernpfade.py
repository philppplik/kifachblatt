"""Builds /lernpfade.html from content/lernpfade.json (guided learning paths).
Steps point at article slugs or static pages; titles are read from the built pages, glossary terms are validated against content/glossary.json.

Optional per-path fields (all backward compatible, missing fields are simply not rendered):
  level, zielgruppe, gruppe (filter group, else derived), zeit|dauer, voraussetzungen|voraussetzung, lernziel,
  danach (list of path ids), check|abschluss_check (einleitung, aufgaben/praxis/szenarien, quiz).
Progress is stored in localStorage only (key kfb-lernpfad-<id>), no server, no tracking."""
import html, json, os, re

BASE = 'https://kifachblatt.de'
LEVELS = ['Einsteiger', 'Praktiker', 'Fortgeschritten', 'Entscheider']
GROUPS = ['Für alle', 'Entwickler und Technik', 'Unternehmen und Entscheider', 'Sicherheit']
LLMS_LINES = ''


def _slugify(t):
    t = t.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def _page_title(slug):
    t = open(slug + '.html', encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S) or re.search(r'<title>(.*?)</title>', t, re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).replace(' | KI Fachblatt', '').strip()


def _levels(p):
    """Level label plus the levels it contains (for the filter); fallback: path name if it is a level."""
    s = p.get('level') or (p['name'] if p['name'] in LEVELS else '')
    return s, [l for l in LEVELS if l.lower() in s.lower()]


def _group(p):
    if p.get('gruppe') in GROUPS:
        return p['gruppe']
    s = ' '.join([p['id'], p['name'], p.get('zielgruppe', '')]).lower()
    if re.search(r'security|sicherheit|red-?team|pentest', s):
        return GROUPS[3]
    if re.search(r'entwickl|developer|software|admin|devops|data|ml-|open-source|offene modelle', s):
        return GROUPS[1]
    if re.search(r'entscheid|unternehm|kmu|hr|recruit|marketing|seo|controlling|finanz|recht|produktmanag|geschäftsführ', s):
        return GROUPS[2]
    return GROUPS[0]


def _iso_duration(z):
    """'ca. 2,5 h' / 'ca. 90 Minuten' / 'ca. 2 Stunden' -> 'PT2H30M'; None if unparsable."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(h\b|std|stunde)', z or '', re.I)
    mins = None
    if m:
        mins = round(float(m.group(1).replace(',', '.')) * 60)
    else:
        m = re.search(r'(\d+)\s*(min)', z or '', re.I)
        if m:
            mins = int(m.group(1))
    if not mins:
        return None
    h, mm = divmod(mins, 60)
    return 'PT' + ('%dH' % h if h else '') + ('%dM' % mm if mm else '')


def _norm_check(p):
    """Different author packages use different field names; normalise to {einleitung, aufgaben, quiz}."""
    c = p.get('abschluss_check') or p.get('check')
    if not isinstance(c, dict):
        return None
    tasks = []
    for t in (c.get('aufgaben') or []) + (c.get('szenarien') or []) + (c.get('praxis') or []):
        q = t.get('frage') or t.get('aufgabe') or ''
        a = t.get('loesung') or t.get('musterloesung') or ''
        if q and a:
            tasks.append({'titel': t.get('titel', ''), 'frage': q, 'loesung': a})
    quiz = []
    for t in c.get('quiz') or []:
        q = t.get('frage') or t.get('q') or ''
        a = t.get('antwort') or t.get('a') or ''
        if q and a:
            quiz.append({'frage': q, 'antwort': a})
    if not tasks and not quiz:
        return None
    return {'einleitung': c.get('einleitung') or c.get('beschreibung') or '', 'aufgaben': tasks, 'quiz': quiz}


PROGRESS_JS = r'''(function(){
var K="kfb-lernpfad-",ls=null;try{ls=window.localStorage;ls.setItem(K+"t","1");ls.removeItem(K+"t")}catch(e){ls=null}
function get(id){try{return JSON.parse(ls.getItem(K+id)||"[]")}catch(e){return[]}}
function put(id,a){try{if(a.length)ls.setItem(K+id,JSON.stringify(a));else ls.removeItem(K+id)}catch(e){}}
var paths=document.querySelectorAll(".lp-path");
function upd(sec){var id=sec.id,boxes=sec.querySelectorAll(".lp-check"),n=0,tot=boxes.length;boxes.forEach(function(b){if(b.checked)n++;b.closest(".lp-step").classList.toggle("done",b.checked)});
var t="Fortschritt: "+n+" von "+tot+" Schritten";sec.querySelector(".lp-prog-t").textContent=t;var pr=sec.querySelector(".lp-prog");pr.value=n;pr.max=tot;pr.setAttribute("aria-valuetext",t);
var card=document.querySelector('.lp-jump[href="#'+id+'"] .lp-cardprog');if(card)card.textContent=n?n+" von "+tot+" erledigt":"";
sec.querySelector(".lp-reset").hidden=!n}
paths.forEach(function(sec){var boxes=sec.querySelectorAll(".lp-check");
if(ls){var done=get(sec.id);boxes.forEach(function(b){b.disabled=false;b.checked=done.indexOf(+b.dataset.i)>-1;b.addEventListener("change",function(){var a=[];boxes.forEach(function(x){if(x.checked)a.push(+x.dataset.i)});put(sec.id,a);upd(sec)})});
sec.querySelector(".lp-reset").addEventListener("click",function(){boxes.forEach(function(b){b.checked=false});put(sec.id,[]);upd(sec)});
sec.querySelectorAll(".lp-js").forEach(function(e){e.hidden=false});upd(sec)}});
var bar=document.querySelector(".lp-filter");if(!bar)return;bar.hidden=false;
var sel={g:"",l:""},st=document.getElementById("lp-count");
function apply(){var shown=0,total=0;document.querySelectorAll(".lp-jump").forEach(function(c){var ok=(!sel.g||c.dataset.g===sel.g)&&(!sel.l||c.dataset.l.split("|").indexOf(sel.l)>-1);c.hidden=!ok;var s=document.getElementById(c.getAttribute("href").slice(1));if(s)s.hidden=!ok;total++;if(ok)shown++});
document.querySelectorAll(".lp-grp").forEach(function(g){g.hidden=!g.querySelector(".lp-jump:not([hidden])")});
st.textContent=shown+" von "+total+" Pfaden"}
bar.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;var k=b.dataset.k;sel[k]=b.dataset.v;bar.querySelectorAll('button[data-k="'+k+'"]').forEach(function(x){x.setAttribute("aria-pressed",x===b?"true":"false")});apply()});
apply()})();'''


def build(simple_page, shell_top, shell_bottom, errors):
    global LLMS_LINES
    cfg = json.load(open('content/lernpfade.json', encoding='utf-8'))
    terms = {_slugify(x['term']): x['term'] for x in json.load(open('content/glossary.json', encoding='utf-8'))}
    esc = lambda s: html.escape(s, quote=True)
    ids = {p['id']: p for p in cfg['paths']}
    for p in cfg['paths']:
        p['_level'], p['_levels'] = _levels(p)
        p['_group'] = _group(p)
        p['_zeit'] = p.get('zeit') or p.get('dauer') or ''
        p['_vor'] = p.get('voraussetzungen') or p.get('voraussetzung') or ''
        p['_check'] = _norm_check(p)
        p['_steps'] = [s for s in p['steps'] if os.path.exists(s['slug'] + '.html')]
        for s in p['steps']:
            if s not in p['_steps']:
                errors.append('lernpfade: page %s.html does not exist' % s['slug'])

    def meta(p):
        bits = ['%d Schritte' % len(p['_steps'])]
        if p['_zeit']:
            bits.append(p['_zeit'])
        return ' · '.join(bits)

    def badge(p):
        if not p['_level']:
            return ''
        k = (p['_levels'] or ['x'])[0].lower()
        return '<span class="lp-badge lp-%s">%s</span>' % (k, esc(p['_level']))

    present_groups = [g for g in GROUPS if any(p['_group'] == g for p in cfg['paths'])]
    present_levels = [l for l in LEVELS if any(l in p['_levels'] for p in cfg['paths'])]

    def fbtn(k, v, on=False):
        return '<button type="button" data-k="%s" data-v="%s" aria-pressed="%s">%s</button>' % (k, esc(v), 'true' if on else 'false', esc(v) if v else 'Alle')
    filt = ''
    if len(cfg['paths']) > 4 and (len(present_groups) > 1 or len(present_levels) > 1):
        filt = ('<div class="lp-filter" role="group" aria-label="Pfade filtern" hidden>'
                '<div class="lp-frow"><span class="lp-flabel" id="lp-fg">Zielgruppe</span><div class="lp-fbtns" role="group" aria-labelledby="lp-fg">%s</div></div>'
                '<div class="lp-frow"><span class="lp-flabel" id="lp-fl">Level</span><div class="lp-fbtns" role="group" aria-labelledby="lp-fl">%s</div></div>'
                '<p id="lp-count" class="lp-count" role="status" aria-live="polite"></p></div>') % (
            fbtn('g', '', True) + ''.join(fbtn('g', g) for g in present_groups),
            fbtn('l', '', True) + ''.join(fbtn('l', l) for l in present_levels))

    def card(p):
        return ('<a class="lp-jump" href="#%s" data-g="%s" data-l="%s">%s<strong>%s</strong><span>%s</span><em class="lp-meta">%s</em><em class="lp-cardprog" aria-hidden="true"></em></a>'
                % (p['id'], esc(p['_group']), esc('|'.join(p['_levels'])), badge(p), esc(p['name']), esc(p['frage']), esc(meta(p))))
    if len(present_groups) > 1:
        nav = ''.join('<div class="lp-grp"><h2 class="lp-grph">%s</h2><div class="lp-cards">%s</div></div>' % (esc(g), ''.join(card(p) for p in cfg['paths'] if p['_group'] == g)) for g in present_groups)
    else:
        nav = '<div class="lp-grp"><div class="lp-cards">%s</div></div>' % ''.join(card(p) for p in cfg['paths'])

    secs, items, n, ld_paths = [], [], 0, []
    for p in cfg['paths']:
        lis, parts = [], []
        for i, st in enumerate(p['_steps'], 1):
            slug = st['slug']
            title = _page_title(slug)
            n += 1; items.append({'@type': 'ListItem', 'position': n, 'name': p['name'] + ': ' + title, 'url': '%s/%s' % (BASE, slug)})
            parts.append({'@type': 'WebPage', 'name': title, 'url': '%s/%s' % (BASE, slug)})
            lis.append('<li class="lp-step"><input class="lp-check" type="checkbox" id="%s-s%d" data-i="%d" disabled aria-label="Schritt %d erledigt: %s"><span class="lp-num" aria-hidden="true">%d</span><div><h3><a href="/%s">%s</a></h3><p>%s</p></div></li>'
                       % (p['id'], i, i, i, esc(title), i, slug, esc(title), esc(st['warum'])))
        chips = []
        for t in p.get('terms', []):
            s = _slugify(t)
            if s not in terms: errors.append('lernpfade: glossary term %r not found' % t); continue
            chips.append('<a class="lp-chip" href="/glossar#%s">%s</a>' % (s, esc(terms[s])))
        facts = []
        for lab, val in (('Zielgruppe', p.get('zielgruppe')), ('Voraussetzungen', p['_vor']), ('Lernziel', p.get('lernziel'))):
            if val: facts.append('<div><dt>%s</dt><dd>%s</dd></div>' % (lab, esc(val)))
        facts_h = '<dl class="lp-facts">%s</dl>' % ''.join(facts) if facts else ''
        c = p['_check']
        toc = ['<a href="#%s-schritte">Schritte</a>' % p['id']]
        if chips: toc.append('<a href="#%s-begriffe">Begriffe</a>' % p['id'])
        if c: toc.append('<a href="#%s-check">Abschluss-Check</a>' % p['id'])
        toc_h = '<nav class="lp-toc" aria-label="In diesem Pfad: %s">%s</nav>' % (esc(p['name']), ''.join(toc)) if len(toc) > 1 else ''
        check_h = ''
        if c:
            pc = ['<h3 id="%s-check-h">Abschluss-Check</h3>' % p['id']]
            if c['einleitung']: pc.append('<p>%s</p>' % esc(c['einleitung']))
            if c['aufgaben']:
                pc.append('<h4>Aufgaben</h4>')
                for j, t in enumerate(c['aufgaben'], 1):
                    pc.append('<details class="lp-qa"><summary>%s</summary><p class="lp-qtext">%s</p><div class="lp-ans"><strong>Musterlösung</strong><p>%s</p></div></details>'
                              % (esc(t['titel'] or 'Aufgabe %d' % j), esc(t['frage']), esc(t['loesung'])))
            if c['quiz']:
                pc.append('<h4>Quiz-Selbsttest</h4><p class="lp-hint">Antworte zuerst im Kopf, dann klappe die Antwort auf.</p>')
                for t in c['quiz']:
                    pc.append('<details class="lp-qa"><summary>%s</summary><div class="lp-ans"><strong>Antwort</strong><p>%s</p></div></details>' % (esc(t['frage']), esc(t['antwort'])))
            check_h = '<section class="lp-checkbox" id="%s-check" aria-labelledby="%s-check-h">%s</section>' % (p['id'], p['id'], ''.join(pc))
        nxt = [ids[x] for x in p.get('danach', []) if x in ids]
        nxt_h = '<p class="lp-next"><strong>Danach weiter mit:</strong> %s</p>' % ', '.join('<a href="#%s">%s</a>' % (x['id'], esc(x['name'])) for x in nxt) if nxt else ''
        ptop = '<div class="lp-pmeta">%s<span>%s</span></div>' % (badge(p), esc(meta(p)))
        prog = ('<div class="lp-js" hidden><progress class="lp-prog" value="0" max="%d" aria-label="Fortschritt im Pfad %s"></progress> <span class="lp-prog-t" aria-live="polite"></span> '
                '<button type="button" class="lp-reset" hidden>Zurücksetzen</button><p class="lp-hint">Dein Fortschritt bleibt auf diesem Gerät gespeichert, nicht auf einem Server.</p></div>') % (len(p['_steps']), esc(p['name']))
        terms_h = ('<p class="lp-terms-h" id="%s-begriffe"><strong>Begriffe auf diesem Weg</strong></p><p class="lp-terms">%s</p>' % (p['id'], ''.join(chips))) if chips else ''
        secs.append('<section class="lp-path" id="%s" aria-labelledby="%s-h"><h2 id="%s-h">%s</h2>%s<p class="lp-q">%s</p><p>%s</p>%s%s'
                    '<h3 class="lp-sh" id="%s-schritte">Schritte</h3>%s<ol class="lp-steps">%s</ol>%s%s%s<p class="lp-top"><a href="#lp-top">Zur Pfad-Übersicht</a></p></section>'
                    % (p['id'], p['id'], p['id'], esc(p['name']), ptop, esc(p['frage']), esc(p['intro']), facts_h, toc_h,
                       p['id'], prog, ''.join(lis), terms_h, check_h, nxt_h))
        lr = {'@type': 'LearningResource', '@id': '%s/lernpfade#%s' % (BASE, p['id']), 'url': '%s/lernpfade#%s' % (BASE, p['id']), 'name': p['name'],
              'description': p.get('lernziel') or p['frage'], 'inLanguage': 'de-DE', 'learningResourceType': 'Lernpfad', 'isPartOf': {'@id': BASE + '/lernpfade#page'},
              'hasPart': parts}
        if p['_level']: lr['educationalLevel'] = p['_level']
        if p.get('zielgruppe'): lr['audience'] = {'@type': 'Audience', 'audienceType': p['zielgruppe']}
        d = _iso_duration(p['_zeit'])
        if d: lr['timeRequired'] = d
        if p.get('lernziel'): lr['teaches'] = p['lernziel']
        if p['_vor']: lr['competencyRequired'] = p['_vor']
        if c: lr['assesses'] = p.get('lernziel') or p['name']
        ld_paths.append(lr)
    inner = ('<div class="legal lp" id="lp-top"><div class="kicker">Lernpfade</div><h1>%s</h1><p>%s</p>%s<div class="lp-nav" aria-label="Pfade">%s</div>%s'
             '<p class="mut">Alle Seiten sind mit Quellen belegt und entstehen mit KI-Unterstützung, redaktionell verantwortet (<a href="/transparenz">so arbeiten wir</a>). Nachschlagen kannst du jederzeit im <a href="/glossar">Glossar</a>.</p></div>'
             '<script>%s</script>') % (esc(cfg['title']), esc(cfg['intro']), filt, nav, ''.join(secs), PROGRESS_JS)
    ld = json.dumps({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': BASE + '/lernpfade#page', 'url': BASE + '/lernpfade', 'name': cfg['title'], 'inLanguage': 'de-DE', 'description': cfg['intro'], 'isPartOf': {'@id': BASE + '/#site'}, 'mainEntity': {'@id': BASE + '/lernpfade#list'}},
        {'@type': 'ItemList', '@id': BASE + '/lernpfade#list', 'name': cfg['title'], 'itemListElement': items}] + ld_paths + [
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Start', 'item': BASE + '/'}, {'@type': 'ListItem', 'position': 2, 'name': 'Lernpfade', 'item': BASE + '/lernpfade'}]}]},
        ensure_ascii=False).replace('</', '<\\/')
    desc = '%d Lernpfade durch das KI Fachblatt, nach Zielgruppe und Level filterbar: Seiten in sinnvoller Reihenfolge, mit Glossar-Begriffen, Fortschritt auf deinem Gerät und Abschluss-Check.' % len(cfg['paths'])
    open('lernpfade.html', 'w', encoding='utf-8').write(simple_page(cfg['title'] + ' | KI Fachblatt', desc, BASE + '/lernpfade', inner, shell_top, shell_bottom, ld=ld))
    LLMS_LINES = ''.join('- [%s](%s/lernpfade#%s): %s%s\n' % (p['name'], BASE, p['id'], p['frage'], (' (%s, %s)' % (p['_level'], p['_zeit'])) if p['_level'] and p['_zeit'] else '') for p in cfg['paths'])
    return n
