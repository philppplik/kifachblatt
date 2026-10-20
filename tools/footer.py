#!/usr/bin/env python3
"""Footer redesign: brand block + three link columns + notice. Idempotent.

Rewrites the legacy KFB footer in every HTML page (run from the repo root, after build and
portraits). All former footer links are kept. Usage: python3 tools/footer.py [root]
"""
import glob, os, re, sys

OLD = re.compile(r'<footer>(?:(?!</footer>).)*?<div class="wrap"><div><h4>KI Fachblatt</h4>.*?</footer>', re.S)
PORT = re.compile(r'<div class="wrap" data-portrait-footer>.*?</div>', re.S)

def render(port, year):
    p = ''
    if port:
        links = re.findall(r'<a href="([^"]+)">([^<]+)</a>', port.group(0))
        p = '<div><h4>Verzeichnis</h4>' + ''.join('<a href="%s">%s</a>' % l for l in links) + '</div>'
    return ('<footer class="kfbf" data-portrait-footer-done><div class="wrap"><div class="kfbf-top"><div class="kfbf-brand">'
        '<a class="kfbf-logo" href="/"><img class="logo-mark" src="/assets/logo-mark-white.svg" alt="" width="22" height="22">KI<span>·</span>Fachblatt</a>'
        '<p>Einordnen statt Hype. Ein deutschsprachiges Fachmagazin über künstliche Intelligenz, von Philipp Paulik.</p></div>'
        '<div class="kfbf-cols">'
        '<div><h4>Lesen</h4><a href="/glossar">Glossar</a><a href="/llm-kostenrechner">LLM-Kostenrechner</a><a href="/berichte">KI-Tagesbericht (PDF)</a><a href="/feed.xml">RSS-Feed</a><a href="/llms.txt">llms.txt</a></div>'
        + p +
        '<div><h4>Redaktion</h4><a href="/ueber">Über das Magazin</a><a href="/redaktion">Redaktion</a><a href="/transparenz">KI-Transparenz</a><a href="/korrekturen">Korrekturen</a><a href="/quellen">Quellen</a></div>'
        '<div><h4>Rechtliches</h4><a href="/impressum">Impressum</a><a href="/datenschutz">Datenschutz</a><a href="https://philipp-paulik.de">Philipp Paulik</a></div>'
        '</div></div>'
        '<p class="proj"><b>Projekte von Philipp Paulik:</b> <a href="https://pblock.philipp-paulik.de">pBlock</a> · <a href="https://custmtab.philipp-paulik.de">cust*m Tab</a> · <a href="https://zwep.philipp-paulik.de">ZWEP</a> · <a href="https://flower.philipp-paulik.de">Flower</a> · <a href="https://ct.philipp-paulik.de">ct</a> · <a href="https://plane.philipp-paulik.de">plane</a></p>'
        '<p class="note">Beiträge entstehen mit KI-Unterstützung und sind bewusst allgemein gehalten. Preise, Versionen und Rechtslage ändern sich: Prüfe wichtige Angaben bei der Quelle. © %s Philipp Paulik</p></div></footer>' % year)

def main(root='.'):
    n = 0
    for f in glob.glob(os.path.join(root, '**/*.html'), recursive=True):
        rel = os.path.relpath(f, root).split(os.sep)[0]
        if rel in ('content', 'tools', 'docs', 'tests', 'authorpage'): continue
        t = open(f, encoding='utf-8').read()
        m = OLD.search(t)
        if not m: continue
        port = PORT.search(m.group(0))
        y = re.search(r'© (\d{4})', m.group(0))
        t = t[:m.start()] + render(port, y.group(1) if y else '2026') + t[m.end():]
        open(f, 'w', encoding='utf-8').write(t); n += 1
    print('KFB footer: %d pages' % n)

if __name__ == '__main__': main(*sys.argv[1:])
