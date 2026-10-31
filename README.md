# ten-days-that-shook-the-world

A 3D map of John Reed's *Ten Days That Shook the World* (1919): Reed's own path through Petrograd in October–December 1917, the factions, who held which building when, and the movements he reports, scene by scene, as he wrote it. It is the sister project of [Raskolnikov Wandering](https://github.com/mauladhanifadhilsalam/raskolnikov-wandering), whose 3D engine it adapts.

**Status: a first working map on a checked seed dataset.** Open `index.html` in a browser (it needs a network connection for three.js and the fonts). This repo holds:
- the assessment of whether, and how, the Raskolnikov treatment fits Reed: [docs/assessment.md](docs/assessment.md);
- a checked seed dataset, and the tools that check it;
- the map: the OSM pipeline for the 1917 city, the story builder and the page.

## The map

- **An introduction for readers who have not read the book.** The first visit opens with three cards over the city: what happened in Petrograd in 1917 and why the dates are "October"; who the sides are, in their map colours; and who Reed was and how he wrote. "Skip the introduction" goes straight to the map, and "About this map" replays it. The first two cards are background in our own words, not data, and nothing on the map rests on them; where they touch Reed's ground (the timetable of the night of 6–7 November, the Committee for Salvation) they say what he says.
- **A tour of Petrograd: 131 of Reed's 157 scenes.** The scenes he sets at the front (Pulkovo, Tsarskoye Selo, Gatchina) and in Moscow stay in the data and in every check, but are not toured; a move that leaves the city is drawn as an arc, and the camera keeps to the city.
- **Scenes on a timeline of real dates.** Each card gives the date and the time and how the time is known, the place, how Reed knew (he was there, he was told, it was reported, or it is a document he prints), his words, and the moves and changes of control in the scene. Tall ticks on the timeline are scenes Reed saw.
- **The people of each scene, and who is still there.** Soldiers in the long belted greatcoat with the rolled coat over the shoulder, under a papakha or a peaked cap; yunkers with "the red shoulder-straps of the yunker-schools"; the Women's Battalion in light fur hats; sailors in black pea coats and peakless caps, some with machine-gun belts crossed on the chest; Red Guards in workmen's clothes with a red arm band (the map's marker, not a documented one); Cossacks, townspeople, and peasant delegates in foot-cloths and bast shoes; armoured cars ("elephant-coloured", in Reed's word, one of them "with two red flags flying from the turret"), trucks, field guns, Maxims, cabs, trams, barricades, trenches, bonfires and torches, a military band's brass; banners and flags, lettered with the words Reed gives them ("Peace! Land!" over the young Red Guards on the Nevsky, the peasants' "Long live the union of the revolutionary and toiling masses!"), and as many as he counts; the Avrora at anchor in the Neva. All are low-poly models built in code (`src/people.js`); [docs/uniforms.md](docs/uniforms.md) gives the photograph behind each uniform and says which colours are assumed. Every body stands where Reed puts it, in the formation he gives it in that scene (a column down the street, in step or ragged as he says, a line across a square, companies drawn up in ranks), and stays until his text removes it: it marches off, is disarmed, or the building it holds falls to the other side. So the yunkers are still in front of the Winter Palace, behind their firewood, until the Red Guards pour through the Red Arch. Each body stands on a patch of its side's colour; the card lists who is on the scene, in Reed's words. Bodies that move march their route in column, or as a bunched mass where Reed has them run ("Like a black river, filling all the street"); companies that march off from their own body take their share of it with them, and a column that leaves the scene files on out of it ("disappearing through the Red Arch"). The camera goes to the scene's action: a body Reed sees on the move (the yunker batteries coming "through the Red Arch at a jingling trot", the Red Guards pouring across the square) is picked up where it sets out and followed; Reed's own long rides are followed only when his journey is the scene (the truck ride, the ambulance), and a ride of his with no known route does not take the camera away from the people at the place. A column Reed sees marching past walks down the street while the scene lasts. Fires burn after dark. The fighting is drawn only where Reed has a body fire, and as he has it: riflemen kneeling or standing to fire at the enemy nearest them, machine guns and armoured cars in bursts, field-guns recoiling and bursting their shells on the walls (the holes stay there in every later scene), a besieged garrison firing from its windows, troops that "surrounded the building" standing all round it, assaults in waves that "crumpled" and fall back or "poured through" the doors, armoured cars "cruising back and forth", the dead lying where he says they fell. A shot he only hears, from a shooter he does not see, is not drawn; and since rifles burnt smokeless powder in 1917, what hangs over a fight is dust, plaster and shell smoke, not gunsmoke. Defenders of a building face out from its walls; everybody else faces it, or what Reed has them look at ("staring at the hotel roof"); a body he puts indoors ("they are in the back rooms") is a label on its building.
- **Pictures from the time: 55, on 51 of the 131 scenes.**
  - **Reed's own facsimiles (11)**, on their scenes under his own captions, quote-checked like every other quotation: his passes, the Military Revolutionary Committee's "To the Citizens of Russia!" that he picked up during the truck ride, Konovalov's pencil draft from the Winter Palace, a leaflet sold in the streets.
  - **Photographs, postcards and documents from Wikimedia Commons (44)**, all public domain:
    - Red Guards at a fire on Smolny Prospekt, and soldiers at the Smolny gates, in November 1917;
    - the defenders' mattresses and a shot-up façade of the Winter Palace, the morning after;
    - the Women's Battalion on Palace Square;
    - the decrees on peace and on land as they were printed;
    - the pamphlet by Lenin that Reed bought on the Nevsky;
    - portraits of Lenin (clean-shaven, as Reed saw him), Trotsky, Kerensky, Martov, Tchernov, Krylenko and Antonov;
    - the Avrora before the war;
    - Reed's buildings on postcards printed before 1917.
  - Each caption says what the picture shows and when, and says so where it is from before or after these days. It corrects Commons where its date is wrong: the morning of 26 October Old Style is 8 November. The licence names the rule that makes the picture public domain.
  - The pictures illustrate; they are not evidence. Click one to enlarge it.
