# Data schema

The data lives in five files under `data/`, with an optional sixth, `pictures.json`. `tools/check_story.py` enforces every rule here, and an unknown field is an error, so a typo cannot slip through. `tools/fmt_story.py` writes the canonical layout: a header line of short fields per record, then one line for each prose field and each nested item.

**The data follows Reed authoritatively.** Every event, time, move and change of control comes from his text, and the data does not check him against other accounts. Outside sources are used for two things only: locating his places (a place's `src` and `geo`) and the 1917 clock. Where two of Reed's own passages disagree, the main narrative wins over his appendices, captions and the documents he prints; between two documents, the more specific one wins.

General rules:

- **Ids** are lower-case slugs: `a-z`, `0-9`, single hyphens.
- **Times** are local clock time in Petrograd, always New Style: `YYYY-MM-DDTHH:MM`. Old Style appears only where the source used it, and then always marked with `cal`.
- **Coordinates** are `[lat, lon]`, at most 6 decimals.
- **References into the book** are a section id plus a verbatim quote. Section ids are `Preface`, `Notes`, `I`…`XII`, and the appendix sub-sections `App.I.1`…`App.XII.2`, as written by `tools/text.py`.

  A quote must occur exactly once in its section after normalisation. Normalisation turns curly quotes straight, `—` into `--`, `–` into `-` and `…` into `...`, drops the `_` italics marks, and collapses whitespace. A quote can be a list of segments, to step over an elision; the segments must be in order and close together.

## meta.json

```
{"meta": {title, text, pdf, calendar, clock, range, zones, speed_kmh, blocs, tags, note},
 "days": [{d, os, label, name}, …]}
```

| field | meaning |
|---|---|
| `text` | `{gutenberg, url, body_sha256, edition}`. `body_sha256` must equal the hash `tools/text.py` pins. If not, the checker exits 2. |
| `pdf` | `{url, sha256, fetched, note}` for the marxists.org PDF that the page numbers `p` refer to. |
| `calendar` | `{store: "NS", os_lag: 13, ref}`. `ref` is Reed's own statement, which is quote-checked. |
| `clock` | `{petrograd: {offset_min, basis, src}, moscow: {…}}`. `offset_min` is minutes east of UTC for the clocks Reed read. In Nov 1917 this is Pulkovo mean time plus the 1917 summer hour. |
| `range` | earliest and latest allowed date |
| `zones` | `{city, front, moscow}`: `[south, west, north, east]` boxes. A pin must lie inside its zone's box. |
| `speed_kmh` | the fastest plausible speed for each move mode, for the feasibility check |
| `blocs` | the legend families for actors (see below) |
| `tags` | the allowed event tags. `shooting` marks a scene where Reed reports firing: its quotes must say so (fire, shots, fusillade, bombardment…). The map draws firing only for the bodies Reed has fire (`fire`, below); shots he only hears are not drawn. |
| `days[]` | timeline groups. `os` must be `d` − 13 days. `city`, if given, is the group's name on the Petrograd tour, when `name` is about a scene outside the city. |

## sources.json

`{id, kind, url?, cite, note?}`. `kind` is `primary | secondary | reference | map | data`.

Only sources actually read for this project go here: what locates a place, and what sets the clock. The book itself is pinned in `meta.text`, not here.

## actors.json

`{id, kind, bloc, track?, part_of?, seat?, wd?, name, reed[], ru?, stance[]?, note?}`

| field | meaning |
|---|---|
| `kind` | `person | party | organ | unit | school | ship | crowd | press | foreign` |
| `bloc` | `soviet | government | opposition | neutral | foreign | observer | public`. A legend family, not a verdict. It is deliberately not "Red vs White": in November 1917 much of the opposition to the Bolsheviks was socialist (the Committee for Salvation was SR and Menshevik). |
| `track` | `true` for actors whose moves must chain end to start: Reed, Kerensky, Krasnov's Cossacks |
| `part_of` | the parent actor (a regiment's division, a ship's fleet) |
| `seat` | its headquarters (a place id) |
| `reed[]` | spellings as Reed writes them ("Trotzky", "yunkers", "Colpinno"). Each must occur in the book. |
| `stance[]` | `{from, s, ev | src | ref, note?}`, in time order. `s` is `support | oppose | neutral | divided | unknown`, toward the insurrection and Soviet power. Every entry needs evidence from Reed: an event, or a passage `{sec, q}`. Colour on the map will come from the stance at time t. |

## places.json

`{id, kind, zone, in?, ll, acc, stage?, conf, exists, osm?, site_osm?, wd?, src?, geo, ctl0?, name, reed[], ru?, addr1917?, addr_now?, ident?, today?, note?}`

| field | meaning |
|---|---|
| `kind` | `building | room | complex | square | street | bridge | station | district | town | area | offmap` |
| `zone` | `city | front | moscow | offmap`. `offmap` places (Pskov, Moghilev, Kronstadt) may start or end a move, never sit in its `via`. |
| `in` | the containing place (a room in Smolny). Must be within 400 m of it, and never cyclic. |
| `ll`, `acc` | the pin, and its uncertainty radius in metres. `ll: null` only with `conf: "unlocated"` (Reed's lodging). |
| `stage` | `[lat, lon]`, display only: the open ground where the place's people are drawn, when the open ground nearest the pin is the wrong side of the building. Within 400 m of `ll`. |
| `conf` | how sure the identification is:<br>• `named`: Reed names it and the site is certain;<br>• `identified`: Reed's name needed interpreting, and `ident` says how ("Military Hotel" is the Astoria);<br>• `conjectural`: our guess, with the reasoning in `ident`;<br>• `unlocated`: no position. |
| `exists` | does the 1917 structure substantially survive? `true`, `false` or `null` (not known) |
| `osm` | the surviving element (`way/…`, `relation/…`, `node/…`). Required for a surviving building, station or complex. Forbidden when `exists` is false; use `site_osm` (what stands on the site now) instead. |
| `src` | sources read for the identification, the 1917 address or the building's survival (`ident`, `addr1917`, `exists`, `today`). The pin's own provenance goes in `geo`. |
| `geo` | where the pin came from: `{m, at?, q?, osm_v?, on?, src?, note?}`. `m` is `osm | wikidata | plan1916 | secondary | hand | pending`:<br>• `osm`: the pin lies inside the OSM element, with `at` saying whether the hand-placed hint was kept or the pin was moved inside the footprint;<br>• `wikidata`: a Wikidata coordinate;<br>• `plan1916`: read off the 1916 plan;<br>• `secondary`: from a source in `src`;<br>• `hand`: placed by hand from the description;<br>• `pending`: fails the check. |
| `ctl0` | who held the place before the first change in the data, as Reed has it: `{state, holder?, by?, as_of, ev | ref}` |
| `addr1917`, `addr_now` | addresses then and now. Geocode with `addr_now`: Znamenskaya is now Vosstaniya, the Ekaterininsky is now the Griboyedov Canal. |
| `ident`, `today` | how it was identified; what is on the site now |

`conf` and `src` (identification), `geo` (provenance of the coordinate) and `acc` (precision) are different things, and are kept apart on purpose.

## events.json

`{id, t, tq, tr?, tp?, cal, dp?, sec, p?, loc, witness, by?, actors?, tags?, title, why?, sum, q, also?, doc?, moves?, ctl?, present?, gone?}`, sorted by `t`. Every event is a passage of Reed's: `sec` and `q` are required. `actors[]` lists the factions and people the scene is about, for filtering by faction; movers and holders are named in `moves` and `ctl` and need not be repeated.

**Time**

| field | meaning |
|---|---|
| `t` | the best estimate, New Style local clock time |
| `tq` | how the time is known:<br>• `stated`: a clock time in Reed's narrative;<br>• `doc`: a time printed on a document;<br>• `approx`: a part-of-day phrase;<br>• `day`: the date is known, the hour not;<br>• `inferred`: from Reed's context, with `why`. Where Reed gives no date, the inference uses his own clues only, and `tr` says how wide the window is. |
| `tr` | `[earliest, latest]`. Required unless `tq` is `stated` or `doc`. Never invent precision: Reed gives about sixty clock times in 121,000 words. |
| `tp` | the time phrase, verbatim, near the quote. For `stated` and `doc` it must parse to `t` ("At 1 A. M.", "10.40 P. M.", "38 minutes past 9 a. m."). |
| `cal`, `dp` | the calendar the dates in the quote use (`NS | OS | none`), and the date phrase itself. `dp` is parsed under `cal` and must give the date of `t`. A weekday in `dp` must match. This is how "Thursday, November 16th" shows up as Old Style: 29 Nov NS was a Thursday, 16 Nov NS a Friday. |

**Text**

| field | meaning |
|---|---|
| `sec`, `q` | the reference: a section and a verbatim quote (a string, or a list of segments) |
| `p` | the marxists.org PDF page. Only a convenience, filled by `fmt_story.py --pages` and checked by `check_story.py --pdf`, because that PDF's pagination is regenerated. |
| `witness` | how Reed knows:<br>• `seen`: Reed was there; his derived position must be at `loc`;<br>• `told`: an informant told him, named in `by` if Reed names them;<br>• `reported`: news, rumour, or his own compiled chronology such as App. III §7;<br>• `document`: a decree, bulletin or proclamation he prints. |
| `also[]` | other passages `{sec, q}` that support the event |
| `doc` | a document read inside the scene: `{at, t, tp, cal, dp?, q}`. It is dated on its own, and must not be dated after the scene that reads it. Example: the Pulkovo telegram, Old Style, read at Smolny at three in the morning. |

**Moves**

`moves[]`: `{who, with?, size?, n?, from, via?, to, mode, rc, t0?, gap?, stay?, kit?, ack?}`.

- `mode` is `foot | march | cavalry | cab | tram | car | truck | armoured | rail | ship | air | unknown`. `cab` is a horse cab (izvozchik).
- `rc` is the route confidence:
  - `stated`: the text gives the streets;
  - `inferred`: our routing;
  - `none`: no route known. The map will draw this as an unrouted line.
- `from` is always explicit. The Raskolnikov engine's implicit "from the previous place" is unsafe when events come from many chapters.
- `t0` is a departure time, only when the text states one.
- `gap` declares that the text skips: the actor turns up somewhere new.
- `ack` explains a speed the checker finds implausible but the text insists on.
- `stay` means the body stays where it arrives (a presence, below, from the next scene on). Only bodies of people and ships stay; a person does not.
- `run` is a body running at the enemy ("rushed", "ran", "stormed", "poured"); it needs the word in the scene's quotes, and the map draws it at a run, bayonets first.
- `kit` is what the body brings, from `fire | barricade | mg | gun | armoured | truck | car | banner | flag | torch | bicycle | leaflets | rifles`, optionally with a count (`gun:4`). `rifles` is a heap of rifles thrown down ("a heap of rifles thrown down by the yunkers"), drawn just inside the body's barricade. Each item needs its word in the scene's quotes ("batteries", "armoured", "flag", "papers"…). A `banner` is carried on two poles and a `flag` on one; Reed's word decides which. A count is drawn as given ("a red flag" is `flag:1`); without one the map draws a few. In a body with an armoured car, its flag flies from the car.
- `say` is the words on the banners and flags, one text each, verbatim from Reed and within 1,500 characters of the passage: the peasants' "Long live the union of the revolutionary and toiling masses!". It needs a `banner` or a `flag` in `kit`, and no more texts than a counted kit has banners and flags. A banner without `say` is drawn plain: Reed does not say what it read.
- `n` is how many figures to draw. It needs `size`, the phrase it reads; it is a display choice, not a head count.

**Control**

`ctl[]`: `{place, state, holder?, by?}`.

- `state` is `held | besieged | contested | neutral | unknown`.
- `besieged` names both the defender (`holder`) and the besieger (`by`).
- Each change lives on the event that reports it, so it inherits that event's time, quote and witness type.
- Every change is one Reed reports. There is no field for a change taken from elsewhere, and no field for checking Reed's claims: the old `check[]` was removed when the project settled on following Reed.

**Presence**

Who stands where between scenes. Reed's text keeps people at a place until it removes them, and the map keeps them there too.

`present[]`: `{who, place?, size?, n?, kit?, say?, form?, march?, face?, inside?, fire?, at?, pose?, assault?, patrol?, brief?, ref?}` — from this scene on, `who` is at `place` (default `loc`).
- `who` is a body: a unit, a school, a crowd, a ship, an organ or a party. Never a single person.
- The evidence is Reed's: `ref` `{sec, q}` is the passage that puts them there; without it, the scene's own quotes. Either way the body must be named there, or within 1,500 characters, under one of its `reed[]` spellings.
- `size`, `n`, `kit` and `say` as for moves; the kit's words must be in the evidence passage.
- `brief: true` keeps them for this scene only: a crowd watching, a column passing. If the same body already stands at the place, the brief entry adds to it for that scene and the map draws the two as one, unless the brief one is marching past (`march`): that is a body of its own.
- `form` is how Reed has them stand: `column | line | ranks | ring`. Each needs its word in the evidence passage or in `size`: "an interminable column of soldiers", "a long double file of cyclists", "a line of soldiers, rifles ready", "a cordon of troops", "three companies of long-coated yunkers were drawn up under arms", "Soviet troops surrounded the building". A formation is the scene's, not the body's: it holds only in the scene that states it, and in later scenes the body stands loose again.
- A `ring` stands round its place's building ("surrounded", "encircled"), so the place must be a building, a station or a complex. The map spreads the body round it in sections, on the open ground 9 to 45 m from its walls with a clear line to them, each section facing the wall nearest it; its guns, machine guns and cars stand with the sections.
- `march: true` is a column on the move ("shuffled", "tramped", "marching out of step"): it needs `form: column` and `brief`, and a word for the movement. The map walks it down the street for the length of the scene. Which way it goes is not data: Reed's "up the Nevsky" is not resolved to a compass direction.
- The map reads the rest of a formation from `size`: how many abreast ("double file" 2, "lines of four" 4, else 4), how many companies, and whether the ranks are ragged ("irregular lines of four", "out of step", "shuffled").
- A line is drawn across: along the shortest chord of open ground through the place, wall to wall, its men spread to fill it, up to 4 m apart. At a street or a bridge it stands on the street's axis, square to the street ("drawn across the Nevsky"), and with `face` it is drawn across the way it looks. It faces a throng that presses on it at the same place, or out from the building its side holds; else it faces in, toward the square or building it closes off. A crowd at a place with a line stands in front of it and faces it, and a brief body or a crowd watching a formation faces it. Where Reed names a part of a place ("the western end" of the Palace Square), that part is a place of its own, and the body stands there.
- `face` is what the body looks at or trains its guns on, a place or a body: "staring at the hotel roof", "all the guns trained toward St. Isaac's", "staring at the brightly-lighted Winter Palace", a cordon "blocking the way to" a column. It needs Reed's word for looking (or blocking) in the passage. Its men turn toward it, a line is drawn across the way it looks (however the ground runs: "diagonally across the wide square"), a column heads toward it, and its guns and cars point at it. Like a formation, it is the scene's.
- `inside: true` is a body Reed puts indoors: "they are in the back rooms", "inside all was uproar". It needs the word, and the place is a building. The map labels the building and draws no one, though its barricades and any heap of rifles stay outside the door; the body does not form up, march or fire in the open. Unlike a formation it is the body's: it holds in later scenes until a later entry says otherwise.
- `fire` is a body firing in this scene: `true` in the open, `"windows"` from inside its building. It needs a word for firing in the passage, `"windows"` the word windows too, and the scene must be tagged `shooting`. `at` names whom or what it fires at, a body or a place; without it the map takes the nearest body of the other side, else the wall of the building the body besieges. Each rifleman, machine gun and field-gun aims at what is nearest him: the nearest part of the enemy body if it stands in the open, else the wall nearest him of the building it holds. The riflemen kneel or stand to fire, each firing every few seconds; machine guns and armoured cars fire bursts; field-guns recoil and burst their shells on the wall, and each shell leaves a hole there, kept for the rest of the tour.
- A body that fires from inside is not drawn: its fire comes from windows on the floors of the walls that face the enemy, all round the building if the enemy is all round. A body with `fire: true` that holds the building it stands at while Reed has it besieged (`ctl` `besieged`) fires from inside too: it is in the building.
- `assault` is a body that runs at the enemy in waves, bayonets first: `repulsed` (the waves are thrown back: words for the attack, "assaulting", "charged", "waves of", and for its failing, "crumpled", "driven back") or `carried` (they get in: "poured through", "stormed into", "burst into"). In a repulsed assault some of each wave fall where they are hit and lie there, the rest run back; in a carried one the body streams into the building.
- `patrol: true` is a body whose armoured cars (or cars, or trucks) cruise up and down the street they stand in ("cruising back and forth", "up and down"): it needs the words, and a vehicle in `kit`. The cars of 1917 had a driver at each end, so they do not turn.
- `pose` is `fallen` (the dead and the wounded, lying on the ground: "dead", "killed", "wounded", "lay") or `prone` (people who throw themselves flat: "falling flat on their faces", "falling down and lying still in the street"). Each needs its word.
- Like a formation, `face`, `fire`, `at`, `assault`, `patrol` and `pose` are the scene's: they hold only in the scene that states them.

`gone[]`: `{who, place?, ref?}` — the text has them leave `place` (default `loc`) after this scene: "the cannon gone", "the sentries in the Square had all disappeared". The checker errors if nobody of that body is there.

A presence also ends, after the scene, when control of its place (or of a place it lies in) passes from its bloc to another: Reed reports the building taken, so its defenders no longer hold it. A later `present` for the same body and place adds to it: its size and count replace the old ones, its kit joins the old kit. `tools/storylib.py` (`presence_spans`) holds these rules, and both the checker and the map use it.

## pictures.json

`{id, kind, from, file, w, h, scenes[], license, author?, date?, url, page?, title?, caption?, ref?, note?}`. Optional: a data set without pictures leaves the file out.

| field | meaning |
|---|---|
| `kind` | `facsimile | photo | portrait | building | document | equipment` |
| `from` | `reed-1919`: a facsimile Reed printed in his book; `commons`: Wikimedia Commons |
| `file`, `w`, `h` | the image under `media/`, and its size, which the checker reads from the file |
| `scenes[]` | the events whose card shows it |
| `license` | it must be public domain, and say by which rule: "Public domain: …" |
| `url`, `page` | where the file comes from; for a facsimile, the page of the edition scanned |
| `ref` | for a facsimile, Reed's own caption, quote-checked like every other quotation |
| `caption`, `author`, `date` | for anything else: what it shows and when, in our words, and who took it. A photograph illustrates a scene; it is not evidence for it. |

A card shows its scene's pictures in this order: Reed's facsimiles, then photographs, documents, portraits, buildings and equipment. The `license` text gives the rule in words ("its photographer, Yakov Steinberg, died in 1942", "a postcard published in the Russian Empire before 1917") and then Commons' own templates. A picture whose Commons date is wrong says so in `note`.

## The tour

`tools/build_story.py` gives the page only the scenes Reed sets in Petrograd (zone `city`). The front, Moscow and the off-map scenes stay in the data, and in every check, but are not toured. A move that leaves the city is still drawn, as an arc.

## What the checker measures (`--report`)

- **Feasible speed** of every tracked move: straight-line distance through its points, over the widest window the times allow. More than 3× the mode's limit is an error unless the move has `ack`.
- **Sun words** ("dawn", "twilight", "dusk") against the sun's elevation at `meta.clock`.
- **Every weekday–date pair in the book**, tested as New and as Old Style.
- **Reed's walking per day.** It is a floor: straight lines between pins.
- **Coverage per section, presence (who stays where, and what ends it), and the control timelines.**

`--osm` fetches each OSM element (cached in `cache/osm/`, one request a second). It checks:

- the element exists;
- its tags suit the place's kind;
- the pin lies inside the footprint, or within 25 m of it;
- its `wikidata` tag agrees with `wd`.
