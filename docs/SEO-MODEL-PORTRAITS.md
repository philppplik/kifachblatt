# Modellporträts: Suchintention, Semantik und Indexierung
Stand: 19.10.2026. Untersuchte Namen: GPT-6 Astra, Claude Opus 5.5, Claude Fable 5.1. Die Eingaben „Atsra“ und „Flable“ sind Tippfehler, keine zusätzlichen Modelle und keine separaten SEO-Seiten.

## Befund aus aktuellen Suchergebnissen
Live-Suchanfragen: „GPT-6 Astra Preis Kontextfenster API deutsch“, „Claude Opus 5.5 Preis API Kontext deutsch“, „Claude Fable 5.1 vs Opus 5.5 API Preis deutsch“. Ergebnisbeobachtung, keine Suchvolumenmessung: offizielle Herstellerseiten dominieren die gefundenen Treffer; ergänzend erscheinen API-Einstiege und Modellvergleiche. Daraus lässt sich keine Position in Google, kein Keywordvolumen und keine garantierte Chance auf Platz 1 ableiten. Keine Keyword-Stuffing-Seiten für Tippfehler.

Beobachtete Beispiele:
- https://openai.com/de-DE/index/gpt-6-astra/
- https://developers.openai.com/api/docs/models/gpt-6-astra
- https://apidog.com/de/blog/gpt-6-astra-api/
- https://felloai.com/de/gpt-6-astra-benchmarks-preis/
- https://platform.claude.com/docs/de/models/opus-5-5/overview
- https://www.datacamp.com/de/tutorial/opus-5-5-api-tutorial
- https://www.gradually.ai/llm-vergleich/claude-opus-5.5-vs-claude-fable-5.1/
Diese Treffer werden nur zur Intent-Einordnung verwendet, nicht als Beleg für Modellfakten.

## Keyword- und Fragen-Cluster
| Zielseite | Hauptbegriff | Ergänzende Intentionen | Antwortabschnitte |
| --- | --- | --- | --- |
| Astra | GPT-6 Astra | GPT-6 Astra API, Preis, Kosten, Kontextfenster, Reasoning, Bilder, Open Weight | Direkte Definition, Tokenlimits, Standard- und Long-Context-Preise, Modalitäten, Werkzeuge |
| Opus | Claude Opus 5.5 | Opus 5.5 API, Preis, Kontext, Thinking, Migration, Fable Vergleich | Definition, synchron/Batch getrennt, Always-on-Thinking, Tool-/Streaming-Änderungen |
| Fable | Claude Fable 5.1 | Fable 5.1 API, Kosten, Kontext, Opus Unterschied, Mythos Unterschied | Definition, Preisbedingungen, Thinking-Verlauf, Beta-Funktionen, Zugangstrennung |

Keine erfundenen Suchvolumina, CTRs oder Keyword-Difficulty-Scores. Ohne GSC-Daten ist Priorisierung qualitativ. Nach Veröffentlichung tatsächliche Suchanfragen, Impressionen, Klicks und Positionen je URL in GSC beobachten, bevor weitere Keywordentscheidungen getroffen werden.

## Umsetzung
- Korrekte Namen und spezifische Seitentitel, nicht nur „Portrait“.
- Direkte kurze Antwort am Anfang, klare H2-Fragen und Sprungnavigation.
- Eigene Kontext-/Ausgabevisualisierung mit Textalternative und exakten Werten.
- Preise mit Einheit, Stand, Basisrate und sichtbaren Ausnahmen statt vereinfachtem Gesamtpreis.
- Sichtbare FAQ mit denselben Antworten im FAQPage-JSON-LD. FAQ-Markup garantiert kein Rich Result; diese Magazine sollten keine FAQ-Sonderdarstellung erwarten.
- Article und BreadcrumbList, eigene Canonical-URL, Beschreibung, indexierbare statische Inhalte, lokale interne Links von Modell-/Anbieterverzeichnis, Sitemap und Suchindex.
- IW betont praktische Modellwahl; KIFB technische Grenzen und Migration. Gemeinsame offizielle Fakten dürfen identisch sein, redaktionelle Haupt-Einordnung unterscheidet sich. Keine Cross-Domain-Canonicals, die eine der beiden gewünschten Seiten aus dem Index drängen würden.
- Keine erfundenen Ratings, Reviews, Vergleichs-Benchmarks oder „beste KI“-Behauptungen. Keine neue Dependency, keine versteckten SEO-Texte, keine Metakeyword-Liste.

## GSC: nach dem Deployment, nicht vom lokalen Patch aus
1. Auf beiden verifizierten Domain-Properties Zugriff prüfen und die nachstehend genannten Live-URLs öffnen.
2. HTTP 200, selbstreferenzierende Canonical, kein noindex und keine robots-Sperre live prüfen.
3. Aktuelle Sitemap https://kifachblatt.de/sitemap.xml und https://intelligenz-welt.de/sitemap.xml prüfen und bei Bedarf in GSC einreichen; bereits vorhandene Einreichung nicht duplizieren.
4. URL-Prüfung für alle sechs Modellseiten; Live-Test, dann Indexierung beantragen, soweit GSC es anbietet. Keine Nutzung der Google Indexing API für normale Modellartikel, kein automatisierter Quoten-Bypass.
5. Indexierungsstatus und Suchleistung später prüfen. Eine beantragte Indexierung ist keine Indexbestätigung, keine Rankinggarantie.

Gewünschte Ziel-URLs, im lokalen Renderer exakt so erzeugt (noch nicht live bestätigt):
https://kifachblatt.de/ki-modelle/gpt-6-astra
https://kifachblatt.de/ki-modelle/claude-opus-5-5
https://kifachblatt.de/ki-modelle/claude-fable-5-1
https://intelligenz-welt.de/ki-modelle/gpt-6-astra/
https://intelligenz-welt.de/ki-modelle/claude-opus-5-5/
https://intelligenz-welt.de/ki-modelle/claude-fable-5-1/

## Primärquellen für alle neuen Modellfakten
- https://developers.openai.com/api/docs/models/gpt-6-astra
- https://platform.claude.com/docs/en/models/opus-5-5/overview
- https://platform.claude.com/docs/en/models/fable-5-1/overview
Alle drei vollständig gelesen, Stand 19.10.2026. Eigene Redaktionstexte und strukturierte Daten lokal im unveränderlichen Snapshot-Archiv, keine fremden Dokumentations-Volltexte veröffentlicht.

Google-Regeln live geprüft: https://developers.google.com/search/blog/2023/08/howto-faq-changes und https://developers.google.cn/search/apis/indexing-api/v3/using-api . FAQ-Rich-Results nur eingeschränkt, Indexing-API nicht für diese Artikel.
