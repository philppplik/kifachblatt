# LLM-Kostenrechner (Produkt 3: kostenloses Tool als SEO- und Lead-Magnet)

**Stand: 20.10.2026 · Status: Prototyp, NICHT live · Branch: tool/llm-kostenrechner**

Kostenloses, rein clientseitiges Vergleichstool für LLM-API-Preise unter `/llm-kostenrechner`.
25 Modelle, 6 Anbieter (OpenAI, Anthropic, Google, Mistral, DeepSeek, xAI), alle Preise aus
Primärquellen mit Abrufdatum. Ziel: SEO-Rankings auf Kosten-Keywords ("LLM API Kosten",
"GPT vs Claude Preis", "Token Kosten Rechner"), Vertrauen, später E-Mail-Einsammlung
(Lead-Magnet-Mechanik kommt mit dem Pro-Konzept, nicht Teil dieses Prototyps).

## 1. Legal-Check (vorab, Ergebnis: frei zum Bauen)

- **Kein Verkauf → kein Kaufrecht.** Kein Checkout, keine Preise, kein Widerruf, keine AGB-Pflichten,
  kein Zahlungsanbieter. Gewerbe-Frage bleibt unberührt, solange das Tool kostenlos ist.
- **Preisdaten sind Fakten.** Einzelne Preise unterliegen keinem Urheberrecht. Wir übernehmen keine
  fremden Tabellenlayouts, Texte oder Datensätze Dritter (kein Scraping von Artificial Analysis o. ä.);
  jeder Wert stammt aus der Primärquelle des Anbieters, mit URL + Abrufdatum im JSON und auf der Seite.
- **Marken:** Nur beschreibende Namensnennung, keine Logos, Disclaimer auf der Seite
  ("Keine Verbindung zu den genannten Anbietern; alle Marken gehören ihren Inhabern").
- **Richtigkeit/Haftung:** Stand-Angabe + "alle Angaben ohne Gewähr" + Verweis auf die Anbieter-Seite
  als verbindliche Referenz; keine Kauf-/Anbieterberatung. Entspricht der Site-Footer-Logik.
- **AI Act / KI-Kennzeichnung:** "Erstellt mit KI-Unterstützung. Preise aus Anbieter-Preislisten, Stand 20.10.2026" steht im
  Methodik-Block; Site-weite Transparenzseite verlinkt.
- **DSGVO:** 100 % clientseitig, genau ein `fetch` auf die eigene Preis-JSON, kein localStorage,
  keine Cookies, kein Server-Call mit Nutzereingaben (Test `test_datenschutz_versprechen_deckt_umsetzung`
  wacht darüber). Szenario-Sharing läuft über den URL-Hash (keine Server-Speicherung).
  Go-Live-To-do: einen Satz zum Tool in /datenschutz ergänzen (auch ohne Pflicht: Transparenz).
- **Keine Provider-ToS-Probleme:** Daten werden redaktionell kuratiert, nicht zur Laufzeit gescraped;
  das Tool ruft keine Anbieter-APIs auf.

## 2. Datenmodell (`data/llm-api-preise.json`)

Ein JSON, ein Stand pro Anbieter, pro Modell Listpreise des Standard-Tarifs in USD/1M Tokens:

- `providers[]`: id, name, stand, `source{url, retrieved}`, `batch_discount` (0.5 bei OpenAI,
  Anthropic, Google, Mistral; null bei DeepSeek/xAI), `offpeak` (DeepSeek-Faktor 0.5 + Zeiten), `notes[]`.
- `models[]`: id, name, tier, entweder flach (`input`, `cached_input`, `output`) oder `tiers[]`
  mit `max_input_tokens` (xAI/Google: 200K-Staffel, wird automatisch nach Eingabegröße gewählt),
  optional `offpeak{}` (DeepSeek), `context`, `scheduled{date, input, output, note}` für
  angekündigte Preisänderungen (aktuell: Gemini 4 Argon 1.12.2026; Gemini 3.8/3.6 Flash 1.1.2027).
- `fx`: EZB-Referenzkurs USD/EUR mit Stand (EUR-Anzeige ist Umrechnung, Abrechnung bleibt USD).

## 3. UX-Konzept (form follows function)

- **Links Eingabe, rechts Ergebnis** (mobil: Eingabe zuerst, gestapelt). Sticky Panel am Desktop.
- **Presets** für die vier Kern-Workloads (Chat-Support, RAG, Coding-Agent, Zusammenfassungen) +
  individuell; jede Zahl editierbar.
- **Cache-Trefferquote** als Slider (RAG/Agenten zahlen real weniger für Eingabe); **Batch-Schalter**
  (50 % wo verfügbar); **DeepSeek-Nebenzeit-Schalter** (halbe Preise außerhalb Peak-Zeiten).
- **Ergebnis:** Bestwert-Kasten (günstigstes Modell pro Anfrage/Monat), Balken-Chart Top 12
  (Rich Media, CSS-only), Volltabelle mit Stück- und Monatskosten, Banner "Angekündigte
  Preisänderungen" aus `scheduled`-Daten.
- **Teilbarkeit:** kompletter Zustand im URL-Hash → "Szenario-Link kopieren" (Social/Newsletter-tauglich).
- **SEO/AEO:** eigener URL ohne Extension, Title/Description, WebApplication- + FAQPage-JSON-LD,
  Methodik- und Quellen-Block (E-E-A-T), interne Links auf die vier Kosten-Artikel, FAQ.
