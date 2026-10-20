#!/usr/bin/env python3
"""Final, idempotent static postprocessor: advertising pages, consent UI, activation gates.
Loads no remote resource. Usage: python3 tools/monetization.py <output-directory>"""
import sys, json, pathlib, html, re, shutil
from urllib.parse import quote, urlparse
ROOT = pathlib.Path(__file__).resolve().parent.parent
E = lambda text: html.escape(str(text), quote=True)
SITE = {'key': 'kfb',
 'p': 'kfb',
 'name': 'KI Fachblatt',
 'base': 'https://kifachblatt.de',
 'urls': {'werben': '/werben', 'werbung': '/werbung', 'cookies': '/cookies', 'datenschutz': '/datenschutz', 'impressum': '/impressum'},
 'files': {'werben': 'werben.html', 'werbung': 'werbung.html', 'cookies': 'cookies.html', 'datenschutz': 'datenschutz.html', 'impressum': 'impressum.html'},
 'body_start': '<main id="main">',
 'wrap_open': '<main id="main"><div class="wrap"><div class="legal @@cls@@">',
 'wrap_close': '</div></div></main>',
 'titles': {'werben': 'Werben & Kooperationen | KI Fachblatt', 'werbung': 'Werbung & Affiliate | KI Fachblatt', 'cookies': 'Cookies & Einstellungen | KI Fachblatt'},
 'descs': {'werben': 'Dezente, klar gekennzeichnete Werbung und Kooperationen im KI Fachblatt. Formate und unverbindliche Anfrage per E-Mail.',
           'werbung': 'Wie das KI Fachblatt Anzeigen, gesponserte Inhalte und Affiliate-Links kennzeichnet und von der Redaktion trennt.',
           'cookies': 'Datenschutzauswahl und lokaler Speicher im KI Fachblatt. Statistik und Werbung sind derzeit deaktiviert.'},
 'cards': [('Anzeige · Gesponsert',
            'Artikel bewerben',
            'Ein klar abgegrenzter Hinweis auf einen passenden Artikel oder ein Angebot. Bezahlte Platzierung, kein Einfluss auf redaktionelle Einordnungen.'),
           ('Anzeige · Affiliate',
            'Affiliate-Kooperation',
            'Passende Angebote mit transparentem Provisionshinweis direkt am Link. Keine versteckten Empfehlungen oder automatische Teilnahme an einem Netzwerk.'),
           ('Anzeige',
            'Dezente Display-Anzeige',
            'Eine ruhige Platzierung außerhalb des Lesetexts. Google AdSense ist erst nach gesonderter Einrichtung, Prüfung und passender Einwilligung vorgesehen.')],
 'werben': '<div class="@@p@@-ad-page"><span class="eyebrow">Kooperationen</span><h1>Gute Inhalte.<br>Klar gekennzeichnet.</h1><p class="@@p@@-lead">Werbung im KI Fachblatt soll zum Thema passen, '
           'erkennbar sein und beim Lesen nicht stören. Redaktion und Anzeigen bleiben getrennt.</p><a class="@@p@@-button primary" href="@@CTA@@">Kooperation per E-Mail anfragen</a><p '
           'class="@@p@@-muted">Unverbindlich an philipp.l.paulik@gmail.com. Kein Formular, keine automatische Buchung.</p>\n'
           '<div class="@@p@@-ad-grid">@@CARDS@@</div>\n'
           '<section class="@@p@@-commercial"><span class="@@p@@-label">Platzierungskonzept, keine aktive Anzeige</span><h2>Raum für einen passenden Hinweis.</h2><p>Geplant: ein abgetrennter Spot '
           'nach dem redaktionellen Inhalt, höchstens eine direkte Kampagne pro Seite. Keine Pop-ups, keine Video-Autostarts, kein Sticky-Werbebanner über dem Text.</p><p>Solange kein geprüftes '
           'Angebot vorliegt, bleibt dieser Platz unsichtbar.</p></section>\n'
           '<h2>Redaktion bleibt Redaktion</h2><p>Eine bezahlte Platzierung kauft Sichtbarkeit, keine positive Bewertung. Das gilt besonders für Modell-, Benchmark- und Tool-Einordnungen: Sie werden '
           'nicht gegen Bezahlung verändert. Werbung wird vor dem Inhalt mit „Anzeige“ gekennzeichnet. „Gesponsert“ oder „Affiliate“ ergänzt die Einordnung. Bei Affiliate-Links steht der '
           'Provisionshinweis direkt am Link.</p>\n'
           '<h2>So läuft eine Anfrage ab</h2><ol><li>Schick Unternehmen, Ziel-URL, Thema und gewünschten Zeitraum per Mail. Ein Budgetrahmen ist optional.</li><li>Wir prüfen, ob das Angebot zum '
           'Magazin passt, und besprechen Format, Kennzeichnung und Konditionen.</li><li>Erst eine gesonderte Vereinbarung macht daraus eine Buchung. Es gibt keine garantierte Veröffentlichung oder '
           'positive redaktionelle Bewertung.</li></ol>\n'
           '<h2>Reichweite und Messung</h2><p>Wir versprechen keine erfundenen Reichweiten, Klickzahlen oder CPMs. Eine spätere Auswertung kann nur tatsächlich gemessene, freigegebene Daten '
           'abdecken. AdSense-Abrechnung und eigene Kampagnen sind getrennte Auswertungen.</p>\n'
           '<p>Aktuell sind keine Werbe- oder Statistikdienste aktiviert. <a href="/werbung">Wie wir Werbung kennzeichnen</a> · <a href="/cookies">Datenschutzeinstellungen</a></p><p>E-Mail: <a '
           'href="mailto:philipp.l.paulik@gmail.com">philipp.l.paulik@gmail.com</a></p></div>',
 'werbung': '<h1>Werbung &amp; Affiliate: klar getrennt</h1><p>Wir bereiten Möglichkeiten vor, das KI Fachblatt durch passende Werbung zu finanzieren. Aktuell sind Google AdSense, '
            'Affiliate-Netzwerke und Statistikdienste nicht aktiviert. Es bestehen durch diese Vorbereitung keine Partnerverträge oder Werbebuchungen.</p>\n'
            '<h2>Anzeige</h2><p>Bezahlte Platzierungen werden vor ihrem Inhalt gut sichtbar mit <strong>Anzeige</strong> gekennzeichnet und vom redaktionellen Inhalt getrennt. Sie beeinflussen keine '
            'redaktionelle Bewertung und sind kein Gütesiegel.</p>\n'
            '<h2>Gesponsert</h2><p>Bei einer gesponserten Platzierung ergänzen wir die Kennzeichnung <strong>Anzeige</strong> um <strong>Gesponsert</strong> und nennen den Auftraggeber. Eine '
            'Bewerbung ist keine Garantie für redaktionelle Berichterstattung. Ein vollständig bezahlter Artikel müsste zusätzlich direkt am Anfang und in allen Vorschauen als Anzeige erkennbar '
            'sein.</p>\n'
            '<h2>Affiliate</h2><p>Ein Affiliate-Link kann bei einem Kauf oder einer anderen vereinbarten Handlung eine Provision auslösen. Der Hinweis auf diesen Zusammenhang steht direkt beim Link. '
            'Ein bloßer Hinweis auf dieser Seite ersetzt die Kennzeichnung am Link nicht.</p>\n'
            '<h2>Portraits, Modelle und Benchmarks</h2><p>Unternehmens-, Modell- und Benchmark-Portraits sowie Methodenbewertungen werden nicht gegen Bezahlung geschrieben oder verändert. Eine '
            'Kooperation kauft keine Platzierung in einer Einordnung und keinen Benchmark-Wert.</p>\n'
            '<h2>Zurückhaltende Platzierung</h2><p>Geplant sind klar abgegrenzte Hinweise nach dem redaktionellen Inhalt. Keine Werbe-Pop-ups, keine automatisch startenden Werbevideos und kein '
            'Sticky-Werbebanner über dem Lesetext. Ungebuchte Plätze bleiben unsichtbar.</p>\n'
            '<h2>Anfragen</h2><p>Formate und unverbindliche Anfrage: <a href="/werben">Werben &amp; Kooperationen</a>. Kontakt: philipp.l.paulik@gmail.com. Preise, Laufzeit und Leistung werden '
            'individuell vereinbart. Es werden keine Reichweite oder Klickzahlen garantiert.</p>\n'
            '<h2>Datenschutz</h2><p>Ohne Einwilligung laden wir keine Statistik- oder Werbedienste. Derzeit ist keiner dieser Dienste aktiviert. Mehr dazu: <a href="/datenschutz">Datenschutz</a> und '
            '<a href="/cookies">Cookies &amp; Einstellungen</a>.</p>',
 'cookies': '<h1>Cookies &amp; Einstellungen</h1><p>Statistik- und Werbedienste sind derzeit ausgeschaltet. Ohne Einwilligung werden sie nicht geladen. Du kannst die Datenschutzeinstellungen '
            'jederzeit über die gleichnamige Schaltfläche im Footer öffnen, deine Auswahl ändern oder eine Einwilligung zurücknehmen. Ablehnen schränkt Lesen und Suchen nicht ein.</p>\n'
            '<h2>Gespeicherte Auswahl</h2><p>Wir speichern deine Datenschutzauswahl im lokalen Speicher deines Browsers (Eintrag <strong>kfb-consent-v1</strong>) und zusätzlich in einem technisch notwendigen First-Party-Cookie <strong>kfb_consent_v1</strong> (Pfad /, 180 Tage, SameSite=Lax, erst nach deinem Klick gesetzt). Der Eintrag enthält die gewählten '
            'Kategorien, die Version des Hinweises und den Zeitpunkt der Auswahl. Er wird nicht an einen Statistik- oder Werbedienst übertragen. Nach spätestens 180 Tagen oder bei einer neuen '
            'Version fragen wir erneut. Sind lokaler Speicher und Cookies gesperrt, gilt deine Auswahl nur für den aktuellen Seitenaufruf.</p><p>Diese Speicherung dient ausschließlich dazu, deine ausdrücklich '
            'gewählte Einstellung zu beachten. Rechtsgrundlagen: § 25 Abs. 2 Nr. 2 TDDDG und Art. 6 Abs. 1 lit. f DSGVO. Keine nutzerübergreifende Kennung und kein Tracking-Profil. Du kannst den '
            'Eintrag jederzeit in den Website-Daten deines Browsers löschen.</p>\n'
            '<h2>Statistik: derzeit aus</h2><p>Es ist noch kein Statistikdienst aktiviert. Es werden keine Analytics-Cookies und keine Analytics-Anfragen gesendet. Die vorbereitete Statistikoption '
            'ist deshalb nicht auswählbar. Vor einer Aktivierung werden Anbieter, Datenarten, Zwecke, Speicherdauer und mögliche Übermittlungen hier und in der Datenschutzerklärung konkret benannt. '
            'Optionale Statistik erfordert eine eigene freiwillige Einwilligung.</p>\n'
            '<h2>Werbung: derzeit aus</h2><p>Google AdSense und andere externe Werbedienste sind nicht aktiviert. Es werden keine Werbe-Cookies gesetzt und keine Google-Werbeanfragen gesendet. Die '
            'vorbereitete Werbeoption ist deshalb nicht auswählbar. Eine künftige AdSense-Integration erfordert eine gesonderte technische und datenschutzrechtliche Einrichtung. Dieser '
            'Einstellungsdialog ist keine Google-zertifizierte Consent-Plattform.</p>\n'
            '<h2>Externe Angebote</h2><p>Werbe- oder Affiliate-Links sind normale Links. Erst beim Anklicken verlässt du gegebenenfalls diese Website; dort gelten die Datenschutzregeln des '
            'jeweiligen Anbieters. Eine Kennzeichnung ist keine Zustimmung zu dessen Tracking.</p>\n'
            '<p><a href="/datenschutz">Datenschutzerklärung</a> · <a href="/werbung">Werbung &amp; Affiliate</a> · <a href="/impressum">Impressum</a></p><p class="kfb-muted">Stand: 19. Oktober 2026, '
            'Vorbereitung ohne aktive Statistik- oder Werbedienste.</p>',
 'panel': {'h': 'Deine Privatsphäre.',
           'intro': 'Du entscheidest über Statistik und Werbung. Ohne Zustimmung bleibt beides aus.',
           'q': 'Wofür dürfen Daten genutzt werden?',
           'nec': 'Seite und Datenschutzauswahl. Kein Tracking.',
           'foot': 'Ohne Auswahl bleiben Statistik und Werbung aus. Jederzeit im Footer änderbar.'},
 'footer_anchor': '<a href="/datenschutz">Datenschutz</a>',
 'footer_links': '<a href="/werben">Werben &amp; Kooperationen</a><a href="/werbung">Werbung &amp; Affiliate</a><a href="/cookies">Cookies &amp; Einstellungen</a><button type="button" '
                 'class="@@p@@-consent-open" data-@@p@@-consent-open>Datenschutzeinstellungen</button><span id="@@p@@-consent-status" class="@@p@@-sr" role="status"></span>',
 'privacy_replacements': [('<h2>Kurzfassung</h2><p>Diese Website setzt keine Cookies, nutzt keine Analyse- oder Werbedienste, bindet keine externen Schriftarten und keine Social-Media-Plugins ein. '
                           'Es gibt kein Formular und keine Registrierung.</p>',
                           '<h2>Kurzfassung</h2><p>Diese Website nutzt derzeit keine Analyse- oder Werbedienste, bindet keine externen Schriftarten und keine Social-Media-Plugins ein. Deine '
                           'Datenschutzauswahl wird ausschließlich im lokalen Speicher deines Browsers und in einem technisch notwendigen First-Party-Cookie gespeichert, nicht als Tracking-Cookie. Auf den Lernpfaden speichert dein Browser außerdem lokal (localStorage), welche Schritte du abgehakt hast. Diese Angaben verlassen dein Gerät nicht, es gibt keine Übertragung an uns oder Dritte, und du kannst sie jederzeit über „Zurücksetzen“ im jeweiligen Pfad oder durch Löschen der Websitedaten entfernen. Alle optionalen Dienste sind ausgeschaltet. Es gibt '
                           'kein Formular und keine Registrierung.</p><h2>Datenschutzauswahl und optionale Dienste</h2><p>Die Datenschutzeinstellungen im Footer lassen sich jederzeit öffnen. Deine '
                           'Auswahl wird unter <strong>kfb-consent-v1</strong> mit Kategorien, Zeitpunkt und Hinweisversion bis zu 180 Tage lokal im Browser gespeichert. Zweck ist ausschließlich die '
                           'Beachtung deiner Auswahl, nicht Reichweitenmessung. Rechtsgrundlagen sind § 25 Abs. 2 Nr. 2 TDDDG und Art. 6 Abs. 1 lit. f DSGVO. Bei gesperrtem Speicher und gesperrten Cookies gilt die Auswahl '
                           'nur für den aktuellen Seitenaufruf. Details: <a href="/cookies">Cookies &amp; Einstellungen</a>.</p><p>Statistik und externe Werbung werden erst nach gesonderter '
                           'Einrichtung, ergänzten Datenschutzhinweisen und deiner freiwilligen Einwilligung aktiviert (Art. 6 Abs. 1 lit. a DSGVO; soweit erforderlich § 25 Abs. 1 TDDDG). Ein '
                           'Widerruf ist jederzeit möglich und wirkt für die Zukunft. Derzeit sind Google Analytics, Google AdSense und Affiliate-Netzwerke nicht eingebunden; es werden weder '
                           'Google-Tags noch ein Tag Manager vorgeladen.</p>'),
                          ('Datenschutzerklärung des KI Fachblatts: keine Cookies, kein Tracking.', 'Datenschutzerklärung des KI Fachblatts: kein Tracking, optionale Dienste ausgeschaltet.')],
 'spot_note': 'Anzeige: bezahlte Platzierung, keine redaktionelle Empfehlung.',
 'spot_dirs': [],
 'spot_wrap': '<div class="wrap">%s</div>',
 'css_vars': ':root{--mn-line:var(--line);--mn-soft:var(--bg2);--mn-ac:var(--amber);--mn-bg:var(--bg);--mn-fg:var(--ink);--mn-mut:var(--mute)}',
 'css_extra': '.kfb-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.kfb-ad-page{padding:10px 0 40px}.kfb-ad-page h1{font:400 clamp(34px,5vw,56px)/1.08 '
              'var(--serif);letter-spacing:-1.5px;margin:14px 0 18px}.kfb-muted{color:var(--mute);font-size:13px}.kfb-ad-card h2{font-family:var(--serif);font-weight:400}.kfb-consent '
              'h2{font-family:var(--serif);font-weight:400}footer '
              '.kfb-consent-open{display:block;font:inherit;color:inherit;min-height:0;padding:0;text-align:left;text-decoration:none;cursor:pointer}footer '
              '.kfb-consent-open:hover{color:var(--amber2);text-decoration:underline}'}
