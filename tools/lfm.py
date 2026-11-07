#!/usr/bin/env python3
"""Generate /lfm (SEO/AEO pillar page: LFM lokal ausfuehren, Geraetecheck, Erklaerer).
Data: content/lfm.json (sources + models). Assets: assets/lfm/lfm.css, assets/lfm/lfm.js.
Shell is taken from lokale-modelle.html. Run: python3 tools/lfm.py  (stdlib only, no network).
Models / company portraits are linked only when the portrait page exists in the repo."""
import re, json, html, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
E = lambda s: html.escape(str(s), quote=True)
D = json.loads((ROOT/'content/lfm.json').read_text())
SRC = D['sources']; BASE = 'https://kifachblatt.de'
STAND_ISO = D['stand']; STAND = '7. November 2026'
SLUG = 'lfm'
TITLE = 'LFM lokal ausführen: Welches Liquid-Modell läuft auf deinem Handy oder PC?'
DESC = ('LFM3 von Liquid AI lokal nutzen: Familie im Überblick, Quantisierung (q4_K_M, q8_0, bf16) einfach erklärt, '
        'Gerätecheck mit offen gelegten Annahmen und die Frage, warum die Modelle so flüssig laufen. Mit Quellen, ohne erfundene Benchmarks.')
def ref(keys):
    order = list(SRC)
    return ''.join('<sup class="lfm-ref"><a href="#q-%s">[%d]</a></sup>' % (k, order.index(k)+1) for k in keys)
def link_if(path, label):
    return '<a href="%s">%s</a>' % (path, label) if (ROOT/(path.strip('/')+'.html')).exists() else E(label)
models = D['models']
PORTRAIT = {'lfm3': 'lfm3-1-7b', 'lfm3-vl': 'lfm3-vl-2b', 'lfm3-audio': 'lfm3-audio-2b', 'lfm3-omni': 'lfm3-omni-2b', 'd1': 'd1-2b'}
def model_name_link(m):
    return link_if('/ki-modelle/'+PORTRAIT[m['id']], m['name'])
rows = ''.join(
 '<tr><td data-l="Modell"><b>%s</b><br><small>%s</small></td><td data-l="Eingabe">%s</td><td data-l="Ausgabe">%s</td><td data-l="Wofür">%s %s</td></tr>'
 % (model_name_link(m), E(m['role']), E(m['in']), E(m['out']), E(m['for']), ref(m['src'])) for m in models)
EXTRA_ROW = '<tr><td data-l="Modell"><b>d1-Omni-2B</b><br><small>Entscheidungsmodell, Omni-Variante</small></td><td data-l="Eingabe">siehe Blog</td><td data-l="Ausgabe">siehe Blog</td><td data-l="Wofür">Sechstes Modell der Familie, auf Basis von LFM3-Omni-2B (Herstellerangabe). Hier nicht näher beschrieben. %s</td></tr>' % ref(['blog'])
rows += EXTRA_ROW
ollama = ''.join(
 '<li><b>%s</b>: <code>%s</code><br><small>%s %s</small></li>' % (E(m['name']), E(m['ollama']['cmd']), E(m['ollama']['status']), ref([m['ollama']['src']]))
 for m in models if m.get('ollama'))
