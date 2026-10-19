/* Basic consent: no Google code, request or ping before explicit statistics consent. */
(function () {
  'use strict';
  var configNode = document.getElementById('kfb-monetization-config');
  if (!configNode) return;
  var cfg = JSON.parse(configNode.textContent), panel = document.getElementById('kfb-consent');
  var key = 'kfb-consent-v1', age = 180 * 86400000, state = null, previousFocus;
  var stats = document.getElementById('kfb-statistics'), ads = document.getElementById('kfb-advertising');
  var analyticsReady = cfg.analytics.enabled && cfg.analytics.provider === 'ga4' && /^G-[A-Z0-9]+$/.test(cfg.analytics.measurementId);
  /* AdSense deliberately has no loader. A certified TCF CMP integration is a separate release. */
  var adReady = false, loaded = false;
  stats.disabled = !analyticsReady && !cfg.metrics.enabled; ads.disabled = !adReady;
  /* The choice is kept in localStorage and mirrored in one first-party cookie (same name with underscores),
     so it survives reloads, other pages and browsers that block either store. Written only after an active click. */
  var cookieName = key.replace(/-/g, '_');
  function readCookie() {
    var m = document.cookie.match(new RegExp('(?:^|; )' + cookieName + '=([^;]*)'));
    if (!m) return null;
    try { return JSON.parse(decodeURIComponent(m[1])); } catch (_) { return null; }
  }
  function writeCookie(s) {
    var d = location.hostname.match(/^(?:www\.)?([a-z0-9-]+\.de)$/i);
    document.cookie = cookieName + '=' + encodeURIComponent(JSON.stringify(s)) + '; Max-Age=' + Math.floor(age / 1000) + '; Path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '') + (d ? '; Domain=' + d[1] : '');
    return readCookie() !== null;
  }
  function valid(s) { return s && s.revision === cfg.consentRevision && typeof s.at === 'number' && Date.now() - s.at <= age && s.at <= Date.now() ? s : null; }
  try { state = valid(JSON.parse(localStorage.getItem(key))); } catch (_) { state = null; }
  if (!state) state = valid(readCookie());
  function permitted() { return !!(state && state.statistics === true); }
  function gtag() { window.dataLayer.push(arguments); }
  function loadAnalytics() {
    if (!permitted() || !analyticsReady || loaded) return;
    loaded = true; window.dataLayer = window.dataLayer || [];
    gtag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
    gtag('consent','update',{analytics_storage:'granted'});
    gtag('js',new Date());
    gtag('config',cfg.analytics.measurementId,{send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false});
    gtag('event','page_view',{page_location:location.origin + location.pathname,page_referrer:'',page_title:document.title});
    var script = document.createElement('script'); script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(cfg.analytics.measurementId);
    document.head.appendChild(script);
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
    state = {revision:cfg.consentRevision,at:Date.now(),statistics:accept && !stats.disabled && stats.checked,advertising:false};
    var stored = false;
    try { localStorage.setItem(key,JSON.stringify(state)); stored = true; } catch (_) {}
    if (writeCookie(state)) stored = true;
    document.getElementById('kfb-consent-status').textContent = stored ? 'Auswahl gespeichert.' : 'Auswahl gilt nur für diese Seite, da der Browser sie nicht speichern konnte.';
    close();
    if (hadStats && !state.statistics) {
      if (loaded) { window['ga-disable-' + cfg.analytics.measurementId] = true; gtag('consent','update',{analytics_storage:'denied'}); }
      eraseAnalyticsCookies();
      /* Full reload removes every previously loaded provider and pending handler. */
      location.reload(); return;
    }
    loadAnalytics();
  }
  document.querySelectorAll('[data-kfb-consent-open]').forEach(function (b) { b.addEventListener('click',open); });
  panel.querySelector('[data-consent="reject"]').addEventListener('click',function () { stats.checked=false; save(false); });
  panel.querySelector('[data-consent="save"]').addEventListener('click',function () { save(true); });
  panel.querySelector('[data-consent="all"]').addEventListener('click',function () { stats.checked=!stats.disabled; save(true); });
  /* No close button, Escape or backdrop dismissal: a visitor decides with reject, accept or save. */
  /* No server, identifier, query string, referrer or external request in this event seam. */
  function metric(name, id) {
    if (!cfg.metrics.enabled || !permitted() || !/^[a-z0-9-]{1,80}$/.test(id)) return;
    var data = {event:name,spot_id:id,page_path:location.pathname};
    window.dispatchEvent(new CustomEvent('kfb:metric',{detail:data}));
    if (analyticsReady && loaded) gtag('event',name,{spot_id:id,page_path:location.pathname});
  }
  document.querySelectorAll('[data-kfb-spot]').forEach(function (spot) {
    var id = spot.getAttribute('data-kfb-spot'), sent=false, timer=null;
    spot.querySelectorAll('a[data-kfb-promotion]').forEach(function (link) { link.addEventListener('click',function () { metric('promotion_click',id); }); });
    if (!('IntersectionObserver' in window)) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        clearTimeout(timer);
        if (entry.isIntersecting && entry.intersectionRatio >= 0.5 && !sent) timer=setTimeout(function () {
          if (!document.hidden && permitted() && cfg.metrics.enabled) { metric('promotion_view',id); sent=true; observer.disconnect(); }
        },1000);
      });
    },{threshold:[0,0.5]});
    observer.observe(spot);
  });
  loadAnalytics();
  if (!state) open();
}());
