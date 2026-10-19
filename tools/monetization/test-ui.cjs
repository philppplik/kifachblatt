// Developer-only UI test (not part of the production build). Needs playwright-core outside the tree:
//   NODE_PATH=/path/to/node_modules SITE_ROOT=site/out PREFIX=fa node tools/monetization/test-ui.cjs
const { chromium } = require('playwright-core');
const http = require('http'), fs = require('fs'), path = require('path');
const P = process.env.PREFIX || 'kfb', EXT = process.env.EXTENSIONLESS === '1' || true;
const root = path.resolve(process.env.SITE_ROOT || '.');
const shots = process.env.SCREENSHOT_DIR || '/tmp/' + P + '-monetization-screenshots'; fs.mkdirSync(shots, { recursive: true });
const types = { '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.png': 'image/png', '.json': 'application/json', '.xml': 'application/xml' };
const server = http.createServer((req, res) => {
  let f = path.join(root, decodeURI(req.url.split('?')[0]));
  if (f.endsWith('/')) f += 'index.html';
  else if (!path.extname(f)) { if (fs.existsSync(f + '.html')) f += '.html'; else if (fs.existsSync(path.join(f, 'index.html'))) f = path.join(f, 'index.html'); }
  try { res.setHeader('Content-Type', types[path.extname(f)] || 'text/html; charset=utf-8'); res.end(fs.readFileSync(f)); } catch (_) { res.statusCode = 404; res.end('x'); }
});
let count = 0; const ok = (v, m) => { if (!v) throw new Error('FAILED: ' + m); count++; };
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r)); const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const werben = EXT ? '/werben' : '/werben/', cookies = EXT ? '/cookies' : '/cookies/', werbung = EXT ? '/werbung' : '/werbung/', ds = EXT ? '/datenschutz' : '/datenschutz/';
  try {
    for (const theme of (process.env.THEMES || 'light').split(',')) for (const [name, w, h] of [['desktop', 1440, 1100], ['tablet', 1024, 900], ['mobile', 390, 844], ['narrow', 320, 760]]) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h } });
      if (theme === 'dark') await ctx.addInitScript(() => { try { localStorage.setItem('fa-theme', 'dark'); } catch (e) {} });
      const page = await ctx.newPage(), reqs = []; page.on('request', r => reqs.push(r.url()));
      await page.goto(base + werben); await page.waitForSelector('#' + P + '-consent:not([hidden])');
      ok(await page.locator('#' + P + '-statistics').isDisabled(), 'stats disabled'); ok(await page.locator('#' + P + '-advertising').isDisabled(), 'ads disabled');
      ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'no overflow ' + name);
      if (name !== 'narrow') await page.screenshot({ path: path.join(shots, P + '-consent-' + theme + '-' + name + '.png') });
      ok(await page.locator('#' + P + '-consent [data-consent="close"], #' + P + '-consent-close').count() === 0, 'no close button'); await page.keyboard.press('Escape'); ok(await page.locator('#' + P + '-consent').isVisible(), 'escape does not dismiss');
      ok(await page.evaluate((P) => localStorage.getItem(P + '-consent-v1') === null, P), 'escape is not consent');
      await page.reload(); await page.waitForSelector('#' + P + '-consent:not([hidden])');
      await page.locator('[data-consent="reject"]').click(); ok(await page.locator('#' + P + '-consent').isHidden(), 'reject closes');
      let s = await page.evaluate((P) => JSON.parse(localStorage.getItem(P + '-consent-v1')), P); ok(s.statistics === false && s.advertising === false, 'rejected stored');
      await page.reload(); ok(await page.locator('#' + P + '-consent').isHidden(), 'persisted'); ok(await page.evaluate((P) => document.cookie.includes(P + '_consent_v1='), P), 'cookie written'); await page.evaluate(() => localStorage.clear()); await page.reload(); ok(await page.locator('#' + P + '-consent').isHidden(), 'cookie fallback persists without localStorage'); await page.goto(base + '/'); ok(await page.locator('#' + P + '-consent').isHidden(), 'no banner on follow-up page'); await page.goto(base + werben);
      if (name !== 'narrow') await page.screenshot({ path: path.join(shots, P + '-werben-' + theme + '-' + name + '.png'), fullPage: true });
      await page.locator('[data-' + P + '-consent-open]').first().click(); ok(await page.locator('#' + P + '-consent').isVisible(), 'reopen');
      await page.locator('[data-consent="all"]').click(); s = await page.evaluate((P) => JSON.parse(localStorage.getItem(P + '-consent-v1')), P); ok(s.statistics === false && s.advertising === false, 'all available = nothing (nothing available)');
      ok(!reqs.some(u => !u.startsWith(base)), 'no external requests ' + reqs.filter(u => !u.startsWith(base)).join(','));
      ok((await page.locator('a[href^="mailto:"]').count()) >= 4, 'mailto links');
      for (const u of ['/', cookies, werbung, ds, '/impressum' + (EXT ? '' : '/')]) { await page.goto(base + u); ok(await page.locator('[data-' + P + '-consent-open]').count() === 1, 'footer button on ' + u); ok(await page.locator('[data-' + P + '-spot]').count() === 0, 'no spot on ' + u); ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'no overflow ' + u + ' ' + name); }
      await page.goto(base + cookies); ok((await page.locator('h1').innerText()) === 'Cookies & Einstellungen', 'cookies h1');
      if (name === 'desktop' || name === 'mobile') { await page.screenshot({ path: path.join(shots, P + '-cookies-' + theme + '-' + name + '.png'), fullPage: true }); await page.goto(base + '/'); await page.locator('[data-consent="reject"]').click().catch(() => {}); await page.screenshot({ path: path.join(shots, P + '-footer-' + theme + '-' + name + '.png'), fullPage: false }); }
      await page.evaluate((P) => { const x = JSON.parse(localStorage.getItem(P + '-consent-v1')); x.at = 0; localStorage.setItem(P + '-consent-v1', JSON.stringify(x)); document.cookie = P + '_consent_v1=' + encodeURIComponent(JSON.stringify(x)) + '; Path=/'; }, P);
      await page.reload(); ok(await page.locator('#' + P + '-consent').isVisible(), 'expiry re-asks');
      await ctx.close();
    }
    console.log(count + ' assertions passed');
  } finally { await browser.close(); server.close(); }
})().catch(e => { console.error(e); server.close(); process.exitCode = 1; });
