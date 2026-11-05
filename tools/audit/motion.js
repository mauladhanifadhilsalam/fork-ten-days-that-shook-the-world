#!/usr/bin/env node
// node tools/audit/motion.js [--secs 20] [--only ID,ID] — people on the move, as the scenes play: every scene
// where a fight is acted out (bodies coming up, running off, a sortie, envoys, men rushing a car), from the
// scene before, sampled four times a second. For each person moving in each sample (coming up, running off,
// going out and back, stepping out of a vehicle's way), drawn where the page draws them:
//   wall     standing in a building (not men storming into one: "poured through windows, doors and holes")
//   through  within 0.7 m of a person of another body (walking through them)
// The crowd.js audit measures where everybody ends; this one measures the way there.
// Exits 1 if more than 1% of the moving samples are in a wall, or 3% walk through another body.
'use strict';
const { open, play, sceneIds } = require('./page');
const LIMITS = { wall: 0.01, through: 0.03 };
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
(async () => {
  const secs = +opt('--secs', 20), all = sceneIds(), { page, errors, close } = await open({ hash: all[0], norender: true });
  let ids = opt('--only') ? opt('--only').split(',') : [];
  if (!ids.length) for (const id of all) {
    if (await page.evaluate((id) => { const td = window.__td; td.select(id, { instant: true }); return td.groups().some(g => g.eng || g.sortie || g.carRush); }, id)) ids.push(id);
  }
  const T = { moving: 0, wall: 0, through: 0 }, rows = [];
  for (const id of ids) {
    await play(page, id, all);
    await page.evaluate(() => { window.__mo = { moving: 0, wall: 0, through: 0, who: {} }; });
    for (let k = 0; k < secs * 4; k++) {
      await page.waitForTimeout(250);
      await page.evaluate(() => {
        const td = window.__td, V = window.__mo, folk = td.folk().filter(f => f.m && !f.m.gone && f.m.pose !== 'fallen');
        const grid = {}, key = (x, y) => Math.floor(x / 2) + ',' + Math.floor(y / 2);
        folk.forEach(f => { (grid[key(f.x, f.y)] = grid[key(f.x, f.y)] || []).push(f); });
        folk.forEach(f => {
          const m = f.m; if (!(m.ein || m.eout || m.esort || m.env || m.run || (m.aside && Math.hypot(m.aside.tx - m.aside.cx, m.aside.ty - m.aside.cy) > 0.05))) return;
          V.moving++;
          // a storm pours into the building, through its doors and windows: not counted
          if (td.wallAt(f.x, f.y) && !(m.run && f.g.assault === 'carried')) { V.wall++; V.who[f.g.who + ' wall'] = (V.who[f.g.who + ' wall'] || 0) + 1; }
          const gx = Math.floor(f.x / 2), gy = Math.floor(f.y / 2); let near = null;
          for (let dy = -1; dy <= 1 && !near; dy++) for (let dx = -1; dx <= 1 && !near; dx++) (grid[(gx + dx) + ',' + (gy + dy)] || []).forEach(o => { if (!near && o.g !== f.g && Math.hypot(o.x - f.x, o.y - f.y) < 0.7) near = o; });
          if (near) { V.through++; const w = f.g.who + ' through ' + near.g.who; V.who[w] = (V.who[w] || 0) + 1; }
        });
      });
    }
    const v = await page.evaluate(() => window.__mo);
    ['moving', 'wall', 'through'].forEach(k => { T[k] += v[k]; });
    rows.push([id, v]);
  }
  await close();
  const pc = (n) => T.moving ? (100 * n / T.moving).toFixed(1) + '%' : '-';
  console.log(`${ids.length} scenes with a fight acted out, ${T.moving} samples of people moving: in a wall ${pc(T.wall)}, through another body ${pc(T.through)}`);
  rows.forEach(([id, v]) => { if (v.moving && (v.wall + v.through) / v.moving > 0.03) console.log(`  ${id}: ${v.moving} moving, wall ${v.wall}, through ${v.through}  ${Object.entries(v.who).sort((a, b) => b[1] - a[1]).slice(0, 3).map(e => e[0] + ' ' + e[1]).join('; ')}`); });
  const fails = Object.keys(LIMITS).filter(k => T.moving && T[k] / T.moving > LIMITS[k]).map(k => `${k} ${pc(T[k])} > ${100 * LIMITS[k]}%`);
  if (errors.length) { fails.push(`${errors.length} page errors`); console.log('page errors:\n  ' + errors.slice(0, 10).join('\n  ')); }
  console.log(fails.length ? 'FAIL: ' + fails.join('; ') : 'ok');
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
