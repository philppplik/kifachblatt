# Editorial pipeline (kifachblatt.de)

Articles are JSON files in `content/articles/<slug>.json`, hero images in `content/images/<slug>.jpg`
(1600x900 JPEG, max 350 KB, "KI-generiert" burned into the pixels for AI images).

Build: `python3 tools/build.py` (stdlib only). It validates every article, then writes
`<slug>.html`, `thema/<section>.html`, `redaktion.html`, `assets/articles/*`, the article table in
`index.html`, `sitemap.xml` (incl. image entries, namespace sitemap-image/1.1), `news-sitemap.xml`
(articles of the last 48 h, news and analysis only), `feed.xml`, `llms.txt` and `robots.txt`.
Articles with a future `published` date are skipped (scheduled).

Required fields: slug, title, dek, section, type (news|analysis|explainer), published, modified
(ISO 8601 with timezone), author, tags, key_takeaways, hero {alt, caption}, body, sources (>=3).
Optional: faq, method, limitations, related. Footnotes in body: `[^n]`.
Sections: grundlagen, architektur, verlaesslichkeit, praxis, datenschutz, methode, analyse, modelle,
agenten, forschung, evals, recht.

URLs are extensionless everywhere (canonical, sitemaps, feeds, JSON-LD, links). The `.html` form
still answers on GitHub Pages; pages carry the clean canonical and a script replaces the address bar.

Publish: add JSON + image, run the build, commit generated files together with the content, push.