pending = ', '.join(E(m['name']) for m in models if not m.get('ollama'))
FAQ = [
 ('Welches lokale Modell läuft gut auf einem normalen Rechner?',
  'Liquid AI baut die LFM3-Modelle für Geräte statt Rechenzentren: Das Textmodell LFM3-1.7B hat 1,73 Milliarden Parameter, seine 4-Bit-Gewichtsdatei ist laut Hersteller etwa 1 GB groß (nur die Datei). Ob es auf deinem Gerät flüssig läuft, hängt von Speicher, Chip und Software ab. Der Gerätecheck auf dieser Seite schätzt den Speicherbedarf mit offen gelegten Annahmen, er misst nichts.'),
 ('Was ist LFM3?',
  'LFM3 ist die dritte Generation der Liquid Foundation Models von Liquid AI: sechs Modelle der 2B-Klasse: Text, Bild, Audio, Omni und zwei Entscheidungsmodelle (d1 und d1-Omni), alle vom Backbone LFM3-1.7B-Base abgeleitet (Herstellerangabe).'),
 ('Was bedeuten q4_K_M, q8_0 und bf16?',
  'Es sind Speicherformate für die Gewichte eines Modells. Weniger Bits pro Gewicht heißt: kleinere Datei und weniger Speicherbedarf, aber meist etwas mehr Qualitätsverlust. bf16 ist das unkomprimierte 16-Bit-Format, q8_0 benutzt etwa 8 Bit, q4_K_M etwa 4 bis 5 Bit pro Gewicht.'),
 ('Wie viel Arbeitsspeicher brauche ich?',
  'Faustregel: Gewichte plus Kontext-Speicher (KV-Cache) plus etwas Laufzeit-Overhead, und das Betriebssystem braucht seinen Teil. Der Rechner auf dieser Seite zeigt die Rechnung und die Annahmen dahinter.'),
 ('Kann ich LFM3 mit Ollama starten?',
  'Die Ollama-Library listet lfm3, lfm3-vl, lfm3-audio, lfm3-omni und d1 (Tag d1:2b). Wir haben keinen dieser Pulls selbst ausgeführt. Ob eine bestimmte Funktion (zum Beispiel Video oder Sprachausgabe) in Ollama schon unterstützt wird, steht beim jeweiligen Modell in der Library.'),
 ('Sind die Benchmarks unabhängig geprüft?',
  'Die Zahlen auf dieser Seite stammen von Liquid AI. Wir haben sie nicht nachgemessen. Der Gerätecheck liefert keine Benchmarks und keine Tokens pro Sekunde, sondern nur eine Speicherschätzung.')]
