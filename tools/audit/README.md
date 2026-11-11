# Checking the drawing

`check_story.py` and the unit tests check the data: quotes, dates, chains, fields. Nothing there looks at
the page. These scripts do: they serve the built page (`index.html` and `media/` at the repo root) on a
free local port, open it in headless Chromium with `?debug`, and drive it through `window.__td`. Run them
after `tools/build.sh --bundle`, from the repo root. They need Node and Playwright with Chromium
(`npm install playwright && npx playwright install chromium`); `sheet.py` needs Pillow.

The page loads three.js from jsDelivr and its fonts from Google. `python3 -I tools/audit/vendor.py` fetches
the scripts once into `cache/vendor/`, each checked against the SHA-256 pinned in `vendor.json` (and checks
that `vendor.json` pins every script `src/app.html` loads); the audit browser then serves them from there.
With `TENDAYS_OFFLINE=1` nothing leaves the machine: any outside request is refused and counted as an
error, fonts aside (they change only the look).

Headless Chromium draws this page at about four frames a second, which stretches every walk, fight and
camera move (the page caps a frame's step at a quarter of a second). `vehicles.js`, `motion.js` and
`camera.js` therefore open the page with `norender`: its clock runs at full speed and nothing is drawn.
They play each scene from the one before, as a reader comes to it, and never call `finish()`, which puts
everybody at their end and so hides whatever goes wrong on the way. `.github/workflows/checks.yml` runs the data checks and
every audit below this way on each push, the audits side by side.

| Script | What it checks or makes | Exit |
|---|---|---|
| `node tools/audit/smoke.js` | every scene, chosen from the timeline as a reader would: page errors, failed requests, figures or a camera with a coordinate that is not a number | 1 on any |
| `node tools/audit/crowds.js` | how the people stand in every scene, seen from its own close frame (below) | 1 past the limits |
| `node tools/audit/frames.js [--phone]` | each scene's own bodies (those it brings in, and Reed) on screen in its close frame: left of the card on a desktop, above the sheet on a phone | 1 if more than 2% are off (5% on a phone) |
| `node tools/audit/vehicles.js` | every scene with a vehicle moving, played at its own pace: someone inside a moving vehicle's outline, the vehicle overlapping a gun, barricade or other vehicle, the vehicle held up, a vehicle still short of its end after its walk | 1 past 2.5%, 1%, 15% of samples, or any vehicle left behind |
| `node tools/audit/motion.js` | every scene where a fight is acted out, played: people on the move (coming up, running off, a sortie, stepping out of a car's way) standing in a building or walking through another body | 1 past 1%, 3% of samples |
| `node tools/audit/camera.js [--phone] [--step N]` | every scene played: how close the camera ends and how much of the time it is close; in each close shot, the share of its people on screen; close shots the scene's time would cut short in Play | 1 if under 90% end close, over 5% of close-shot samples leave people off, or any scene cuts its shots |
| `node tools/audit/hall.js [--phone] [--only ID,ID]` | every scene in a meeting-hall, played from when the camera comes down into it: a delegate off a bench seat of its block, two people within 0.9 m, one standing on a bench or outside the hall, one in the gallery not on it, anyone not at the height of what is drawn under them (raycast against the hall's own meshes), a body Reed puts on the platform not on it, the speaker not at the reading stand; as they walk out or in, ten samples a second, someone crossing a bench, going through a wall (anywhere but the door), within 0.7 m of a person of another body standing, or within 0.5 m of another walker; anyone walking out still in the hall at the end, or walking in not in their seat; the bodies that rise, vote, cheer or hoot not those pinned for the scene in `hall-react.json`, or anyone walking out or in cheering or hooting; a walker more than 0.6 m off what is drawn under them; two in each other's arms standing in the presidium table; the scene ending before the hall's walks are done; and the camera's hall shots leaving out the hall, the way of those walking out or in, or the speaker | 1 on any seat, stand, platform, speaker, exit, react, table, short or shot finding, or past 1% bench (or the reading stand), wall or float, 3% through, 5% crowd |
| `node tools/audit/shot.js OUTDIR [--phone] ID...` | screenshots: each scene in its own close frame; `--close 110 ID[:WHO[:PLACE]]` close up over a body; `--play ID` the scene played at its own pace, the camera following | 1 on page errors |
| `python3 -I tools/audit/sheet.py SHOTDIR OUTDIR` | contact sheets, six scenes to a sheet, for looking through the whole tour | |

`crowds.js --shots DIR` saves each scene's frame as it goes, so one run gives both the numbers and the
pictures for `sheet.py`; `--json OUT` keeps the numbers per scene and body; `--only ID,ID` runs a few.

## What `crowds.js` measures

For each body within 320 m of the frame's target (gun and machine-gun crews, who stand round their gun,
left out):

- **closer than 1.3 m**: members that near another of their body;
- **run together**: members nearer to another than 0.6 of the size the figure is drawn at, so that on
  screen the two figures merge (a figure is drawn at least twice life size, larger as the camera draws
  back, and in a crowd no wider than its room);
- **in a wall**: members whose drawn figure reaches into a building;
- **hidden**: members whose head the buildings hide from the camera;
- **in another body**: members within 1 m of a member of another body;
- **drawn short**: bodies drawn with fewer than 90% of the figures they are given (cars' crews aside).

It prints the totals, then each body where more than 30% run together, more than 15% stand in a wall
or are hidden, or two or more stand in another body. It fails if any member stands in another body, any
body is drawn short, or more than 1% of all figures run together, 1% stand in a wall, or 8% are hidden.

The scenes are taken in tour order from the first, because a frame depends a little on where the camera
comes from: the numbers repeat only along the same path. On the build after the second review's fixes,
over 131 scenes and 6,015 figures standing in the open: 26 closer than 1.3 m, 14 run together (all in
columns of fours), 22 in a wall, 289 hidden (4.8%), none in another body, no body drawn short.
`frames.js`: 38 of the 4,146 members of the scenes' own bodies off the clear screen on a desktop (0.9%), 88 on
a phone (2.1%). `vehicles.js`: 14 scenes, someone inside a moving vehicle in 0.4% of 994 samples, a vehicle
overlapping something in 0.2%, held in 8.8%, none left behind its walk. `motion.js`: 19 scenes, 0.4% of the
samples of people moving in a wall, 0.3% through another body.

After the halls (phases 1 and 2): frames 38 of 4,145 on a desktop, 93 on a phone; `vehicles.js` someone inside
0.7%, overlapping 0.0%, held 13.2%; `motion.js` 0.6% in a wall, 0.1% through; `camera.js` a median 133 m (128 of
130 within 250 m), 4 of 951 close-shot samples under 70%; on a phone a median 211 m, 12 of 438; `hall.js` 16
scenes, no finding on desktop or phone. The held vehicles rose because the hall's new records shift the layout
seeds of the bodies after them in the data (a body's seed is its index there), so other scenes' crowds are laid
out afresh: the truck ride's and the Kirochnaya lunch's cars are held longer now. Seeds that do not depend on
the order of the data would stop an edit in one scene reshuffling another. `camera.js`: the camera ends a median 136 m
off (128 of 130 scenes within 250 m; the other two are rides that leave the drawn city), every close shot
with at least 70% of its people on screen in all but 4 of 1,128 samples; on a phone (every other scene) a
median 215 m, 12 of 534 samples under 70%, the wide bodies seen in part.

After the City Duma's halls (phase 3): `hall.js` 20 scenes, no finding on desktop or phone (one sample in 10,863
of Spiridonova brushing the reading stand on a phone); frames 38 of 4,145 on a desktop, 172 on a phone (45 of them
the yunkers by St Isaac's in `up-the-morskaya-nov5`, off a phone's frame whenever that scene is staged on its own,
at every commit tried, and in a full run only after some scenes and not others); `vehicles.js` someone inside 1.3%,
overlapping 0.4%, held 13.3%; `motion.js` 0.7% in a wall, 0.2% through; `camera.js` a median 131 m (128 of 130
within 250 m), 4 of 913 close-shot samples under 70%; on a phone (every other scene) a median 201 m, 12 of 415.
The hall's new records moved the layout seeds again: three armoured cars patrolling the Nevsky in
`sadovaya-red-spark` drove through each other in one run and not in another (where a patrol car is depends on
the page's clock), so each patrolling car now keeps to its own stretch of the street.

After Fontanka 6 and laughter (phase 4): `hall.js` 23 scenes, no finding on desktop or phone (one sample in
11,840 of Spiridonova brushing the reading stand on a desktop); smoke 132 scenes, no error; frames 38 of 4,144 on a
desktop, 172 on a phone (as before, the Morskaya yunkers among them); `vehicles.js` someone inside 1.0%,
overlapping 0.0%, held 13.1%; `motion.js` 0.7% in a wall, 0.2% through; `camera.js` a median 128 m (129 of 131
within 250 m), 4 of 889 close-shot samples under 70%; on a phone (every other scene) a median 211 m, 12 of 430.

After the Mariinsky's Council hall and the Riding School (phase 5): `hall.js` 26 scenes, no finding on desktop or
phone (the Riding School's crossing to the left: 6 of 3,479 walking samples within 0.5 m of another walker); smoke
132 scenes, no error; frames 38 of 4,144 on a desktop, 121 on a phone (the Morskaya yunkers' 45 among them);
`vehicles.js` someone inside 0.0%, overlapping 0.0%, held 6.5%; `motion.js` 0.4% in a wall, 0.1% through;
`camera.js` a median 126 m (129 of 131 within 250 m), 0 of 863 close-shot samples under 70%; on a phone (every
other scene) a median 209 m, 12 of 414. The new records moved the layout seeds once more, so the vehicle and frame
numbers moved with them, not because anything outside the halls was fixed.

`shot.js --film ID` takes a scene as it plays (at 2, 6, 10, 14 and 18 s): the way to look at a fight.

These numbers say where to look, not that a scene is right: a body can pass every test and still stand
where Reed does not put it. Look at the sheets as well.
