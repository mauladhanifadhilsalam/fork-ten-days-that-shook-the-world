# Assessment: a 3D map of Reed's *Ten Days That Shook the World*

This assesses whether the *Raskolnikov Wandering* treatment (a 3D, scene-by-scene map of a book over the real street plan of St Petersburg) can be given to John Reed's *Ten Days That Shook the World* (1919): his Petrograd of October–December 1917, its factions, and the movements he reports. It is written after building the seed dataset in `data/`, so its numbers come from that work. Each number can be reproduced with the commands at the end.

## 1. Verdict

It is worth doing, but it is not the same treatment, and pretending otherwise would produce a worse map.

*Raskolnikov Wandering* rests on four assumptions:
- one fictional walker;
- one walk per scene;
- 23 km² of streets around the Haymarket;
- places hidden behind initials, so the rigour goes into resolving addresses.

*Ten Days* breaks every one of them:
- **Many actors move at once,** and buildings change hands, some of them three times in five days.
- **The dates are real, and both the calendar and the clock are traps** (§4).
- **The action runs 43 km south,** to Gatchina, and the trip to Moscow covers 635 km.
- **The places are mostly certain; the claims are not.** Of 74 places, 43 are named outright by Reed. Of 134 scenes, only 79 are things Reed saw.

So the doubt moves from *where* to *whether*: the confidence chip that matters is on the claim, not the pin.

About 40% of the old engine carries over as it is (§6); the rest needs a new model. The deciding cost is not code but data. A reviewed dataset of this size took most of this round. Every line of it is tied to a verbatim quote and machine-checked, and the checks found real contradictions inside the book.

The map's distinct angle should be **the map of Reed's book, not of the revolution.** That means his path, his claims, how he knew them, and where the record (or Reed himself) disagrees. Generic hour-by-hour maps of Petrograd in 1917 already exist (§8).

## 2. What the book gives a mapmaker

