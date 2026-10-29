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
- **The places are mostly certain; the claims are not.** Of 75 places, 43 are named outright by Reed. Of 138 scenes, only 81 are things Reed saw.

So the doubt moves from *where* to *whether*: the confidence chip that matters is on the claim, not the pin.

About 40% of the old engine carries over as it is (§6); the rest needs a new model. The deciding cost is not code but data. A reviewed dataset of this size took most of this round. Every line of it is tied to a verbatim quote and machine-checked, and the checks found real contradictions inside the book.

The map's distinct angle should be **the map of Reed's book, not of the revolution.** That means his path, his claims, how he knew them, and where the record (or Reed himself) disagrees. Generic hour-by-hour maps of Petrograd in 1917 already exist (§8).

## 2. What the book gives a mapmaker

From `tools/text.py` (Gutenberg #3076, body pinned by SHA-256):

- **Structure.** 26 sections: Preface, Notes and Explanations, Chapters I–XII, and twelve appendices with 73 numbered sub-sections. All 71 "(See App. X, Sect. n)" cross-references resolve. 17 facsimile markers.
- **Length.** 92,359 words of main text and 28,156 of appendices.
- **Clock times.** Only 62 explicit clock times in the whole book: 36 in the text and 26 in the appendices. Chapter IV, the night of 7–8 November, has three. So most times in any map of this book are estimates, and the data says so: of 138 events, 22 have a time Reed states and 2 a time printed on a document. 29 come from a part-of-day phrase, 2 are known only to the day, 1 is dated from another source (the Moscow funeral, which Reed leaves undated), and 82 are inferred from the order of events, each with its reasoning in `why`.

What the seed dataset holds (`tools/check_story.py --report`):

| | count |
|---|---|
| events (scenes) | 138 |
| moves (one actor's leg) | 117 |
| places with a control timeline | 19 |
| places | 75: 54 city, 10 front, 8 Moscow (text only), 3 off-map |
| places tied to an OSM element | 37 (33 surviving structures, 4 sites of vanished ones) |
| actors (factions, bodies, units, people, crowds) | 64 |
| claims checked against the record | 17 (6 *differs*, 6 *disputed*, 1 *partly*, 4 left *unchecked*) |

**Reed's own path** is the true counterpart of Raskolnikov's walks, and it is better than expected.
- On 5–9 and 13 November he names his streets as often as Dostoevsky does:
  - up the Morskaya, through the Red Arch, over the barricaded Police Bridge;
  - on the MRC truck down the Suvorovsky, across Znamensky Square and along the Nevsky;
  - by ambulance down the Liteiny and the Zagorodny and under the Moskovsky Gate.
- Many legs are therefore drawn solid (`rc: "stated"`), as in the original.

The track has real holes, and the data marks them as `gap`:
- Reed never says where he lodged ("the Russian household where I lived"), so walks from home start at an unlocated point.
- His whereabouts are unknown on the morning of 11 Nov, on 14–15 Nov and on about 17–20 Nov.
- Reed leaves the Moscow trip undated, and its return is not narrated. The record dates the funeral he marched in to 23 Nov, which puts the trip at about 20–23 Nov.

## 3. Why it is not the same treatment

| | Raskolnikov Wandering | Ten Days |
|---|---|---|
| actors | one walker (plus Svidrigailov) | Reed, plus 63 factions, units and people, several moving at once |
| time | day index + "HH:MM" | real New Style dates. Old Style appears in documents. Clock on 1917 summer time. |
| place doubt | which house the initials mean | mostly settled; the doubt is in the claims |
| state | none | buildings and towns change hands (19 timelines) |
| extent | 4.6 × 5.0 km | city ~10 × 10 km, plus a front reaching 43 km south, plus a Moscow trip |
| movement | walks on streets | walks, cabs, trucks, trams, trains, cavalry, armoured cars, ships |
| text check | Garnett and the Russian | Reed against Reed, and Reed against the record |

## 4. Reed as a source

**How he knows.** Of the 138 scenes:
- 81 are `seen` (Reed is there);
- 11 are `told` (an informant: Albert Rhys Williams at the Telephone Exchange, Louise Bryant at St Isaac's, a sailor at the Mariinsky, Lazimir, Zorin and Shatov at Smolny, an ensign of the Pavlovsky Regiment, a Commissar leaving the palace, the ambulance driver at Pulkovo, and "Trusishka", who forced his way into Antonov's car);
- 40 are `reported` (news, rumour, or his own compiled chronology);
- 6 are `document` (orders and bulletins he prints).

The famous minute-by-minute night of 6–7 November does not come from his eyewitness chapter. "At 1 A. M. … the Telegraph Agency. At 1.35 the Post Office … at 5 o'clock the Telephone Exchange" is Appendix III §7, a chronology he compiled. Reed himself says much of the book rests on "several hundred assorted Russian newspapers" and the French *Bulletin de la Presse* (Notes, "Sources"). Most of the fighting of 11–12 November is second-hand.

**Reed against Reed.** These contradictions are inside the book, each recorded as a `check` with the passages side by side:
- **Aurora.** Ch. IV: "two shells from the battleship *Avrora* had struck" the palace cornice. His own App. IV §1: "only three small shrapnels". In Ch. III he calls her one of "the leading Bolshevik cruisers of the Baltic Fleet", which she was. The Aurora's commissar reported orders for blank shots, shrapnel only "if necessary", and "no occasion" for it (`elov1923`).
- **The Telegraph Agency.** Taken "at 1 A. M." in App. III §7. Yet "toward four in the morning" Zorin tells Reed a regiment is still "on the march to capture … the Telegraph Agency" (Ch. III).
- **The truck ride.** In the narrative of Ch. IV it comes before the storming. His caption to the proclamation's facsimile says "just after the surrender of the Winter Palace".
- **Kerensky's route.** App. IV §2: "Kerensky did not arrive at Pskov", then Luga, the South-West Front, Moghilev. But Ch. V quotes a prikaz "launched by him at Pskov", and Ch. VI has him in Gatchina by the night of 8–9 Nov. The data does not draw the Moghilev leg.
- **The Women's Battalion.** A Commissar says the women were marched to the Finland Station and sent to Levashovo. The Duma commission in App. IV §4 says they were first taken to the Pavlovsky barracks.
- **Tsarskoye Selo.** "Entirely occupied" by midnight on the 12th (MRC bulletin, App. IX §1), yet only its "north-eastern extremity" is held at 09:38 on the 13th (Order Number I, Ch. IX).
- **Dybenko.** Reed sees him drive off only after Reed himself has come back from the Rifles' barracks, which he reached when "it was dark". Yet Dybenko reaches Gatchina "toward nightfall". At the inferred 19:30 the sun was 21° below the horizon.

**Measurements that test the text**, the counterpart of the "730 paces". All distances are straight lines between pins: OSM footprints for buildings, hand pins (with their stated radius) for towns and districts.

| Reed says | measured |
|---|---|
| "Gatchina, about thirty kilometers south-west" | 42.9 km, bearing 194° (south-south-west) |
| "Narvskaya Zastava, about ten miles out" | 4.8 km from the Winter Palace, 8.4 km from Smolny |
| the Nicolai Railroad sends trains "southwest" | Moscow lies on a bearing of 134°: south-east |
| the Duma's march "to die in the Winter Palace" | stopped at the Ekaterina Canal, 176 m from the Duma |

The first draft had a fifth row: the MRC bulletin's Cossacks retreating "towards Gatchina and Colpinno", though Kolpino lies 10.8 km east-north-east of Tsarskoye Selo and Gatchina 23.3 km south-west. Review struck it. "Colpinno" also names a sector of the front: a Soviet detachment formed there, Order No. I has it "on our left", and Krasnov's truce offer names "the line Ligovo-Pulkovo-Colpinno" (App. IX §3). The bulletin may mean a retreat along the front, so the claim is now `unchecked`.

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

**Reed against the record, from reference works.** Three verdicts rest on Russian Wikipedia and the Encyclopaedia of St Petersburg, read for this purpose. Their own citations (the Great Soviet Encyclopedia, Abramov 1988, regiment.ru) were not checked, so treat them as leads, not as settled:
- **Vera Slutskaya.** The driver tells Reed on 13 Nov that she was killed "early this morning". The record has 30 Oct Old Style, which is 12 Nov, the day of the Pulkovo battle.
- **The Brotherhood Grave.** "To-morrow we shall bury here five hundred proletarians." 238 coffins were lowered on the day, and 240 burials were made in 1917 in all. The record also dates the funeral to 10 Nov Old Style (23 Nov), which this data uses to date Reed's Moscow days.
- **The Pavlovsk school** (`partly`). Reed has it surrounded on 11 Nov, and all the other schools "surrendered without resistance". The record says it was surrounded and disarmed on the night of 6–7 Nov and took no part in the rising. That fits Reed's own Duma report of 8 Nov, about Pavlovsk yunkers held prisoner in Peter-Paul.

**What remains unchecked.** Four claims are marked `unchecked` rather than given a verdict nobody verified:
- Kerensky's departure "about 9 A. M.". The record has him leave from the Winter Palace, with an American embassy car under the US flag, but gives no hour. Reed's own palace officer, telling how they borrowed gasoline for his car, points the same way, so the data now starts Kerensky's track at the palace.
- Krasnov's "(A. M.)", a bracketed gloss in the reprint.
- Where the Red Cross car went.
- The Cossack retreat "towards Gatchina and Colpinno" (above).

Kerensky's and Krasnov's memoirs and the standard histories would settle most of these; they were not consulted here.

## 5. Period geography

- **Extent and scale.** Smolny, the Finland and Nicolai stations, the Putilov and Obukhov works and the Petrograd Side yunker schools all lie outside the old 23 km² box. The southern front (Pulkovo 18.5 km, Tsarskoye Selo 24.7 km, Gatchina 42.9 km from the Winter Palace) is a different scale altogether. It should be its own view: terrain (the Pulkovo heights), railways and towns, and *no modern buildings*, since nearly all the southern suburbs postdate 1917.
- **Vanished and rebuilt.**
  - The Cirque Moderne is gone.
  - The Nicolai Bridge (rebuilt 1936–38 and 2005–07) and the Finland Station (rebuilt 1960) survive only as sites.
  - The Vladimir yunker school's barracks were demolished in October 2007, apart from one small wing.
  - Moscow's Iberian Gate is a 1995 rebuild.
  - These have `exists: false` (or `null`) and, where useful, `site_osm`. Bridges that did not exist in 1865 but did in 1917 (Palace, Trinity, Bolsheokhtinsky) must come back.
- **Weak identifications.** Six places are conjectural, and two are unlocated (Reed's lodging, and the cross-roads "toward Romanov" where he was nearly shot). The conjectural ones:
  - the Telegraph Agency: TASS's history puts it on Pochtamtskaya, but the house is unknown;
  - the Tsarskoye Soviet's palace;
  - the 2nd Tsarskoye Rifles' barracks;
  - the Cirque Moderne;
  - the Kirochnaya barracks;
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

1. **Review this data** (the user's call). Fix what a human reader finds, decide on the four unchecked claims, and replace the reference-work verdicts with the primary sources behind them.
2. **Port the engine.** Copy it into this repo and drive it from the extended config, actor table and story clock. Render the 3D city core first, with Reed's track, the 19 control timelines and the moves.
3. **The front view.** Terrain, 1917 railways and roads, and towns without modern suburbs.
4. **The 1916 plan overlay** and 1917 bridges, including raised and lowered states where the text gives them.
5. **Coverage.** Chapter I background, the Chapter XI decrees and the appendix documents. Possibly a Moscow inset.

## 10. Open questions and known gaps

- **Reed's lodging.** Biographies may settle it.
- **The clock.** It is assumed that Reed's clock times are local summer time.
- **Unchecked claims.** Four claims need sources that were not consulted, and three verdicts rest on reference works (§4).
- **Uncertain buildings:**
  - house numbers may have changed since 1917: Nevsky 86 is now part of the plot 84-86, and which courtyard wing held apartment 229 is unknown;
  - the Pavlovsk school: OSM has no Krasnogo Kursanta 21, so the pin is in the academy building that fronts the street between nos. 18 and 23, taken to be it.

**What review found.** An independent reviewer checked a sample of 20 events and 20 places against the text and OSM. Every finding was re-read against the text before anything changed, and all but one held up:
- Reed left the palace "through a door opening onto the Neva quay", not across the square.
- The town "held for Kerensky" was a control change with no basis: the Colonel takes it back two sentences later.
- One place misquoted Reed: the "Pulkovo fork" stood on "where the road divided", but Reed's words are "At Pulkovo the road divided".
- Some moves had no support in the text: the yunkers' march to the Grebetskaya corner (the corner was where the Soviet fire came from), the sailors' march on the Morskaya, and Reed walking out to the yunker sortie, which he watched from a window.
- Some witness types were wrong, and one cab ride was recorded as a car.
- The exception: the reviewer would have made the Morskaya `named`. It stays `identified`, because Reed never says which Morskaya.

Checking the findings turned up more:
- a paraphrase in our own notes printed as a Reed quote ("a day and two nights" on the Moscow train);
- the Pavlovsk school's disarming on 6–7 Nov;
- the Vladimir school's demolition.

All are fixed. The lesson for the next round is that the validator catches what can be checked mechanically (quotes, dates, chains, footprints), not what has been misread.

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
- Russian Wikipedia, tertiary sources whose own citations were not checked: [Слуцкая, Вера Климентьевна](https://ru.wikipedia.org/wiki/Слуцкая,_Вера_Климентьевна); [Некрополь у Кремлёвской стены](https://ru.wikipedia.org/wiki/Некрополь_у_Кремлёвской_стены); [Керенский, Александр Фёдорович](https://ru.wikipedia.org/wiki/Керенский,_Александр_Фёдорович); [Павловское военное училище](https://ru.wikipedia.org/wiki/Павловское_военное_училище); [Малая Гребецкая улица](https://ru.wikipedia.org/wiki/Малая_Гребецкая_улица); [Дом Союзов](https://ru.wikipedia.org/wiki/Дом_Союзов).
- [Encyclopaedia of St Petersburg, "Красного Курсанта улица"](https://encspb.ru/object/2804017850): the Pavlovsk school at no. 21 from 1894.
- [Suvorin, *Plan of Petrograd*, 1916](https://commons.wikimedia.org/wiki/File:Plan_Petrograd_Suvorin_1916.jpg) (Wikimedia Commons).
- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL): every pin, footprint and distance.
