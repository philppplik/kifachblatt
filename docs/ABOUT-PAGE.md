# Über das Magazin

`tools/about.py` replaces only the existing main content, reusing header/footer/consent/metadata. Called from `tools/build.py` with the already publication-filtered article list. Standalone mode filters future articles. Stats are regenerated on build, not visitor/traffic or success claims.

Evidence map:
- Analyses: published `content/articles/*.json` union `content/home-legacy.json` by slug. Currently 4 + 6 = 10.
- Company/model/benchmark counts: `content/portraits.json`, currently 6/8/4. Directory overview pages are not counted as portraits.
- Glossary: entries in `content/glossary.json`, currently 83.
- Editorial process, sourcing, responsibility, AI disclosure, corrections: existing `content/pages/redaktion.md`, `quellen.md`, `transparenz.md`, `korrekturen.md`. Described explicitly as published editorial principles, not independently audited compliance. No new promises about turnaround or publication frequency.
- Daily report schedule: `.github/workflows/kfb-daily-report.yml`, 05:20 UTC daily. Described as configured, not a delivery guarantee. `tools/report.py` supplies HF trends and the latest two articles. Automatic data reports are distinguished from editorial article approval.
- Ads/analytics: both disabled in `content/monetization.json`; status text derives from those flags on every build. Monetization preparation and consent controls exist. Not a permanent ad-free pledge. No changes to ad/consent activation.

Native, static SVG inventory chart (shared zero-based scale) and process diagram, with text equivalents and responsive numbered process cards. No external embeds, imagery claiming real people, invented reach or testimonials. On phones SVG inventory label size increases; process diagram gives way to readable text steps. Existing house style retained. Contact only philipp.l.paulik@gmail.com; no telephone added.

Tests: count derivation, schedule evidence, idempotence, SVG accessibility labels, local content links. Browser viewport checks 320/390/768/1440; desktop/mobile screenshots inspected.
