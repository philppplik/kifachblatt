# Portrait-PDFs

Alle Unternehmens- und Modellportraits erhalten einen echten PDF-Download sowie eine Druckansicht. Die bestehende report_core/to_pdf-Pipeline mit installiertem Chrome erzeugt die PDFs beim normalen Build. Keine neue Abhängigkeit und kein Netzwerkabruf. Inhalte, Fakten, Preise, Warnhinweise, Diagramme, FAQs und Quellen stammen aus demselben Markup wie das Webportrait. Alle FAQ-Antworten sind im PDF geöffnet. Lokale Logos sind eingebettet, Marken-/Rechtehinweise bleiben sichtbar. Jeder Export nennt seinen Quellenstand und die Webfassung.

Dateien: /portrait-pdf/unternehmen-SLUG.pdf und /portrait-pdf/ki-modelle-SLUG.pdf, daneben .html-Druckansichten. Die Druckansichten sind noindex und canonicalisieren auf das zugehörige Webportrait. Content-SHA256-Sidecars vermeiden unnötige Chrome-Aufrufe bei identischen Inhalten. Bei Änderung wird neu gerendert. Bei Fehler wird ein veraltetes PDF gelöscht, kein Downloadbutton angeboten und stattdessen die funktionierende Druckansicht erklärt. Kein leeres/falsches PDF als Erfolg. Die vorhandene 5-MB-Gültigkeitsprüfung bleibt bestehen.

IW baut nach site/out; kein Einchecken dieser Ausgabe nötig. KIFB hält statische Exporte in portrait-pdf und nimmt den Ordner im vorhandenen Build-Commit mit. Keine Änderung an Sitemap/Portrait-Canonical nötig. Künftige Unternehmens-/Modellerweiterungen werden beim nächsten Build automatisch exportiert.

Tests: python3 -m unittest discover -s tests -p 'test_portrait_pdf.py'. Visuelle Prüfung echter PDFs und Downloadtest in lokalem Browser vor Lieferung. Kein Live-Push durch dieses Patch.
