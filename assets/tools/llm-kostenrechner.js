/* LLM-API-Kostenrechner — kifachblatt.de
   Rein clientseitig. Daten: /data/llm-api-preise.json (Primärquellen, mit Stand).
   Zustand wird im URL-Hash gespeichert (teilbarer Link). */
(function () {
  'use strict';

  var PRESETS = {
    chat:    { label: 'Chat-Support',        input: 1500,  output: 250,  requests: 2000, cache: 40 },
    rag:     { label: 'RAG / Wissens-Chat',  input: 6000,  output: 600,  requests: 800,  cache: 70 },
    coding:  { label: 'Coding-Agent',        input: 30000, output: 4000, requests: 300,  cache: 50 },
    summary: { label: 'Zusammenfassungen',   input: 8000,  output: 400,  requests: 500,  cache: 10 },
    custom:  { label: 'Individuell',         input: 0,     output: 0,    requests: 0,    cache: 0 }
  };

  var state = { preset: 'chat', input: 1500, output: 250, requests: 2000, cache: 40, batch: false, offpeak: false, cur: 'USD' };
  var DATA = null;

  function $(id) { return document.getElementById(id); }

  /* ---------- Zustand <-> URL-Hash ---------- */
  function readHash() {
    if (!location.hash || location.hash.length < 2) return;
    var parts = location.hash.slice(1).split('&');
    parts.forEach(function (p) {
      var kv = p.split('='); if (kv.length !== 2) return;
      var k = kv[0], v = decodeURIComponent(kv[1]);
      if (k === 'preset' && PRESETS[v]) { state.preset = v; }
      if (k === 'in')  state.input = clampInt(v, 1, 10000000, state.input);
      if (k === 'out') state.output = clampInt(v, 1, 1000000, state.output);
      if (k === 'req') state.requests = clampInt(v, 1, 10000000, state.requests);
      if (k === 'cache') state.cache = clampInt(v, 0, 100, state.cache);
      if (k === 'batch') state.batch = v === '1';
      if (k === 'offpeak') state.offpeak = v === '1';
      if (k === 'cur' && (v === 'USD' || v === 'EUR')) state.cur = v;
    });
  }
  function writeHash() {
    var h = '#preset=' + state.preset + '&in=' + state.input + '&out=' + state.output +
      '&req=' + state.requests + '&cache=' + state.cache +
      (state.batch ? '&batch=1' : '') + (state.offpeak ? '&offpeak=1' : '') + '&cur=' + state.cur;
    history.replaceState(null, '', h);
  }
  function clampInt(v, min, max, fallback) {
    var n = parseInt(v, 10);
    if (isNaN(n)) return fallback;
    return Math.max(min, Math.min(max, n));
  }

  /* ---------- Preis-Logik ---------- */
  function priceSet(model, inputTokens, offpeak) {
    // DeepSeek-Nebenzeit
    if (offpeak && model.offpeak) return model.offpeak;
    // Staffelpreise (xAI, Google) nach Eingabegröße
    if (model.tiers) {
      for (var i = 0; i < model.tiers.length; i++) {
        var t = model.tiers[i];
        if (t.max_input_tokens === null || inputTokens <= t.max_input_tokens) return t;
      }
      return model.tiers[model.tiers.length - 1];
    }
    return model;
  }

  function costPerRequest(model, s) {
    var p = priceSet(model, s.input, s.offpeak);
    var cachedShare = p.cached_input != null ? s.cache / 100 : 0;
    var fresh = s.input * (1 - cachedShare);
    var cached = s.input * cachedShare;
    var usd = (fresh * p.input + cached * (p.cached_input != null ? p.cached_input : p.input) + s.output * p.output) / 1e6;
    if (s.batch && currentProvider(model).batch_discount) usd *= (1 - currentProvider(model).batch_discount);
    return usd;
  }

  var modelProvider = {};
  function currentProvider(model) { return modelProvider[model.id]; }

  /* ---------- Formatierung ---------- */
  function fmt(usd, monthly) {
    var v = usd;
    var sym = '$';
    if (state.cur === 'EUR') { v = usd / DATA.fx.usd_per_eur; sym = '€'; }
    var dec = v >= 100 ? 0 : v >= 10 ? 1 : v >= 1 ? 2 : v >= 0.01 ? 3 : 4;
    var txt = v.toLocaleString('de-DE', { minimumFractionDigits: dec, maximumFractionDigits: dec });
    return txt + ' ' + sym;
  }
  function fmtNum(n) { return n.toLocaleString('de-DE'); }

  /* ---------- Rendering ---------- */
  function compute() {
    var rows = [];
    DATA.providers.forEach(function (prov) {
      prov.models.forEach(function (m) {
        modelProvider[m.id] = prov;
        var perReq = costPerRequest(m, state);
        rows.push({
          model: m, provider: prov,
          perRequest: perReq,
          perMonth: perReq * state.requests * 30
        });
      });
    });
    rows.sort(function (a, b) { return a.perMonth - b.perMonth; });
    return rows;
  }

  function render() {
    var rows = compute();
    var best = rows[0];

    // Ergebnis-Kasten
    $('kr-best').innerHTML =
      '<strong>Günstigstes Modell für dieses Szenario: ' + esc(best.provider.name) + ' ' + esc(best.model.name) + '</strong>' +
      ' — ' + fmt(best.perRequest) + ' pro Anfrage, ' + fmt(best.perMonth) + ' pro Monat ' +
      '(' + fmtNum(state.requests) + ' Anfragen/Tag × 30 Tage).' +
      (state.batch ? ' Batch-Rabatt berücksichtigt, wo verfügbar.' : '') +
      (state.offpeak ? ' DeepSeek-Nebenzeit aktiv.' : '');

    // Balkendiagramm (Top 12)
    var top = rows.slice(0, 12);
    var chartMax = top[top.length - 1].perMonth || 1;
    var html = '';
    top.forEach(function (r, i) {
      var w = Math.max(1.5, (r.perMonth / chartMax) * 100);
      html += '<div class="kr-row' + (i === 0 ? ' kr-first' : '') + '">' +
        '<div class="kr-lab"><b>' + esc(r.model.name) + '</b><span>' + esc(r.provider.name) + '</span></div>' +
        '<div class="kr-track"><div class="kr-bar" style="width:' + w.toFixed(1) + '%"></div>' +
        '<div class="kr-val">' + fmt(r.perMonth) + '/Monat · ' + fmt(r.perRequest) + '/Anfrage</div></div></div>';
    });
    $('kr-chart').innerHTML = html;

    // Tabelle (alle Modelle)
    var th = '';
    rows.forEach(function (r, i) {
      var p = priceSet(r.model, state.input, state.offpeak);
      th += '<tr' + (i === 0 ? ' class="kr-top"' : '') + '><td>' + (i + 1) + '</td>' +
        '<td><b>' + esc(r.model.name) + '</b><br><span class="kr-mute">' + esc(r.provider.name) + ' · ' + esc(r.model.tier || '') + '</span></td>' +
        '<td>' + money(p.input) + '</td><td>' + money(p.cached_input) + '</td><td>' + money(p.output) + '</td>' +
        '<td>' + fmt(r.perRequest) + '</td><td><b>' + fmt(r.perMonth) + '</b></td></tr>';
    });
    $('kr-tbody').innerHTML = th;
    $('kr-count').textContent = rows.length + ' Modelle, ' + DATA.providers.length + ' Anbieter';

    // Anstehende Preisänderungen
    var upcoming = [];
    DATA.providers.forEach(function (prov) {
      prov.models.forEach(function (m) {
        if (m.scheduled) upcoming.push({ prov: prov, m: m });
      });
    });
    if (upcoming.length) {
      $('kr-changes').hidden = false;
      $('kr-changes-list').innerHTML = upcoming.map(function (u) {
        return '<li><b>' + esc(u.m.name) + '</b> (' + esc(u.prov.name) + '): ' + esc(u.m.scheduled.note) + '</li>';
      }).join('');
    }

    // Quellen mit Stand
    $('kr-sources').innerHTML = DATA.providers.map(function (p) {
      return '<li><a href="' + p.source.url + '" rel="noopener">' + esc(p.name) + ' — offizielle Preisliste</a>, abgerufen am ' + deDate(p.source.retrieved) + '</li>';
    }).join('') +
      '<li><a href="' + DATA.fx.source + '" rel="noopener">EZB-Referenzkurs Euro/US-Dollar</a> (' + DATA.fx.usd_per_eur + '), Stand ' + deDate(DATA.fx.stand) + '</li>';
    $('kr-stand').textContent = deDate(DATA.stand);

    writeHash();
  }

  function money(v) {
    if (v == null) return '–';
    var sym = state.cur === 'EUR' ? '€' : '$';
    var x = state.cur === 'EUR' ? v / DATA.fx.usd_per_eur : v;
    return x.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 3 }) + ' ' + sym;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function deDate(iso) {
    var p = iso.split('-'); return p[2] + '.' + p[1] + '.' + p[0];
  }

  /* ---------- Events ---------- */
  function bind() {
    $('kr-preset').addEventListener('change', function () {
      var p = PRESETS[this.value];
      state.preset = this.value;
      if (this.value !== 'custom') {
        state.input = p.input; state.output = p.output; state.requests = p.requests; state.cache = p.cache;
        syncInputs();
      }
      render();
    });
    [['kr-input', 'input'], ['kr-output', 'output'], ['kr-requests', 'requests']].forEach(function (pair) {
      $(pair[0]).addEventListener('input', function () {
        state[pair[1]] = clampInt(this.value, 1, 10000000, state[pair[1]]);
        state.preset = 'custom'; $('kr-preset').value = 'custom';
        render();
      });
    });
    $('kr-cache').addEventListener('input', function () {
      state.cache = clampInt(this.value, 0, 100, 0);
      this.style.setProperty('--fill', state.cache + '%');
      $('kr-cache-val').textContent = state.cache + ' %';
      render();
    });
    $('kr-batch').addEventListener('change', function () { state.batch = this.checked; render(); });
    $('kr-offpeak').addEventListener('change', function () { state.offpeak = this.checked; render(); });
    document.querySelectorAll('input[name="kr-cur"]').forEach(function (r) {
      r.addEventListener('change', function () { state.cur = this.value; render(); });
    });
    $('kr-copy').addEventListener('click', function () {
      var url = location.href;
      var done = function () { $('kr-copy').textContent = 'Link kopiert ✓'; setTimeout(function () { $('kr-copy').textContent = 'Szenario-Link kopieren'; }, 2000); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done, done);
      else done();
    });
  }

  function syncInputs() {
    $('kr-input').value = state.input;
    $('kr-output').value = state.output;
    $('kr-requests').value = state.requests;
    $('kr-cache').value = state.cache;
    $('kr-cache').style.setProperty('--fill', state.cache + '%');
    $('kr-cache-val').textContent = state.cache + ' %';
    $('kr-batch').checked = state.batch;
    $('kr-offpeak').checked = state.offpeak;
    $('kr-preset').value = state.preset;
    document.querySelectorAll('input[name="kr-cur"]').forEach(function (r) { r.checked = r.value === state.cur; });
  }

  /* ---------- Start ---------- */
  readHash();
  fetch('/data/llm-api-preise.json').then(function (r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function (d) {
    DATA = d;
    bind();
    syncInputs();
    render();
  }).catch(function (e) {
    $('kr-best').innerHTML = '<strong>Preisdaten konnten nicht geladen werden.</strong> Bitte Seite neu laden. (' + esc(e.message) + ')';
  });
})();