- **Reed's walks along the streets he names.** Routes with `rc: "stated"` are solid, routes we inferred are dashed, and moves Reed gives no route for (or that go by train or leave the city) are arcs. Reed is ink by day and pale by night; every other mover takes its bloc's colour.
- **Who holds what.** The 22 buildings that are Reed's places stand out of the city, and the ones Reed reports as held take the holder's colour on the roof, as he reports it at that moment. A besieged building pulses in the besieger's colour.
- **A sky for each scene** on the 1917 Petrograd clock (about UTC+3:01), and the city turns white after Reed's first snow on 13 November.
- **The city's edge.** The detailed city runs from the Petrograd Side to Smolny. The southern gates and the factories beyond it are pins on a gridded plain.
- Drag to pan, right-drag or two fingers to rotate, scroll or pinch to zoom. ←/→ step through scenes, space plays. `index.html#storming` opens a scene.

## What is here

```
docs/assessment.md     the critical assessment: verdict, what the book gives, Reed as a source, the plan
docs/schema.md         field reference for the data files
data/meta.json         text and PDF pins, calendar rule, clock, map zones, move speeds, timeline days
data/sources.json      the sources actually consulted
data/actors.json       74 factions, bodies, units, people and crowds, with stance over time
data/places.json       90 places in the city, at the front, off-map, and in Moscow (not toured)
data/events.json       157 scenes: time and its quality, verbatim quote, witness type, moves, control changes,
                       and who is present or gone (143 presence spans)
data/pictures.json     the pictures the scenes show, each public domain, with its provenance; media/ holds them
tools/text.py          downloads Gutenberg #3076 and splits it into sections (pinned by SHA-256)
tools/check_story.py   the validator; fails hard. --report, --osm, --pdf
tools/fmt_story.py     writes the canonical layout; --check, --pages
tools/geocode.py       finds OSM buildings around a hint (OSM API only), --accept writes them
tools/storylib.py      shared schema, layout, quote normalisation, date and time parsers, geometry, sun
tests/test_check.py    one failing fixture per error code, plus mutation tests on the real data

tools/mapconf.py       the 3D extent, the projection, and the bridges that did not stand in 1917
tools/fetch_osm.py     OSM API tiles over the city core, plus every water relation they touch -> cache/
tools/build_map.py     land, water, parks, bridges, buildings (Reed's apart), streets, rail; the street graph
tools/build_story.py   the data -> what the page draws: the Petrograd tour, places in metres, street routes,
                       control timelines, presence spans and the figures each body is drawn with
tools/bundle.py        packs build/*.json into src/app.html -> index.html (+ a CSP pinned to the script)
tools/build.sh         the whole pipeline; --bundle only re-packs the page
src/app.html           the page
src/people.js          the low-poly people, vehicles, kit and the Avrora (inlined by bundle.py)
build/map.json         the built city (committed, so the page can be rebuilt without OSM)
build/story.json       the built story
index.html             the built page
Dockerfile, deploy/    a small nginx container for Cloud Run, as in Raskolnikov Wandering
```

## What the data asserts

**The data follows Reed authoritatively.** The map portrays his account as he wrote it, sympathies included; it is not a fact-check. Every event, time, move and change of control comes from his text. Outside sources only locate his places and set the 1917 clock. Where two of his own passages disagree, the main narrative wins over his appendices, captions and the documents he prints.

