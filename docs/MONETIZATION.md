# Advertising and measurement preparation

Status: preparation only, no deployed tracking, no connected provider/account, no active campaign. Reviewed on 2026-10-19.

## Pages and surfaces

- `/werben/`: advertiser formats and mailto requests to the explicitly supplied public address. No form/backend or submission. No prices, reach, endorsements or existing partners asserted.
- `/werbung/`: editorial separation and labels. Use `Anzeige` first. `Gesponsert`/`Affiliate` supplement it. Commission explanation belongs immediately next to each affiliate link.
- `/cookies/`, `/datenschutz/`: accurate off-state disclosures, 180-day local consent record, revocation entry in every normal footer.
- Desktop privacy panel; mobile bottom drawer. Essential service fixed; statistics/advertising disabled while unavailable. No close button, Escape or backdrop dismissal: the visitor chooses reject, accept or save (no choice = no optional cookies/tags; the panel does not block reading). Reject and accept have equal treatment. No focus trap because this is a non-modal settings region.
- Unbooked spots render nothing. V1 direct placement: maximum one campaign, after editorial content, no popups/autoplay/sticky ads. No dummy ad creative, buyer logo, price or performance.
- Print editions deliberately excluded from the new UI.

## Architecture and activation locks

`content/monetization.json` is the single config. `tools/monetization.py` runs last in `site/build.py`; assets are local. The subsequent existing author-page job inherits its common footer. Sitemap includes the new pages. No production dependency added.

Build intentionally fails if analytics, metrics or AdSense is turned on without an implementation review. This preparation is NOT a finished GA4 installation or a certified CMP. A real activation is a separate change with provider-specific disclosures and integration tests. No publisher IDs, keys, ads.txt entries or invented identifiers included.

1. Owner selects GA4 or another measurement service. No account has been created or inspected.
2. Obtain genuine measurement ID, review controller/processor arrangements, retention, transfers, security and actual events. Update all off-state disclosures and consent revision. Complete legal review with owner.
3. GA4 code seam is *basic* consent, not advanced: no Google request or tag before statistics consent; no denied-consent pings by default. Query strings/referrer are omitted from explicit page events; signals and ad personalization disabled. Review automatic/enhanced measurement in the actual property, redaction and IP/transfer implications before activation. Test withdrawal and cookies against the real property.
4. AdSense: apply using owner account, verify site access and original policy-compliant content, obtain approval. Aggregated RSS headlines do not guarantee approval. Obtain genuine publisher/slot IDs and account-provided ads.txt content if required. Select an appropriate Google-certified TCF CMP. Google's own Privacy & messaging is one possible option; do not silently select it. Our drawer is NOT certified and CANNOT unlock AdSense. Integrate CMP and avoid conflicting duplicate prompts. Rejection must leave scripts absent under this project's stricter no-request rule, including no non-personalized-ad workaround. Test the real integration and update notices before release.
5. Direct campaigns: owner reviews exact sponsor, wording, target and dates; destination/content must be real. Every paid preview and paid article must carry its own label. Do not turn an independent editorial article into paid content merely because a separate ad points to it. V1 configuration supports external offers; local paid article destinations deliberately require the separate article/list labeling pass first. No network is automatically joined.

No automatic booking, purchase, email or publishing is performed by the mailto link. It opens a draft in the visitor's mail application; copying the visible address works without an app.

## Measurement choices for the owner

| Option | Useful for | Tradeoff / setup |
| --- | --- | --- |
| GA4, basic consent | Page views, events, promotion clicks/views, reports | Google service and property required; consent, processor/transfer/retention decisions. Rejected visitors absent, so not total audience. |
| Self-hosted Matomo | Controlled first-party analytics and reports | Requires server, updates and operations. Static GitHub Pages alone cannot host it. Cookieless JavaScript is not automatically consent-free in Germany. Still consent-first in this implementation. |
| First-party aggregate collector | Narrow sponsored-spot counts, no third-party browser script | Requires explicit backend/log access, rate limiting, retention and reporting. Browser-only events are not aggregated reporting. Not implemented/connected. |

Recommendation for the current static site if standard reports matter: GA4 *basic consent*, only after the owner chooses it and supplies an actual property. Choose self-hosted Matomo if owning the analytics stack is worth operating another service. No paid service selected.

Prepared browser event seam: `kfb:metric`, containing only `event`, `spot_id`, `page_path`. Only emits if configured AND statistics consent is current. No identifier/referrer/query string. Optional GA4 adapter can send the same event only after consent. This seam has no collection backend and reports nothing today.

- `promotion_view`: a prepared local proxy definition, at least 50% visible for one continuous second in a foreground tab, once per rendered placement. Not a certified/viewability-audited metric, not Google's AdSense impression definition. Not billable inventory by itself.
- `promotion_click`: click on the placement's marked link, after statistics consent.
- CTR = measured clicks / measured impressions * 100, only for a matched campaign/window. CPM = agreed campaign spend / agreed impressions * 1000; revenue CPM/eCPM = realized revenue / measured impressions * 1000. No revenue source connected and no numeric dashboard invented.
- Consent losses, blockers, repeat clicks and bots affect coverage. Never represent these counts as all visitors or audited ad delivery. No cross-tab/user deduplication or fraud controls in this preparation.