From `tools/text.py` (Gutenberg #3076, body pinned by SHA-256):

- **Structure.** 26 sections: Preface, Notes and Explanations, Chapters I–XII, and twelve appendices with 73 numbered sub-sections. All 71 "(See App. X, Sect. n)" cross-references resolve. 17 facsimile markers.
- **Length.** 92,359 words of main text and 28,156 of appendices.
- **Clock times.** Only 62 explicit clock times in the whole book: 36 in the text and 26 in the appendices. Chapter IV, the night of 7–8 November, has three. So most times in any map of this book are estimates, and the data says so: of 134 events, 22 have a time Reed states and 2 a time printed on a document. 28 come from a part-of-day phrase, 1 is known only to the day, and 81 are inferred from the order of events, each with its reasoning in `why`.

What the seed dataset holds (`tools/check_story.py --report`):

| | count |
|---|---|
| events (scenes) | 134 |
| moves (one actor's leg) | 113 |
| places with a control timeline | 19 |
| places | 74: 53 city, 11 front, 7 Moscow (text only), 3 off-map |
| places tied to an OSM element | 34 (30 surviving buildings, 4 sites of vanished ones) |
| actors (factions, bodies, units, people, crowds) | 63 |
| claims checked against the record | 16 (5 *differs*, 6 *disputed*, 5 left *unchecked*) |

**Reed's own path** is the true counterpart of Raskolnikov's walks, and it is better than expected.
- On 5–9 and 13 November he names his streets as often as Dostoevsky does:
  - up the Morskaya, through the Red Arch, over the barricaded Police Bridge;
  - on the MRC truck down the Suvorovsky, across Znamensky Square and along the Nevsky;
  - by ambulance down the Liteiny and the Zagorodny and under the Moskovsky Gate.
- Many legs are therefore drawn solid (`rc: "stated"`), as in the original.

The track has real holes, and the data marks them as `gap`:
- Reed never says where he lodged ("the Russian household where I lived"), so walks from home start at an unlocated point.
- His whereabouts are unknown on the morning of 11 Nov, on 14–15 Nov and on about 17–22 Nov.
- The Moscow trip is undated, and its return is not narrated.

## 3. Why it is not the same treatment

| | Raskolnikov Wandering | Ten Days |
|---|---|---|
| actors | one walker (plus Svidrigailov) | Reed, plus 62 factions, units and people, several moving at once |
| time | day index + "HH:MM" | real New Style dates. Old Style appears in documents. Clock on 1917 summer time. |
| place doubt | which house the initials mean | mostly settled; the doubt is in the claims |
| state | none | buildings and towns change hands (19 timelines) |
| extent | 4.6 × 5.0 km | city ~10 × 10 km, plus a front reaching 43 km south, plus a Moscow trip |
| movement | walks on streets | walks, trucks, trams, trains, cavalry, armoured cars, ships |
| text check | Garnett and the Russian | Reed against Reed, and Reed against the record |

## 4. Reed as a source

**How he knows.** Of the 134 scenes:
- 79 are `seen` (Reed is there);
- 10 are `told` (an informant: Albert Rhys Williams at the Telephone Exchange, Louise Bryant at St Isaac's, a sailor at the Mariinsky, Zorin and Shatov at Smolny);
- 39 are `reported` (news, rumour, or his own compiled chronology);
- 6 are `document` (orders and bulletins he prints).

The famous minute-by-minute night of 6–7 November does not come from his eyewitness chapter. "At 1 A. M. … the Telegraph Agency. At 1.35 the Post Office … at 5 o'clock the Telephone Exchange" is Appendix III §7, a chronology he compiled. Reed himself says much of the book rests on "several hundred assorted Russian newspapers" and the French *Bulletin de la Presse* (Notes, "Sources"). Most of the fighting of 11–12 November is second-hand.

**Reed against Reed.** These contradictions are inside the book, each recorded as a `check` with the passages side by side:
- **Aurora.** Ch. IV: "two shells from the battleship *Avrora* had struck" the palace cornice. His own App. IV §1: "only three small shrapnels", and there he calls her the cruiser she was. The Aurora's commissar reported orders for blank shots, shrapnel only "if necessary", and "no occasion" for it (`elov1923`).
- **The Telegraph Agency.** Taken "at 1 A. M." in App. III §7. Yet "toward four in the morning" Zorin tells Reed a regiment is still "on the march to capture … the Telegraph Agency" (Ch. III).
- **The truck ride.** In the narrative of Ch. IV it comes before the storming. His caption to the proclamation's facsimile says "just after the surrender of the Winter Palace".
- **Kerensky's route.** App. IV §2: "Kerensky did not arrive at Pskov", then Luga, the South-West Front, Moghilev. But Ch. V quotes a prikaz "launched by him at Pskov", and Ch. VI has him in Gatchina by the night of 8–9 Nov. The data does not draw the Moghilev leg.
- **The Women's Battalion.** A Commissar says the women were marched to the Finland Station and sent to Levashovo. The Duma commission in App. IV §4 says they were first taken to the Pavlovsky barracks.
- **Tsarskoye Selo.** "Entirely occupied" by midnight on the 12th (MRC bulletin, App. IX §1), yet only its "north-eastern extremity" is held at 09:38 on the 13th (Order Number I, Ch. IX).
- **Dybenko.** He leaves Tsarskoye after dark, yet reaches Gatchina "toward nightfall".

**Measurements that test the text**, the counterpart of the "730 paces". All distances are straight lines between the OSM pins:

| Reed says | measured |
|---|---|
| "Gatchina, about thirty kilometers south-west" | 42.9 km, bearing 194° (south-south-west) |
| "Narvskaya Zastava, about ten miles out" | 4.8 km from the Winter Palace, 8.4 km from Smolny |
| the Nicolai Railroad sends trains "southwest" | Moscow lies on a bearing of 134°: south-east |
| the Cossacks retreat "towards Gatchina and Colpinno" | Kolpino is 10.8 km east-north-east of Tsarskoye, Gatchina 23.3 km south-west |
| the Duma's march "to die in the Winter Palace" | stopped at the Ekaterina Canal, 176 m from the Duma |

**The calendar.** In Notes, "Chronology and Spelling", Reed writes: "I have adopted in this book our Calendar throughout, instead of the former Russian Calendar, which was thirteen days earlier." His narrative keeps to this, but the documents he prints do not. Each date in the data therefore carries the calendar it was written in (`cal`) and is checked against the event's New Style date:
- The Pulkovo staff's telegram, "The night of October 30th to 31st", is Old Style (= 12–13 Nov). It sits beside an Order Number I dated New Style, "November 13, 1917".
- In Chapter XII, the peasants' torchlit march falls on "Thursday, November 16th". 16 Nov New Style was a Friday; 16 Nov Old Style (29 Nov) was a Thursday. The line comes just after a New Style "Wednesday morning, November 28th".

Every weekday–date pair in the book was tested both ways:

| section | phrase | fits as New Style | fits as Old Style |
|---|---|---|---|
| III | Sunday, November 4 | yes | no |
| III | Tuesday morning, November 6 | yes | no |
| IV | Wednesday, November 7 | yes | no |
| V | Thursday, November 8 | yes | no |
| VI | Friday, November 9 | yes | no |
| VII | Saturday, November 10 | yes | no |
| XII | Wednesday morning, November 28 | yes | no |
| XII | Thursday, November 16 | no | **yes** |

**The clock.** The IANA tz database has Russia on summer time, one hour ahead, from 1 July 1917 until Decree No. 142 of late December. Whether its dates are Old or New Style is disputed, but November falls inside either way. Petrograd clocks therefore ran about UTC+3:01 (Pulkovo mean time plus an hour). The old map's sky assumes local mean time, which would put every 1917 scene an hour out. On 7 November that clock gives sunrise at about 08:36 and sunset at about 16:51. The light table in `--report` shows Reed's "dusk" and "twilight" scenes are consistent with that sun. It cannot *prove* the offset, because most of those scenes' times are our estimates. That Reed read local clocks is assumed, not shown.

**What he could not have seen:** the night's seizures, the dispersal of the Council of the Republic (he saw only its aftermath), Lenin's first appearance at the Soviet (it was over when he arrived), Kerensky's flight, and the Women's Battalion's fate.

**Partisan framing.** Reed says himself: "my sympathies were not neutral" (Preface). It shows in sweeping claims such as "on that night not a single hold-up occurred, not a single robbery". In the data such lines stay claims, not facts.

**What remains unchecked.** Five claims are marked `unchecked` rather than given a verdict nobody verified:
- Kerensky's departure "about 9 A. M.";
- Krasnov's "(A. M.)";
- the date of Slutskaya's death;
- the "five hundred" dead in the Brotherhood Grave;
- where the Red Cross car went.

Verifying them needs Kerensky's and Krasnov's memoirs and standard histories, which were not consulted here.

## 5. Period geography

- **Extent and scale.** Smolny, the Finland and Nicolai stations, the Putilov and Obukhov works and the Petrograd Side yunker schools all lie outside the old 23 km² box. The southern front (Pulkovo 18.5 km, Tsarskoye Selo 24.7 km, Gatchina 42.9 km from the Winter Palace) is a different scale altogether. It should be its own view: terrain (the Pulkovo heights), railways and towns, and *no modern buildings*, since nearly all the southern suburbs postdate 1917.
- **Vanished and rebuilt.**
  - The Cirque Moderne is gone.
  - The Nicolai Bridge (rebuilt 1936–38 and 2005–07) and the Finland Station (rebuilt 1960) survive only as sites.
  - The Vladimir yunker school's building is uncertain.
  - Moscow's Iberian Gate is a 1995 rebuild.
  - These have `exists: false` (or `null`) and, where useful, `site_osm`. Bridges that did not exist in 1865 but did in 1917 (Palace, Trinity, Bolsheokhtinsky) must come back.
- **Weak identifications.** Seven places are conjectural, and two are unlocated (Reed's lodging, and the cross-roads "toward Romanov" where he was nearly shot). Among the conjectural ones:
  - the Telegraph Agency: TASS's history puts it on Pochtamtskaya, but the house is unknown;
  - the Tsarskoye Soviet's palace;
  - the 2nd Tsarskoye Rifles' barracks;
  - the Pulkovo fork;
  - "Uncle Tom's Cabin".
- **The period plan.** Suvorin's *Plan of Petrograd with its immediate surroundings* (1916, 1:21,000, public domain, on Wikimedia Commons) is the natural replacement for the 1868 Musnitsky overlay, warped with the same `georef_plan.py` method. A 1917 edition is reportedly on Commons too; that has not been verified.
- **Moscow** stays text only, as decided. Its seven places carry coordinates and OSM ids in case an inset is ever wanted.

## 6. The engine: what carries over

From a read-only survey of `raskolnikov-wandering`:

**Reusable as it is:**
- the bundle and container (`tools/bundle.py`, Dockerfile, nginx);
- the routing helpers in `build_story.py` (snap, Dijkstra, the smoothing passes);
- the quote check;
- the plan-warping method;
- from `src/app.html`: ground and building construction, the sky shader, labels, the trail mechanics, camera flights, hash routing and the intro.

**Needs generalising:**
- **Configuration.** The extent and origin are hard-coded in `build_map.py:26` and `fetch_osm.py:59-68`, and bridges are matched by name substring. They need a config, with bridges keyed by OSM id and by year.
- **Actors and the clock.** The R/S special cases (about 16 in `app.html`) become an actor table, and one story clock drives several movers.
- **Changing state.** Buildings that change hands need their own meshes, keyed by OSM id. Today all buildings are one anonymous mesh.
- **Calendar and sky.** Dates in both calendars, and `sunPos(date, time)` on the 1917 clock.
- **Routing by mode:** rail, road, water, free-form.
- **Two scales:** a 3D city core and a coarse 2D front.

**Drop:** the Russian-text checks, the fever band, the 730-paces and verst measures, and the Crime and Punishment copy.

**Bugs found in passing** (in the old repo, not fixed here):
- street centre-lines over the removed bridges are still drawn;
- the bridge filter also strips ordinary streets (Биржевой проезд, Биржевой переулок, Дворцовый проезд) from routing;
- 87% of park vertices are consecutive duplicates, about 0.6 MB of the page.

**The larger extent's data.** Overpass and Geofabrik are not reachable from this build environment; the OSM API is, so the first rendering round should plan around it. The data tools here already use it: `tools/geocode.py` finds buildings in small boxes around a hint, and `check_story.py --osm` tests each pin against its footprint.

## 7. The data model

`docs/schema.md` has the full reference. In brief:
- **Control** lives on the event that reports it, so a change of hands inherits that event's time, quote and witness type.
- **Times** carry a quality (`tq`), bounds (`tr`), the verbatim phrase (`tp`) and, when inferred, the reasoning (`why`).
- **Claims** are checked as `check[]` entries quoting the exact words at issue.
- **Reed's track** must chain, and every `seen` scene must be where his track puts him.

Factions are coloured by stance toward the insurrection over time, deliberately not "Red vs White". In November 1917 the Committee for Salvation was led by SRs and Mensheviks, not by Whites.

## 8. Prior art and positioning

- **Bard College, *Petrograd 1917*.** Built with the Yeltsin Presidential Library and the National Library of Russia, it maps the February and October days hour by hour from eyewitness accounts. Its site was not reachable from this environment, so the description is second-hand.
- **The Presidential Library's *Petrograd in 1917: what, where, when*.** An interactive calendar with addresses and archive photographs.
- **Notre Dame's *Red Wheel* map,** for Solzhenitsyn's novels.

None of these is a map of *Reed's book*: his route, his claims and their sources, and where he contradicts himself. That is the gap this project fills. It also argues against padding the map with events Reed does not report; the dataset has no `context` events at all yet.

## 9. Roadmap

1. **Review this data** (the user's call). Fix what a human reader finds, and decide on the five unchecked claims and their sources.
2. **Port the engine.** Copy it into this repo and drive it from the extended config, actor table and story clock. Render the 3D city core first, with Reed's track, the 19 control timelines and the moves.
3. **The front view.** Terrain, 1917 railways and roads, and towns without modern suburbs.
4. **The 1916 plan overlay** and 1917 bridges, including raised and lowered states where the text gives them.
5. **Coverage.** Chapter I background, the Chapter XI decrees and the appendix documents. Possibly a Moscow inset.

## 10. Open questions and known gaps

- **Reed's lodging.** Biographies may settle it.
- **The clock.** It is assumed that Reed's clock times are local summer time.
- **Unchecked claims.** Five claims need sources that were not consulted (§4).
- **Uncertain buildings:**
  - house numbers may have changed since 1917 (Nevsky 86);
  - the Pavlovsk school (OSM has no Krasnogo Kursanta 21; the pin sits by nos. 23–25);
  - the Vladimir school (part of the site is now housing).

## Reproducing the numbers

```bash
python3 -I tools/text.py cache
```

```bash
python3 -I tools/check_story.py --report
```

```bash
python3 -I tools/check_story.py --osm
```

```bash
python3 -I tools/check_story.py --pdf cache/ten-days-reed.pdf
```

The last one needs pypdf and the PDF downloaded to `cache/` (see the README).

## Sources

- John Reed, *Ten Days That Shook the World*, [Project Gutenberg #3076](https://www.gutenberg.org/ebooks/3076); the [Marxists Internet Archive PDF](https://www.marxists.org/ebooks/reed/ten-days-that-shook-the-world-reed.pdf) for page numbers.
- [Report of the commissar of the cruiser Aurora](https://soviethistory.msu.edu/1917/bolsheviks-seize-power/bolsheviks-seize-power-texts/action-of-the-cruiser-aurora/) (Elov, *Krasnaia letopis'* 6, 1923), via *Seventeen Moments in Soviet History*.
- [IANA tz database, `europe`](https://github.com/eggert/tz/blob/main/europe) (Rule Russia 1917); [tz mailing list, March 2021](https://mm.icann.org/pipermail/tz/2021-March/054958.html).
- [TASS, "History"](https://tass.com/history): the PTA building on Pochtamtskaya.
- [Suvorin, *Plan of Petrograd*, 1916](https://commons.wikimedia.org/wiki/File:Plan_Petrograd_Suvorin_1916.jpg) (Wikimedia Commons).
- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL): every pin, footprint and distance.
