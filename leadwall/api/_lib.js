'use strict';
// Lead-Wall backend helpers. No npm dependencies: Node fetch + crypto only.
const crypto = require('crypto');
const TEXT_VERSION = 'lw-2026-10-20-v1'; // Einwilligungstext Baustein 6.1 (Rechtspapier 20.10.2026)
const SITE = process.env.SITE_URL || 'https://kifachblatt.de';
const API = process.env.API_URL || '';
const FROM = process.env.MAIL_FROM || 'KI Fachblatt <briefing@hob.philipp-paulik.de>';
const REPLY = process.env.MAIL_REPLY_TO || 'redaktion@kifachblatt.de';

const b64 = (b) => Buffer.from(b).toString('base64url');
const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');
const key = () => { const k = process.env.LW_SECRET; if (!k || k.length < 24) throw new Error('LW_SECRET missing'); return k; };
const sign = (msg) => crypto.createHmac('sha256', key()).update(msg).digest('base64url');
const norm = (e) => String(e || '').trim().toLowerCase();
const validEmail = (e) => e.length <= 254 && /^[^\s@<>"']+@[^\s@<>"']+\.[^\s@<>"']{2,}$/.test(e);
const idOf = (email) => sha(norm(email)).slice(0, 40);

// Tokens carry only the id hash, never the address. purpose separates DOI / download / unsubscribe.
function token(purpose, id, ttlSec) {
  const exp = ttlSec ? Math.floor(Date.now() / 1000) + ttlSec : 0;
  const body = [purpose, id, exp].join('.');
  return b64(body) + '.' + sign(body);
}
function verify(purpose, tok) {
  try {
    const [p, s] = String(tok).split('.');
    const body = Buffer.from(p, 'base64url').toString();
    const a = Buffer.from(s || ''); const b = Buffer.from(sign(body));
    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
    const [pur, id, exp] = body.split('.');
    if (pur !== purpose) return null;
    if (Number(exp) && Number(exp) < Date.now() / 1000) return null;
    return id;
  } catch (e) { return null; }
}

// Store: Vercel Blob REST (private-ish, unguessable path) or in-memory for tests.
const mem = new Map();
const store = {
  async get(id) {
    if (process.env.LW_STORE === 'memory') return mem.get(id) || null;
    const base = process.env.BLOB_BASE_URL; // https://<store>.public.blob.vercel-storage.com
    const r = await fetch(base + '/optin/' + id + '.json?ts=' + Date.now());
    return r.ok ? r.json() : null;
  },
  async put(id, rec) {
    if (process.env.LW_STORE === 'memory') { mem.set(id, rec); return; }
    const r = await fetch('https://blob.vercel-storage.com/optin/' + id + '.json', {
      method: 'PUT',
      headers: { authorization: 'Bearer ' + process.env.BLOB_READ_WRITE_TOKEN, 'x-api-version': '7', 'x-add-random-suffix': '0', 'x-allow-overwrite': '1', 'x-content-type': 'application/json' },
      body: JSON.stringify(rec)
    });
    if (!r.ok) throw new Error('store put ' + r.status);
  }
};

async function sendMail({ to, subject, html, text, headers }) {
  if (process.env.LW_MAIL === 'dry') { sendMail.last = { to, subject, html, text, headers }; return { id: 'dry' }; }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + process.env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({ from: FROM, to: [to], reply_to: REPLY, subject, html, text, headers })
  });
  if (!r.ok) throw new Error('resend ' + r.status);
  return r.json();
}

function cors(req, res) {
  const o = req.headers.origin;
  if (o === SITE || o === SITE.replace('://', '://www.')) res.setHeader('access-control-allow-origin', o);
  res.setHeader('vary', 'origin');
  res.setHeader('access-control-allow-methods', 'POST, OPTIONS');
  res.setHeader('access-control-allow-headers', 'content-type');
  if (req.method === 'OPTIONS') { res.statusCode = 204; res.end(); return true; }
  return false;
}
const json = (res, code, obj) => { res.statusCode = code; res.setHeader('content-type', 'application/json'); res.setHeader('cache-control', 'no-store'); res.end(JSON.stringify(obj)); };
const redirect = (res, url) => { res.statusCode = 303; res.setHeader('location', url); res.setHeader('cache-control', 'no-store'); res.end(); };
const ip = (req) => String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || (req.socket && req.socket.remoteAddress) || '';
const readBody = async (req) => { if (req.body) return typeof req.body === 'string' ? JSON.parse(req.body) : req.body; let d = ''; for await (const c of req) d += c; return d ? JSON.parse(d) : {}; };

module.exports = { TEXT_VERSION, SITE, API, idOf, norm, validEmail, token, verify, store, sendMail, cors, json, redirect, ip, readBody };