- **Währung:** USD (Abrechnungswährung) mit EUR-Umrechnung per EZB-Kurs.

## 4. QA-KPIs

Automatisiert in `tests/test_llm_kostenrechner.py` (15 Tests, stdlib):

| KPI | Ziel | Messung |
|---|---|---|
| K1 Datenherkunft | 100 % der Modelle mit Primärquelle + Abrufdatum | Test: jeder Provider hat source.url + retrieved |
| K2 Frische | Datenstand ≤ 14 Tage | Test schlägt fehl, wenn retrieved älter (Pflege-Alarm) |
| K3 Rechenlogik | 5 Referenzrechnungen exakt (Basis, Cache, Batch, Off-Peak, Staffel) | node-Cross-Check der JS-Logik |
| K4 Plausibilität | 0 < input ≤ 100 $, 0 < output ≤ 200 $, cached < input, offpeak = 50 % | Schema-Test |
| K5 Pflichtangaben | Quellenblock, Stand, Disclaimer, Markenhinweis, EZB-Kurs auf der Seite | String-Tests |
| K6 Datenschutz | 1 fetch (eigene JSON), kein localStorage/Cookie, kein Drittanbieter-Code | Static-Checks auf JS/HTML |
| K7 Mobil & a11y | Breakpoint 900px, reduced-motion, aria/role, Fokus sichtbar | CSS/HTML-Checks + Sichtprüfung |
| K8 SEO | JSON-LD (WebApplication + FAQPage), Description 60–200 Zeichen | Test |

Manuell (vor jedem Go-Live): Screenshot Desktop 1440px + Mobil 390px prüfen, Consent-Overlay-Verhalten,
Szenario-Link in neuem Tab öffnen.

Produkt-KPIs nach Go-Live (GA4, erst nach Baseline): Tool-Pageviews/Woche, Interaktionsrate
(Preset-/Slider-Events), Szenario-Link-Kopien, Klickrate auf Kosten-Artikel, später
Newsletter-Anmeldungen von der Tool-Seite. Zielvorgabe nach 4 Wochen Datenlage setzen.

## 5. Pflegeprozess Preisupdates

- **Kadenz:** alle 14 Tage die 6 Quell-URLs prüfen (K2-Test wird sonst rot). Aufwand ca. 20 Min.
- **Ereignis-getrieben:** angekündigte Änderungen sind in `scheduled` hinterlegt — die Seite warnt
  automatisch; am Stichtag Werte umstellen und `scheduled` entfernen. Aktuell bekannt:
  1.12.2026 (Gemini 4 Argon), 1.1.2027 (Gemini 3.8/3.6 Flash), 1.11.2026 (DeepSeek Search/Fetch-Billing,
  betrifft Tool nicht). Empfehlung: Instinct-Wake auf 30.11.2026 und 29.12.2026.
- **Update-Ablauf:** Quelle abrufen → Werte in `data/llm-api-preise.json` ändern → `retrieved`/`stand`
  bzw. `fx` hochsetzen → `python3 tests/test_llm_kostenrechner.py` (muss grün) → Screenshot-Check →
  Commit (Author: Philipp Paulik <noreply>, kein Agent-Trailer) → Eintrag ins Changelog unten.
- **Neues Modell aufnehmen:** nur mit Primärquelle; flaches Modell oder `tiers`; bei neuem
  Rabatt-Mechanismus Datenmodell erweitern, nicht tricksen.
- **Qualitätsregel:** kein Wert ohne Quelle + Datum; bei widersprüchlichen Angaben (Landing vs. Doku)
  gilt die Entwickler-Doku und ein `notes`-Eintrag dokumentiert das.

## 6. Go-Live-Checkliste (nach Philipps Go)

1. Sitemap: URL in sitemap.xml aufnehmen (build.py integriert generierte Seiten — Eintrag analog
   der statischen Seiten), news-sitemap NICHT (kein News-Content).
2. Navigation/Einstiege: Link aus `api-preise-vergleichen.html`, `tokens-und-kosten.html`,
   `kosten-pro-aufgabe-messen.html`, `kosten-latenz-tuning.html` (Kasten "Tool: LLM-Kostenrechner");
   optional Startseiten-Card; Footer-Spalte "Lesen" um "LLM-Kostenrechner" ergänzen.
3. /datenschutz: ein Satz zum Tool (clientseitig, keine Übertragung).
4. Screenshot-Check nach Deploy (1440/390), Klicktest Szenario-Link, GA4-Ereignisse prüfen.
5. GSC: Indexierungs-Anfrage für /llm-kostenrechner (Tageslimit beachten).

## 7. Changelog

- 2026-10-20: Erstversion. 25 Modelle / 6 Anbieter, Primärquellen vom 20.10.2026, EZB-Kurs 19.10.2026.
- 2026-10-20 (Fix): Mobiler Überlauf behoben (Grid-Item min-width:0 / minmax(0,1fr) — die Tabelle im
  Scroll-Wrapper trieb sonst die Spalte auf ~805px); Range-Slider bekam eigenes Track-/Thumb-Styling
  (das globale input-Styling der Seite hatte ihn als weiße Pille gerendert); Select auf max-width:100%.
  Verifiziert per Screenshot bei 320/390/768/1440px. Hinweis zur Messung: Headless-Chrome erzwingt
  mindestens 500px Fensterbreite — 320/390 über iframe-Harness geprüft.
