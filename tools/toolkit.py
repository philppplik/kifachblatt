#!/usr/bin/env python3
"""Generate the EU-KI-Toolkit pages (Gratis-Download hinter Lead-Wall) from korrekturen.html as shell.
Run: python3 tools/toolkit.py. Landing page /toolkit is index,follow and in the sitemap since Philipp's go (22.10.2026); the confirmation page /toolkit-bestaetigt stays noindex."""
import re, pathlib, importlib.util
ROOT = pathlib.Path(__file__).resolve().parent.parent
T = (ROOT/'korrekturen.html').read_text()
lw = (ROOT/'tools'/'leadwall.py').read_text()
LWCSS = re.search(r"^CSS = '(<style>.*?</style>)'", lw, re.M).group(1)
TKCSS = ('<style>.tk{max-width:760px}.tk h2{margin:36px 0 12px}.tk .tk-lead{font-size:1.12em;line-height:1.6}'
 '.tk ul.tk-ben{padding-left:0;list-style:none;display:grid;gap:12px;margin:20px 0}.tk ul.tk-ben li{border:1px solid rgba(127,127,127,.28);border-radius:10px;padding:14px 16px;background:var(--bg2)}'
 '.tk figure{margin:28px 0}.tk figure img{width:100%;height:auto;border:1px solid rgba(127,127,127,.28);border-radius:10px;background:#fff}.tk figcaption{font-size:13px;color:var(--mute);margin-top:8px}'
 '.tk table{width:100%;border-collapse:collapse;margin:16px 0;font-size:15px}.tk th,.tk td{text-align:left;padding:10px 12px;border-bottom:1px solid rgba(127,127,127,.28);vertical-align:top}.tk th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}'
 '.tk .tk-box{border:1px solid #7040cd;border-radius:12px;padding:20px;margin:28px 0;background:var(--bg2)}.tk .tk-box h2{margin-top:0}'
 '.tk .tk-rdg{border:1px solid #b9770e;border-radius:10px;padding:14px 16px;margin:28px 0;background:rgba(185,119,14,.08);font-size:14px;line-height:1.6}'
 '.tk .tk-stand{font-size:14px;color:var(--mute)}.tk .tk-ai{font-size:12px;color:var(--mute);margin-top:10px}@media(max-width:640px){.tk table,.tk thead,.tk tbody,.tk tr,.tk td,.tk th{display:block}.tk thead{display:none}.tk td{border:0;padding:2px 0}.tk tr{border-bottom:1px solid rgba(127,127,127,.28);padding:10px 0}}</style>')
CONSENT = ('Ja, ich möchte das EU-KI-Toolkit des KI Fachblatts kostenlos herunterladen. Dafür erhalte ich per E-Mail den KI-Tagesbericht des KI Fachblatts, '
 'Hinweise auf neue Versionen des Toolkits und gelegentlich Hinweise auf neue Produkte des KI Fachblatts (jederzeit abbestellbar). '
 'Ich kann meine Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen, z. B. über den Abmeldelink in jeder E-Mail oder per E-Mail an '
 '<a href="mailto:redaktion@kifachblatt.de">redaktion@kifachblatt.de</a>. Der Versand erfolgt über den Dienstleister Resend (PLUS FIVE FIVE, Inc., USA); eine Übermittlung in die USA kann dabei stattfinden; '
 'Details in der <a href="/datenschutz#tagesbericht-anmeldung">Datenschutzerklärung</a>.')
FORM = ('<form class="lw" id="lw-form" data-ep="tksub" method="post" novalidate><label for="lw-email">E-Mail-Adresse</label><input id="lw-email" name="email" type="email" autocomplete="email" inputmode="email" required>'
 '<div class="lw-hp" aria-hidden="true"><label>Nicht ausfüllen<input name="website" tabindex="-1" autocomplete="off"></label></div>'
 '<label class="lw-c" for="lw-consent"><input id="lw-consent" name="consent" type="checkbox" required><span>'+CONSENT+'</span></label>'
 '<button class="lw-go" type="submit">Bestätigungsmail anfordern</button><div id="lw-msg" class="lw-msg" role="status" hidden></div>'
 '<small>Nur die E-Mail-Adresse ist Pflicht. Du bekommst eine Bestätigungsmail (Double-Opt-in); erst nach dem Klick auf den Link kannst du das Toolkit laden. Keine Tracking-Pixel in unseren Mails. Anmeldezeitpunkt, Bestätigungszeitpunkt, Textversion und IP-Adresse werden als Einwilligungsnachweis gespeichert.</small></form>')
