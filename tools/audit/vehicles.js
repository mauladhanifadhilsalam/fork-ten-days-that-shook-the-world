#!/usr/bin/env node
// node tools/audit/vehicles.js [--secs 14] [--only ID,ID] — vehicles and what is in their way, as the scenes
// play: every scene with a vehicle moving (on a route, coming up into a fight, or patrolling), from the scene
// before, sampled four times a second for --secs seconds. For each moving vehicle in each sample:
//   inside   someone stands inside its drawn outline
//   overlap  its outline overlaps a gun, barricade, trench, heap, fire or other vehicle
//   held     it is stopped by someone or something in its way
//   late     a second after its walk is over (the walk waits up to 8 s for a vehicle held up), it is still
//            short of its journey's end
// Exits 1 if, over all samples, more than 2.5% have someone inside, 1% overlap something, or 15% are held,
// or if any vehicle is still short of its end after its walk.
'use strict';
const { open, play, sceneIds } = require('./page');
const LIMITS = { inside: 0.025, overlap: 0.01, held: 0.15 };
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
(async () => {
  const secs = +opt('--secs', 14), all = sceneIds(), { page, errors, close } = await open({ hash: all[0], norender: true });
  let ids = opt('--only') ? opt('--only').split(',') : [];
  if (!ids.length) for (const id of all) {   // the scenes with a vehicle that moves
    if (await page.evaluate((id) => { const td = window.__td; td.select(id, { instant: true });
      return td.movers().some(mv => mv.veh && !mv.arc && !mv.m.done) || td.groups().some(g => (g.props || []).some(p => ['car', 'truck', 'armoured', 'cab', 'tram'].includes(p.k) && (p.path || p.ein))); }, id)) ids.push(id);
  }
  const T = { samples: 0, inside: 0, overlap: 0, held: 0, late: 0 }, rows = [];
  for (const id of ids) {
    await play(page, id, all);
    await page.evaluate(() => { window.__va = { samples: 0, inside: 0, overlap: 0, held: 0, last: {}, walkEnd: null, late: 0 }; });
    for (let k = 0; k < secs * 4; k++) {
      await page.waitForTimeout(250);
      await page.evaluate(() => {
        const td = window.__td, V = window.__va, C = 2, folk = td.folk(), HL = td.halfLen;
        const OB = td.obst || { barricade: [2.9, 0.65], barricade2: [2.9, 0.65], gun: [0.9, 1.9], mg: [0.45, 0.7], armoured: [1.05, 2.7], truck: [1.05, 2.9], car: [0.95, 2.3], cab: [0.8, 2.4], trench: [3.0, 1.0], logs: [0.8, 0.8], rifles: [0.9, 0.9] };
        const HW = td.halfW || { car: 0.95, truck: 1.05, armoured: 1.05, cab: 0.8, tram: 1.2 };
        // boxes a tenth smaller than drawn, so grazing does not count
        const box = (x, y, yaw, w, l) => ({ x, y, ax: [Math.cos(yaw), Math.sin(yaw)], bx: [Math.sin(yaw), -Math.cos(yaw)], w: w * C * 0.9, l: l * C * 0.9 });
        const proj = (B, d) => B.w * Math.abs(B.ax[0] * d[0] + B.ax[1] * d[1]) + B.l * Math.abs(B.bx[0] * d[0] + B.bx[1] * d[1]);
        const hit = (A, B) => [A.ax, A.bx, B.ax, B.bx].every(d => Math.abs((B.x - A.x) * d[0] + (B.y - A.y) * d[1]) < proj(A, d) + proj(B, d));
        const inBox = (B, x, y) => { const dx = x - B.x, dy = y - B.y; return Math.abs(dx * B.ax[0] + dy * B.ax[1]) < B.w && Math.abs(dx * B.bx[0] + dy * B.bx[1]) < B.l; };
        const cars = [], things = [];
        td.movers().forEach(mv => {
          if (!mv.veh || mv.arc || mv.lx == null || (mv.handover && mv.f >= 1)) return;
          const L = V.last[mv.m.who + mv.m.from]; let yaw = mv.yawNow;
          if (yaw == null && L && Math.hypot(mv.lx - L[0], mv.ly - L[1]) > 0.05) yaw = Math.atan2(mv.lx - L[0], -(mv.ly - L[1]));
          if (yaw == null) yaw = L ? L[2] : 0; V.last[mv.m.who + mv.m.from] = [mv.lx, mv.ly, yaw];
          if (mv.f > 0 && (mv.f < 1 || mv.lag > 0.5)) cars.push({ B: box(mv.lx, mv.ly, yaw, HW[mv.veh] || 1, HL[mv.veh] || 2.5), held: mv.held > 0.3, self: null });
        });
        td.groups().forEach(g => (g.props || []).forEach(pr => {
          const ax = pr.aside ? pr.aside.cx : 0, ay = pr.aside ? pr.aside.cy : 0;
          if (OB[pr.k] && !pr.ship) things.push({ pr, B: box(pr.x + ax, pr.y + ay, pr.yaw, OB[pr.k][0], OB[pr.k][1]) });
          if (HL[pr.k] && (pr.path || pr.ein)) cars.push({ B: box(pr.x, pr.y, pr.yaw, HW[pr.k], HL[pr.k]), held: pr.held > 0.3 || !!(pr.ein && pr.ein.held > 0.3), self: pr });
        }));
        // a vehicle on a route at its journey's end once its walk is over (at most 8 s of waiting after it)
        if (!td.walk() && V.walkEnd == null) V.walkEnd = performance.now();
        if (V.walkEnd != null && performance.now() - V.walkEnd > 1000) td.movers().forEach(mv => { if (mv.veh && !mv.arc && !mv.m.done && mv.lag > 2) V.late++; });
        cars.forEach(c => {
          V.samples++; if (c.held) V.held++;
          if (folk.some(f => !f.walker && f.m && f.m.pose !== 'fallen' && inBox(c.B, f.x, f.y))) V.inside++;
          if (things.some(p => p.pr !== c.self && hit(c.B, p.B))) V.overlap++;
        });
      });
    }
    const v = await page.evaluate(() => window.__va);
    ['samples', 'inside', 'overlap', 'held', 'late'].forEach(k => { T[k] += v[k]; });
    rows.push([id, v]);
  }
  await close();
  const pc = (n) => T.samples ? (100 * n / T.samples).toFixed(1) + '%' : '-';
  console.log(`${ids.length} scenes with a moving vehicle, ${T.samples} vehicle samples: someone inside ${pc(T.inside)}, overlapping something ${pc(T.overlap)}, held ${pc(T.held)}`);
  rows.forEach(([id, v]) => { if (v.late || (v.samples && (v.inside / v.samples > 0.1 || v.overlap / v.samples > 0.05 || v.held / v.samples > 0.4))) console.log(`  ${id}: ${v.samples} samples, inside ${v.inside}, overlap ${v.overlap}, held ${v.held}${v.late ? ', still short of its end after its walk ' + v.late : ''}`); });
  const fails = Object.keys(LIMITS).filter(k => T.samples && T[k] / T.samples > LIMITS[k]).map(k => `${k} ${pc(T[k])} > ${100 * LIMITS[k]}%`);
  if (T.late) fails.push(`${T.late} samples of a vehicle still short of its end after its walk`);
  if (errors.length) { fails.push(`${errors.length} page errors`); console.log('page errors:\n  ' + errors.slice(0, 10).join('\n  ')); }
  console.log(fails.length ? 'FAIL: ' + fails.join('; ') : 'ok');
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
