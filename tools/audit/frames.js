#!/usr/bin/env node
// node tools/audit/frames.js [--phone] [--only ID,ID] — is what each scene brings in on screen? Every scene
// staged in turn, the camera at its close frame; for each body the scene itself brings in (and Reed), the
// members outside the clear part of the screen the page fits its frames to (td.clearBox): left of the card and
// between the title and the timeline on a desktop (1280 x 800), between the title and the map's buttons above
// the sheet on a phone (390 x 844). Prints the scenes that leave any out, and how many more stand within 24 px of
// its edge (their labels cut by it; the bodies with a third of theirs there are listed); exits 1 if more than 2%
// of such members are out (5% on a phone, whose frame is a third of the size).
'use strict';
const { open, stage, sceneIds } = require('./page');
const args = process.argv.slice(2), phone = args.includes('--phone'), oi = args.indexOf('--only');
(async () => {
  const all = sceneIds(), ids = oi >= 0 ? args[oi + 1].split(',') : all;
  const { page, errors, close } = await open({ hash: all[0], viewport: phone ? { width: 390, height: 844 } : { width: 1280, height: 800 } });
  let tot = 0, off = 0, edge = 0; const bad = [], tight = [];
  for (const id of ids) {
    await stage(page, id, 700);
    const r = await page.evaluate(() => {
      const td = window.__td, _cm = td.camera.updateMatrixWorld(), cam = td.camera, cur = td.cur(), W = innerWidth, H = innerHeight, v = new cam.position.constructor();
      const pr = document.getElementById('panel').getBoundingClientRect(), narrow = W <= 760, E = 24;
      const box = td.clearBox ? td.clearBox() : narrow ? [0, W, 0, pr.height ? pr.top : H] : [0, W - pr.width, 0, H];
      return td.groups().filter(g => g.members && g.members.length && !g.inside && !g.ship && (g.reed || (g.p && g.p.ev === cur.id))).map(g => {
        let n = 0, e = 0; g.members.forEach(m => { v.set(m.x, 0, -m.y).project(cam); const x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * H;
          if (v.z > 1 || x < box[0] || x > box[1] || y < box[2] || y > box[3]) n++; else if (x < box[0] + E || x > box[1] - E || y < box[2] + E || y > box[3] - E) e++; });
        return [g.reed ? 'Reed' : `${g.who}@${g.place}`, n, g.members.length, e];
      });
    });
    r.forEach(([b, n, m, e]) => { tot += m; off += n; edge += e; if (n) bad.push(`${id}: ${b} ${n}/${m} off`); if (e * 3 >= m && e) tight.push(`${id}: ${b} ${e}/${m} at the edge`); });
  }
  await close();
  console.log(`${ids.length} scenes (${phone ? 'phone' : 'desktop'}): ${off} of ${tot} members of the scenes' own bodies off the clear screen, ${edge} more within 24 px of its edge`);
  if (bad.length) console.log('  ' + bad.join('\n  '));
  if (tight.length) console.log('at the edge:\n  ' + tight.join('\n  '));
  if (errors.length) console.log('page errors:\n  ' + errors.slice(0, 20).join('\n  '));
  const fail = errors.length || off > (phone ? 0.05 : 0.02) * tot;
  console.log(fail ? 'FAIL' : 'ok');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
