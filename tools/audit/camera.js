#!/usr/bin/env node
// node tools/audit/camera.js [--secs 18] [--step N] [--only ID,ID] [--phone] — the camera as the scenes play:
// every scene (every Nth with --step), from the scene before, sampled once a second for --secs seconds.
//   end        how far the camera is from what it looks at when the time is up (it should have come in close)
//   close      the share of the time it is within 220 m (320 m on a phone)
//   on screen  in each close shot, once it has settled (2 s after it starts), the share of the shot's people
//              inside the clear part of the screen (left of the card, or above the sheet on a phone)
//   cut        the scene's time is up less than 3 s after its last close shot starts (Play moves on, cutting it)
// Exits 1 if fewer than 90% of the scenes end within 250 m (360 m on a phone), more than 5% of the settled
// close-shot samples have less than 70% of their people on screen, or any scene cuts its close shots.
'use strict';
const { open, play, sceneIds } = require('./page');
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const phone = args.includes('--phone'), NEAR = phone ? 320 : 220, END = phone ? 360 : 250;
(async () => {
  const secs = +opt('--secs', 18), step = +opt('--step', 1), all = sceneIds();
  const { page, errors, close } = await open({ hash: all[0], norender: true, viewport: phone ? { width: 390, height: 844 } : { width: 1280, height: 800 } });
  const ids = opt('--only') ? opt('--only').split(',') : all.filter((id, i) => i > 0 && (i - 1) % step === 0);
  const rows = [];
  let shots = 0, shotsOff = 0;
  for (const id of ids) {
    await play(page, id, all);
    const t0 = await page.evaluate(() => performance.now() / 1000);
    const ds = [];
    for (let k = 0; k < secs; k++) {
      await page.waitForTimeout(1000);
      const r = await page.evaluate(() => {
        const td = window.__td, c = td.camera, tg = td.controls.target, d = c.position.distanceTo(tg), b = td.bcam && td.bcam(), now = performance.now() / 1000;
        c.updateMatrixWorld();
        let share = null;
        if (b && b.i > 0) {
          const st = b.steps[b.i - 1];
          if (st.site && now - st.at > 2) {
            const W = innerWidth, H = innerHeight, pr = document.getElementById('panel').getBoundingClientRect(), v = new c.position.constructor();
            const box = W <= 760 ? [0, W, 0, pr.height ? pr.top : H] : [0, W - pr.width, 0, H];
            let on = 0; st.site.pts.forEach(q => { v.set(q[0], 0, -q[1]).project(c); const x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * H; if (v.z < 1 && x >= box[0] && x <= box[1] && y >= box[2] && y <= box[3]) on++; });
            share = on / Math.max(1, st.site.pts.length);
          }
        }
        return { d, share };
      });
      ds.push(r.d);
      if (r.share != null) { shots++; if (r.share < 0.7) shotsOff++; }
    }
    const cut = await page.evaluate((t0) => { const b = window.__td.bcam(), dur = window.__td.sceneDur() / 1000; if (!b || !b.steps.length) return false; return b.steps[b.steps.length - 1].at > t0 + dur - 3; }, t0);
    rows.push({ id, end: Math.round(ds[ds.length - 1]), near: ds.filter(d => d <= NEAR).length / ds.length, cut });
  }
  await close();
  const med = (a) => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)] || 0;
  const ended = rows.filter(r => r.end <= END).length;
  console.log(`${rows.length} scenes (${phone ? 'phone' : 'desktop'}): the camera ends a median ${med(rows.map(r => r.end))} m off, ${ended} within ${END} m; within ${NEAR} m ${Math.round(100 * rows.reduce((a, r) => a + r.near, 0) / Math.max(1, rows.length))}% of the time; close shots with under 70% of their people on screen: ${shotsOff} of ${shots} samples`);
  rows.filter(r => r.end > END).forEach(r => console.log(`  ${r.id}: ends ${r.end} m off`));
  rows.filter(r => r.cut).forEach(r => console.log(`  ${r.id}: its last close shot starts less than 3 s before the scene's time is up (cut short when playing)`));
  const fails = [];
  if (rows.some(r => r.cut)) fails.push(`${rows.filter(r => r.cut).length} scenes cut their close shots short`);
  if (ended < 0.9 * rows.length) fails.push(`only ${ended} of ${rows.length} scenes end within ${END} m`);
  if (shots && shotsOff > 0.05 * shots) fails.push(`${shotsOff} of ${shots} close-shot samples leave people off screen`);
  if (errors.length) { fails.push(`${errors.length} page errors`); console.log('page errors:\n  ' + errors.slice(0, 10).join('\n  ')); }
  console.log(fails.length ? 'FAIL: ' + fails.join('; ') : 'ok');
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
