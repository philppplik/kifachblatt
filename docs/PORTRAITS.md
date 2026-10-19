# Curated portraits

Data: `content/portraits.json`. Rendering: `tools/portraits.py`. No dependencies or network calls. Both sites share a schema, not runtime infrastructure. KFB renders companies, models and benchmarks; IW renders the basic company/model subset. Entries are a selected starting set, not a complete or latest-model ranking.

Every technical fact and score references a source key with HTTPS URL and date checked. Keep model version, precision and benchmark split separate. Manufacturer scores must remain labeled; do not imply independent tests. Missing setup or measurement date must stay explicit. No automatic leaderboard imports, no copied questions, no third-party logo requests.

Source metadata is not a universal reuse license. Review each model artifact's license before linking a new download. Code and dataset licenses can differ. Third-party hosted API models are not necessarily developed by the host.

Build integration runs after local search is generated, then appends portrait search records and sitemap entries idempotently. Index filters use local JavaScript; cards and all detail pages work without JS. Monograms are locally rendered text. Existing article heroes/watermarks are untouched.

Maintenance: update the date only after reviewing the affected primary sources. No claim of automatic freshness. Add a new sourced record, run build and tests, inspect desktop/mobile pixels, then deliver a reviewed patch.

Tests: `python3 -m unittest discover -s tests -p test_portraits.py`. Browser tests additionally covered text filter, combined provider filter, no-results state and overflow at widths 320, 390, 768, 1024 and 1440. Generated internal links, JSON-LD and local search membership were checked on every new page.