TITLE = 'EU-KI-Toolkit für KMU – kostenlos: KI-Richtlinie, Tool-Checkliste, Schulungsnachweis und Risikoeinstufung'
LANDING = (
 '<div class="tk"><div class="kicker">Toolkit · Gratis-Download</div><h1>'+TITLE+'</h1>'
 '<p class="tk-lead">Ihr Team nutzt längst ChatGPT &amp; Co. – aber ist das dokumentiert? Seit Februar 2025 verlangt Art. 4 der EU-KI-Verordnung Maßnahmen zur KI-Kompetenz, seit August 2026 gelten die Transparenzpflichten und die Aufsicht läuft. '
 'Unser kostenloses Toolkit bringt Sie an einem Nachmittag von null auf dokumentierte KI-Nutzung: vier editierbare Vorlagen (Word + PDF), auf dem Stand der konsolidierten Verordnung inklusive KI-Omnibus vom Juli 2026.</p>'
 '<div id="tk-known" class="lw-msg" hidden>Du bist auf diesem Gerät bereits angemeldet. <a class="lw-go" href="#">Toolkit direkt herunterladen</a></div>'
 '<p><a class="lw-go" href="#download" style="display:inline-flex;min-height:46px;padding:12px 20px;border-radius:8px;background:#7040cd;color:#fff;text-decoration:none;font:600 15px system-ui,sans-serif;align-items:center">Kostenlos herunterladen</a></p>'
 '<ul class="tk-ben">'
 '<li><b>Sofort einsetzbar:</b> Firmennamen einsetzen, beschließen, ablegen – vier Vorlagen als Word und PDF, dazu ein 90-Minuten-Umsetzungsplan mit Fristen-Zeitstrahl.</li>'
 '<li><b>Aktueller Rechtsstand:</b> Auf Basis der konsolidierten EU-KI-Verordnung inkl. Digital Omnibus on AI (Juli 2026) erstellt – inklusive der verschobenen Hochrisiko-Frist (02.12.2027) und der neuen Verbote ab 02.12.2026.</li>'
 '<li><b>Schulung dokumentiert:</b> Der Schulungsnachweis nach Art. 4 folgt dem offiziellen Q&amp;A der Europäischen Kommission – ohne teures Zertifikat, die interne Aufzeichnung genügt.</li>'
 '<li><b>Ehrlich statt verkäuflich:</b> Keine leeren Versprechen. Wir sagen klar, was die Vorlagen leisten – und wo Sie eine Fachanwältin oder einen Datenschutzberater brauchen.</li></ul>'
 '<figure><img src="/assets/toolkit/ki-vo-fristen.png" width="2300" height="854" loading="lazy" alt="Zeitstrahl der EU-KI-Verordnung: 01.08.2024 Inkrafttreten, 02.02.2025 Verbote und KI-Kompetenz, 02.08.2025 GPAI-Pflichten, 02.08.2026 Transparenzpflichten und Aufsicht, 02.12.2026 neue Verbote, 02.12.2027 Hochrisiko Anhang III, 02.08.2028 Hochrisiko in Produkten, 02.08.2030 Bestandssysteme öffentlicher Stellen">'
 '<figcaption>Fristen der EU-KI-Verordnung im Überblick. Quelle: Verordnung (EU) 2024/1689 i. d. F. des Digital Omnibus on AI, Stand 20.10.2026. Bestandteil des Toolkits.</figcaption></figure>'
 '<h2>Das ist im Toolkit</h2><table><thead><tr><th>Datei</th><th>Wofür</th></tr></thead><tbody>'
 '<tr><td><b>Vorlage 1: KI-Richtlinie</b></td><td>Interne Regeln für die Nutzung von KI-Werkzeugen im Unternehmen (Word + PDF).</td></tr>'
 '<tr><td><b>Vorlage 2: Tool-Checkliste</b></td><td>Welche KI-Tools nutzt das Team, mit welchen Daten, unter welchen Bedingungen (Word + PDF).</td></tr>'
 '<tr><td><b>Vorlage 3: Schulungsnachweis</b></td><td>Interne Dokumentation der KI-Kompetenz-Maßnahmen nach Art. 4 (Word + PDF).</td></tr>'
 '<tr><td><b>Vorlage 4: Risikoeinstufung</b></td><td>Entscheidungspfad und Protokoll für die Einstufung eines KI-Systems (Word + PDF).</td></tr>'
 '<tr><td><b>Beiheft</b></td><td>Lese- und Umsetzungsplan für 90 Minuten, mit Fristen-Zeitstrahl.</td></tr></tbody></table>'
 '<div class="tk-box" id="download"><h2>Toolkit kostenlos herunterladen</h2><p>E-Mail-Adresse eintragen, Bestätigungsmail öffnen, Link klicken, ZIP laden. Kein Kauf, kein Preis.</p>'+FORM+
 '<p class="tk-ai">Erstellt mit KI-Unterstützung. Stand: 20.10.2026.</p></div>'
 '<figure><img src="/assets/toolkit/risikoeinstufung-entscheidungspfad.png" width="1465" height="1795" loading="lazy" alt="Entscheidungspfad zur Risikoeinstufung: Schritt 0 Rolle bestimmen, Schritt 1 verbotene Praktiken, Schritt 2 Hochrisiko, Schritt 3 Transparenzpflichten, dann Ergebnis dokumentieren">'
 '<figcaption>Entscheidungspfad aus Vorlage 4. Vereinfachte Darstellung, maßgeblich ist allein die Verordnung.</figcaption></figure>'
 '<p class="tk-stand"><b>Rechtsstand: 20.10.2026</b> (EU-KI-Verordnung konsolidiert inkl. Digital Omnibus on AI). Wir aktualisieren das Toolkit bei Rechtsänderungen – mit deiner E-Mail-Adresse informieren wir dich über neue Versionen (abbestellbar jederzeit).</p>'
 '<div class="tk-rdg" role="note"><b>Wichtiger Hinweis:</b> Das EU-KI-Toolkit ist eine Arbeitshilfe des KI Fachblatts. Es erteilt keine Rechts-, Steuer- oder Datenschutzberatung und ersetzt diese nicht. '
 'Die Vorlagen sind allgemeine Muster ohne Prüfung Ihres Einzelfalls; ob Ihre Maßnahmen den Anforderungen genügen, bewertet im Zweifel die zuständige Marktüberwachungsbehörde. '
 'Maßgeblich ist allein die Verordnung (EU) 2024/1689 in der jeweils geltenden Fassung. Bei Hochrisiko-Systemen oder konkreten Rechtsfragen empfehlen wir anwaltliche Beratung.</div>'
 '<p class="tk-ai"><a href="/impressum">Impressum</a> · <a href="/datenschutz">Datenschutz</a> · <a href="/transparenz">KI-Transparenz</a></p></div>')
