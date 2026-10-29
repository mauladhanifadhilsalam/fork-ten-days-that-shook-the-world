# Data schema

The data lives in five files under `data/`. `tools/check_story.py` enforces every rule here, and an unknown field is an error, so a typo cannot slip through. `tools/fmt_story.py` writes the canonical layout: a header line of short fields per record, then one line for each prose field and each nested item.

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
| `tags` | the allowed event tags |
| `days[]` | timeline groups. `os` must be `d` − 13 days. |

## sources.json

`{id, kind, url?, cite, note?}`. `kind` is `primary | secondary | reference | map | data`.

Only sources actually read for this project go here. A claim marked `differs` with a source nobody opened is worse than `unchecked`.

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
| `stance[]` | `{from, s, ev | src | ref, note?}`, in time order. `s` is `support | oppose | neutral | divided | unknown`, toward the insurrection and Soviet power. Every entry needs evidence: an event, a source, or a passage `{sec, q}`. Colour on the map will come from the stance at time t. |

## places.json

`{id, kind, zone, in?, ll, acc, conf, exists, osm?, site_osm?, wd?, src?, geo, ctl0?, name, reed[], ru?, addr1917?, addr_now?, ident?, today?, note?}`

| field | meaning |
|---|---|
| `kind` | `building | room | complex | square | street | bridge | station | district | town | area | offmap` |
| `zone` | `city | front | moscow | offmap`. `offmap` places (Pskov, Moghilev, Kronstadt) may start or end a move, never sit in its `via`. |
| `in` | the containing place (a room in Smolny). Must be within 400 m of it, and never cyclic. |
| `ll`, `acc` | the pin, and its uncertainty radius in metres. `ll: null` only with `conf: "unlocated"` (Reed's lodging). |
| `conf` | how sure the identification is:<br>• `named`: Reed names it and the site is certain;<br>• `identified`: Reed's name needed interpreting, and `ident` says how ("Military Hotel" is the Astoria);<br>• `conjectural`: our guess, with the reasoning in `ident`;<br>• `unlocated`: no position. |
| `exists` | does the 1917 structure substantially survive? `true`, `false` or `null` (not known) |
| `osm` | the surviving element (`way/…`, `relation/…`, `node/…`). Required for a surviving building, station or complex. Forbidden when `exists` is false; use `site_osm` (what stands on the site now) instead. |
| `src` | sources read for the identification, the 1917 address or the building's survival (`ident`, `addr1917`, `exists`, `today`). The pin's own provenance goes in `geo`. |
| `geo` | where the pin came from: `{m, at?, q?, osm_v?, on?, src?, note?}`. `m` is `osm | wikidata | plan1916 | secondary | hand | pending`:<br>• `osm`: the pin lies inside the OSM element, with `at` saying whether the hand-placed hint was kept or the pin was moved inside the footprint;<br>• `wikidata`: a Wikidata coordinate;<br>• `plan1916`: read off the 1916 plan;<br>• `secondary`: from a source in `src`;<br>• `hand`: placed by hand from the description;<br>• `pending`: fails the check. |
| `ctl0` | who held the place before the first change in the data: `{state, holder?, by?, as_of, ev | src | ref}` |
| `addr1917`, `addr_now` | addresses then and now. Geocode with `addr_now`: Znamenskaya is now Vosstaniya, the Ekaterininsky is now the Griboyedov Canal. |
| `ident`, `today` | how it was identified; what is on the site now |

`conf` and `src` (identification), `geo` (provenance of the coordinate) and `acc` (precision) are different things, and are kept apart on purpose.

## events.json

`{id, t, tq, tr?, tp?, cal, dp?, sec, p?, loc, witness, by?, actors?, tags?, src?, title, why?, sum, q, also?, doc?, moves?, ctl?, check?}`, sorted by `t`. `actors[]` lists the factions and people the scene is about, for filtering by faction; movers and holders are named in `moves` and `ctl` and need not be repeated.

**Time**

| field | meaning |
|---|---|
| `t` | the best estimate, New Style local clock time |
| `tq` | how the time is known:<br>• `stated`: a clock time in Reed's narrative;<br>• `doc`: a time printed on a document;<br>• `approx`: a part-of-day phrase;<br>• `day`: the date is known, the hour not;<br>• `inferred`: from context, with `why`;<br>• `secondary`: from another source, with `src`. |
| `tr` | `[earliest, latest]`. Required unless `tq` is `stated` or `doc`. Never invent precision: Reed gives about sixty clock times in 121,000 words. |
| `tp` | the time phrase, verbatim, near the quote. For `stated` and `doc` it must parse to `t` ("At 1 A. M.", "10.40 P. M.", "38 minutes past 9 a. m."). |
| `cal`, `dp` | the calendar the dates in the quote use (`NS | OS | none`), and the date phrase itself. `dp` is parsed under `cal` and must give the date of `t`. A weekday in `dp` must match. This is how "Thursday, November 16th" shows up as Old Style: 29 Nov NS was a Thursday, 16 Nov NS a Friday. |

**Text**

| field | meaning |
|---|---|
| `sec`, `q` | the reference: a section and a verbatim quote (a string, or a list of segments) |
| `p` | the marxists.org PDF page. Only a convenience, filled by `fmt_story.py --pages` and checked by `check_story.py --pdf`, because that PDF's pagination is regenerated. |
| `witness` | how Reed knows:<br>• `seen`: Reed was there; his derived position must be at `loc`;<br>• `told`: an informant told him, named in `by` if Reed names them;<br>• `reported`: news, rumour, or his own compiled chronology such as App. III §7;<br>• `document`: a decree, bulletin or proclamation he prints;<br>• `context`: not in Reed at all. A context event has no `sec` or `q`, and needs `src`. |
| `also[]` | other passages `{sec, q}` that support the event |
| `doc` | a document read inside the scene: `{at, t, tp, cal, dp?, q}`. It is dated on its own, and must not be dated after the scene that reads it. Example: the Pulkovo telegram, Old Style, read at Smolny at three in the morning. |

**Moves**

`moves[]`: `{who, with?, size?, from, via?, to, mode, rc, t0?, gap?, ack?}`.

- `mode` is `foot | march | cavalry | cab | tram | car | truck | armoured | rail | ship | air | unknown`. `cab` is a horse cab (izvozchik).
- `rc` is the route confidence:
  - `stated`: the text gives the streets;
  - `inferred`: our routing;
  - `none`: no route known. The map will draw this as an unrouted line.
- `from` is always explicit. The Raskolnikov engine's implicit "from the previous place" is unsafe when events come from many chapters.
- `t0` is a departure time, only when the text states one.
- `gap` declares that the text skips: the actor turns up somewhere new.
- `ack` explains a speed the checker finds implausible but the text insists on.

**Control**

`ctl[]`: `{place, state, holder?, by?, basis?}`.

- `state` is `held | besieged | contested | neutral | unknown`.
- `besieged` names both the defender (`holder`) and the besieger (`by`).
- Each change lives on the event that reports it, so it inherits that event's time, quote and witness type.
- `basis: "record"` marks a change taken from other sources; the event then carries `src`.

**Checks: Reed against the record**

`check[]`: `{claim, v, src?, rec?, cf?, note?}`.

- `claim` is a verbatim piece of `q`.
- `v` is `agrees | partly | differs | disputed | unchecked`. Anything but `unchecked` needs `src`, a source actually read. `partly`, `differs` and `disputed` also need `rec`, what the record says. An `unchecked` claim may still carry `src`, when a source was read but does not settle it (it gives no hour, say).
- `cf[]` points to other Reed passages that bear on the claim, including where Reed contradicts himself.

## What the checker measures (`--report`)

- **Feasible speed** of every tracked move: straight-line distance through its points, over the widest window the times allow. More than 3× the mode's limit is an error unless the move has `ack`.
- **Sun words** ("dawn", "twilight", "dusk") against the sun's elevation at `meta.clock`.
- **Every weekday–date pair in the book**, tested as New and as Old Style.
- **Reed's walking per day.** It is a floor: straight lines between pins.
- **Coverage per section, the control timelines, and the claims table.**

`--osm` fetches each OSM element (cached in `cache/osm/`, one request a second). It checks:

- the element exists;
- its tags suit the place's kind;
- the pin lies inside the footprint, or within 25 m of it;
- its `wikidata` tag agrees with `wd`.
