#!/usr/bin/env node
// node tools/audit/crowds.js [--json OUT.json] [--shots DIR] [--only ID,ID] — how the people stand, in every
// scene, seen from the scene's own close frame. For each body within 320 m of the frame's target:
//   close   members nearer than 1.3 m to another of the body
//   over    members nearer to another than 0.6 of their drawn size (figures run into each other on screen)
//   wall    members whose drawn figure reaches into a building
//   hid     members whose head the buildings hide from the camera
//   cross   members within 1 m of a member of another body
//   short   bodies drawn with fewer than 90% of the figures they are given (cars' crews aside)
// Gun and machine-gun crews, placed round their gun, are left out. Prints the totals and the bodies that
// stand badly, and exits 1 if the totals pass the limits below (see tools/audit/README.md).
'use strict';
const fs = require('fs');
const { open, stage, sceneIds } = require('./page');
const LIMITS = { cross: 0, short: 0, over: 0.01, wall: 0.01, hid: 0.08 };   // counts, or fractions of all figures

const args = process.argv.slice(2), opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
(async () => {
  // from the first scene on, in order: a frame depends a little on where the camera comes from, so the
  // numbers repeat only along the same path
  const all = sceneIds(), { page, errors, close } = await open({ hash: all[0] });
  const only = opt('--only'), shots = opt('--shots'), ids = only ? only.split(',') : all;
  if (shots) fs.mkdirSync(shots, { recursive: true });
  const res = {};
  for (const id of ids) {
    await stage(page, id, 500);
    res[id] = await page.evaluate(() => {
      const td = window.__td, _cm = td.camera.updateMatrixWorld(), cam = td.camera.position, tg = td.controls.target, camD = cam.distanceTo(tg), FS = Math.max(2, Math.min(7, camD / 85));
      const B = td.bgrid(), inRing = td.inRing, fr = td.frame() || { x: tg.x, y: -tg.z };
      const scaleOf = td.figScale || ((m, F) => (m.room && m.ox == null ? Math.min(F, Math.max(2, m.room / 0.8)) : F));
      function heightAt(x, y) {
        const c = B[Math.floor(x / 100) + ',' + Math.floor(y / 100)]; if (!c) return 0;
        for (const rec of c) { const b = rec.b; if (x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3] && inRing(rec.r, x, y) && !rec.holes.some(q => inRing(q, x, y))) return rec.h || 12; }
        return 0;
      }
      function seen(x, y, h) {
        const cx = cam.x, cy = -cam.z, cz = cam.y, L = Math.hypot(cx - x, cy - y);
        for (let d = 1.2; d < Math.min(L, 220); d += 1.5) { const t = d / L, bh = heightAt(x + (cx - x) * t, y + (cy - y) * t); if (bh && h + (cz - h) * t < bh) return false; }
        return true;
      }
      const near = td.groups().filter(g => g.members && g.members.length && !g.inside && !g.reed && !g.ship && g.cx != null && Math.hypot(g.cx - fr.x, g.cy - fr.y) < 320);
      const bodies = near.map(g => {
        const M = g.members.filter(m => !m.gone && !m.away && m.ox == null), out = { who: g.who, place: g.place, form: g.form || g.assault || '', n: M.length, given: g.n || 0, close: 0, over: 0, wall: 0, hid: 0, cross: 0, nn: 0 };
        if (!M.length) return out;
        let nnS = 0;
        M.forEach(m => {
          let b = 1e9; M.forEach(o => { if (o !== m) b = Math.min(b, Math.hypot(o.x - m.x, o.y - m.y)); });
          const sc = scaleOf(m, FS);
          if (b < 1e8) { nnS += b; if (b < 1.3) out.close++; if (b < 0.6 * sc) out.over++; }
          const r = 0.25 * sc; if ([[r, 0], [-r, 0], [0, r], [0, -r]].some(q => heightAt(m.x + q[0], m.y + q[1]))) out.wall++;
          if (!seen(m.x, m.y, 1.5 * sc)) out.hid++;
          if (near.some(h => h !== g && h.members && h.members.some(o => !o.gone && !o.away && Math.hypot(o.x - m.x, o.y - m.y) < 1.0))) out.cross++;
        });
        out.nn = +(nnS / M.length).toFixed(2);
        return out;
      });
      const short = td.groups().filter(g => g.n && !g.inside && !g.ship && g.members && g.members.length < g.n * 0.9 && !(g.props || []).some(p => p.k === 'armoured'))
        .map(g => `${g.who}@${g.place} ${g.members.length}/${g.n}`);
      return { camD: Math.round(camD), FS: +FS.toFixed(1), bodies, short };
    });
    if (shots) await page.screenshot({ path: `${shots}/${id}.png` });
  }
  await close();
  const tot = { figures: 0, close: 0, over: 0, wall: 0, hid: 0, cross: 0, short: 0 }, flagged = [];
  for (const [id, r] of Object.entries(res)) {
    tot.short += r.short.length; r.short.forEach(s => flagged.push(`${id}: drawn short ${s}`));
    for (const b of r.bodies) {
      tot.figures += b.n; ['close', 'over', 'wall', 'hid', 'cross'].forEach(k => { tot[k] += b[k]; });
      const why = [];
      if (b.n >= 4 && b.over / b.n > 0.3) why.push(`${b.over} run together`);
      if (b.wall >= 2 && b.wall / b.n > 0.15) why.push(`${b.wall} in a wall`);
      if (b.hid >= 3 && b.hid / b.n > 0.3) why.push(`${b.hid} hidden`);
      if (b.cross >= 2) why.push(`${b.cross} in another body`);
      if (why.length) flagged.push(`${id} (figures x${r.FS}): ${b.who}@${b.place}${b.form ? '/' + b.form : ''} n=${b.n} spacing ${b.nn} m: ${why.join(', ')}`);
    }
  }
  if (opt('--json')) fs.writeFileSync(opt('--json'), JSON.stringify(res, null, 1));
  const frac = (k) => tot.figures ? tot[k] / tot.figures : 0, fails = [];
  ['cross', 'short'].forEach(k => { if (tot[k] > LIMITS[k]) fails.push(`${k} ${tot[k]} > ${LIMITS[k]}`); });
  ['over', 'wall', 'hid'].forEach(k => { if (frac(k) > LIMITS[k]) fails.push(`${k} ${(100 * frac(k)).toFixed(1)}% > ${100 * LIMITS[k]}%`); });
  if (errors.length) fails.push(`${errors.length} page errors`);
  console.log(`${ids.length} scenes, ${tot.figures} figures: ${tot.close} closer than 1.3 m, ${tot.over} run together, ${tot.wall} in a wall, ${tot.hid} hidden, ${tot.cross} in another body; ${tot.short} bodies drawn short`);
  if (flagged.length) console.log('bodies that stand badly:\n  ' + flagged.join('\n  '));
  if (errors.length) console.log('page errors:\n  ' + errors.slice(0, 20).join('\n  '));
  console.log(fails.length ? 'FAIL: ' + fails.join('; ') : 'ok');
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
