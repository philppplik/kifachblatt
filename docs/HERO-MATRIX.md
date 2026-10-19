# Hero-Signalfeld

Eigener Canvas-2D-Code, kein Shader-Paket, keine Dependencies, kein Netzwerkzugriff. Dekorative lila Dot-Matrix auf der rechten Desktop-Herohälfte; kein Datenchart und kein Leistungsmesswert.

Statisches Inline-SVG als Fallback bei ausgeschaltetem JS, fehlendem Canvas/IntersectionObserver oder Reduced Motion. Das Raster ist bereits im HTML. CSS reserviert die Geometrie mit aspect-ratio; Canvas und SVG liegen absolut darin. Mobile <=800px blendet die Grafik aus und startet keine Animation.

Animation: requestAnimationFrame, maximal etwa 30 Zeichnungen/s, 775 Punkte, DPR maximal 1,5, begrenzter Zeitschritt. Pause bei verstecktem Tab, nicht sichtbarem Element, Reduced Motion und Mobile. Ein Resize initialisiert nur die Zeichenfläche. Keine Pointer-Listener, kein Scroll-Handler, keine Fonts oder Bilder nachgeladen.

aria-hidden und pointer-events:none; bestehender Text, Links und Fokusreihenfolge bleiben erhalten. Kein neues Timing, keine Messwerte und keine Tracking-Events.

Prüfung lokal mit Chrome: ca. 30 Zeichnungen/s, CLS 0 einschließlich Consent-Ablehnen, Offscreen-Pause, Reduced-Motion-Pause und Mobile-Pause bestätigt. Echte Desktop-/Mobile-/Reduced-Motion-Screenshots und Animationsframes geprüft. Kein Lighthouse-Binary installiert; daher kein Lighthouse-Gesamtscore behauptet. Manuelle Pause-Schaltfläche für die laufende Dekoration vorhanden, ohne Animation/auf Mobile verborgen.