FAQ_HTML = ''.join('<details class="faq"><summary>%s</summary><p>%s</p></details>' % (E(q), E(a)) for q, a in FAQ)
SOURCES = ''.join('<li id="q-%s"><a href="%s" rel="noopener">%s</a> · %s · abgerufen %s</li>' % (k, E(s['url']), E(s['title']), E(s['publisher']), E(s['accessed'])) for k, s in SRC.items())
MODEL_JSON = json.dumps([{k: m.get(k) for k in ('id', 'name', 'role', 'params_b', 'params_note', 'in', 'out', 'for', 'ctx', 'ctx_max', 'quants', 'extra_gb', 'extra_note')} for m in models], ensure_ascii=False)
BODY = f'''<main id="main"><div class="wrap lfm"><div class="art-head"><div class="kicker">Lokale Modelle · Liquid AI</div><h1>{E(TITLE)}</h1>
<p class="deck">LFM3 ist für Geräte gebaut, nicht für Rechenzentren. Hier steht, was die Familie kann, was Quantisierung bedeutet und ob dein Gerät mitkommt.</p>
<p class="byline"><a rel="author" href="{BASE}/redakteur/philipp-paulik">Philipp Paulik</a>, Redaktion KI Fachblatt · mit KI-Unterstützung erstellt, redaktionell verantwortet (<a href="/transparenz">so arbeiten wir</a>) · <time datetime="{STAND_ISO}">Stand {STAND}</time></p></div>
<section class="lfm-answer" aria-labelledby="kurz"><h2 id="kurz">Kurz gesagt</h2>
<p><b>LFM3</b> von Liquid AI ist eine Familie aus sechs Modellen der 2B-Klasse für Text, Bild, Audio und Entscheidungen. Das Textmodell hat 1,73 Milliarden Parameter. Seine 4-Bit-Gewichtsdatei ist laut Hersteller rund 1 GB groß {ref(['blog','card'])}. Das ist nur die Datei. Dazu kommen Speicher für den Kontext und die Software. Ob ein Modell auf deinem Gerät läuft, hängt von Modell, Format, Kontextlänge, Gesamtspeicher und Software ab. Der Gerätecheck unten schätzt den <b>Speicherbedarf</b> und legt jede Annahme offen. Eine Geschwindigkeit sagt er nicht voraus.</p></section>
<nav class="lfm-toc" aria-label="Inhalt"><a href="#familie">Die Familie</a><a href="#warum">Warum es flüssig läuft</a><a href="#quant">Quantisierung erklärt</a><a href="#erklaerer">Erklär-Simulator</a><a href="#check">Gerätecheck</a><a href="#start">Lokal starten</a><a href="#faq">Häufige Fragen</a><a href="#quellen">Quellen</a></nav>
<section id="familie"><h2>Die LFM3-Familie im Überblick</h2>
<p>Alle Modelle stammen von <b>{link_if('/unternehmen/liquid-ai','Liquid AI')}</b> und zweigen vom gemeinsamen Backbone LFM3-1.7B-Base ab {ref(['blog'])}. Ausführliche Analyse: <a href="/lfm3-liquid-ai-analyse">LFM3: Liquid AIs 2B-Familie für jede Modalität im Check</a>.</p>
<div class="lfm-tablewrap"><table class="lfm-table"><thead><tr><th>Modell</th><th>Eingabe</th><th>Ausgabe</th><th>Wofür</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="lfm-note">Alle Angaben sind Herstellerangaben. Ein Eintrag in einer Modellsammlung belegt nicht, dass jede Funktion in jeder Software läuft.</p></section>
<section id="warum"><h2>Warum LFM3 so flüssig laufen soll</h2>
<p>Drei Gründe nennt Liquid, und wir ordnen sie ein:</p>
<ol class="lfm-list"><li><b>Wenig Rechenarbeit pro Wort.</b> 13 der 24 Schichten sind kurze Faltungen, nur 5 Schichten nutzen Aufmerksamkeit mit kleinem Fenster (256 Token) und 6 volle Aufmerksamkeit {ref(['blog','card'])}. Je weniger volle Aufmerksamkeit, desto weniger wächst der Speicher mit langem Text.</li>
<li><b>Kleiner Kontext-Speicher.</b> Ein voller 128K-Kontext belegt laut Liquid 1,6 GB KV-Cache, bei Qwen3.5-4B sind es 4,3 GB {ref(['blog'])}. Der KV-Cache ist der Zwischenspeicher, in dem sich das Modell merkt, was schon gesagt wurde.</li>
<li><b>Auf echten Geräten entworfen.</b> Die Architektur wurde mit einer Suche entwickelt, die direkt auf 14 Geräte- und Software-Kombinationen misst, vom Samsung Galaxy S26 Ultra bis zum Raspberry Pi 5 {ref(['blog'])}.</li></ol>
<p class="lfm-note">Das sind Herstellerangaben. Wir haben keine eigenen Geschwindigkeitsmessungen gemacht und geben deshalb keine Tokens pro Sekunde für bestimmte Geräte an.</p></section>
<section id="quant"><h2>Quantisierung ohne Fachchinesisch</h2>
<p>Ein Modell besteht aus Milliarden Zahlen, den Gewichten. <b>Quantisierung</b> speichert jede Zahl mit weniger Bits. Das ist wie ein Foto mit weniger Farben: kleinere Datei, aber feine Unterschiede können verloren gehen. Wie stark sich das auswirkt, hängt von Modell, Format und Aufgabe ab. Eine allgemeingültige Rangliste für Qualität oder Tempo gibt es nicht.</p>
<div class="lfm-tablewrap"><table class="lfm-table"><thead><tr><th>Format</th><th>Ungefähr Bit pro Gewicht</th><th>In einfachen Worten</th></tr></thead><tbody>
<tr><td data-l="Format"><b>bf16</b></td><td data-l="Bit">16</td><td data-l="Erklärung">Unkomprimiert (16 Bit). Größte Datei und höchster Speicherbedarf.</td></tr>
<tr><td data-l="Format"><b>q8_0</b></td><td data-l="Bit">ca. 8,5</td><td data-l="Erklärung">Etwa halb so groß wie bf16. Der Qualitätsverlust ist oft klein, hängt aber von Modell und Aufgabe ab.</td></tr>
<tr><td data-l="Format"><b>q4_K_M</b></td><td data-l="Bit">ca. 4,8</td><td data-l="Erklärung">Verbreiteter Kompromiss: etwa ein Drittel der Größe von bf16, mit Qualitätsverlust, der von Modell und Aufgabe abhängt.</td></tr>
<tr><td data-l="Format"><b>q4_0</b></td><td data-l="Bit">ca. 4,5</td><td data-l="Erklärung">Einfaches 4-Bit-Format, ältere Bauart. Bei LFM3-1.7B ist die q4_0-Datei laut Hugging Face allerdings der QAD-Checkpoint (siehe nächste Zeile).</td></tr>
<tr><td data-l="Format"><b>qad-q4_0</b></td><td data-l="Bit">ca. 4,5</td><td data-l="Erklärung">Ein q4_0-Modell, das mit „Quantization-Aware Distillation“ (QAD) nachtrainiert wurde, damit beim Runterrechnen weniger Qualität verloren geht. Die q4_0-Datei von LFM3-1.7B ist laut Hugging Face-README dieser QAD-Checkpoint. {ref(['ollama-lfm3','hf-gguf'])}</td></tr>
<tr><td data-l="Format"><b>mxfp8, nvfp4, mlx-bf16</b></td><td data-l="Bit">8 / 4 / 16</td><td data-l="Erklärung">Weitere Tags in der Ollama-Library. „MLX“ ist Apples Framework für Apple-Chips, kein Rundungsverfahren. „MX“ steht für Microscaling: Kleine Gruppen von Zahlen teilen sich einen gemeinsamen Skalierungsfaktor. mxfp8 und nvfp4 sind Gleitkomma-Formate mit 8 beziehungsweise 4 Bit. Ob deine Software sie kann und ab welcher Version, musst du vorher prüfen. {ref(['ollama-lfm3'])}</td></tr></tbody></table></div>
<p class="lfm-note">Bit-Werte sind gerundete Näherungen aus der llama.cpp-Dokumentation {ref(['llamacpp-quant'])}. Die echte Dateigröße weicht ab, weil nicht alle Teile eines Modells gleich stark komprimiert werden.</p></section>
<section id="erklaerer"><h2>Erklär-Simulator: welches Modell, welches Format?</h2>
<p>Wähle ein Modell und ein Format. Dateigrößen von LFM3-1.7B stammen aus den Repositories, Bit-Werte sind Näherungen.</p>
<div id="lfm-explain" class="lfm-card"><noscript>Für den Simulator wird JavaScript benötigt. Die Tabellen oben enthalten die gleichen Angaben als Text.</noscript></div></section>
<section id="check"><h2>Gerätecheck: läuft das auf meinem Gerät?</h2>
<p>Das ist eine <b>Speicherschätzung</b>, keine Messung. Du siehst, wie viel Speicher ein Modell mit Kontext ungefähr braucht und ob dein Gerät genug frei hat. Zur Geschwindigkeit geben wir bewusst keine Zahl an: Sie hängt von Chip, Software und Einstellungen ab und lässt sich seriös nur auf deinem Gerät messen.</p>
<div id="lfm-check" class="lfm-card"><noscript>Für den Gerätecheck wird JavaScript benötigt.</noscript></div></section>
<section id="start"><h2>Lokal starten</h2>
<p>Liquid nennt Unterstützung für die Programme llama.cpp, MLX, vLLM und SGLang sowie das ONNX-Format. GGUF ist dabei das Dateiformat, das llama.cpp und Ollama lesen {ref(['blog','hf-gguf'])}. Versionen zählen: Laut den Hugging Face-Hinweisen braucht LFM3 ein aktuelles llama.cpp (ab Build b11960) und Ollama ab Version 0.40.12, je nach Plattform 0.40.13. Die NVFP4-Dateien laufen erst ab llama.cpp b12088, ältere Builds liefern laut README falsche Ausgaben. Prüfe die Version, bevor du ein Format ausprobierst.</p>
{('<ul class="lfm-list">'+ollama+'</ul>') if ollama else ''}
<p class="lfm-note">Ein Eintrag in der Ollama-Library heißt nicht, dass jede Funktion (zum Beispiel Video oder Sprachausgabe) dort schon läuft. Für d1-Omni-2B geben wir hier keine Startanleitung an. Einen eigenen Test haben wir nicht durchgeführt.</p></section>
<section id="grenzen"><h2>Grenzen dieser Seite</h2><ul class="lfm-list"><li>Keine eigenen Benchmarks. Herstellerzahlen bleiben Herstellerzahlen.</li><li>Der Gerätecheck kennt dein Gerät nicht. Er rechnet mit Klassenwerten, die du ändern kannst.</li><li>Bilder, Video und Audio brauchen zusätzlichen Speicher, den die Schätzung nicht abbildet.</li><li>Die LFM Open License v1.0 begrenzt kommerzielle Nutzung. Lies den Lizenztext, bevor du ein Modell einsetzt.</li></ul></section>
<section id="faq"><h2>Häufige Fragen</h2>{FAQ_HTML}</section>
<section id="quellen"><h2>Quellen</h2><ol class="lfm-src">{SOURCES}</ol><p class="lfm-note">Weiterlesen: <a href="/lokale-modelle">Lokale Modelle: Wann sich der eigene Rechner lohnt</a> · <a href="/llm-kostenrechner">LLM-Kostenrechner</a> · <a href="/llm-quantisierung-verfahren-grundlagen">Quantisierung im Detail</a> · <a href="/inferenz-und-kosten-verstehen">Inferenz und Kosten</a> · <a href="/glossar#quantisierung">Glossar: Quantisierung</a> · <a href="/glossar#kv-cache">Glossar: KV-Cache</a></p>
<p class="lfm-note">Stand {STAND}. Erstellt mit KI-Unterstützung, redaktionell verantwortet.</p></section></div></main>
<script>window.LFM_MODELS={MODEL_JSON};</script><script src="/assets/lfm/lfm.js" defer></script>'''
ld = {"@context": "https://schema.org", "@graph": [
 {"@type": "Organization", "@id": BASE+"/#org", "name": "KI Fachblatt", "url": BASE+"/", "logo": {"@type": "ImageObject", "url": BASE+"/assets/logo-512.png"}},
 {"@type": "WebSite", "@id": BASE+"/#site", "url": BASE+"/", "name": "KI Fachblatt", "inLanguage": "de-DE", "publisher": {"@id": BASE+"/#org"}},
 {"@type": "Article", "@id": BASE+"/lfm#article", "headline": TITLE, "description": DESC, "inLanguage": "de-DE", "datePublished": STAND_ISO, "dateModified": STAND_ISO,
  "author": {"@type": "Person", "name": "Philipp Paulik", "url": BASE+"/redakteur/philipp-paulik"}, "publisher": {"@id": BASE+"/#org"}, "image": BASE+"/assets/lfm/lfm-social-20261107.jpg", "mainEntityOfPage": BASE+"/lfm"},
 {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Start", "item": BASE+"/"}, {"@type": "ListItem", "position": 2, "name": "LFM lokal", "item": BASE+"/lfm"}]},
 {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}]}
t = (ROOT/'lokale-modelle.html').read_text()
rep = lambda pat, val, s: re.sub(pat, lambda m: m.group(1)+val+(m.group(2) if m.lastindex and m.lastindex > 1 else ''), s, 1, re.S)
t = re.sub(r'<title>.*?</title>', lambda m: '<title>%s | KI Fachblatt</title>' % E(TITLE), t, 1, re.S)
t = rep(r'(<meta name="description" content=")[^"]*', E(DESC), t)
t = rep(r'(<link rel="canonical" href=")[^"]*', BASE+'/lfm', t)
t = rep(r'(<meta property="og:title" content=")[^"]*', E(TITLE), t)
t = rep(r'(<meta property="og:description" content=")[^"]*', E(DESC), t)
t = rep(r'(<meta property="og:url" content=")[^"]*', BASE+'/lfm', t)
t = t.replace('https://kifachblatt.de/assets/kifachblatt-og.png', BASE+'/assets/lfm/lfm-social-20261107.jpg')
t = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda m: '<script type="application/ld+json">'+json.dumps(ld, ensure_ascii=False)+'</script>', t, 1, re.S)
t = t.replace('</head>', '<link rel="stylesheet" href="/assets/lfm/lfm.css"></head>', 1)
t = re.sub(r'<main id="main">.*?</main>', lambda m: BODY.split('</main>')[0]+'</main>', t, 1, re.S)
t = t.replace('</body>', BODY.split('</main>')[1]+'</body>', 1)
(ROOT/'lfm.html').write_text(t)
print('lfm.html written', len(t))

