# Startseite: redaktionelle Karten und Datenblick

Die frühere Analysentabelle ist ein responsives Kartenraster mit einer doppelt breiten Lead-Karte. Vorhandene Diagramm-Thumbnails werden vollständig gezeigt, nicht abgeschnitten. Die sechs älteren Grundlagenbeiträge bleiben über content/home-legacy.json enthalten; die vier aktuellen Analysen kommen aus dem bestehenden Artikeldatenmodell. Textsuche und Themenfilter bleiben lokal.

Datenblick: drei SVG-Balkendiagramme aus der aktuellen Nemotron-Analyse. Primärquelle live geprüft am 19.10.2026: https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Super-and-Lightning/

- Einzellauf vs. Parallelität/Selbstverifikation: Terminal-Bench 2.1 62,7/71,9; DeepSWE 24,6/34,5; BrowseComp 71,5/79,8 Prozent.
- RULER-1M vor/nach Erholung: 33,5/81,0. Zusätzliche Erholungsstufe mit 9 Mrd. Token.
- Akzeptanzlänge vor/nach MTP-Boosting: Greedy 4,287/4,718; probabilistisches Sampling 3,787/4,612 Token pro Schritt.

Herstellerangaben sind direkt am Chart als solche markiert, keine eigene Messung, keine unabhängige Rangliste und kein Vergleich unterschiedlicher Modelle. Achsen beginnen bei null. Textbeschreibung, Legenden und aufklappbare exakte Werte ergänzen die SVGs. Keine Preis-/Zeitreihen erfunden. Kein externer Request, keine Dependency, kein Chart-Paket.

Geometrie wird im HTML/CSS reserviert: SVG viewBox, Bildmaße und aspect-ratio. Browserprüfung Desktop/Mobile: Filter und Nulltreffer, kein Überlauf; lokal CLS 0 einschließlich Consent-Ablehnen. Kein Lighthouse-Gesamtscore behauptet. Build ruft tools/home_editorial.py anstelle der alten Tabellen-Ersetzung auf. Wiederholtes Rendern erzeugt keine doppelten Abschnitte.
