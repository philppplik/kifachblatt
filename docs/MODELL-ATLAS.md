# Modell-Atlas (Prototyp)

Stand: 20.10.2026. Status: Prototyp, nicht freigegeben, nicht live. Datenbank-Seite /modell-atlas mit
Detailseiten je Modell plus Beispiel-PDF des geplanten Modell-Radars (berichte/prototyp-modell-radar.pdf).

## Daten

`content/modell-atlas.json` (schema_version 1): `sources` (HTTPS-URL + Pruefdatum), `providers`
(Datenschutz-Steckbrief mit Status `geprueft` oder `in_pruefung`), `models` (Zugang, Lizenz, Preis,
Benchmark-Belege, Quellen je Eintrag).

Regeln (werden von `tools/modell_atlas.py` validate() und `tests/test_modell_atlas.py` erzwungen):

- Jede Zahl (Preis, Kontext, Benchmark) hat einen Quellen-Schluessel; jede Quelle hat HTTPS-URL und
  Pruefdatum (ISO). Keine Fakten ohne Quelle.
- Preise nur, wenn an der Anbieter-Primärquelle geprueft: Betrag, Waehrung (USD), Einheit, Tarif und
  Hinweistext sind Pflicht. Fehlende Preise werden als "nicht gepflegt" angezeigt, nie geschaetzt.
- Datenschutz-Aussagen nur mit Status `geprueft` samt Quellen; sonst sichtbar "in Pruefung".
- Benchmarks bleiben Herstellerangaben (reported_by Pflicht), keine eigenen Messungen, keine Rangliste.
- Keine Fremdlogos: Modelle bekommen Monogramme (initials).

## Render

`python3 tools/modell_atlas.py .` (in build.py nach den Portraits eingehängt). Schreibt
`modell-atlas.html`, `modell-atlas/<slug>.html`, `assets/modell-atlas.css/.js`, ergänzt Sitemap und
Suchindex idempotent und verlinkt Atlas in Navigation und Footer. Keine Netzaufrufe beim Rendern.

`python3 tools/modell_radar.py .` rendert die Beispiel-PDF (Layout aus report_core, Chrome-Druck).

## Pflegeprozess (Vorschlag)

- Woechentlich: Preise der gepflegten Modelle an den Anbieter-Preisseiten gegenpruefen, `accessed`
  aktualisieren, Build, Tests, Commit.
- Taeglich laeuft nur der bestehende Tagesbericht-Workflow; der Atlas wird nicht automatisch mit
  Live-Daten beschrieben (kein Scraping; siehe Recherche: OpenRouter-ToS verbieten Wettbewerbsnutzung,
  Artificial Analysis ist proprietär).
- Neu: Modell aufnehmen = Eintrag mit Quellen, validate + Tests grün, mobil pruefen (320/390 px),
  dann committen. Snapshot-Prinzip der Porträts (unveränderliche Snapshots) bleibt Vorbild.

## Bekannte Grenzen des Prototyps

- 18 Seed-Modelle aus dem Porträtbestand; 8 mit gepflegtem Preis, 3 Anbieter mit geprueftem
  Datenschutz-Steckbrief. Erweiterung ist Pflegearbeit an Primärquellen, kein Codeproblem.
- Kontextfenster nur dort befuellt, wo das Porträt-Datenmodell sie hergibt.
- EUR-Umrechnung bewusst nicht im Prototyp (Wechselkurs wäre eine weitere zu pflegende Quelle mit Datum).

## Pflegedurchlauf 2 (20.10.2026)

- Preise aus Primaerquellen nachgepflegt: Mistral (Small 4: 0,15/0,6 $; Large 3: 0,5/1,5 $),
  MiniMax (M3: 0,3/1,2 $ Promo; M3.1 Flash: 0,15/0,6 $; M2.7/M2.5/M2.1: je 0,3/1,2 $),
  Meta Muse Spark (1,25/4,25 $ Standard-Modus), DeepSeek-V4-Flash-Vision-Exp (eingestellt,
  Flash-Tarif). GPT-6 Astra und Claude Opus 5.5 an den offiziellen Modellseiten re-verifiziert
  (10/50 $ bzw. 4/20 $); beide fehlen auf den Marketing-Uebersichtsseiten, haben aber eigene
  Dokumentationsseiten mit Preis.
- Kontextfenster aus Primaerquellen: 15/18 (Claude/Gemini/DeepSeek/Meta/MiniMax M3+M3.1F 1M,
  Mistral 256k, Nemotron 1M). Ohne offizielle Angabe: MiniMax M2.x (Legacy).
- Datenschutz-Steckbriefe jetzt fuer alle 8 Anbieter geprueft (Mistral Opt-out-Modell,
  DeepSeek Training + Speicherung VR China, MiniMax Singapur/US, Meta Standard- vs.
  Contributor-Modus, NVIDIA NIM-Telemetrie abschaltbar).
- KPI-Stand: Preis 17/18 (94 %), Kontext 15/18 (83 %), Lizenz 100 %, Datenschutz 100 %,
  Quellen-Abdeckung 100 %, Aktualitaet 0-1 Tag.

## Pflegedurchlauf 3 (22.10.2026) — Benchmark-Substantiierung

- Benchmark-Belege von 3 auf 16 von 18 Modellen erweitert (7 auf 56 Eintraege). Alle Werte sind Herstellerangaben aus Primaerquellen (Modellkarten, Ankuendigungen, Systemkarten), am 22.10. erneut geoeffnet; Abrufdatum der verwendeten Quellen entsprechend aktualisiert.
- Neue Quellen: OpenAI-Ankuendigung GPT-6 Astra, Anthropic-Ankuendigung Claude Opus 5.5, Anthropic System Card Claude Sonnet 5 (PDF).
- Setup-Kontext je Eintrag in der Variante (z. B. Harness, Effort-Stufe, "mit/ohne Werkzeuge", Partial Score). Keine eigenen Messungen, keine uebernommenen Fremdvergleiche: Werte anderer Anbieter aus Hersteller-Vergleichstabellen wurden NICHT uebernommen (Ausnahme belegt: DeepSeek V4-Pro Terminal-Bench 2.1 aus der V4.1-Flash-Modellkarte, gleicher Anbieter und gleiches Setup).
- Bewusst ohne Beleg: Mistral Small 4 und Mistral Large 3 (keine Werte zu den zehn portraitierten Benchmarks in den Primaerquellen); Werte abweichender Benchmark-Versionen (z. B. Terminal-Bench 4.0/2.0) wurden nicht auf das portraitierte Terminal-Bench 2.1 gebucht.
- Renderer: Anzeigenamen fuer alle zehn portraitierten Benchmarks (BENCH_NAMES) ergaenzt.
