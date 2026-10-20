"""Report landing page with real PDF previews. Standard library, optional system pdftoppm."""
from pathlib import Path
import datetime
import html
import json
import shutil
import subprocess
import tempfile

def build(root, output, key, dates, current, prefix):
    root=Path(root);out=Path(output);pdf=out/'berichte'/current
    configs={
      'fa':('Dein Marktüberblick.\nZum Mitnehmen.','Indizes, Aktien, Devisen und Schlagzeilen: der Marktbericht von finanz adjust als PDF. Für deinen Überblick, nicht als Anlageempfehlung.','Marktbericht','Indizes und Marktbreite|Gewinner, Verlierer und Devisen|Schlagzeilen mit Quellenlinks'),
      'iw':('Weniger Tabs.\nMehr KI-Überblick.','Die neuesten Artikel und KI-Schlagzeilen in einer druckfreundlichen Ausgabe. Zum Lesen, Speichern und später Wiederfinden.','Tagesausgabe','Meldung des Tages und weitere Artikel|KI-Pulse mit externen Schlagzeilen|Quellen, Impressum und Redaktionsschluss'),
      'kfb':('Dein KI-Update.\nBleibt nicht im Feed.','Trending-Modelle und die neuesten Analysen des KI Fachblatts als PDF. Ein fester Stand, den du in Ruhe lesen und aufbewahren kannst.','KI-Tagesbericht','20 Trending-Modelle von Hugging Face|Die zwei neuesten Analysen|Quellen, Impressum und Redaktionsschluss')}
    headline,lead,name,includes=configs[key];e=html.escape
    preview_dir=out/'assets/report-preview';preview_dir.mkdir(parents=True,exist_ok=True)
    # Keep a checked-in real-PDF snapshot when the CI image has no renderer.
    fallback=root/'content/report-preview'
    images=[]; fresh=False
    if pdf.is_file() and shutil.which('pdftoppm'):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result=subprocess.run(['pdftoppm','-f','1','-l','2','-scale-to','1000','-jpeg','-jpegopt','quality=82',str(pdf),str(Path(tmp)/'page')],capture_output=True,timeout=45)
                generated=sorted(Path(tmp).glob('page-*.jpg'))[:2]
                if result.returncode==0 and generated:
                    for stale in preview_dir.glob('page-*.jpg'):stale.unlink()
                    for image in generated:shutil.copy2(image,preview_dir/image.name)
                    fresh=True
        except (OSError,subprocess.TimeoutExpired):
            print('::warning::PDF preview conversion failed; preserving the supplied snapshot')
    images=sorted(preview_dir.glob('page-*.jpg'))[:2]
    if not images and fallback.is_dir():
        for image in sorted(fallback.glob('page-*.jpg'))[:2]:shutil.copy2(image,preview_dir/image.name)
        images=sorted(preview_dir.glob('page-*.jpg'))[:2]
    # Compact thumbnail for the in-article report breaker. A distinct name keeps the
    # page-*.jpg globs above from treating it as a landing preview page.
    thumb=preview_dir/'breaker-thumb.jpg'
    if fresh:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                small=subprocess.run(['pdftoppm','-f','1','-l','1','-scale-to','420','-jpeg','-jpegopt','quality=80',str(pdf),str(Path(tmp)/'thumb')],capture_output=True,timeout=45)
                made=sorted(Path(tmp).glob('thumb-*.jpg'))
                if small.returncode==0 and made:shutil.copy2(made[0],thumb)
        except (OSError,subprocess.TimeoutExpired):
            print('::warning::breaker thumbnail conversion failed; the report breaker falls back to page-1.jpg')
    if not thumb.is_file():
        supplied=fallback/'breaker-thumb.jpg'
        if supplied.is_file():shutil.copy2(supplied,thumb)
    thumb2=preview_dir/'breaker-thumb2.jpg'
    if fresh:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                small=subprocess.run(['pdftoppm','-f','2','-l','2','-scale-to','420','-jpeg','-jpegopt','quality=80',str(pdf),str(Path(tmp)/'thumb2')],capture_output=True,timeout=45)
                made=sorted(Path(tmp).glob('thumb2-*.jpg'))
                if small.returncode==0 and made:shutil.copy2(made[0],thumb2)
        except (OSError,subprocess.TimeoutExpired):
            print('::warning::breaker thumbnail 2 conversion failed; the breaker falls back to page-2.jpg')
    if not thumb2.is_file():
        supplied2=fallback/'breaker-thumb2.jpg'
        if supplied2.is_file():shutil.copy2(supplied2,thumb2)
    preview_caption='Vorschauseiten aus dem aktuellen PDF. Für lesbare Details das PDF öffnen.' if fresh else 'Echte PDF-Vorschau vom 19.10.2026. Die aktuelle Ausgabe kann abweichen; für den neuesten Stand das PDF öffnen.'
    css='''
.rlp{--rl-ac:var(--ac,#1d6bc0);--rl-bg:var(--p,#fff);--rl-fg:var(--hd,#10182b);--rl-muted:var(--mut,#657080);--rl-line:var(--b,#e2e6ee);--rl-soft:var(--p2,#f3f6fb);max-width:1160px;padding:42px 24px 64px;margin:auto;color:var(--rl-fg)}.rlp[data-brand=kfb]{--rl-ac:#7040cd;--rl-bg:#fff;--rl-soft:#f7f3ff;--rl-fg:#17161b;--rl-muted:#615d6b;--rl-line:#e6def1}.rlp[data-brand=iw]{--rl-ac:#1d6bc0;--rl-bg:#fff;--rl-soft:#f0f6fd;--rl-fg:#10182b;--rl-muted:#56677e;--rl-line:#dce7f3}.rlp *{box-sizing:border-box}.rl-hero{display:grid;grid-template-columns:1.2fr 1fr;gap:42px;align-items:center;padding:32px 0 48px}.rl-tag{font-size:11px;font-weight:750;letter-spacing:.13em;color:var(--rl-ac);text-transform:uppercase;margin:0 0 18px}.rlp h1{font-size:clamp(36px,5vw,62px);line-height:1.07;letter-spacing:-.045em;margin:0 0 24px;color:var(--rl-fg);font-weight:800}.rl-lead{font-size:18px;line-height:1.65;max-width:610px;color:var(--rl-muted)}.rl-button{display:inline-block;padding:15px 22px;background:var(--rl-ac);color:#fff!important;border-radius:10px;font-weight:750;min-height:48px;text-decoration:none!important}.rl-button:hover{filter:brightness(1.08)}.rl-fine{font-size:12px;color:var(--rl-muted);line-height:1.6;margin:12px 0}.rl-proof{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0}.rl-proof span{padding:6px 10px;border:1px solid var(--rl-line);border-radius:30px;font-size:12px;background:var(--rl-bg)}.rl-preview{background:var(--rl-soft);border:1px solid var(--rl-line);padding:24px;border-radius:18px;display:grid;gap:12px;grid-template-columns:1fr 1fr;align-items:start}.rl-preview a{display:block}.rl-preview img{width:100%;height:auto;display:block;box-shadow:0 10px 30px #0002;border-radius:3px}.rl-preview a:nth-child(2){margin-top:34px}.rl-preview figcaption{grid-column:1/-1;color:var(--rl-muted);font-size:11px;line-height:1.5}.rl-section{padding:38px 0;border-top:1px solid var(--rl-line)}.rlp h2{font-size:28px;line-height:1.2;letter-spacing:-.025em;margin:0 0 20px;color:var(--rl-fg)}.rl-benefits{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;list-style:none;padding:0;margin:0}.rl-benefits li{background:var(--rl-bg);border:1px solid var(--rl-line);border-radius:12px;padding:20px;line-height:1.5}.rl-benefits b{display:block;font-size:16px;margin-bottom:7px}.rl-benefits b::before{content:'✓';color:var(--rl-ac);margin-right:9px}.rl-benefits span{display:block;color:var(--rl-muted);font-size:13px}.rl-inside{display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:start}.rl-inside ul{margin:0;padding-left:20px;line-height:2}.rl-note{padding:22px;border-radius:12px;background:var(--rl-soft);border:1px solid var(--rl-line);font-size:14px;line-height:1.65}.rl-archive{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding:0;list-style:none;margin:22px 0}.rl-archive a{display:grid;gap:9px;padding:18px;background:var(--rl-bg);border:1px solid var(--rl-line);border-radius:10px;text-decoration:none}.rl-archive a:hover{border-color:var(--rl-ac)}.rl-archive small{color:var(--rl-muted)}.rl-archive b{font-size:17px;color:var(--rl-fg)}.rl-archive span{font-size:12px;color:var(--rl-ac);font-weight:700}.rlp details{border-bottom:1px solid var(--rl-line);padding:0}.rlp summary{cursor:pointer;min-height:52px;padding:16px 0;font-weight:700;font-size:15px}.rlp details p{max-width:820px;line-height:1.7;color:var(--rl-muted);font-size:14px;margin:0 0 20px}.rl-close{background:var(--rl-soft);border:1px solid var(--rl-line);border-radius:16px;text-align:center;padding:34px 22px;margin-top:36px}.rl-close p{color:var(--rl-muted)}.rlp a:focus-visible,.rlp summary:focus-visible{outline:3px solid var(--rl-ac);outline-offset:4px}@media(max-width:700px){.rlp{padding:26px 18px 42px}.rl-hero{grid-template-columns:1fr;gap:24px;padding:12px 0 30px}.rlp h1{font-size:41px}.rl-lead{font-size:16px}.rl-button{width:100%;text-align:center}.rl-preview{padding:18px;gap:14px}.rl-benefits{grid-template-columns:1fr}.rl-benefits li{padding:18px}.rl-inside{grid-template-columns:1fr;gap:14px}.rl-archive{grid-template-columns:repeat(2,minmax(0,1fr))}.rl-archive a{padding:14px}.rl-section{padding:28px 0}.rlp h2{font-size:26px}}
'''
    (preview_dir/'landing.css').write_text(css)
    stamp=dates[0] if dates else 'noch nicht verfügbar'
    url='/berichte/'+current
    previews=''.join('<a href="%s" aria-label="PDF öffnen, Vorschau Seite %s"><img src="/assets/report-preview/%s" width="707" height="1000" alt="Echte PDF-Vorschau, Seite %s" loading="%s"></a>'%(url,i+1,p.name,i+1,'eager' if i==0 else 'lazy') for i,p in enumerate(images))
    if not previews:previews='<p>Die Vorschau ist gerade nicht verfügbar. Das PDF kannst du direkt öffnen.</p>'
    benefits=[('Gratis lesen','Kein Abo, kein Kauf und keine Bezahlschranke.'),('Ohne Anmeldung','Kein Konto und keine E-Mail nötig.'),('Quellen dabei','Quellen und Redaktionsschluss stehen im PDF.'),('Für Papier und Bildschirm','Helles PDF zum Lesen, Speichern und Drucken.'),('Täglich automatisch','Die vorhandenen Seitenläufe stellen die Ausgabe zusammen.'),('Ein Tag, eine Archiv-Ausgabe','Der erste erfolgreiche Lauf pro Berliner Kalendertag bleibt erhalten.')]
    cards=''.join('<li><b>%s</b><span>%s</span></li>'%(e(t),e(v)) for t,v in benefits)
    archive=''.join('<li><a href="/berichte/%s%s.pdf"><small>Archiv-Ausgabe</small><b>%s</b><span>PDF öffnen ↓</span></a></li>'%(prefix,d,datetime.date.fromisoformat(d).strftime('%d.%m.%Y')) for d in dates)
    faq=[('Was steckt im Bericht?',includes.replace('|',', ')+'. Die Zusammenstellung kann sich mit dem Datenstand ändern. Details und Quellen stehen in der Ausgabe.'),('Wie oft erscheint eine Ausgabe?','Die Erstellung läuft täglich automatisch im bestehenden Seitenlauf. Im Archiv bleibt der erste erfolgreiche PDF-Stand je Berliner Kalendertag. Der aktuelle Download kann später aktualisiert werden. Bei Ausfällen bleibt die letzte gültige Ausgabe verfügbar; fehlende Tage werden nicht erfunden.'),('Muss ich mich anmelden oder meine E-Mail angeben?','Nein. Du öffnest oder lädst das PDF direkt. Kein Konto, kein E-Mail-Feld, kein Newsletter. Der Download enthält kein Tracking-Skript. Für die Website gelten die Datenschutzeinstellungen.'),('Woher kommen die Inhalte?', 'Die Ausgabe nennt ihre Quellen und den Redaktionsschluss. Redaktionelle Beiträge stammen von dieser Website; externe Schlagzeilen verlinken die Originalquelle. Daten und Meldungen können verzögert oder fehlerhaft sein.'),('Darf ich das PDF weiterverwenden?','Die kostenlose Bereitstellung ist keine pauschale Freigabe für Nachdruck, kommerzielle Nutzung oder Bearbeitung. Rechte an fremden Inhalten bleiben bei ihren Rechteinhabern. Bitte verlinke die Ausgabe; weitergehende Nutzung vorab klären.'),('Ist das eine Empfehlung oder Beratung?','Nein. Der Bericht dient der Information und Einordnung. Er ist keine Anlageberatung, Kaufempfehlung oder Zusage zur Leistung eines Modells oder Produkts. Für Entscheidungen die Originalquellen und deren Stand prüfen.')]
    questions=''.join('<details><summary>%s</summary><p>%s</p></details>'%(e(q),e(a)) for q,a in faq)
    return '''<link rel="stylesheet" href="/assets/report-preview/landing.css"><main class="rlp" data-brand="%s"><section class="rl-hero"><div><p class="rl-tag">%s / PDF-Ausgabe</p><h1>%s</h1><p class="rl-lead">%s</p><div class="rl-proof"><span>Gratis</span><span>Ohne Anmeldung</span><span>Ohne E-Mail</span></div><a class="rl-button" href="%s">%s gratis laden ↓</a><p class="rl-fine">PDF direkt öffnen oder speichern. Archivstand: %s.<br>Kein Newsletter. Kein E-Mail-Capture.</p></div><figure class="rl-preview">%s<figcaption>%s</figcaption></figure></section><section class="rl-section"><p class="rl-tag">Dein Überblick, ohne Umwege</p><h2>Lesen. Speichern. Wiederfinden.</h2><ul class="rl-benefits">%s</ul></section><section class="rl-section rl-inside"><div><p class="rl-tag">Das steckt drin</p><h2>Ein fester Stand.<br>Mit Quellen zum Weiterlesen.</h2><ul>%s</ul></div><aside class="rl-note"><b>Überblick statt endlos weiterscrollen.</b><p>Das PDF hält einen konkreten Redaktionsstand fest. Spätere Änderungen stehen nicht automatisch darin. Für aktuelle Details immer die verlinkten Quellen prüfen.</p></aside></section><section class="rl-section" id="archiv"><p class="rl-tag">Nicht nur die heutige Ausgabe</p><h2>Dein Tagesarchiv.</h2><p class="rl-lead">Ein PDF pro Tag, dauerhaft auffindbar. Neueste Ausgabe zuerst.</p><ul class="rl-archive">%s</ul><p class="rl-fine">Archivdatum: Europe/Berlin. Aktuelle Ausgabe und Tages-Snapshot können sich unterscheiden. Bei einem fehlgeschlagenen Lauf bleibt der letzte gültige Stand erhalten.</p></section><section class="rl-section"><h2>Gut zu wissen.</h2>%s</section><aside class="rl-close"><h2>Dein nächster Überblick ist ein PDF entfernt.</h2><p>Gratis, ohne Anmeldung und ohne E-Mail.</p><a class="rl-button" href="%s">%s jetzt laden ↓</a></aside></main>'''%(key,name,e(headline).replace('\n','<br>'),e(lead),url,name,stamp,previews,preview_caption,cards,''.join('<li>'+e(t)+'</li>' for t in includes.split('|')),archive or '<li>Noch keine Ausgabe im Archiv.</li>',questions,url,name)
