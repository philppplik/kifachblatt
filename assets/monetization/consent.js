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
  try {
    state = JSON.parse(localStorage.getItem(key));
    if (!state || state.revision !== cfg.consentRevision || typeof state.at !== 'number' || Date.now() - state.at > age || state.at > Date.now()) state = null;
  } catch (_) { state = null; }
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
    try { localStorage.setItem(key,JSON.stringify(state)); document.getElementById('kfb-consent-status').textContent='Auswahl gespeichert.'; }
    catch (_) { document.getElementById('kfb-consent-status').textContent='Auswahl gilt nur für diese Seite, da der Browser sie nicht speichern konnte.'; }
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
  panel.querySelector('[data-consent="close"]').addEventListener('click',close);
  panel.addEventListener('keydown',function (e) { if (e.key === 'Escape') close(); });
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