Every scene quotes Reed verbatim, and the validator proves each quote occurs exactly once in the named section of Gutenberg #3076. Each scene also says:

- **how Reed knows it** (`witness`):
  - `seen`: he was there;
  - `told`: an informant, named in `by`;
  - `reported`: news, rumour, or his own compiled chronology;
  - `document`: something he prints.
- **how its time is known** (`tq`): stated, on a document, a part-of-day phrase, the day only, inferred with a reason, or from another source. Times carry bounds (`tr`). Reed gives about sixty clock times in 121,000 words, so most times are estimates and are labelled as such.
- **which calendar its dates use** (`cal`). Reed keeps to New Style, but the documents he prints sometimes use Old Style, and the validator catches the difference (weekdays included).

Places carry three separate things:
- the identification (`conf`: named, identified, conjectural or unlocated, with the reasoning in `ident` and any source read for it in `src`);
- where the pin came from (`geo`);
- how precise it is (`acc`, metres).

A surviving building is tied to its OSM element, and `check_story.py --osm` tests that the pin lies inside the footprint.

Who stands where between scenes (`present`, `gone`, and a move's `stay`) is Reed's too: each body is named in the scene's quote or in a passage it cites, and every piece of kit drawn with it (a fire, a barricade, machine guns, a field gun, an armoured car, a banner) has its word in that passage. The figures drawn are not a head count. See [docs/schema.md](docs/schema.md), "Presence".

Read [docs/assessment.md](docs/assessment.md) §4 and §10 before relying on any of it.

## Running the checks

Standard-library Python 3.12 or later, run with `-I`. The first command downloads Reed's text into `./cache` and pins its hash:

```bash
python3 -I tools/text.py cache
```

```bash
python3 -I tools/check_story.py
```

```bash
python3 -I -m unittest discover -s tests
```

```bash
python3 -I tools/fmt_story.py --check data
```

The measurement tables (speeds, Reed's daily distances, sun against "dusk" and "twilight", every weekday–date pair, control timelines):

```bash
python3 -I tools/check_story.py --report
```

Check every pin against its OSM footprint (online once, then from `cache/osm`):

```bash
python3 -I tools/check_story.py --osm
```

Check the convenience page numbers `p` against the marxists.org PDF (needs `pypdf`; `meta.json` pins the PDF's SHA-256):

```bash
curl -L -o cache/ten-days-reed.pdf https://www.marxists.org/ebooks/reed/ten-days-that-shook-the-world-reed.pdf
```

```bash
python3 -I tools/check_story.py --pdf cache/ten-days-reed.pdf
```

The marxists.org PDF is regenerated from time to time. If its hash changes, refill the page numbers with `python3 -I tools/fmt_story.py --pages cache/ten-days-reed.pdf data`. Section plus quote remains the reference that counts.

## Building the map

The map step needs Shapely (`pip install shapely`); the rest is standard-library Python. The first run downloads about 210 MB of OSM data into `./cache`, slowly and politely, from the OSM API:

```bash
tools/build.sh
```

After editing only `src/app.html`:

```bash
tools/build.sh --bundle
```

To deploy on Cloud Run, from the repo root:

```bash
gcloud run deploy ten-days --source . --region europe-north1 --allow-unauthenticated
```

The container serves `/`, `/index.html` and `/healthz`, and returns 404 for everything else.

## Adding or changing data

1. Find the passage. The section ids are those in `cache/sections.json`.
2. Copy the quote exactly. Curly or straight quotes, `—` or `--`, and the `_` italics marks all normalise the same way.
3. Add the record, then run `tools/fmt_story.py data` and `tools/check_story.py`. An unknown field, a quote that is not in the section, a date phrase that disagrees with the time, or a Reed move that does not start where the last one ended is an error, not a warning.

New places: put a rough hint in `ll`, set `geo` to `{"m": "pending", "q": "<address or name>"}`, then:

```bash
python3 -I tools/geocode.py
```

Pick the right element from its list, then accept it:

```bash
python3 -I tools/geocode.py --accept ID=way/123
```

## Sources and licences

- John Reed, *Ten Days That Shook the World* (1919). Public domain. Text from [Project Gutenberg #3076](https://www.gutenberg.org/ebooks/3076); page numbers from the [Marxists Internet Archive PDF](https://www.marxists.org/ebooks/reed/ten-days-that-shook-the-world-reed.pdf).
- Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). The coordinates and element ids in `data/places.json`, and the geometry in `build/map.json`, are derived from OSM and are available under the [Open Database License](https://opendatacommons.org/licenses/odbl/).
- The 3D engine, the OSM pipeline and the routing helpers are adapted from Raskolnikov Wandering, designed and developed by @altf4m8.
- The other sources consulted are listed in `data/sources.json` and cited in the assessment.