## QA

Build as usual; the postprocessor is part of the normal build.

Optional developer-only UI test: install Playwright outside the production tree, set `NODE_PATH` to its node_modules and `CHROME_PATH` if needed; run `node tools/monetization/test-ui.cjs`. No production package added. Test starts and closes a local ephemeral server and browser. Screenshots go to `SCREENSHOT_DIR` (default `/tmp/iw-monetization-screenshots`).

42 browser checks: 1440px, 390px and 320px, no external network calls, disabled unavailable categories, reject/accept-available persistence, expiry, settings reopen, article integration, mailto and overflow. Visual review covers desktop + mobile advertiser page and drawer. IW currently has no dark mode; no unrelated theme introduced.

## Sources, checked 2026-10-19

- Google AdSense, eligibility: https://support.google.com/adsense/answer/9724
- Google AdSense, certified TCF CMP requirements for personalized ads in EEA/UK/Switzerland; Google certification is not full legal certification: https://support.google.com/adsense/answer/13554116
- Google Analytics, basic vs advanced consent: https://support.google.com/analytics/answer/10000067?hl=en
- Matomo, current cookie/consent guidance (vendor source, not legal advice): https://matomo.org/faq/new-to-piwik/how-do-i-use-matomo-analytics-without-consent-or-cookie-banner/
- §25 TDDDG, consent and necessary-service exception: https://www.gesetze-im-internet.de/ttdsg/__25.html
- German media authorities, labeling guide: https://www.die-medienanstalten.de/service/merkblaetter-und-leitfaeden/leitfaden-werbekennzeichnung-bei-online-medien/
- Accessible guide PDF (commercial posts: Werbung/Anzeige at start; affiliate disclosure beside link): https://www.die-medienanstalten.de/fileadmin/user_upload/die_medienanstalten/Service/Merkblaetter_Leitfaeden/Leitfaden_Werbekennzeichnung_Onlinemedien_ua.pdf

The owner reviews legal/business matters. These pages document the actual inactive implementation, not a declaration of legal compliance or a promise of AdSense approval.

## Site notes (KI Fachblatt)

Pages are committed static HTML. `tools/monetization.py .` is idempotent and runs at the end of `tools/build.py` (after portraits), so regenerated pages (for example berichte.html) keep footer link, panel and script. It edits datenschutz.html in place (marker `kfb-consent-v1`). Portrait, model and benchmark texts are declared not for sale on /werbung.


## Owner-approved GA4 activation, 2026-10-19

Supersedes off-state preparation above. Owner requested all three sites on GA4 at 15:17, then asked to finish. Account 363019915 already has accepted Data Processing Terms (19 October 2026) and approved Primary contact. Property 559586961, stream 16159228686, measurement ID G-75G1VNDHJW. New separate property; no old property deleted. Germany time zone, EUR, News category, smallest size bucket, traffic objective.

Verified after fresh navigation: event/user retention 2 months, reset on activity OFF (Google may take 24h to apply); Signals OFF, user-provided data OFF, granular device/location OFF, ads personalization 0/307. Enhanced Measurement OFF in finished stream, confirmed after complete reload. Creation-time toggle is not reliable; final stream state was checked. IP addresses reach Google on connection, but Google's GA4 policy says individual IPs are not logged/stored; no anonymity claim.

Basic consent: no Google tag/request/ping until statistics consent, ads storage/user-data/personalization remain denied. Cookie lifetime 180 days with no refresh. Query/referrer omitted in config and explicit page_view. Consent expiry checked for new events/foreground return; cross-tab storage changes reload. Withdrawal disables collection, clears accessible GA cookies and reloads without emitting a denied ping. Existing necessary first-party consent-cookie fallback remains. Advertising and promotion metrics remain OFF. New consent revision invalidates old off-state selections.

QA: NODE_PATH=/tmp/node_modules node tools/monetization/test-ga4.cjs (set CHROME executable in test if needed). 48 assertions on 1440/390/320: no requests before consent or after rejection, exact intended tag after explicit consent, flags/redaction/cookie duration, withdrawal/cookie deletion, updated disclosure, width. ALL HTTPS intercepted, no synthetic events sent to real Google. Run against built site (FA) or repository static pages (KFB).

Deployment is separate. After publication verify initial/reject/accept/withdraw network and actual page_view collect, then check GA4 real-time. Patch is not proof of ingestion or a live dashboard. Consent counts are not total visitors. Legal disclosure is a factual configuration review, not a compliance certificate.

Sources checked 2026-10-19: https://www.google.com/analytics/terms/de.html (Google Ireland), https://privacy.google.com/businesses/processorterms/ (accepted terms), https://www.dataprivacyframework.gov/participant/5780 (Google LLC Active), https://policies.google.com/privacy/frameworks?hl=de (transfer basis), https://support.google.com/analytics/answer/7667196 (retention), https://support.google.com/analytics/answer/10000067?hl=en (Basic Consent).