P = SITE['p']
SKIP_DIRS = {'content', 'tools', 'docs', 'tests', 'site', 'authorpage', '.github', 'node_modules', 'berichte'}

def validate(cfg):
    if cfg['advertising']['enabled']:
        raise ValueError('AdSense is locked: integrate and test a Google-certified TCF CMP first')
    if cfg['analytics']['enabled']:
        if cfg['analytics']['provider'] != 'ga4' or not re.fullmatch(r'G-[A-Z0-9]+', cfg['analytics']['measurementId']):
            raise ValueError('An approved GA4 property ID is required')
        if cfg['analytics'].get('eventRetentionMonths') != 2 or cfg['analytics'].get('cookieLifetimeDays') != 180 or cfg['analytics'].get('resetRetentionOnActivity') is not False: raise ValueError('Reviewed short GA4 profile required')
        if not cfg['analytics'].get('activationApproved'): raise ValueError('Owner activation approval required')
        if not cfg['analytics'].get('privacyReviewed'):
            raise ValueError('Update privacy/cookies, processor agreement, retention and settings before activation')
    if cfg['metrics']['enabled'] and not cfg['analytics']['enabled']:
        raise ValueError('No collector selected: local events alone are not an aggregate metrics system')
    if len(cfg['spots']) > 1:
        raise ValueError('Unobtrusive v1: at most one direct campaign')
    for s in cfg['spots']:
        if not re.fullmatch(r'[a-z0-9-]{1,80}', s['id']): raise ValueError('Invalid spot ID')
        if s['kind'] not in ('sponsored', 'affiliate'): raise ValueError('Unknown campaign type')
        if not all(s.get(x) for x in ('sponsor', 'title', 'description', 'url')): raise ValueError('Missing campaign disclosure')
        u = urlparse(s['url'])
        if not (u.scheme == 'https' and u.netloc and not u.username): raise ValueError('Use a verified HTTPS destination; paid local content needs its own labelling pass')
        if not s.get('approved'): raise ValueError('Campaign recipient, wording and destination must be approved')
    return cfg

