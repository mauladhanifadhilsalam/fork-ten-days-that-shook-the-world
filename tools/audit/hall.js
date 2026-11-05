#!/usr/bin/env node
// node tools/audit/hall.js [--phone] [--only ID,ID] — the meeting-hall scenes (a scene whose place has a hall):
// who sits and stands where, and the walks out and in, as the scene plays, sampled ten times a second.
//   seat      a seated delegate not on a bench seat of its block, or two people within 0.9 m of each other
//   stand     one standing on a bench, or outside the hall
//   platform  a body Reed puts on the platform not up on it
//   speaker   the scene's speaker not at the reading stand
//   bench     a sample of someone walking across a bench, not along a row or an aisle
//   wall      a sample of someone walking through the hall's walls (anywhere but the door)
//   through   a sample of someone walking within 0.7 m of a person standing (who should have made way)
//   squeeze   a sample of someone passing within 0.7 m of one who stays seated in the same row: squeezing
//             past their knees to the aisle (counted, not a failure: the row's other end had more in the way)
//   exit      one walking out still in the hall at the end, or one walking in not in its seat
//   frame     the camera's hall shots leaving out the hall (overview), the walkers' way (walk), or the
//             speaker (front), in the part of the screen beside the card
// Exits 1 on any seat, stand, platform, speaker, exit or frame finding, or more than 1% bench or wall samples,
// or 3% through.
'use strict';
const { open, sceneIds, ROOT } = require('./page');
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; }, phone = args.includes('--phone');
(async () => {
  const all = sceneIds(), { page, errors, close } = await open({ hash: all[0], norender: true, viewport: phone ? { width: 390, height: 844 } : undefined });
  // the scenes set in a hall, from the built story
  const S = JSON.parse(require('fs').readFileSync(require('path').join(ROOT, 'build', 'story.json')));
  const ids = opt('--only') ? opt('--only').split(',') : S.events.filter(e => (S.places[e.loc] || {}).hall).map(e => e.id);
  const T = { samples: 0, bench: 0, wall: 0, through: 0, squeeze: 0 }, hard = { seat: 0, stand: 0, platform: 0, speaker: 0, exit: 0, frame: 0 }, rows = [];
  for (const id of ids) {
    await page.evaluate((id) => { const td = window.__td; td.select(id, { instant: true }); td.finish(); td.still(); }, id);
    await page.waitForTimeout(300);
    // where everyone sits and stands, before anyone moves
    const st = await page.evaluate(() => {
      const td = window.__td, H = td.hall(), out = { seat: [], stand: [], platform: [], speaker: [], walkEnd: 0 };
      const uv = (x, y) => { const dx = x - H.c[0], dy = y - H.c[1]; return [dx * H.f[0] + dy * H.f[1], dx * H.lf[0] + dy * H.lf[1]]; };
      const onBench = (u, v) => { for (let r = 0; r < H.rows; r++) { const ur = H.uf - r * H.rp; if (u > ur - 0.45 && u < ur + 0.56) for (const b in H.blocks) if (Math.abs(v - H.blocks[b]) < H.bw / 2) return true; } return false; };
      const gs = td.groups().filter(g => g.hall), still = [];
      gs.forEach(g => g.members.forEach(m => {
        const p = uv(m.home ? H.c[0] + H.f[0] * m.home.u + H.lf[0] * m.home.v : m.x, m.home ? H.c[1] + H.f[1] * m.home.u + H.lf[1] * m.home.v : m.y), u = p[0], v = p[1];
        if (m.walkPath) out.walkEnd = Math.max(out.walkEnd, m.walkAt + 0.6 + m.walkPath.len / (1.6 * 2));
        if (m.enter) return;   // not in the hall yet
        still.push([u, v, g.label]);
        if (g.speaker) { if (Math.hypot(u - (H.tribune[0] + 0.7), v - H.tribune[1]) > 0.3 || Math.abs(m.home.hy - H.Hp) > 0.01) out.speaker.push(g.label); return; }
        if (g.bench === 'platform') { if (u < H.L / 2 - H.Dp || Math.abs(m.home.hy - H.Hp) > 0.01) out.platform.push(g.label); return; }
        if (m.seat) {
          const ur = H.uf - m.seat.row * H.rp;
          if (Math.abs(u - ur) > 0.05 || Math.abs(v - H.blocks[m.seat.block]) > H.bw / 2) out.seat.push(g.label + ' off its bench');
        } else if (m.home.hy < 1 && (onBench(u, v) || Math.abs(u) > H.L / 2 || Math.abs(v) > H.W / 2)) out.stand.push(g.label);
      }));
      for (let i = 0; i < still.length; i++) for (let j = i + 1; j < still.length; j++) if (Math.hypot(still[i][0] - still[j][0], still[i][1] - still[j][1]) < 0.9) out.seat.push(still[i][2] + ' on ' + still[j][2]);
      out.n = still.length;
      return out;
    });
    // the camera's shots: what each leaves out of the clear part of the screen
    const fr = await page.evaluate(() => {
      const td = window.__td, H = td.hall(), bc = td.hallShots(), cam = td.camera.clone(), W = innerWidth, Hh = innerHeight;
      if (!bc) return ['no hall shots'];
      const panel = document.getElementById('panel'), pr = panel.getBoundingClientRect();
      const box = W < 700 ? [8, W - 8, 60, pr.top - 8] : [20, W - pr.width - 30, 90, Hh - 110];
      const at = (u, v) => [H.c[0] + H.f[0] * u + H.lf[0] * v, H.c[1] + H.f[1] * u + H.lf[1] * v];
      const gs = td.groups().filter(g => g.hall), walkers = [], speaker = gs.filter(g => g.speaker)[0];
      gs.forEach(g => g.members.forEach(m => { if (m.walkPath && m.leave) m.walkPath.pts.forEach(p => { if (p.x != null) walkers.push([p.x, p.y]); }); }));
      const bad = [];
      bc.steps.forEach((s, i) => {
        cam.position.copy(s.fr.pos); cam.lookAt(s.fr.target); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
        const kind = i === 0 ? 'over' : i === bc.steps.length - 1 ? 'front' : 'walk';
        const pts = kind === 'over' ? [at(-H.L / 2, H.W / 2), at(-H.L / 2, -H.W / 2), at(H.L / 2, H.W / 2), at(H.L / 2, -H.W / 2)]
          : kind === 'walk' ? walkers.filter((p, k) => k % 2 === 0) : speaker ? [[speaker.members[0].x, speaker.members[0].y]] : [];
        let off = 0;
        pts.forEach(p => { const v = new td.camera.position.constructor(p[0], 1.5, -p[1]).project(cam), x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * Hh; if (v.z > 1 || x < box[0] || x > box[1] || y < box[2] || y > box[3]) off++; });
        if (off > (kind === 'walk' ? pts.length * 0.1 : 0)) bad.push(`${kind}: ${off} of ${pts.length} off`);
      });
      return bad;
    });
    // the walks, sampled as the hall's clock runs from the start
    await page.evaluate(() => { window.__td.hallGo(0); window.__hv = { samples: 0, bench: 0, wall: 0, through: 0, squeeze: 0, who: {} }; });
    const secs = Math.min(60, st.walkEnd + 2);
    for (let k = 0; k < secs * 10; k++) {
      await page.waitForTimeout(100);
      await page.evaluate(() => {
        const td = window.__td, H = td.hall(), V = window.__hv;
        const uv = (x, y) => { const dx = x - H.c[0], dy = y - H.c[1]; return [dx * H.f[0] + dy * H.f[1], dx * H.lf[0] + dy * H.lf[1]]; };
        const gs = td.groups().filter(g => g.hall), walkers = [], others = [];
        gs.forEach(g => g.members.forEach(m => { if (m.gone || m.dx == null) return; (m.walk ? walkers : others).push({ m, g, p: uv(m.dx, m.dy) }); }));
        walkers.forEach(w => {
          const [u, v] = w.p; V.samples++;
          const own = w.m.home && Math.hypot(u - w.m.home.u, v - w.m.home.v) < 0.75;   // rising from one's own seat
          if (w.m.hy < 0.1 && !own) for (let r = 0; r < H.rows; r++) { const ur = H.uf - r * H.rp; if (u > ur - 0.45 && u < ur + 0.56) for (const b in H.blocks) if (Math.abs(v - H.blocks[b]) < H.bw / 2 - 0.1) { V.bench++; V.who[w.g.label + ' bench'] = (V.who[w.g.label + ' bench'] || 0) + 1; r = H.rows; break; } }
          const inHall = Math.abs(u) < H.L / 2 && Math.abs(v) < H.W / 2, atDoor = Math.abs(v) < 1.3 && u < -H.L / 2 + 0.6;
          if (!inHall && !atDoor) { V.wall++; V.who[w.g.label + ' wall'] = (V.who[w.g.label + ' wall'] || 0) + 1; }
          let near = null;
          others.forEach(o => { if (!near && Math.hypot(o.p[0] - u, o.p[1] - v) < 0.7 && Math.abs((o.m.hy || 0) - (w.m.hy || 0)) < 1) near = o; });
          if (near) {
            const sq = near.m.seat && w.m.home && w.m.home.u != null && Math.abs(near.m.seat.u + 0.7 - u) < 0.6;
            if (sq) V.squeeze++; else { V.through++; const k = w.g.label + ' through ' + near.g.label; V.who[k] = (V.who[k] || 0) + 1; }
          }
        });
      });
    }
    const v = await page.evaluate(() => {
      const td = window.__td, H = td.hall(), out = window.__hv; out.exit = [];
      td.groups().filter(g => g.hall).forEach(g => g.members.forEach(m => {
        if (m.leave && !m.gone) out.exit.push(g.label + ' still in the hall');
        if (m.enter && (m.gone || m.walk || Math.hypot(m.x - (H.c[0] + H.f[0] * m.home.u + H.lf[0] * m.home.v), m.y - (H.c[1] + H.f[1] * m.home.u + H.lf[1] * m.home.v)) > 0.1)) out.exit.push(g.label + ' not in its seat');
      }));
      return out;
    });
    ['samples', 'bench', 'wall', 'through', 'squeeze'].forEach(k => { T[k] += v[k]; });
    hard.seat += st.seat.length; hard.stand += st.stand.length; hard.platform += st.platform.length; hard.speaker += st.speaker.length; hard.exit += v.exit.length; hard.frame += fr.length;
    rows.push(`${id}: ${st.n} in the hall; walking samples ${v.samples}: bench ${v.bench}, wall ${v.wall}, through ${v.through}, squeeze ${v.squeeze}`
      + [].concat(st.seat.slice(0, 3), st.stand.slice(0, 3), st.platform.slice(0, 3), st.speaker, v.exit.slice(0, 3), fr).map(x => '\n    ' + x).join('')
      + Object.keys(v.who).sort((a, b) => v.who[b] - v.who[a]).slice(0, 4).map(k => `\n    ${k}: ${v.who[k]}`).join(''));
  }
  rows.forEach(r => console.log(r));
  const pc = k => T.samples ? T[k] / T.samples : 0;
  console.log(`\n${ids.length} hall scenes${phone ? ' (phone)' : ''}; walking samples ${T.samples}: bench ${(100 * pc('bench')).toFixed(1)}%, wall ${(100 * pc('wall')).toFixed(1)}%, through ${(100 * pc('through')).toFixed(1)}%, squeeze ${(100 * pc('squeeze')).toFixed(1)}%`);
  console.log(`seat ${hard.seat}, stand ${hard.stand}, platform ${hard.platform}, speaker ${hard.speaker}, exit ${hard.exit}, frame ${hard.frame}`);
  console.log('page errors:', errors.length ? errors.slice(0, 5).join(' | ') : 'none');
  await close();
  const fail = errors.length || Object.values(hard).some(n => n) || pc('bench') > 0.01 || pc('wall') > 0.01 || pc('through') > 0.03;
  process.exit(fail ? 1 : 0);
})();
