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

async function open(opts = {}) {
  const { chromium } = playwright(), srv = await serve(opts.root || ROOT);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: opts.viewport || { width: 1280, height: 800 } });
  const errors = [];
  page.on('pageerror', e => errors.push(`${e.message} ${((e.stack || '').split('\n')[1] || '').trim()}`));
  page.on('requestfailed', r => errors.push(`request failed: ${r.url()}`));
  await page.addInitScript(() => { try { localStorage.setItem('tendays-intro-seen', '1'); } catch (e) {} });
  await page.goto(`${srv.url}index.html?debug${opts.hash ? '#' + opts.hash : ''}`, { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => document.getElementById('loading').hidden, null, { timeout: 180000 });
  return { page, errors, close: async () => { await browser.close(); srv.close(); } };
}

// the scene staged at once, its walks finished, the camera at its close frame and held there
async function stage(page, id, wait = 600) {
  await page.evaluate((id) => { const td = window.__td; td.select(id, { instant: true }); td.finish(); td.flyClose(); td.still(); }, id);
  await page.waitForTimeout(wait);
}

module.exports = { ROOT, open, serve, stage, sceneIds };