def u(name): return SITE['urls'][name]

PANEL = '''<section id="@@p@@-consent" class="@@p@@-consent" role="region" aria-labelledby="@@p@@-consent-title" hidden>
<h2 id="@@p@@-consent-title">%(h)s</h2>
<p>%(intro)s</p>
<fieldset><legend>%(q)s</legend>
<label><input type="checkbox" checked disabled><span><strong>Notwendig</strong><small>%(nec)s</small></span></label>
<label><input type="checkbox" id="@@p@@-statistics"><span><strong>Statistik</strong><small>Seitenaufrufe und Interaktionen. Derzeit aus.</small></span></label>
<label><input type="checkbox" id="@@p@@-advertising"><span><strong>Werbung</strong><small>AdSense und Werbedienste. Derzeit aus.</small></span></label>
</fieldset><div class="@@p@@-consent-actions"><button type="button" data-consent="reject">Alle ablehnen</button><button type="button" data-consent="all">Alle verfügbaren akzeptieren</button><button type="button" data-consent="save">Auswahl speichern</button></div>
<p><a href="%(ds)s">Datenschutz</a> · <a href="%(ck)s">Cookies &amp; Einstellungen</a> · <a href="%(im)s">Impressum</a></p><p class="@@p@@-muted">%(foot)s</p></section>'''.replace('@@p@@', P) % dict(SITE['panel'], ds=u('datenschutz'), ck=u('cookies'), im=u('impressum'))

