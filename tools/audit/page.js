// Shared by the audit scripts: serve the built page (index.html and media/ at the repo root) on a free
// local port, open it in headless Chromium with ?debug (which exposes window.__td) and the intro skipped,
// and collect page errors. Needs Playwright with Chromium; the page loads three.js and its fonts from the
// network, as it does for a reader.
'use strict';
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml' };

function serve(root) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split(/[?#]/)[0]);
      if (p.endsWith('/')) p += 'index.html';
      const f = path.join(root, path.normalize(p));
      if (!f.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
      fs.readFile(f, (err, buf) => {
        if (err) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': TYPES[path.extname(f).toLowerCase()] || 'application/octet-stream' });
        res.end(buf);
      });
    });
    srv.listen(0, '127.0.0.1', () => resolve({ url: `http://127.0.0.1:${srv.address().port}/`, close: () => srv.close() }));
  });
}

function playwright() {
  try { return require('playwright'); } catch (e) {
    console.error('These scripts need Playwright with Chromium: npm install playwright && npx playwright install chromium');
    process.exit(2);
  }
}

// the scene ids of the tour, in order
function sceneIds() { return JSON.parse(fs.readFileSync(path.join(ROOT, 'build', 'story.json'))).events.map(e => e.id); }

// the pinned copies of the page's scripts (tools/audit/vendor.py), if they are there: the checks run offline
// and always on the same three.js; else the browser fetches them as a reader's does
function vendored() {
  const map = {}, crypto = require('crypto');
  let files = [];
  try { files = JSON.parse(fs.readFileSync(path.join(__dirname, 'vendor.json'))).files; } catch (e) { return map; }
  files.forEach(f => {
    const p = path.join(ROOT, 'cache', 'vendor', f.url.split('/npm/')[1].replace(/\//g, '_'));
    try { const buf = fs.readFileSync(p); if (crypto.createHash('sha256').update(buf).digest('hex') === f.sha256) map[f.url] = buf; } catch (e) {}
  });
  return map;
}
const FONT_RE = /^https:\/\/fonts\.(googleapis|gstatic)\.com\//;   // looks only: a font that does not load is no error
async function open(opts = {}) {
  const vend = vendored();
  if (process.env.TENDAYS_OFFLINE && !Object.keys(vend).length) throw new Error('offline, and no pinned copies of the page\'s scripts: run python3 -I tools/audit/vendor.py first');
  const { chromium } = playwright(), srv = await serve(opts.root || ROOT);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: opts.viewport || { width: 1280, height: 800 } });
  const errors = [];
  // offline (TENDAYS_OFFLINE=1): nothing leaves this machine; any request that would is refused, and is an
  // error unless it is a font (registered first, so the routes after it are tried before it)
  if (process.env.TENDAYS_OFFLINE) await page.route(/^https?:\/\/(?!127\.0\.0\.1[:/])/, route => route.abort());
  if (Object.keys(vend).length) await page.route('https://cdn.jsdelivr.net/**', route => {
    const buf = vend[route.request().url()];
    return buf ? route.fulfill({ status: 200, contentType: 'text/javascript', body: buf }) : route.continue();
  });
  page.on('pageerror', e => errors.push(`${e.message} ${((e.stack || '').split('\n')[1] || '').trim()}`));
  page.on('requestfailed', r => { if (!FONT_RE.test(r.url())) errors.push(`request failed: ${r.url()}`); });
  await page.addInitScript(() => { try { localStorage.setItem('tendays-intro-seen', '1'); } catch (e) {} });
  await page.goto(`${srv.url}index.html?debug${opts.hash ? '#' + opts.hash : ''}`, { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => document.getElementById('loading').hidden, null, { timeout: 180000 });
  // norender: the page's clock runs without drawing, at full speed (headless Chromium draws this page at
  // about four frames a second, which stretches every walk, fight and camera move); for measuring, not
  // for screenshots. A check that projects onto the screen must update the camera's matrices itself.
  if (opts.norender) await page.evaluate(() => { window.__td.norender = true; });
  return { page, errors, close: async () => { await browser.close(); srv.close(); } };
}

// the scene played as a reader comes to it: the scene before it staged at once and finished, then this one
// selected as from the timeline, its walks and fights running at their own pace
async function play(page, id, all) {
  const prev = all[all.indexOf(id) - 1];
  if (prev) { await page.evaluate((p) => { window.__td.select(p, { instant: true }); window.__td.finish(); }, prev); await page.waitForTimeout(800); }
  await page.evaluate((id) => window.__td.select(id), id);
}
// the scene staged at once, its walks finished, the camera at its close frame and held there
async function stage(page, id, wait = 600) {
  await page.evaluate((id) => { const td = window.__td; td.select(id, { instant: true }); td.finish(); td.flyClose(); td.still(); }, id);
  await page.waitForTimeout(wait);
}

module.exports = { ROOT, open, serve, stage, play, sceneIds };
