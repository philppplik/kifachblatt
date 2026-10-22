#!/usr/bin/env python3
"""Generate the Lead-Wall pages from korrekturen.html as shell. Run: python3 tools/leadwall.py"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
T = (ROOT/'korrekturen.html').read_text()
API = '__LW_API__'  # replaced by data-api attribute at deploy time, see assets/leadwall.js
CONSENT = ('Ja, ich möchte den KI-Tagesbericht des KI Fachblatts kostenlos per E-Mail erhalten (täglich, jederzeit abbestellbar) '
 'und gelegentlich Hinweise auf neue Produkte des KI Fachblatts. Ich kann meine Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen, '
 'z. B. über den Abmeldelink in jeder E-Mail oder per E-Mail an <a href="mailto:redaktion@kifachblatt.de">redaktion@kifachblatt.de</a>. '
 'Der Versand erfolgt über den Dienstleister Resend (PLUS FIVE FIVE, Inc., USA) als Auftragsverarbeiter; Details in der <a href="/datenschutz#tagesbericht-anmeldung">Datenschutzerklärung</a>.')
CSS = '<style>.lw{max-width:560px}.lw label{display:block;font-weight:600;margin:18px 0 6px}.lw input[type=email]{box-sizing:border-box;width:100%;min-height:46px;padding:10px 12px;font:inherit;border:1px solid rgba(127,127,127,.5);border-radius:8px;background:var(--bg2);color:var(--ink)}.lw .lw-c{display:flex;gap:10px;align-items:flex-start;margin:16px 0;font-size:14px;line-height:1.55;font-weight:400}.lw .lw-c input{margin:3px 0 0;padding:0;min-height:20px;width:20px;height:20px;flex:none;accent-color:#7040cd}.lw button.lw-go,.lw a.lw-go{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:12px 20px;border:0;border-radius:8px;background:#7040cd;color:#fff;font:600 15px system-ui,sans-serif;cursor:pointer;text-decoration:none}.lw button:disabled{opacity:.6}.lw .lw-hp{position:absolute;left:-9999px;height:0;overflow:hidden}.lw .lw-msg{margin-top:16px;padding:12px 14px;border:1px solid rgba(127,127,127,.28);border-radius:8px}.lw .lw-err{border-color:#c0392b}.lw small{display:block;margin-top:14px;color:var(--mute)}</style>'
CONSENT_ATLAS = ('Ja, ich möchte das Modell-Atlas-Datenpaket des KI Fachblatts kostenlos herunterladen und erhalte dafür E-Mails mit dem Bestätigungslink und nach Bestätigung dem Download-Link. '
 'Ein Newsletter-Abonnement ist damit nicht verbunden. Ich kann meine Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen, z. B. per E-Mail an <a href="mailto:redaktion@kifachblatt.de">redaktion@kifachblatt.de</a>. '
 'Der Versand erfolgt über den Dienstleister Resend (PLUS FIVE FIVE, Inc., USA) als Auftragsverarbeiter; Details in der <a href="/datenschutz#atlas-datenpaket">Datenschutzerklärung</a>.')
PAGES_ATLAS = {
 'atlas-daten-anmelden': ('Modell-Atlas-Datenpaket gratis erhalten', 'Anmeldung zum kostenlosen Modell-Atlas-Datenpaket des KI Fachblatts. Double-Opt-In, jederzeit abbestellbar.',
  '<div class="kicker">Modell-Atlas</div><h1>Modell-Atlas-Datenpaket gratis erhalten</h1><p>Die komplette Auswertung als PDF, dazu alle Werte als CSV und JSON. Trage deine E-Mail-Adresse ein. Du bekommst eine Bestätigungsmail. Erst nach dem Klick auf den Link in dieser Mail kannst du das Datenpaket laden.</p>'
  '<form class="lw" id="lw-form" data-ep="atlassub" method="post" novalidate><label for="lw-email">E-Mail-Adresse</label><input id="lw-email" name="email" type="email" autocomplete="email" inputmode="email" required>'
  '<div class="lw-hp" aria-hidden="true"><label>Nicht ausfüllen<input name="website" tabindex="-1" autocomplete="off"></label></div>'
  '<label class="lw-c" for="lw-consent"><input id="lw-consent" name="consent" type="checkbox" required><span>'+CONSENT_ATLAS+'</span></label>'
  '<button class="lw-go" type="submit">Bestätigungsmail anfordern</button><div id="lw-msg" class="lw-msg" role="status" hidden></div>'
  '<small>Nur die E-Mail-Adresse ist Pflicht. Kein Kauf, kein Preis. Keine Tracking-Pixel in unseren Mails. Anmeldezeitpunkt, Bestätigungszeitpunkt, Textversion und IP-Adresse werden als Einwilligungsnachweis gespeichert.</small></form>'),
 'atlas-daten-bestaetigt': ('Anmeldung bestätigt', 'Bestätigung der Anmeldung zum Modell-Atlas-Datenpaket.',
  '<div class="kicker">Modell-Atlas</div><h1 id="lw-h">Anmeldung bestätigt</h1><div class="lw" id="lw-ok" hidden><p>Danke. Du bist angemeldet. Hier ist dein Datenpaket (ZIP mit PDF-Auswertung, CSV und JSON):</p><p><a class="lw-go" id="lw-dl" href="/atlas-daten-anmelden">Datenpaket herunterladen</a></p>'
  '<p><button class="lw-go" type="button" id="lw-keep">Herunterladen und auf diesem Gerät eingetragen bleiben</button></p><small>Mit „eingetragen bleiben“ speichern wir auf diesem Gerät einen Eintrag (Anmeldestatus, 12 Monate), damit du dich nicht erneut anmelden musst. Löschbar über die Browserdaten.</small></div>'
  '<div class="lw" id="lw-bad" hidden><p>Der Bestätigungslink ist abgelaufen oder ungültig. <a href="/atlas-daten-anmelden">Bitte melde dich erneut an.</a></p></div>')}
PAGES = {
 'tagesbericht-anmelden': ('KI-Tagesbericht gratis erhalten', 'Anmeldung zum kostenlosen KI-Tagesbericht des KI Fachblatts. Double-Opt-In, jederzeit abbestellbar.',
  '<div class="kicker">Tagesbericht</div><h1>KI-Tagesbericht gratis erhalten</h1><p>Trage deine E-Mail-Adresse ein. Du bekommst eine Bestätigungsmail. Erst nach dem Klick auf den Link in dieser Mail bist du angemeldet und kannst den Bericht als PDF laden.</p>'
  '<form class="lw" id="lw-form" method="post" novalidate><label for="lw-email">E-Mail-Adresse</label><input id="lw-email" name="email" type="email" autocomplete="email" inputmode="email" required>'
  '<div class="lw-hp" aria-hidden="true"><label>Nicht ausfüllen<input name="website" tabindex="-1" autocomplete="off"></label></div>'
  '<label class="lw-c" for="lw-consent"><input id="lw-consent" name="consent" type="checkbox" required><span>'+CONSENT+'</span></label>'
  '<button class="lw-go" type="submit">Bestätigungsmail anfordern</button><div id="lw-msg" class="lw-msg" role="status" hidden></div>'
  '<small>Nur die E-Mail-Adresse ist Pflicht. Keine Tracking-Pixel in unseren Mails. Anmeldezeitpunkt, Bestätigungszeitpunkt, Textversion und IP-Adresse werden als Einwilligungsnachweis gespeichert.</small></form>'),
 'tagesbericht-bestaetigt': ('Anmeldung bestätigt', 'Bestätigung der Anmeldung zum KI-Tagesbericht.',
  '<div class="kicker">Tagesbericht</div><h1 id="lw-h">Anmeldung bestätigt</h1><div class="lw" id="lw-ok" hidden><p>Danke. Du bist angemeldet. Hier ist der aktuelle Tagesbericht:</p><p><a class="lw-go" id="lw-dl" href="/tagesbericht-anmelden">PDF herunterladen</a></p>'
  '<p><button class="lw-go" type="button" id="lw-keep">PDF herunterladen und auf diesem Gerät eingetragen bleiben</button></p><small>Mit „eingetragen bleiben“ speichern wir auf diesem Gerät einen Eintrag (Anmeldestatus, 12 Monate), damit du die Anmeldung nicht erneut eintippen musst. Löschbar über die Browserdaten.</small></div>'
  '<div class="lw" id="lw-bad" hidden><p>Der Bestätigungslink ist abgelaufen oder ungültig. <a href="/tagesbericht-anmelden">Bitte melde dich erneut an.</a></p></div>'),
 'abmelden': ('Abgemeldet', 'Abmeldung vom KI-Tagesbericht.',
  '<div class="kicker">Tagesbericht</div><h1>Abmeldung</h1><div class="lw"><p id="lw-u">Du bist abgemeldet. Der Versand wurde gestoppt. Die Adresse wird nach 30 Tagen gelöscht, der Einwilligungsnachweis bleibt getrennt gespeichert.</p></div>')}
PAGES.update(PAGES_ATLAS)
for slug,(title,desc,body) in PAGES.items():
    t = T
    t = re.sub(r'<title>.*?</title>', '<title>'+title+' · KI Fachblatt</title>', t, 1, re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>'+desc, t, 1)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>https://kifachblatt.de/'+slug, t, 1)
    t = re.sub(r'<main id="main">.*?</main>', lambda m:'<main id="main"><div class="wrap"><div class="legal">'+body+'</div></div></main>', t, 1, re.S)
    t = t.replace('</head>', CSS+'<meta name="robots" content="noindex,follow"></head>', 1)
    t = t.replace('</body>', '<script src="/assets/leadwall.js" defer></script></body>', 1)
    (ROOT/(slug+'.html')).write_text(t)
print('ok', list(PAGES))