OK = ('<div class="kicker">Toolkit</div><h1 id="lw-h">Anmeldung bestätigt</h1><div class="lw" id="lw-ok" hidden><p>Danke. Hier ist dein kostenloses EU-KI-Toolkit (ZIP mit Word- und PDF-Vorlagen):</p><p><a class="lw-go" id="lw-dl" href="/toolkit">Toolkit herunterladen</a></p>'
 '<p><button class="lw-go" type="button" id="lw-keep">Herunterladen und auf diesem Gerät eingetragen bleiben</button></p><small>Mit „eingetragen bleiben“ speichern wir auf diesem Gerät einen Eintrag (Anmeldestatus, 12 Monate), damit du dich nicht erneut anmelden musst. Löschbar über die Browserdaten.</small>'
 '<p class="tk-ai">Erstellt mit KI-Unterstützung. Stand: 20.10.2026. Arbeitshilfe, keine Rechtsberatung.</p></div>'
 '<div class="lw" id="lw-bad" hidden><p>Der Bestätigungslink ist abgelaufen oder ungültig. <a href="/toolkit">Bitte melde dich erneut an.</a></p></div>')
PAGES = {
 'toolkit': (TITLE+' | KI Fachblatt', 'Kostenloses EU-KI-Toolkit für KMU: KI-Richtlinie, Tool-Checkliste, Schulungsnachweis und Risikoeinstufung als Word und PDF. Gratis-Download per E-Mail-Bestätigung.', LANDING),
 'toolkit-bestaetigt': ('Toolkit: Anmeldung bestätigt · KI Fachblatt', 'Bestätigung der Anmeldung und Download des EU-KI-Toolkits.', OK)}
for slug,(title,desc,body) in PAGES.items():
    t = T
    t = re.sub(r'<title>.*?</title>', lambda m:'<title>'+title+'</title>', t, 1, re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*', lambda m:m.group(1)+desc, t, 1)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m:m.group(1)+'https://kifachblatt.de/'+slug, t, 1)
    t = re.sub(r'<main id="main">.*?</main>', lambda m:'<main id="main"><div class="wrap"><div class="legal">'+body+'</div></div></main>', t, 1, re.S)
    t = re.sub(r'<meta name="robots" content="index,follow[^>]*>', '', t, 1)
    t = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m:m.group(1)+title, t, 1)
    t = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m:m.group(1)+desc, t, 1)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m:m.group(1)+'https://kifachblatt.de/'+slug, t, 1)
    robots = 'index,follow,max-image-preview:large,max-snippet:-1' if slug == 'toolkit' else 'noindex,nofollow'
    t = t.replace('</head>', LWCSS+TKCSS+'<meta name="robots" content="'+robots+'"></head>', 1)
    t = t.replace('</body>', '<script src="/assets/leadwall.js" defer></script></body>', 1)
    (ROOT/(slug+'.html')).write_text(t)
print('ok', list(PAGES))
