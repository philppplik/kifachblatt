# Licensed text-only news pilot

19 October 2026. No new libraries or paid services.

Whitelist: FA uses official Destatis press releases (PD URLs only), standard ECB /press/pr/ press releases (no speeches, blogs or author papers), and existing headline-only FinanzNachrichten. IW and KFB use KI-relevant heise /news/ articles from the official RSS feed. Promotional titles are filtered out. Conditions are recorded in tools/licensed_news.py and linked on every page. Article images/logos are never fetched by this feature. A direct original link is visible before and after the excerpt, with target=_blank and noopener/noreferrer/nofollow. No automatic redirect, added tracking, frames or forced delay. Existing site consent remains unchanged. A leaving notice is orientation, not a legal permission.

Feed descriptions are used as supplied, with HTML converted to plain text. No translation, guessed excerpt, article scraping or reuse of old aggregator descriptions. ECB currently sends titles without descriptions, so those pages show only a headline.

## Durable storage

data/news-pages.json contains the first saved approved record per original URL, including its title, complete RSS excerpt, feed URL, timestamp and rights-check date. It is never pruned by this feature. The first saved title determines a deterministic hashed URL that stays stable when a publisher changes its title. Future builds restore all saved records after cleaning the output directory. Existing workflows commit data before publication. KFB also commits the generated news/ pages and CSS since it publishes its root tree. No new CI schedules.

Network/XML failure preserves saved records. Invalid permanent JSON aborts rather than overwriting the archive. Individual oversized/malformed entries are skipped. Saved rights can be revoked by publishers: keeping this archive forever does not override a later removal/revocation request. To remove or correct an entry, edit the explicit record after checking rights; for root-published KFB remove its generated news/<slug>/ directory too. No 404 recovery is guessed.

All detail pages and full source archives carry noindex,follow and no canonical. They are excluded from sitemaps, the exported RSS and site search as local pages; any existing external headline search results stay direct. The rolling news pages link to the full saved archive; KFB adds a KI-News navigation link to the homepage and generated source pages. Existing unapproved publishers stay direct.

## Tests

python3 -m unittest discover -s tools -p test_licensed_news.py

Covers strict host/path allowlist, HTML escaping/text extraction, no publisher images, two original links, stable URLs, noindex, outage retention, corrupt archive protection and rejection of aggregator teasers.