# sitemap + site search (idempotent; build.py keeps existing sitemap entries)
sp = ROOT/'sitemap.xml'
sm = sp.read_text()
sm = re.sub(r'<url><loc>'+re.escape(BASE)+r'/lfm</loc>.*?</url>\n?', '', sm, flags=re.S)
entry = ('<url><loc>%s/lfm</loc><lastmod>%s</lastmod><image:image><image:loc>%s/assets/lfm/lfm-social-20261107.jpg</image:loc></image:image></url>\n' % (BASE, STAND_ISO, BASE))
sm = sm.replace('</urlset>', entry+'</urlset>', 1); sp.write_text(sm)
ip = ROOT/'search-index.json'
if ip.exists():
    pl = json.loads(ip.read_text())
    pl['docs'] = [x for x in pl['docs'] if x.get('u') != '/lfm'] + [{'t': 'LFM lokal ausführen: Gerätecheck und Quantisierung erklärt', 'u': '/lfm', 'k': 'Modelle', 'd': DESC, 'g': 'LFM3 Liquid AI lokal Ollama Quantisierung Gerätecheck', 'x': DESC, 'ts': 0, 'dt': '07.11.2026'}]
    ip.write_text(json.dumps(pl, ensure_ascii=False, separators=(',', ':')))
print('sitemap + search updated')
