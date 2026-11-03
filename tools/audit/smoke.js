#!/usr/bin/env node
// node tools/audit/smoke.js — every scene of the tour, chosen from the timeline as a reader would: page
// errors, failed requests, and figures or a camera with a coordinate that is not a number. Exits 1 on any.
'use strict';
const { open } = require('./page');
(async () => {
  const { page, errors, close } = await open({ viewport: { width: 900, height: 600 } });
  const res = await page.evaluate(async () => {
    const out = [], ticks = Array.from(document.querySelectorAll('.tick'));
    for (const tick of ticks) {
      tick.click();
      window.__td.finish();
      await new Promise(r => setTimeout(r, 60));
      await new Promise(r => requestAnimationFrame(() => r()));   // one drawn frame: columns move, the camera flies
      const g = window.__td.groups(), c = window.__td.camera.position;
      const nan = g.reduce((a, x) => a + (x.members || []).filter(m => !(isFinite(m.x) && isFinite(m.y) && isFinite(m.yaw))).length, 0) + (isFinite(c.x + c.y + c.z) ? 0 : 1000);
      out.push([location.hash.slice(1), g.length, g.reduce((a, x) => a + (x.members || []).length + (x.props || []).length, 0), nan]);
    }
    return out;
  });
  await close();
  const bad = res.filter(r => r[3]);
  console.log(`${res.length} scenes; busiest: ${res.slice().sort((a, b) => b[2] - a[2]).slice(0, 3).map(r => r[0] + ' ' + r[2]).join(', ')}`);
  console.log(`not-a-number: ${bad.length ? bad.map(r => r[0] + ':' + r[3]).join(', ') : 'none'}`);
  console.log(`page errors: ${errors.length ? '\n  ' + errors.slice(0, 20).join('\n  ') : 'none'}`);
  process.exit(bad.length || errors.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