def mailto(kind):
    body = 'Hallo Philipp,\n\nich interessiere mich für: ' + kind + '\n\nUnternehmen / Website:\nBeworbener Artikel oder Ziel-URL:\nThema und Zielgruppe:\nGewünschter Zeitraum:\nOptionaler Budgetrahmen:\nHinweise / Kontakt:\n\nMir ist klar: Die Anfrage ist keine Buchung.\n'
    return 'mailto:philipp.l.paulik@gmail.com?subject=' + quote('Werbeanfrage ' + SITE['name'] + ': ' + kind) + '&body=' + quote(body)

def advertiser_page():
    cards = ''
    for label, title, desc in SITE['cards']:
        cards += '<section class="@@p@@-ad-card"><span class="@@p@@-label">%s</span><h2>%s</h2><p>%s</p><a class="@@p@@-button" href="%s">Format anfragen</a></section>'.replace('@@p@@', P) % (E(label), E(title), E(desc), E(mailto(title)))
    t = SITE['werben'].replace('@@p@@', P)
    return t.replace('@@CTA@@', E(mailto('Kooperation'))).replace('@@CARDS@@', cards)

def wrap_body(inner, cls=''):
    return SITE['wrap_open'].replace('@@cls@@', cls) + inner + SITE['wrap_close']

