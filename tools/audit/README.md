# Checking the drawing

`check_story.py` and the unit tests check the data: quotes, dates, chains, fields. Nothing there looks at
the page. These scripts do: they serve the built page (`index.html` and `media/` at the repo root) on a
free local port, open it in headless Chromium with `?debug`, and drive it through `window.__td`. Run them
after `tools/build.sh --bundle`, from the repo root. They need Node and Playwright with Chromium
(`npm install playwright && npx playwright install chromium`); `sheet.py` needs Pillow. The page loads
three.js and its fonts from the network, as it does for a reader.

| Script | What it checks or makes | Exit |
|---|---|---|
| `node tools/audit/smoke.js` | every scene, chosen from the timeline as a reader would: page errors, failed requests, figures or a camera with a coordinate that is not a number | 1 on any |
| `node tools/audit/crowds.js` | how the people stand in every scene, seen from its own close frame (below) | 1 past the limits |
| `node tools/audit/frames.js [--phone]` | each scene's own bodies (those it brings in, and Reed) on screen in its close frame: left of the card on a desktop, above the sheet on a phone | 1 if more than 2% are off (5% on a phone) |
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
comes from: the numbers repeat only along the same path. After the review fixes (the commit after
`7e8912d`), over 131 scenes and 6,010 figures standing in the open: 26 closer than 1.3 m, 14 run together
(all in columns of fours), 22 in a wall, 279 hidden (4.6%, most in reported scenes framed from 500 m or
more), none in another body, no body drawn short. `frames.js`: 69 of the 4,146 members of the scenes' own
bodies are off the clear screen on a desktop (1.7%), 185 on a phone (4.5%).

These numbers say where to look, not that a scene is right: a body can pass every test and still stand
where Reed does not put it. Look at the sheets as well.
