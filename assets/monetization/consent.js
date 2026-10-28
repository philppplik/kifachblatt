/* Rich-Analytics-Entwurf (lokal, nicht deployed). Basis: aktueller consent.js-Loader.
   Einzige Site-Anpassung wie bisher: Praefix fa/iw/kfb in den IDs und dem Storage-Key.
   Neu gegenueber live, alles nur nach erneuter Statistik-Einwilligung (consentRevision-Bump):
   - attribution-Modus aus cfg.analytics.attribution: "stripped" (eigene Kategorien) | "cleaned" (nur Herkunfts-Domain + feste Kampagnen, native GA4-Quellen)
   - content_group, scroll_percent, outbound_click, file_download, contact_click
   - acquisition_bucket nur im Modus "stripped" (eigene grobe Herkunftskategorien)
   - excludePaths: Routen ohne jegliches Tag (Tokens, DOI, Abmeldung, /somnia/)
   Keine Formular-/Rechner-Eingaben, keine vollen externen Ziel-URLs, keine Werbung. */
(function () {
  'use strict';
  var configNode = document.getElementById('kfb-monetization-config');
  if (!configNode) return;
  var cfg = JSON.parse(configNode.textContent), panel = document.getElementById('kfb-consent');
  var key = 'kfb-consent-v1', age = 180 * 86400000, state = null, previousFocus;
  var stats = document.getElementById('kfb-statistics'), ads = document.getElementById('kfb-advertising');
  var analyticsReady = cfg.analytics.enabled && cfg.analytics.provider === 'ga4' && /^G-[A-Z0-9]+$/.test(cfg.analytics.measurementId);
  var adReady = false, loaded = false;
  stats.disabled = !analyticsReady && !cfg.metrics.enabled; ads.disabled = !adReady;

  /* --- NEU: Konfiguration der Erweiterung mit sicheren Defaults --- */
  var attr = cfg.analytics.attribution === 'cleaned' ? 'cleaned' : 'stripped';
  var excludes = Array.isArray(cfg.analytics.excludePaths) ? cfg.analytics.excludePaths : [];
  var groups = cfg.analytics.contentGroups && typeof cfg.analytics.contentGroups === 'object' ? cfg.analytics.contentGroups : {};
  var downloadAllow = Array.isArray(cfg.analytics.downloadAllowlist) ? cfg.analytics.downloadAllowlist : []; /* leer = keine Download-Events */
  var outboundAllow = Array.isArray(cfg.analytics.outboundAllowlist) ? cfg.analytics.outboundAllowlist : []; /* leer = keine Outbound-Events */
  var toolAllow = Array.isArray(cfg.analytics.toolUsageAllowlist) ? cfg.analytics.toolUsageAllowlist : []; /* leer = keine Rechner-/Tool-Events */
  /* Feste Feldnamen reichen nicht: utm_campaign koennte E-Mail/Token enthalten.
     Nur exakt freigegebene Werte je Feld, alles andere wird verworfen. */
  var utmAllow = cfg.analytics.campaignValues && typeof cfg.analytics.campaignValues === 'object' ? cfg.analytics.campaignValues : {};
  function anyMatch(list, value) {
    for (var i = 0; i < list.length; i++) { try { if (new RegExp(list[i]).test(value)) return true; } catch (_) {} }
    return false;
  }
  var bucketKey = key + '-bucket', bucketAge = 30 * 60000; /* 30 Minuten Inaktivitaet */

  function pathExcluded() {
    for (var i = 0; i < excludes.length; i++) {
      try { if (new RegExp(excludes[i]).test(location.pathname)) return true; } catch (_) {}
    }
    return false;
  }
  /* Im Modus "cleaned" bleiben nur exakt freigegebene Kampagnenwerte aus
     utm_source/medium/campaign erhalten. Alles andere in der Query geht nie an GA4. */
  function pageLocation() {
    var loc = location.origin + location.pathname;
    if (attr !== 'cleaned') return loc;
    var keep = [];
    location.search.replace(/^\?/, '').split('&').forEach(function (pair) {
      var m = pair.match(/^utm_(source|medium|campaign)=(.*)$/i);
      if (!m) return;
      var field = m[1].toLowerCase(), value;
      try { value = decodeURIComponent(m[2]); } catch (_) { return; }
      var allowed = Array.isArray(utmAllow[field]) ? utmAllow[field] : [];
      if (allowed.indexOf(value) !== -1) keep.push('utm_' + field + '=' + encodeURIComponent(value));
    });
    return keep.length ? loc + '?' + keep.join('&') : loc;
  }
  /* Nur Scheme+Host der Herkunft, niemals Pfad oder Query des Referrers. */
  function pageReferrer() {
    if (attr !== 'cleaned' || !document.referrer) return '';
    try { return new URL(document.referrer).origin; } catch (_) { return ''; }
  }
  function contentGroup() {
    for (var pattern in groups) {
      try { if (new RegExp(pattern).test(location.pathname)) return groups[pattern]; } catch (_) {}
    }
    return 'other';
  }
  /* Grobe eigene Herkunftskategorien statt Rohreferrer. Nur Kategorie + Zeitstempel
     im Session-Speicher, keine URL, kein Query, keine Identifier. */
  function bucketize(host) {
    if (!host) return 'direct';
    host = host.toLowerCase();
    if (/(^|\.)google\.[a-z.]+$/.test(host)) return 'google';
    if (/(^|\.)(bing|duckduckgo|ecosia|yahoo|startpage|qwant)\.[a-z.]+$/.test(host)) return 'other_search';
    if (/(^|\.)(chatgpt|claude|perplexity|gemini|copilot)\.[a-z.]+$|(^|\.)chat\.openai\.com$/.test(host)) return 'ai';
    if (/(^|\.)(facebook|instagram|twitter|x|linkedin|mastodon|bsky|reddit|tiktok|youtube|pinterest)\.[a-z.]+$/.test(host)) return 'social';
    return 'external';
  }
  function acquisitionBucket() {
    var now = Date.now(), own = location.hostname.replace(/^www\./, ''), rec = null;
    try { rec = JSON.parse(sessionStorage.getItem(bucketKey)); } catch (_) { rec = null; }
    if (!rec || typeof rec.at !== 'number' || now - rec.at > bucketAge) {
      var ref = '';
      try { ref = document.referrer ? new URL(document.referrer).hostname.replace(/^www\./, '') : ''; } catch (_) { ref = ''; }
      rec = { bucket: ref && ref !== own ? bucketize(ref) : 'direct', at: now };
    } else {
      rec.at = now;
    }
    try { sessionStorage.setItem(bucketKey, JSON.stringify(rec)); } catch (_) {}
    return rec.bucket;
  }

  var cookieName = key.replace(/-/g, '_');
  function readCookie() {
    var m = document.cookie.match(new RegExp('(?:^|; )' + cookieName + '=([^;]*)'));
    if (!m) return null;
    try { return JSON.parse(decodeURIComponent(m[1])); } catch (_) { return null; }
  }
  function writeCookie(s) {
    /* HOST-ONLY: kein Domain-Attribut - Consent-Cookie bleibt auf diesem Host, Subdomains (hob, db, agent) unberuehrt. Alter Domain-Fallback entfernt. */
    var d = null;
    document.cookie = cookieName + '=' + encodeURIComponent(JSON.stringify(s)) + '; Max-Age=' + Math.floor(age / 1000) + '; Path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '') + (d ? '; Domain=' + d[1] : '');
    return readCookie() !== null;
  }
  function valid(s) { return s && s.revision === cfg.consentRevision && typeof s.at === 'number' && Date.now() - s.at <= age && s.at <= Date.now() ? s : null; }
  try { state = valid(JSON.parse(localStorage.getItem(key))); } catch (_) { state = null; }
  if (!state) state = valid(readCookie());
  function permitted() { return !!(valid(state) && state.statistics === true); }
  function gtag() { window.dataLayer.push(arguments); }

  /* --- NEU: Interaktions-Events, alle ohne Eingabewerte --- */
  function pagePath() { return location.pathname; }
  function bindScroll() {
    var marks = [25, 50, 75, 90], sent = {}, max = 0;
    function check() {
      var h = document.documentElement, total = h.scrollHeight - h.clientHeight;
      if (total <= 0) return;
      var pct = Math.min(100, Math.round(((window.scrollY || h.scrollTop) / total) * 100));
      if (pct > max) max = pct;
      marks.forEach(function (m) {
        if (!sent[m] && max >= m) {
          sent[m] = true;
          gtag('event', 'scroll_percent', { percent_scrolled: m, page_path: pagePath(), content_group: contentGroup() });
        }
      });
    }
    var t = null;
    window.addEventListener('scroll', function () { clearTimeout(t); t = setTimeout(check, 300); }, { passive: true });
  }
  function bindClicks() {
    var own = location.hostname.replace(/^www\./, '');
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (/^mailto:/i.test(href)) { gtag('event', 'contact_click', { contact_type: 'email', page_path: pagePath(), content_group: contentGroup() }); return; }
      if (/^tel:/i.test(href)) { gtag('event', 'contact_click', { contact_type: 'phone', page_path: pagePath(), content_group: contentGroup() }); return; }
      var u;
      try { u = new URL(a.href); } catch (_) { return; }
      var host = u.hostname.replace(/^www\./, '');
      if (host && host !== own) {
        /* Nur freigegebene Ziel-Domains, nie die volle URL. */
        if (outboundAllow.length && anyMatch(outboundAllow, host)) {
          gtag('event', 'outbound_click', { link_domain: host, page_path: pagePath(), content_group: contentGroup() });
        }
        return;
      }
      var ext = (u.pathname.match(/\.([a-z0-9]{2,5})$/i) || [])[1];
      /* Nur explizit freigegebene oeffentliche Download-Pfade, keine Token-Links. */
      if (ext && downloadAllow.length && anyMatch(downloadAllow, u.pathname)) {
        gtag('event', 'file_download', { file_extension: ext.toLowerCase(), file_path: u.pathname, page_path: pagePath(), content_group: contentGroup() });
      }
    });
  }

  function bindShares() {
    /* Nur Elemente mit Opt-in-Attribut data-kfb-share; keine geteilten Inhalte/Werte. */
    document.querySelectorAll('[data-kfb-share]').forEach(function (el) {
      el.addEventListener('click', function () {
        gtag('event', 'share_click', { page_path: pagePath(), content_group: contentGroup() });
      });
    });
  }
  function loadAnalytics() {
    if (!permitted() || !analyticsReady || loaded) return;
    if (pathExcluded()) return; /* NEU: sensible Routen komplett ohne Tag */
    loaded = true; window.dataLayer = window.dataLayer || [];
    gtag('consent', 'default', { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });
    gtag('consent', 'update', { analytics_storage: 'granted' });
    gtag('js', new Date());
    var common = { send_page_view: false, allow_google_signals: false, allow_ad_personalization_signals: false, cookie_expires: 180 * 86400, cookie_update: false, cookie_domain: location.hostname }; /* NEU: host-only, keine Reichweite auf Schwester-Subdomains */
    var view = { page_location: pageLocation(), page_referrer: pageReferrer(), page_title: document.title, content_group: contentGroup() };
    if (attr === 'stripped') view.acquisition_bucket = acquisitionBucket();
    gtag('config', cfg.analytics.measurementId, common);
    gtag('event', 'page_view', view);
    var script = document.createElement('script'); script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(cfg.analytics.measurementId);
    document.head.appendChild(script);
    if (toolAllow.length && anyMatch(toolAllow, location.pathname)) {
      /* Allgemeine Nutzung ja/nein, niemals Eingaben, Ergebnisse oder gespeicherten Fortschritt. */
      gtag('event', 'tool_used', { tool_path: location.pathname, content_group: contentGroup() });
    }
    bindScroll(); bindClicks(); bindShares();
  }
  function open() {
    previousFocus = document.activeElement;
    stats.checked = !stats.disabled && permitted(); ads.checked = false;
    panel.hidden = false; panel.querySelector('[data-consent="reject"]').focus();
  }
  function close() { panel.hidden = true; if (previousFocus && previousFocus.focus) previousFocus.focus(); }
  function eraseAnalyticsCookies() {
    document.cookie.split(';').forEach(function (item) {
      var name = item.trim().split('=')[0];
      if (!/^_ga(?:_|$)|^_gid$|^_gat/.test(name)) return;
      var parts = location.hostname.split('.'), domains = [''];
      for (var i = 0; i < parts.length - 1; i++) domains.push(parts.slice(i).join('.'));
      domains.forEach(function (domain) { document.cookie = name + '=; Max-Age=0; path=/; SameSite=Lax' + (domain ? '; domain=' + domain : ''); });
    });
  }
  function save(accept) {
    var hadStats = permitted();
    state = { revision: cfg.consentRevision, at: Date.now(), statistics: accept && !stats.disabled && stats.checked, advertising: false };
    var stored = false;
    try { localStorage.setItem(key, JSON.stringify(state)); stored = true; } catch (_) {}
    if (writeCookie(state)) stored = true;
    document.getElementById('kfb-consent-status').textContent = stored ? 'Auswahl gespeichert.' : 'Auswahl gilt nur für diese Seite, da der Browser sie nicht speichern konnte.';
    close();
    if (hadStats && !state.statistics) {
      if (loaded) { window['ga-disable-' + cfg.analytics.measurementId] = true; }
      try { sessionStorage.removeItem(bucketKey); } catch (_) {}
      eraseAnalyticsCookies();
      location.reload(); return;
    }
    loadAnalytics();
  }
  document.querySelectorAll('[data-kfb-consent-open]').forEach(function (b) { b.addEventListener('click', open); });
  panel.querySelector('[data-consent="reject"]').addEventListener('click', function () { stats.checked = false; save(false); });
  panel.querySelector('[data-consent="save"]').addEventListener('click', function () { save(true); });
  panel.querySelector('[data-consent="all"]').addEventListener('click', function () { stats.checked = !stats.disabled; save(true); });
  function metric(name, id) {
    if (!cfg.metrics.enabled || !permitted() || !/^[a-z0-9-]{1,80}$/.test(id)) return;
    var data = { event: name, spot_id: id, page_path: pagePath() };
    window.dispatchEvent(new CustomEvent('kfb:metric', { detail: data }));
    if (analyticsReady && loaded) gtag('event', name, { spot_id: id, page_path: pagePath() });
  }
  document.querySelectorAll('[data-kfb-spot]').forEach(function (spot) {
    var id = spot.getAttribute('data-kfb-spot'), sent = false, timer = null;
    spot.querySelectorAll('a[data-kfb-promotion]').forEach(function (link) { link.addEventListener('click', function () { metric('promotion_click', id); }); });
    if (!('IntersectionObserver' in window)) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        clearTimeout(timer);
        if (entry.isIntersecting && entry.intersectionRatio >= 0.5 && !sent) timer = setTimeout(function () {
          if (!document.hidden && permitted() && cfg.metrics.enabled) { metric('promotion_view', id); sent = true; observer.disconnect(); }
        }, 1000);
      });
    }, { threshold: [0, 0.5] });
    observer.observe(spot);
  });
  window.addEventListener('storage', function (e) { if (e.key === key) { if (loaded) window['ga-disable-' + cfg.analytics.measurementId] = true; location.reload(); } });
  document.addEventListener('visibilitychange', function () { if (!document.hidden && state && !permitted() && loaded) { window['ga-disable-' + cfg.analytics.measurementId] = true; location.reload(); } });
  loadAnalytics();
  if (!state) open();
}());
