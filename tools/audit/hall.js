#!/usr/bin/env node
// node tools/audit/hall.js [--phone] [--only ID,ID] — the meeting-hall scenes (a scene whose place has a hall):
// who sits and stands where, and the walks out and in, as the scene plays, sampled ten times a second.
//   seat      a seated delegate not on a bench seat of its block, or two people within 0.9 m of each other
//   stand     one standing on a bench, or outside the hall; one in the gallery not on it; anyone in place not at
//             the height of what is drawn under them (a step, a sill, the platform, the gallery: raycast against
//             the hall's own meshes, not worked out again from the layout)
//   platform  a body Reed puts on the platform not up on it
//   speaker   the scene's speaker not at the reading stand
//   bench     a sample of someone walking across a bench or the reading stand, not along a row or an aisle
//   wall      a sample of someone walking through the hall's walls (anywhere but the door)
//   through   a sample of someone walking within 0.7 m of a person of another body standing (who should have
//             made way), not counting those still waiting to walk or done walking
//   crowd     a sample of two people walking within 0.5 m of each other
//   react     the bodies with anyone rising, voting, cheering or hooting, not those pinned for the scene in
//             hall-react.json; or one walking out or in cheering or hooting
//   float     a sample of someone walking more than 0.6 m above or below what is drawn under them
//   table     a sample of two in each other's arms standing in the presidium table
//   short     the scene ending (its last shot held four seconds) before the hall's walks are done
//   squeeze   a sample of someone passing within 0.7 m of one who stays seated in the same row: squeezing
//             past their knees to the aisle (counted, not a failure: the row's other end had more in the way)
//   exit      one walking out still in the hall at the end, or one walking in not in its seat
//   frame     the camera's hall shots leaving out the hall (overview), the walkers' way (walk), or the
//             speaker (front), in the part of the screen beside the card
// Exits 1 on any seat, stand, platform, speaker, exit, react, table, short or frame finding, or more than 1% bench, wall or float
// samples, 3% through or 5% crowd.
'use strict';
const { open, sceneIds, ROOT } = require('./page');
const REACT = require('./hall-react.json');
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; }, phone = args.includes('--phone');
(async () => {
  const all = sceneIds(), { page, errors, close } = await open({ hash: all[0], norender: true, viewport: phone ? { width: 390, height: 844 } : undefined });
  // the scenes set in a hall, from the built story
  const S = JSON.parse(require('fs').readFileSync(require('path').join(ROOT, 'build', 'story.json')));
  const ids = opt('--only') ? opt('--only').split(',') : S.events.filter(e => (S.places[e.loc] || {}).hall).map(e => e.id);
  const T = { samples: 0, bench: 0, wall: 0, through: 0, squeeze: 0, crowd: 0, float: 0 }, hard = { seat: 0, stand: 0, platform: 0, speaker: 0, exit: 0, react: 0, table: 0, short: 0, frame: 0 }, rows = [];
  for (const id of ids) {
    await page.evaluate((id) => { const td = window.__td; td.select(id, { instant: true }); td.finish(); td.still(); }, id);
    await page.waitForTimeout(300);
    // where everyone sits and stands, before anyone moves
    const st = await page.evaluate(() => {
      const td = window.__td, H = td.hall(), out = { seat: [], stand: [], platform: [], speaker: [], walkEnd: 0 };
      const uv = (x, y) => { const dx = x - H.c[0], dy = y - H.c[1]; return [dx * H.f[0] + dy * H.f[1], dx * H.lf[0] + dy * H.lf[1]]; };
      const floor = (x, y, hy) => td.hallFloor(x, y, hy + 1);   // what is drawn under one, from the hall's own meshes
      const onBench = (u, v) => { for (let r = 0; r < H.rows; r++) { const ur = H.uf - r * H.rp; if (u > ur - 0.45 && u < ur + 0.56) for (const b in H.blocks) if (Math.abs(v - H.blocks[b]) < H.bw / 2) return true; } return false; };
      const gs = td.groups().filter(g => g.hall), still = [];
      gs.forEach(g => g.members.forEach(m => {
        const p = uv(m.home ? H.c[0] + H.f[0] * m.home.u + H.lf[0] * m.home.v : m.x, m.home ? H.c[1] + H.f[1] * m.home.u + H.lf[1] * m.home.v : m.y), u = p[0], v = p[1];
        if (m.walkPath) out.walkEnd = Math.max(out.walkEnd, m.walkAt + 0.6 + m.walkPath.len / (1.6 * 2));
        if (m.enter) return;   // not in the hall yet
        still.push([u, v, g.label]);
        const hx = H.c[0] + H.f[0] * m.home.u + H.lf[0] * m.home.v, hyy = H.c[1] + H.f[1] * m.home.u + H.lf[1] * m.home.v, fl = floor(hx, hyy, m.home.hy);
        if (fl == null || Math.abs(m.home.hy - fl) > 0.1) out.stand.push(g.label + ` at ${m.home.hy.toFixed(2)} m over a floor at ${fl == null ? 'none' : fl.toFixed(2)}`);
        if (g.speaker) { if (Math.hypot(u - (H.tribune[0] + 0.7), v - H.tribune[1]) > 0.3 || Math.abs(m.home.hy - H.Hp) > 0.01) out.speaker.push(g.label); return; }
        if (g.bench === 'platform') { if (u < H.L / 2 - H.Dp || Math.abs(v) > H.W / 2 - 1.6 || Math.abs(m.home.hy - H.Hp) > 0.01) out.platform.push(g.label); return; }
        if (m.seat) {
          const ur = H.uf - m.seat.row * H.rp;
          if (Math.abs(u - ur) > 0.05 || Math.abs(v - H.blocks[m.seat.block]) > H.bw / 2) out.seat.push(g.label + ' off its bench');
          if (u > H.L / 2 - H.Dp - 0.9 || u < -H.L / 2 + 1 || Math.abs(v) > H.W / 2 - 1.8) out.seat.push(g.label + ' seated off the floor of the benches');
        } else if (g.bench === 'gallery') {
          if (!H.gal || Math.abs(m.home.hy - H.Hg) > 0.01 || v * -H.view < H.W / 2 - H.Dg + 0.4 || v * -H.view > H.W / 2 - 0.4 || u < -H.L / 2 + 0.4 || u > H.L / 2 - H.Dp - 0.4) out.stand.push(g.label + ' off the gallery');
        } else if (!m.home.sill && (onBench(u, v) || Math.abs(u) > H.L / 2 || Math.abs(v) > H.W / 2)) out.stand.push(g.label);
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
      gs.forEach(g => g.members.forEach(m => { if (m.walkPath) m.walkPath.pts.forEach(p => { if (p.x != null) walkers.push([p.x, p.y, p.h || 0]); }); }));   // out or in, at the height of the floor they are on
      const bad = [];
      bc.steps.forEach((s, i) => {
        cam.position.copy(s.fr.pos); cam.lookAt(s.fr.target); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
        const kind = s.kind; if (kind === 'outside') return;   // the scene's own outside the hall: frames.js measures that
        const pts = kind === 'over' ? [at(-H.L / 2, H.W / 2), at(-H.L / 2, -H.W / 2), at(H.L / 2, H.W / 2), at(H.L / 2, -H.W / 2)]
          : kind === 'walk' ? walkers.filter((p, k) => k % 2 === 0) : speaker ? [[speaker.members[0].x, speaker.members[0].y]] : [];
        let off = 0;
        pts.forEach(p => { const v = new td.camera.position.constructor(p[0], (p[2] || 0) + 1.5, -p[1]).project(cam), x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * Hh; if (v.z > 1 || x < box[0] || x > box[1] || y < box[2] || y > box[3]) off++; });
        if (off > (kind === 'walk' ? pts.length * 0.1 : 0)) bad.push(`${kind}: ${off} of ${pts.length} off`);
      });
      return { bad, start: bc.start, lastAt: bc.steps[bc.steps.length - 1].at };
    });
    if (fr.lastAt != null && fr.lastAt + 4 < fr.start + st.walkEnd) fr.bad.push(`short: the scene ends ${(fr.start + st.walkEnd - fr.lastAt - 4).toFixed(1)} s before its walks are done`);
    const frBad = fr.bad || fr;
    // the walks, sampled as the hall's clock runs from the start
    await page.evaluate(() => { window.__td.hallGo(0); window.__hv = { samples: 0, bench: 0, wall: 0, through: 0, squeeze: 0, crowd: 0, float: 0, who: {} }; });
    const secs = Math.min(60, st.walkEnd + 2);
    for (let k = 0; k < secs * 10; k++) {
      await page.waitForTimeout(100);
      await page.evaluate(() => {
        const td = window.__td, H = td.hall(), V = window.__hv;
        const uv = (x, y) => { const dx = x - H.c[0], dy = y - H.c[1]; return [dx * H.f[0] + dy * H.f[1], dx * H.lf[0] + dy * H.lf[1]]; };
        const gs = td.groups().filter(g => g.hall), walkers = [], others = [];
        gs.forEach(g => g.members.forEach(m => { if (m.gone || m.dx == null) return; (m.walk ? walkers : others).push({ m, g, p: uv(m.dx, m.dy) }); }));
        others.forEach(o => { if (o.m.pose === 'embrace' && Math.abs(o.p[0] - H.tableU) < 0.95 + 0.3 && Math.abs(o.p[1]) < 3.4 + 0.2) { V.table = (V.table || 0) + 1; } });
        walkers.forEach(w => {
          const [u, v] = w.p; V.samples++;
          const own = w.m.home && Math.hypot(u - w.m.home.u, v - w.m.home.v) < 0.75;   // rising from one's own seat
          if ((w.m.hy || 0) > H.Hp - 0.1 && Math.abs(u - H.tribune[0]) < 0.5 + 0.3 && Math.abs(v - H.tribune[1]) < 0.72 + 0.3) { V.bench++; V.who[w.g.label + ' stand'] = (V.who[w.g.label + ' stand'] || 0) + 1; }
          const fl = td.hallFloor(w.m.dx, w.m.dy, (w.m.hy || 0) + 1);
          if (fl == null || Math.abs((w.m.hy || 0) - fl) > 0.6) { V.float++; V.who[w.g.label + ' float'] = (V.who[w.g.label + ' float'] || 0) + 1; }
          if (fl != null && (w.m.hy || 0) - fl < 0.2 && !own) for (let r = 0; r < H.rows; r++) { const ur = H.uf - r * H.rp; if (u > ur - 0.45 && u < ur + 0.56) for (const b in H.blocks) if (Math.abs(v - H.blocks[b]) < H.bw / 2 - 0.1) { V.bench++; V.who[w.g.label + ' bench'] = (V.who[w.g.label + ' bench'] || 0) + 1; r = H.rows; break; } }
          const inHall = Math.abs(u) < H.L / 2 && Math.abs(v) < H.W / 2, atDoor = Math.abs(v) < 1.3 && u < -H.L / 2 + 0.6;
          if (!inHall && !atDoor) { V.wall++; V.who[w.g.label + ' wall'] = (V.who[w.g.label + ' wall'] || 0) + 1; }
          let near = null;
          others.forEach(o => { if (!near && o.g !== w.g && !o.m.walkPath && Math.hypot(o.p[0] - u, o.p[1] - v) < 0.7 && Math.abs((o.m.hy || 0) - (w.m.hy || 0)) < 1) near = o; });
          if (walkers.some(x => x !== w && Math.hypot(x.p[0] - u, x.p[1] - v) < 0.5)) { V.crowd++; V.who[w.g.label + ' crowd'] = (V.who[w.g.label + ' crowd'] || 0) + 1; }
          if (near) {
            const sq = near.m.seat && w.m.home && w.m.home.u != null && Math.abs(near.m.seat.u + 0.7 - u) < 0.6;
            if (sq) V.squeeze++; else { V.through++; const k = w.g.label + ' through ' + near.g.label; V.who[k] = (V.who[k] || 0) + 1; }
          }
        });
      });
    }
    // who answers: the bodies with anyone rising, voting, cheering or hooting, against those pinned for the scene in
    // hall-react.json (so a change to who answers shows as a finding until the pin is changed with it); and no one
    // walking out or in cheering or hooting
    const v = await page.evaluate((pin) => {
      const td = window.__td, H = td.hall(), out = window.__hv; out.exit = []; out.react = []; out.table = out.table || 0;
      const got = new Set();
      td.groups().filter(g => g.hall).forEach(g => g.members.forEach(m => {
        if (m.leave && !m.gone) out.exit.push(g.label + ' still in the hall');
        if (m.react) got.add(g.who + '@' + (g.bench || ''));
        if ((m.pose === 'cheer' || m.pose === 'jeer') && m.walkPath) out.react.push(g.label + ' ' + m.pose + 's walking');
        if (m.enter && (m.gone || m.walk || Math.hypot(m.x - (H.c[0] + H.f[0] * m.home.u + H.lf[0] * m.home.v), m.y - (H.c[1] + H.f[1] * m.home.u + H.lf[1] * m.home.v)) > 0.1)) out.exit.push(g.label + ' not in its seat');
      }));
      if (!pin) out.react.push('no pinned response in hall-react.json');
      else {
        [...got].filter(k => !pin.includes(k)).forEach(k => out.react.push(k + ' answers, not pinned'));
        pin.filter(k => !got.has(k)).forEach(k => out.react.push(k + ' pinned, does not answer'));
      }
      return out;
    }, REACT[id] || null);
    ['samples', 'bench', 'wall', 'through', 'squeeze', 'crowd', 'float'].forEach(k => { T[k] += v[k]; });
    hard.react += v.react.length; hard.table += v.table ? 1 : 0;
    hard.seat += st.seat.length; hard.stand += st.stand.length; hard.platform += st.platform.length; hard.speaker += st.speaker.length; hard.exit += v.exit.length; hard.frame += frBad.filter(x => !/^short/.test(x)).length; hard.short += frBad.filter(x => /^short/.test(x)).length;
    rows.push(`${id}: ${st.n} in the hall; walking samples ${v.samples}: bench ${v.bench}, wall ${v.wall}, through ${v.through}, squeeze ${v.squeeze}, crowd ${v.crowd}, float ${v.float}`
      + [].concat(st.seat.slice(0, 3), st.stand.slice(0, 3), st.platform.slice(0, 3), st.speaker, v.exit.slice(0, 3), v.react.slice(0, 3), v.table ? [`${v.table} samples in each other's arms in the table`] : [], frBad).map(x => '\n    ' + x).join('')
      + Object.keys(v.who).sort((a, b) => v.who[b] - v.who[a]).slice(0, 4).map(k => `\n    ${k}: ${v.who[k]}`).join(''));
  }
  rows.forEach(r => console.log(r));
  const pc = k => T.samples ? T[k] / T.samples : 0;
  console.log(`\n${ids.length} hall scenes${phone ? ' (phone)' : ''}; walking samples ${T.samples}: bench ${(100 * pc('bench')).toFixed(1)}%, wall ${(100 * pc('wall')).toFixed(1)}%, through ${(100 * pc('through')).toFixed(1)}%, crowd ${(100 * pc('crowd')).toFixed(1)}%, squeeze ${(100 * pc('squeeze')).toFixed(1)}%, float ${(100 * pc('float')).toFixed(1)}%`);
  console.log(`seat ${hard.seat}, stand ${hard.stand}, platform ${hard.platform}, speaker ${hard.speaker}, exit ${hard.exit}, react ${hard.react}, table ${hard.table}, short ${hard.short}, frame ${hard.frame}`);
  console.log('page errors:', errors.length ? errors.slice(0, 5).join(' | ') : 'none');
  await close();
  const fail = errors.length || Object.values(hard).some(n => n) || pc('bench') > 0.01 || pc('wall') > 0.01 || pc('through') > 0.03 || pc('crowd') > 0.05 || pc('float') > 0.01;
  process.exit(fail ? 1 : 0);
})();
