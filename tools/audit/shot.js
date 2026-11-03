#!/usr/bin/env node
// Screenshots of scenes, 1280 x 800, to OUTDIR/<id>.png:
//   node tools/audit/shot.js OUTDIR ID...                    each scene in its own close frame, at once
//   node tools/audit/shot.js OUTDIR --close 110 ID[:WHO[:PLACE]]...
//                                                            the camera 110 m from a body of the scene (its
//                                                            largest, or WHO's, or WHO's at PLACE), from the
//                                                            frame's heading: how the people stand, close up
//   node tools/audit/shot.js OUTDIR --play ID...             arrive from the scene before and let the scene
//                                                            play at its own pace, the camera following
//                                                            (what a reader sees; slow)
'use strict';
const fs = require('fs');
const { open, stage, sceneIds } = require('./page');
const args = process.argv.slice(2), out = args.shift();
if (!out || !args.length) { console.error('usage: shot.js OUTDIR [--close METRES | --play] ID...'); process.exit(2); }
let mode = 'frame', dist = 110;
if (args[0] === '--close') { mode = 'close'; args.shift(); dist = +args.shift(); }
else if (args[0] === '--play') { mode = 'play'; args.shift(); }
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const all = sceneIds(), { page, errors, close } = await open({ hash: all[0] });
  for (const spec of args) {
    const [id, who, place] = spec.split(':');
    if (all.indexOf(id) < 0) { console.log(`${id}: no such scene`); continue; }
    let note = '', name = id;
    if (mode === 'play') {
      const prev = all[all.indexOf(id) - 1];
      if (prev) { await page.evaluate((p) => { window.__td.select(p, { instant: true }); window.__td.finish(); }, prev); await page.waitForTimeout(2500); }
      const w = await page.evaluate((id) => { window.__td.select(id); const w = window.__td.walk(); return w ? w.dur : 0; }, id);
      await page.waitForTimeout(Math.min(60000, w + 4500));
      note = `walk ${Math.round(w)} ms`;
    } else {
      await stage(page, id, mode === 'close' ? 800 : 700);
      if (mode === 'close') {
        note = await page.evaluate(([who, place, D]) => {
          const td = window.__td, c = td.controls, cam = c.object, fr = td.frame() || { x: c.target.x, y: -c.target.z };
          const gs = td.groups().filter(g => g.members && g.members.length && !g.inside && !g.reed && (!who || g.who === who) && (place ? g.place === place : Math.hypot(g.cx - fr.x, g.cy - fr.y) < 260))
            .sort((a, b) => b.members.length - a.members.length);
          const g = gs[0]; if (!g) return 'no such body';
          let cx = 0, cy = 0; g.members.forEach(m => { cx += m.x; cy += m.y; }); cx /= g.members.length; cy /= g.members.length;
          const dx = cam.position.x - c.target.x, dz = cam.position.z - c.target.z, hd = Math.hypot(dx, dz) || 1, pol = 0.95;
          c.target.set(cx, 0, -cy); cam.position.set(cx + dx / hd * Math.sin(pol) * D, Math.cos(pol) * D, -cy + dz / hd * Math.sin(pol) * D); c.update();
          return `${g.who}@${g.place}, ${g.members.length} figures`;
        }, [who, place, dist]);
        name = [id, who, place].filter(Boolean).join('-') + '-close';
        await page.waitForTimeout(900);
      }
    }
    await page.screenshot({ path: `${out}/${name}.png` });
    console.log(`${out}/${name}.png${note ? '  ' + note : ''}`);
  }
  await close();
  if (errors.length) { console.log('page errors:\n  ' + errors.join('\n  ')); process.exit(1); }
})().catch(e => { console.error(e); process.exit(2); });
