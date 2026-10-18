"""Minimal markdown -> HTML for static policy pages (content/pages/*.md). stdlib only.
Supported: '# title' (first line), '## h2', '- ' lists, paragraphs, **bold**, [text](url), bare e-mail addresses.
Optional first-line comment: <!-- desc: meta description -->"""
import html, os, re

def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), t)
    t = re.sub(r'(?<![\w">:])([\w.+-]+@[\w-]+\.[\w.-]+)(?![\w<])', r'<a href="mailto:\1">\1</a>', t)
    return t

def parse(text):
    title, desc, out, ul, para, ids = '', '', [], [], [], set()
    def flush():
        nonlocal ul, para
        if ul: out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % _inline(x) for x in ul)); ul = []
        if para: out.append('<p>%s</p>' % _inline(' '.join(para))); para = []
    for ln in text.split('\n'):
        s = ln.rstrip()
        m = re.match(r'<!--\s*desc:\s*(.*?)\s*-->', s)
        if m: desc = m.group(1); continue
        if s.startswith('# '): flush(); title = s[2:].strip(); continue
        if s.startswith('## '):
            flush(); h = s[3:].strip(); i = re.sub(r'[^a-z0-9]+', '-', h.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')).strip('-')
            out.append('<h2 id="%s">%s</h2>' % (i, _inline(h))); continue
        if s.startswith('- '):
            if para: flush()
            ul.append(s[2:].strip()); continue
        if not s.strip(): flush(); continue
        if ul: flush()
        para.append(s.strip())
    flush()
    if not desc:
        first = re.sub(r'<[^>]+>', '', next((x for x in out if x.startswith('<p>')), ''))
        desc = first if len(first) <= 157 else first[:157].rsplit(' ', 1)[0] + '…'
    return title, desc, '\n'.join(out)

def load(dirpath):
    res = {}
    if not os.path.isdir(dirpath): return res
    for f in sorted(os.listdir(dirpath)):
        if f.endswith('.md'):
            t, d, h = parse(open(os.path.join(dirpath, f), encoding='utf-8').read())
            res[f[:-3]] = {'slug': f[:-3], 'title': t, 'desc': d, 'html': h}
    return res