def page_path(out, name):
    return out / SITE['files'][name]

def build_page(out, shell, name, title, desc, inner, cls=''):
    t = shell
    i = t.index(SITE['body_start']); k = t.index('<footer')
    head, foot = t[:i], t[k:]
    canon = SITE['base'] + u(name)
    head = re.sub(r'<div class="crumbs">.*?</div>', '', head, flags=re.S)
    head = re.sub(r'<title>.*?</title>', '<title>' + E(title) + '</title>', head, flags=re.S)
    head = re.sub(r'<meta (?:property="og:(?:title|description|url|type)"|name="description")[^>]*>', '', head)
    head = re.sub(r'<link rel="canonical"[^>]*>', '<link rel="canonical" href="%s">' % canon, head)
    head = re.sub(r'<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)
    head = head.replace('</head>', '<meta name="description" content="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:type" content="website"></head>' % (E(desc), E(title), E(desc), canon), 1)
    f = page_path(out, name); f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(head + wrap_body(inner, cls) + foot)

def patch_privacy(out):
    f = page_path(out, 'datenschutz')
    if not f.exists(): raise ValueError('Datenschutz page missing: ' + str(f))
    t = f.read_text()
    if SITE['key'] + '-consent-v1' in t: return
    for old, new in SITE['privacy_replacements']:
        if old not in t: raise ValueError('Privacy marker not found: ' + old[:60])
        t = t.replace(old, new, 1)
    f.write_text(t)

GA4_DETAILS = '<h3>Anbieter und Zweck</h3><p>Google Analytics 4 ist ein Dienst von Google. Vertragspartner nach den deutschen Google-Analytics-Nutzungsbedingungen ist Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland; Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA 94043, USA, und weitere Auftragsverarbeiter können an der Verarbeitung beteiligt sein. Zweck ist die statistische Auswertung von Seitenaufrufen, Nutzung und gekennzeichneten Werbeplatzierungen. Werbung, Google Signals, User-ID, personalisierte Anzeigen und Verknüpfungen mit Google Ads sind nicht Teil dieser Konfiguration.</p>\n<h3>Einwilligung und Daten</h3><p>Rechtsgrundlagen sind deine freiwillige Einwilligung nach Art. 6 Abs. 1 lit. a DSGVO und für das Speichern beziehungsweise Auslesen auf deinem Gerät § 25 Abs. 1 TDDDG. Ohne Statistik-Einwilligung laden wir den Google-Tag nicht und senden auch keine cookielosen Ablehnungs-Pings (Basic Consent Mode). Lesen und Suche bleiben möglich. Bei Einwilligung können Seitenpfad, Seitentitel, Zeitpunkte, technische Browser-/Geräteinformationen, grobe Standortinformationen und eine pseudonyme Cookie-Kennung verarbeitet werden. Beim Verbindungsaufbau wird deine IP-Adresse an Google übermittelt; Google beschreibt für GA4, dass einzelne IP-Adressen nicht protokolliert oder gespeichert werden. Das ist keine Zusage vollständiger Anonymität.</p>\n<p>Die ausdrücklich gesendeten Seitenereignisse enthalten keine URL-Suchparameter oder Referrer. Es werden keine Namen oder E-Mail-Adressen als Ereignisparameter gesendet. Enhanced Measurement ist in der Property ausgeschaltet, damit keine zusätzlichen Formular-, Such- oder Outbound-Link-Daten automatisch erfasst werden. Platzierungsereignisse enthalten nur Ereignisart, Spot-ID und Seitenpfad; keine vollständige Ziel-URL.</p>\n<h3>Cookies und Speicherdauer</h3><p>GA4 kann die First-Party-Cookies _ga und _ga_&lt;Kennung&gt; verwenden. Wir begrenzen ihre Laufzeit auf 180 Tage und verlängern sie nicht mit jedem Besuch; Browser können sie früher löschen. Die eingestellte Property-Aufbewahrung für nutzer- und ereignisbezogene Daten beträgt zwei Monate, ohne Zurücksetzen bei neuer Aktivität. Diese Einstellung betrifft nicht automatisch alle bereits aggregierten Standardberichte. Google weist darauf hin, dass Änderungen der Aufbewahrung bis zu 24 Stunden brauchen können.</p>\n<h3>Drittlandübermittlung und Auftragsverarbeitung</h3><p>Eine Verarbeitung in den USA und anderen Ländern außerhalb des EWR ist möglich. Für dieses Analytics-Konto wurden am 19. Oktober 2026 die Google Ads Data Processing Terms als Vereinbarung zur Auftragsverarbeitung nach Art. 28 DSGVO akzeptiert. Google LLC ist im offiziellen Register als aktiver Teilnehmer des EU-US Data Privacy Framework aufgeführt (geprüft am 19. Oktober 2026). Für davon erfasste Übermittlungen in die USA dient der entsprechende Angemessenheitsbeschluss als Grundlage. Soweit erforderlich, sehen Googles Datenverarbeitungsbedingungen ergänzend Standardvertragsklauseln vor. Andere Drittländer können ein anderes Datenschutzniveau haben; Statistik-Einwilligung beseitigt dieses Risiko nicht.</p>\n<h3>Widerruf</h3><p>Öffne jederzeit „Datenschutzeinstellungen“ im Footer und wähle „Alle ablehnen“ oder deaktiviere Statistik. Der Widerruf gilt für die Zukunft. Weitere Statistik-Ereignisse werden gestoppt, bekannte GA-Cookies auf dieser Domain soweit technisch zugänglich entfernt und die Seite ohne Tag neu geladen. Bereits rechtmäßig verarbeitete Daten werden dadurch nicht automatisch rückwirkend gelöscht. Für Auskunft oder Löschung kontaktiere philipp.l.paulik@gmail.com.</p>\n<p>Weitere Informationen: <a href="https://policies.google.com/privacy?hl=de" rel="noopener">Google-Datenschutzerklärung</a>, <a href="https://support.google.com/analytics/answer/11397207" rel="noopener">GA4-Cookies</a>, <a href="https://support.google.com/analytics/answer/7667196" rel="noopener">Datenaufbewahrung</a>, <a href="https://privacy.google.com/businesses/processorterms/" rel="noopener">Google-Datenverarbeitungsbedingungen</a>, <a href="https://www.dataprivacyframework.gov/participant/5780" rel="noopener">DPF-Registereintrag Google LLC</a>, <a href="https://www.google.com/analytics/terms/de.html" rel="noopener">Analytics-Nutzungsbedingungen</a>.</p>'

def active_wording(t):
    t=t.replace('Statistik und Werbung sind derzeit deaktiviert.','Google Analytics 4 nur nach Statistik-Einwilligung; Werbung bleibt aus.')
    t=t.replace('Statistik und Werbung sind noch nicht aktiviert.','Google Analytics 4 ist nur mit Statistik-Einwilligung verfügbar. Werbung bleibt aus.')
    t=t.replace('Aktuell sind keine Werbe- oder Statistikdienste aktiviert.','Google Analytics 4 wird nur nach Statistik-Einwilligung geladen. Externe Werbung bleibt aus.')
    t=t.replace('Statistik und externe Werbung sind derzeit nicht aktiv. Sie würden erst nach gesonderter Einrichtung, ergänzten Datenschutzhinweisen und Ihrer freiwilligen Einwilligung aktiviert (Art. 6 Abs. 1 lit. a DSGVO; soweit erforderlich § 25 Abs. 1 TDDDG).','Google Analytics 4 wird nur mit freiwilliger Statistik-Einwilligung eingesetzt (Art. 6 Abs. 1 lit. a DSGVO und § 25 Abs. 1 TDDDG). Externe Werbung bleibt aus.')
    t=t.replace('Derzeit sind Google Analytics, Google AdSense und Affiliate-Netzwerke nicht eingebunden; es werden weder Google-Tags noch ein Tag Manager vorgeladen.','Google Analytics 4 lädt nur nach Statistik-Einwilligung. Google AdSense und Affiliate-Netzwerke bleiben aus. Ohne Einwilligung gibt es keine Google-Tags oder Ablehnungs-Pings; ein Tag Manager wird nicht verwendet.')
    t=t.replace('Statistik und externe Werbung sind derzeit ausgeschaltet.','Google Analytics 4 ist nur mit Statistik-Einwilligung verfügbar. Externe Werbung bleibt ausgeschaltet.')
    t=t.replace('Statistik: derzeit aus','Statistik mit Einwilligung')
    t=t.replace('Stand: 19. Oktober 2026, Vorbereitung ohne aktive Statistik- oder Werbedienste.','Stand: 19. Oktober 2026. Statistik nur mit Einwilligung; Werbung aus.')
    t=t.replace('Statistik- und Werbedienste sind derzeit ausgeschaltet.', 'Google Analytics 4 ist nur mit Statistik-Einwilligung verfügbar. Externe Werbung bleibt aus.')
    t=re.sub(r'Es ist noch kein Statistikdienst aktiviert\..*?Optionale Statistik erfordert eine eigene freiwillige Einwilligung\.', 'Google Analytics 4 lädt nur mit freiwilliger Statistik-Einwilligung. Ohne Zustimmung gibt es keine Analytics-Cookies und keine Statistik-Anfragen. Details stehen im GA4-Abschnitt dieser Seite.', t, flags=re.S)
    t=re.sub(r'Statistik und externe Werbung werden erst nach gesonderter Einrichtung,.*?§ 25 Abs. 1 TDDDG\)\.', 'Google Analytics 4 lädt nur nach freiwilliger Statistik-Einwilligung (Art. 6 Abs. 1 lit. a DSGVO und § 25 Abs. 1 TDDDG). Externe Werbung bleibt aus.',t,flags=re.S)
    t=t.replace('Diese Website nutzt derzeit keine Analyse- oder Werbedienste', 'Diese Website nutzt Google Analytics 4 nur mit Statistik-Einwilligung, aber keine externen Werbedienste')
    t=t.replace('Alle optionalen Dienste sind ausgeschaltet.', 'Ohne Statistik-Einwilligung bleibt Google Analytics 4 aus. Werbung bleibt immer aus.')
    return t

def main(out):
    out = pathlib.Path(out).resolve()
    cfg = validate(json.loads((ROOT / 'content/monetization.json').read_text()))
    active = cfg['analytics']['enabled']
    asset = out / 'assets/monetization'; asset.mkdir(parents=True, exist_ok=True)
    for name in ('consent.css', 'consent.js'): shutil.copy(ROOT / 'tools/monetization' / name, asset / name)
    shell = page_path(out, 'impressum').read_text()
    # Shell is taken from the imprint page of the build, minus its own consent artefacts if re-run in place.
    shell = re.sub(r'<link rel="stylesheet" href="/assets/monetization/consent.css">', '', shell)
    shell = re.sub(r'<section id="%s-consent".*?</section>' % P, '', shell, flags=re.S)
    shell = re.sub(r'<script type="application/json" id="%s-monetization-config">.*?</script><script src="/assets/monetization/consent.js" defer></script>' % P, '', shell, flags=re.S)
    build_page(out, shell, 'werben', SITE['titles']['werben'], SITE['descs']['werben'], advertiser_page(), P + '-ad-page')
    build_page(out, shell, 'werbung', SITE['titles']['werbung'], SITE['descs']['werbung'], SITE['werbung'], P + '-doc')
    build_page(out, shell, 'cookies', SITE['titles']['cookies'], SITE['descs']['cookies'], SITE['cookies'], P + '-doc')
    patch_privacy(out)
    config = '<script type="application/json" id="%s-monetization-config">' % P + json.dumps(cfg, ensure_ascii=True).replace('<', '\\u003c') + '</script>'
    panel = PANEL
    if active:
        panel = panel.replace('Seitenaufrufe und Interaktionen. Derzeit aus.', 'Google Analytics 4 (Google Ireland / Google LLC): Seitenaufrufe und Interaktionen, Cookies bis 180 Tage; USA-Übermittlung möglich. Nur nach Zustimmung.')
    extra = panel + config + '<script src="/assets/monetization/consent.js" defer></script>'
    spot = ''
    for s in cfg['spots']:
        label = 'Anzeige · ' + ('Affiliate' if s['kind'] == 'affiliate' else 'Gesponsert')
        notice = '<p>Affiliate-Link: Bei einem Kauf über diesen Link können wir eine Provision erhalten.</p>' if s['kind'] == 'affiliate' else ''
        spot += '<aside class="%s-commercial" aria-label="Anzeige" data-%s-spot="%s"><span class="%s-label">%s · Auftraggeber: %s</span><h2>%s</h2><p>%s</p>%s<p class="%s-muted">%s</p><a class="%s-button" data-%s-promotion href="%s" rel="sponsored nofollow noopener">Angebot ansehen</a></aside>' % (P, P, E(s['id']), P, E(label), E(s['sponsor']), E(s['title']), E(s['description']), notice, P, E(SITE['spot_note']), P, P, E(s['url']))
    footer_anchor = SITE['footer_anchor']
    links = SITE['footer_links'].replace('@@p@@', P)
    for f in out.rglob('*.html'):
        rel = f.relative_to(out)
        if rel.parts[0] in SKIP_DIRS or any(x.startswith('.') for x in rel.parts): continue
        t = f.read_text()
        t = re.sub(r'<section id="%s-consent".*?</section>' % P, '', t, flags=re.S)
        t = re.sub(r'<script type="application/json" id="%s-monetization-config">.*?</script><script src="/assets/monetization/consent.js" defer></script>' % P, '', t, flags=re.S)
        if '</body>' not in t or '<footer' not in t: continue
        t = t.replace('<link rel="stylesheet" href="/assets/monetization/consent.css">', '')
        t = t.replace('</head>', '<link rel="stylesheet" href="/assets/monetization/consent.css"></head>', 1)
        fi = t.find('<footer')
        if '/werben' not in t[fi:] and footer_anchor in t[fi:]:
            t = t[:fi] + t[fi:].replace(footer_anchor, footer_anchor + links, 1)
        if spot and rel.name == 'index.html' and (len(rel.parts) == 1 or rel.parts[0] in SITE['spot_dirs']):
            at = t.find('<footer'); t = t[:at] + SITE['spot_wrap'] % spot + t[at:]
        if active:
            t = active_wording(t)
            if f in (page_path(out,'cookies'),page_path(out,'datenschutz')):
                t = re.sub(r'<section id="ga4-disclosure">.*?</section>', '', t, flags=re.S)
                end = '</div></div></main>' if P=='kfb' else '</div><footer'
                disclosure = '<section id="ga4-disclosure"><h2>Google Analytics 4: Statistik mit Einwilligung</h2>'+GA4_DETAILS+'</section>'
                if P=='kfb': t=t.replace('</div></div></main>',disclosure+'</div></div></main>',1)
                else:
                    fi=t.find('<footer'); close=t.rfind('</div>',0,fi); t=t[:close]+disclosure+t[close:]
        t = t.replace('</body>', extra + '</body>', 1); f.write_text(t)
    p = out / 'sitemap.xml'
    if p.exists():
        xml = p.read_text(); add = ''
        for n in ('werben', 'werbung', 'cookies'):
            loc = SITE['base'] + u(n)
            if '<loc>' + loc + '</loc>' not in xml: add += '<url><loc>%s</loc></url>' % loc
        if add: p.write_text(xml.replace('</urlset>', add + '</urlset>'))
    print('Monetization: consent-gated GA4 available; advertising off')

if __name__ == '__main__': main(sys.argv[1])
