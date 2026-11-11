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
- **The places are mostly certain; the times and the vantage point are not.** Of 104 places, 42 are named outright by Reed. Of 157 scenes, only 94 are things Reed saw, and most times are estimates.

About 40% of the old engine carries over as it is (§6); the rest needs a new model. The deciding cost is not code but data. A reviewed dataset of this size took most of this round, and every line of it is tied to a verbatim quote and machine-checked against Reed's text.

**The map follows Reed authoritatively.** It is the map of Reed's book, not of the revolution: his path, what he saw and heard, and how he knew it, told his way. It portrays his account, sympathies included, and is not a fact-check: nothing in it is corrected or flagged from other sources. Outside sources locate his places and set the 1917 clock, and, where Reed leaves a gap in a scene he does tell, may fill it, always marked as not his (§10). In this round they placed one thing: the field-pieces that shelled the Vladimir school, on the Malaya Raznochinnaya, from a Russian Wikipedia sentence that carries no footnote of its own. For who retook the Military Hotel, where the cruisers Trotzky names lay, and the Telegraph Agency's house, no source reachable from here says, so those remain the map's, and say so. Generic hour-by-hour maps of Petrograd in 1917 already exist (§8); this one is Reed's.

## 2. What the book gives a mapmaker

From `tools/text.py` (Gutenberg #3076, body pinned by SHA-256):

- **Structure.** 26 sections: Preface, Notes and Explanations, Chapters I–XII, and twelve appendices with 73 numbered sub-sections. All 71 "(See App. X, Sect. n)" cross-references resolve. 17 facsimile markers.
- **Length.** 92,359 words of main text and 28,156 of appendices.
- **Clock times.** Only 62 explicit clock times in the whole book: 36 in the text and 26 in the appendices. Chapter IV, the night of 7–8 November, has three. So most times in any map of this book are estimates, and the data says so: of 157 events, 22 have a time Reed states and 2 a time printed on a document. 31 come from a part-of-day phrase, 2 are known only to the day, and 100 are inferred from Reed's own sequence of events, each with its reasoning in `why`.

What the dataset holds (`tools/check_story.py --report`):

| | count |
|---|---|
| events (scenes) | 157 |
| moves (one actor's leg) | 142 |
| places with a control timeline | 20 |
| places | 104: 83 city, 10 front, 8 Moscow (text only), 3 off-map |
| places tied to an OSM element | 38 (33 surviving structures, the Mikhailovsky school's building, 4 sites of vanished ones) |
| actors (factions, bodies, units, people, crowds) | 77 |

**Reed's own path** is the true counterpart of Raskolnikov's walks, and it is better than expected.
- On 5–9 and 13 November he names his streets as often as Dostoevsky does:
  - up the Morskaya, through the Red Arch, over the barricaded Police Bridge;
  - on the MRC truck down the Suvorovsky, across Znamensky Square and along the Nevsky;
  - by ambulance down the Liteiny and the Zagorodny and under the Moskovsky Gate.
- Many legs are therefore drawn solid (`rc: "stated"`), as in the original.

The track has real holes, and the data marks them as `gap`:
- Reed never says where he lodged ("the Russian household where I lived"), so walks from home start at an unlocated point.
- His whereabouts are unknown on the morning of 11 Nov, on 14–15 Nov and on about 17–18 Nov.
- Reed leaves the Moscow trip undated, and its return is not narrated. His own clues fix only the earliest day: he decided to go once the Kremlin had been Bolshevik "for two days" (it surrendered on 15 Nov), and the Commissars who had just resigned were on his train. The data puts the train on the evening of 19 Nov and the funeral on the 21st, with a window of about a week.

## 3. Why it is not the same treatment

| | Raskolnikov Wandering | Ten Days |
|---|---|---|
| actors | one walker (plus Svidrigailov) | Reed, plus 76 factions, units and people, several moving at once |
| time | day index + "HH:MM" | real New Style dates. Old Style appears in documents. Clock on 1917 summer time. |
| place doubt | which house the initials mean | mostly settled |
| state | none | buildings and towns change hands (20 timelines) |
| extent | 4.6 × 5.0 km | city ~10 × 10 km, plus a front reaching 43 km south, plus a Moscow trip |
| movement | walks on streets | walks, cabs, trucks, trams, trains, cavalry, armoured cars, ships |
| text check | Garnett and the Russian | Reed's English text: every quote, date and step of his path |

## 4. Reading Reed

**How he knows.** The map keeps Reed's own vantage point. Of the 157 scenes:
- 94 are `seen` (Reed is there);
- 11 are `told` (an informant: Albert Rhys Williams at the Telephone Exchange, Louise Bryant at St Isaac's, a sailor at the Mariinsky, Lazimir, Zorin and Shatov at Smolny, an ensign of the Pavlovsky Regiment, a Commissar leaving the palace, the ambulance driver at Pulkovo, and "Trusishka", who forced his way into Antonov's car);
- 46 are `reported` (news, rumour, or his own compiled chronology);
- 6 are `document` (orders and bulletins he prints).

The famous minute-by-minute night of 6–7 November does not come from his eyewitness chapter. "At 1 A. M. … the Telegraph Agency. At 1.35 the Post Office … at 5 o'clock the Telephone Exchange" is Appendix III §7, a chronology he compiled. Reed himself says much of the book rests on "several hundred assorted Russian newspapers" and the French *Bulletin de la Presse* (Notes, "Sources"). Most of the fighting of 11–12 November reaches him second-hand. He could not have seen the night's seizures, the dispersal of the Council of the Republic (he saw only its aftermath), Lenin's first appearance at the Soviet (it was over when he arrived), Kerensky's flight, or the Women's Battalion's fate; the map draws those as told or reported, in Reed's words.

**His sympathies.** "My sympathies were not neutral" (Preface). The map keeps his framing by design: it portrays his side of the story.

**When Reed disagrees with himself,** the map still has to draw one version. The rule: the main narrative wins over his appendices, captions and the documents he prints; between two documents, the more specific one wins. It settles every case met so far:
- the palace cornice struck by "two shells from the battleship *Avrora*" (Ch. IV), not App. IV's "three small shrapnels";
- the proclamation truck ride before the storming, as Ch. IV narrates it, not "just after the surrender", as his facsimile caption has it;
- Kerensky by Ostrov and Luga (App. IV §2), since the narrative only quotes a prikaz "launched by him at Pskov";
- the Women's Battalion marched to the Finland Station, as the Commissar tells Reed;
- Tsarskoye Selo "entirely occupied" by midnight on the 12th, from the MRC bulletin;
- the Telegraph Agency taken "at 1 A. M.", from App. III §7, the only account of the seizure;
- Dybenko leaving Tsarskoye after dark, as Reed watched him go.

**The calendar.** In Notes, "Chronology and Spelling", Reed writes: "I have adopted in this book our Calendar throughout, instead of the former Russian Calendar, which was thirteen days earlier." His narrative keeps to this, but the documents he prints do not. Following Reed means reading each date in the calendar it was written in, so each date in the data carries its calendar (`cal`) and is checked against the event's New Style date:
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

**The clock.** The IANA tz database has Russia on summer time, one hour ahead, from 1 July 1917 until Decree No. 142 of late December. Whether its dates are Old or New Style is disputed, but November falls inside either way. Petrograd clocks therefore ran about UTC+3:01 (Pulkovo mean time plus an hour). The old map's sky assumes local mean time, which would put every 1917 scene an hour out. On 7 November that clock gives sunrise at about 08:36 and sunset at about 16:51. The light table in `--report` shows Reed's "dusk" and "twilight" scenes sit under that sun. That Reed read local clocks is assumed, not shown.

## 5. Period geography

- **Extent and scale.** Smolny, the Finland and Nicolai stations, the Putilov and Obukhov works and the Petrograd Side yunker schools all lie outside the old 23 km² box. The southern front (Pulkovo 18.5 km, Tsarskoye Selo 24.7 km, Gatchina 42.9 km from the Winter Palace) is a different scale altogether. It should be its own view: terrain (the Pulkovo heights), railways and towns, and *no modern buildings*, since nearly all the southern suburbs postdate 1917.
- **Vanished and rebuilt.**
  - The Cirque Moderne is gone.
  - The Nicolai Bridge (rebuilt 1936–38 and 2005–07) and the Finland Station (rebuilt 1960) survive only as sites.
  - The Vladimir yunker school's barracks were demolished in October 2007, apart from one small wing.
  - Moscow's Iberian Gate is a 1995 rebuild.
  - These have `exists: false` (or `null`) and, where useful, `site_osm`. Bridges that did not exist in 1865 but did in 1917 (Palace, Trinity, Bolsheokhtinsky) must come back.
- **Weak identifications.** Twenty-one places are conjectural, and two are unlocated (Reed's lodging, and the cross-roads "toward Romanov" where he was nearly shot). The conjectural ones:
  - the Telegraph Agency: TASS's history puts it on Pochtamtskaya, but the house is unknown;
  - the Tsarskoye Soviet's palace;
  - the 2nd Tsarskoye Rifles' barracks;
  - the Cirque Moderne;
  - the Kirochnaya barracks;
  - "Uncle Tom's Cabin";
  - the "moving picture show near the Kazan Cathedral", and the Avrora's anchorage in the Neva;
  - the parts of places Reed gives only by a street or a gate: the corners of the Liteiny and of the Sadovaya on the Nevsky, the Nevsky at "the corner of the Ekaterina Canal" on the Duma side, the Morskaya off St Isaac's Square, Smolny's "outer gates" and "inner gate", the end of the Nicolai Bridge the picket ran to, and Reed's "Voskressensky Prospect", taken to be the Voznesensky (the Voskresensky lay 4 km off, out of his sight from the Marinsky).
  - points the map picks where Reed names no spot: the entrance to the Palace Square from the Millionnaya, a street-corner near Smolny, the anchorages of the Oleg and the Respublica in the Neva, and, from another source, the end of the Malaya Raznochinnaya where the Vladimir school's shelling is drawn from.
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

**Bugs found in passing** (in the old repo, not fixed there; the copies here are fixed):
- street centre-lines over the removed bridges are still drawn;
- the bridge filter also strips ordinary streets (Биржевой проезд, Биржевой переулок, Дворцовый проезд) from routing;
- 87% of park vertices are consecutive duplicates, about 0.6 MB of the page;
- the sun is mirrored north to south. `setLight` builds the sun's direction as `(sin az, …, cos az)`, but world `z` points south, so a noon sun (azimuth 180°) is placed in the north and the shadows fall south. The glow in the sky shader has the same sign error. Here the direction is `(sin az, …, −cos az)`.

**Fixed while porting.** Line materials created after the first resize kept a 1×1 resolution, which made a 4-pixel route line several screens wide; they now take the canvas size when they are made. A pin inside a building could snap onto a courtyard path cut off from the street network, which left the router stranded; snapping now uses the main network only.

**The larger extent's data.** Overpass and Geofabrik are not reachable from this build environment, so `tools/fetch_osm.py` uses the OSM API: 153 small tiles over the 7.0 × 5.0 km core (about 205 MB), plus the 34 water relations they touch, fetched whole. The core holds 10,327 buildings and Reed's 22.

## 7. The data model

`docs/schema.md` has the full reference. In brief:
- **Control** lives on the event that reports it, so a change of hands inherits that event's time, quote and witness type.
- **Times** carry a quality (`tq`), bounds (`tr`), the verbatim phrase (`tp`) and, when inferred, the reasoning (`why`).
- **Only Reed** drives events, times, moves and control. Every event is a passage of his, and when his passages disagree the narrative wins (§4). Outside sources appear only on places (`src`, `geo`) and in the clock.
- **Reed's track** must chain, and every `seen` scene must be where his track puts him.

Factions are coloured by stance toward the insurrection over time, deliberately not "Red vs White". In November 1917 the Committee for Salvation was led by SRs and Mensheviks, not by Whites.

## 8. Prior art and positioning

- **Bard College, *Petrograd 1917*.** Built with the Yeltsin Presidential Library and the National Library of Russia, it maps the February and October days hour by hour from eyewitness accounts. Its site was not reachable from this environment, so the description is second-hand.
- **The Presidential Library's *Petrograd in 1917: what, where, when*.** An interactive calendar with addresses and archive photographs.
- **Notre Dame's *Red Wheel* map,** for Solzhenitsyn's novels.

None of these is a map of *Reed's book*: his route, what he saw and heard, and how he knew it. That is the gap this project fills. It also rules out padding the map with events Reed does not report: every event in the data is a passage of his.

## 9. Roadmap

1. **Review this data** (the user's call), and fix what a human reader finds.
2. **Port the engine.** *Begun.* The engine is copied into this repo and driven by the data: the 3D city core (7.0 × 5.0 km), Reed's track and the other moves, the 20 control timelines on Reed's buildings, the 1917 sky, the first snow, and a three-card introduction for readers new to the book. Next: a places index, and the tram and rail lines of 1917.
   - *Done since:*
     - The tour keeps to Petrograd: 131 of the 157 scenes.
     - The people of each scene are on the map, as low-poly 1917 figures, vehicles, kit and the Avrora. They stay where Reed's text keeps them: 175 presence spans, each tied to a passage of his.
     - They stand in the formation Reed gives them in that scene: columns, lines, companies drawn up, columns marching past. Their banners and flags carry his words.
     - 55 pictures illustrate 51 scenes. 11 are Reed's own facsimiles; 44 are public-domain photographs, postcards and documents from Wikimedia Commons, each captioned with what it shows and when.
     - The uniforms rest on photographs; docs/uniforms.md lists them.
     - The fighting is drawn where Reed has a body fire, and as he has it: rings of sections round a besieged building ("surrounded the building and opened fire"), a garrison firing from its windows, field-guns whose shells leave holes in the walls for the later scenes, armoured cars "cruising back and forth", assault waves that "crumpled" or that "poured through" the doors, the dead where they fell, crowds "falling flat on their faces". A shot he only hears is not drawn, and neither is a shooter he does not see. Reed's own storming of the Winter Palace has no firing in it ("The shooting had ceased"), so the map draws it as he does: a mass that pours through the Red Arch, huddles behind the Alexander Column, and goes over the barricade of firewood past "a heap of rifles thrown down by the yunkers".
     - Where bodies stand was re-read scene by scene against Reed (a survey of every tour scene, then edit plans checked op by op): the parts of places he names have places of their own (Smolny's door and outer gates, the Nevsky before the Duma's door, the Kazan Square, the corner of the Liteiny, the western end of the Palace Square); lines stand across the street or the opening he names; defenders face out from their walls, and a body faces what Reed has it watch; moves he separates in time are separate scenes, so no column walks both ways at once.
   - *What the figures are not:* a head count, or a claim about any uniform in particular. Every kind of person Reed names in a body shows, however few ("with only a few scattered soldiers"). The counts drawn are display choices from Reed's phrases ("two thousand" is drawn as 140), the faces are all alike, and the uniforms are the common ones of 1917 Petrograd, not the regiment's. Where a body stands within a place is the open ground nearest the place (or its stage, the ground before its door), not something Reed says, except where the data names the part of the place he gives. So is how far off besiegers keep: Reed puts the sailors besieging the Telephone Exchange "in the middle of the Morskaya", not how far down it, and the map stands them in the street before the building, behind their barricades. A formation is drawn only where Reed's words give it. Which way a passing column walks is ours unless Reed has it face something or gives the way: "up the Nevsky" is read as Reed uses it when the procession goes "back up the Nevsky" to the Duma, away from the Admiralty; where a column comes from and goes to on the street is ours. In a fight, who fires at whom is Reed's; how often each man fires, where each section of a ring stands, which window a shot comes from, where a shell strikes and how far an armoured car cruises, where along a bridge it opens, and how loosely a crowd that "blocked the Nevsky" stands are the map's. One body is drawn that Reed does not name: the Military Hotel and the Telegraph Agency were "bloodily recaptured", by whom he does not say, and the map draws sailors (who had held the hotel) storming both, the yunkers firing from the windows; the scene's card says so. Two touches are the map's own, not the record's: the Red Guard's red arm band, and the machine-gun belts some sailors wear crossed on the chest.
   - *What the pictures are not:* evidence. Most show the place or the people, not the moment. The postcards are from before 1917, the Avrora from 1909–14, Trotsky probably from 1918, Lenin from August 1917, and several Commons photographs have no exact day. The captions say so. No public-domain photograph was found for six scenes' places: the Telephone Exchange, the Post Office, the Telegraph Agency, the Astoria, the Hotel France and the Kirochnaya barracks.
3. **The front view**, if the tour is ever to leave the city: terrain, 1917 railways and roads, and towns without modern suburbs.
4. **The 1916 plan overlay** and 1917 bridges, including raised and lowered states where the text gives them.
5. **Coverage.** Chapter I background, the Chapter XI decrees and the appendix documents. Possibly a Moscow inset.

## 10. Open questions and known gaps

- **Reed's lodging.** Biographies may settle it.
- **The clock.** It is assumed that Reed's clock times are local summer time.
- **The Moscow dates.** Reed's clues give only the earliest day (§2); the window is about a week wide.
- **Uncertain buildings:**
  - house numbers may have changed since 1917: Nevsky 86 is now part of the plot 84-86, and which courtyard wing held apartment 229 is unknown;
  - the Pavlovsk school: OSM has no Krasnogo Kursanta 21, so the pin is in the academy building that fronts the street between nos. 18 and 23, taken to be it.
- **Limits of the drawing** (the map's, not the record's):
  - *Night.* After dark one warm light hangs over the scene, standing in for the street lamps, which are not drawn; buildings show no lit windows ("in the light that streamed out of all the Winter Palace windows" is not drawn).
  - *The Nevsky.* The whole avenue is one place with one pin, by the Duma, so a body Reed puts "on the Nevsky" with no nearer landmark is drawn there, whichever stretch he means. Its named parts (the corners of the Morskaya, the Sadovaya and the Liteiny, the Kazan Bridge, the Duma's door) have places of their own.
  - *Indoors.* A body is drawn inside a building only where Reed's words put it there ("in the lobby", "in the back rooms", "inside") or where the fighting does (besieged, stormed, taken); a body he sets at a building without saying it is inside stands at its door. Inside, it is a label on the building: no rooms or stairs are drawn, save the meeting-halls of Smolny and the City Duma (below), so the scenes in the Winter Palace's corridors, the Military Revolutionary Committee's rooms or Fontanka 6 show only who stands outside.
  - *Movement off the city.* Moves that leave the detailed city (the front, Moscow, Gatchina) are drawn as a flying pennant on an arc, not as people on the road; a train leaving a station on the map pulls out along the railway and is gone. The Moscow Gate, where the workers "poured" to dig trenches, lies about 3.7 km beyond the drawn city, so that march is an arc and the ground at its end is blank.
  - *The camera.* Each scene's frames are chosen by rules, not by hand. It opens on a frame that keeps the scene's own (its place, the bodies it brings in, Reed, where its moves set out and arrive) in view beside the card, drawing back until the bodies still standing from earlier scenes are in too, then comes in close, 110 to 200 m off, to each place where the scene's own are, and ends close on the first. Up close, a body spread wider than about 90 m (70 m on a phone) is seen in part, and a scene whose people are all indoors ends on the building's walls and labels. The frame depends a little on where the camera came from. The speed control speeds up walks and rides, not fights or close shots, so a scene with a fight lasts as long at 2× as at 1×.
  - *The Faction Map.* Reed's definitions and his words for each person are his, quote-checked. The rest is ours: which side each faction is marked as taking on 7 November is our reading of Reed's account in one word, and "between" covers both the neutral (the Vikzhel) and the divided (the Cossacks); the backgrounds and the lives are our summaries of the Wikipedia articles linked with them, checked against those articles' own summaries for dates and offices, not against the scholarship behind them. The members are Reed's own "representatives in this book" for each party, and the people his narrative puts at the head of each body. People Reed names only in a list, with no life we could check (Martinov, Kramarov, Shatsky), are left out, and so is any portrait that Commons does not mark public domain. A portrait's licence rule is Commons' own templates put into words, not our judgement of who took the photograph and when: four rest on the bare {{PD-US}}, which names no rule, and one (Peshekhonov's) was dropped because its only claim was the uploader's own work.
  - *Crowds.* A figure stands for many people, and the spacing is the map's, not Reed's: "ten thousand black-clothed men and women packed around a scaffolding" are 150 figures 2.5 m apart, so that each can be seen, and far out each is drawn smaller than a lone figure so the crowd does not merge. A crowd therefore covers more ground than its figures would and less than the people Reed describes would, and "packed" and "jammed up" read looser than he wrote them. A body with no formation has no inner order beyond facing what it watches, or, in a debate, its nearest neighbour; the workmen "in trenches" at the Narva Gate stand round their trench, not in it.
  - *Fights as they happen.* Who fights, whom they fire at, who falls and who holds the building after are Reed's; how the fight unfolds is the map's. The way a body comes up (from behind its place, along the open ground), the rushes, the timing, the three envoys at the Vladimir school's door, the size of the party that comes out of it to be "driven back", and the way the beaten side runs off are drawn so that the fight reads as one; Reed gives none of them. Guns are hauled by their crews at a walk and cars drive up at 11 km/h along open ground; Reed says how the guns arrived nowhere. The relief at the Telephone Exchange is drawn as the four who fall: Reed has "several being killed" and does not say how many came. A fight Reed tells as already over ("had been taken") is still acted out in its scene.
  - *The halls.* Smolny's great hall is drawn for the Congress scenes. Reed's are its rows, aisles, window-sills, platform, presidium table, chairman's bell, reading stand and "white chandeliers"; who sits on the platform ("On the platform sat the leaders of the old _Tsay-ee-kah_"), who is packed in the aisles, who walks out and when ("fifty delegates got up and pushed their way out"; "only part of the Mensheviki Internationalists left the Congress"), who comes in ("the entrance of the presidium"), and the hall's response (hooting, cheering, a show of cards). The map's: where the hall is in Smolny, its size and the end its platform is at (outside sources call it the White or Assembly Hall, but none read here gives its place or size); the blocks the factions sit in (Reed says whose benches were whose only at the Peasants' Congress); the split of the Socialist Revolutionaries' seven presidium seats between the Left and the rest; the sizes of the Mensheviki Internationalists and the _Bund_; which aisle a walker takes; and the walking itself. The factions' sizes follow the presidium Reed says was chosen "upon proportionality", and by those proportions more walk out than his "fifty delegates": his two counts disagree, and the map keeps the factions whole rather than choose. The Front group, who also "will leave the Congress", is not drawn: it is not a body in the data. The figures are twice life size, as close in the city, so the hall holds about 135 seats where the Congress had some 650 delegates (an outside count). The other sessions there follow the same rules. Reed's are the bodies and what they do: "the 'moderate' Socialist intellectuals, officers, members of Army Committees, the _Tsay-ee-kah_" "there in force" against "workmen, peasants and common soldiers" on 30 October (four groups, drawn as one body under the old _Tsay-ee-kah_'s name); "soldiers and workmen, a monstrous dun mass" filling the hall on 6 November; the cries of "Lie! Shame!" at Dan; Trotzky leaving the platform on 12 November; the hooting and the applause for Larin's resolution and the vote of 34 to 24 on 17 November (drawn one figure to a vote); the procession coming in, the presidiums embracing, the two banners and the empty frame on 29 November. The map's: who sits where; that a session is drawn for its scene only; the frame's being on the wall from the first of these scenes, though Reed mentions it only at the last; whose the two banners were, and that they hang together once both presidiums are up; the speaker coming in last of those who walk in; and in the press decree's vote, the minority of 24 drawn as Left Socialist Revolutionaries though Reed puts the Bolsheviki Riazanov and Lozovsky among them, all the Bolsheviki drawn hooting though "a part of the Bolsheviki" applauded, and a hall Reed calls "packed" drawn with only its 58 voting members.
  - *The City Duma's halls.* The Alexander Hall and the Nicolai Hall are drawn by the same rules for four scenes. Reed's: "the galleried Alexander Hall, hung with its great, gold-framed, red-shrouded Imperial portraits"; "the high, amphitheatrical Nicolai Hall"; "About a hundred people were grouped around the platform, where Skobeliev was speaking"; the Bolsheviki leaving the chamber "followed by cries of 'German agents! Down with the traitors!'"; "ironic laughter from the Bolshevik benches, and imprecations from the right"; at the Peasants' Congress, the soldiers on the left, "a sprinkling of officers' epaulettes" on the right, "a few peasants, non-commissioned officers, and some soldiers" in the centre, "The galleries were thronged with workers", the old Executive Committee leaving the hall and Zinoviev "hooted down". The map's: where each hall is in the Duma's footprint, its size (32 by 14 m and 30 by 13 m) and the end its platform is at; two blocks of benches, the halls being narrow, the centre's seated first by the centre aisle and each side then filled file by file from its wall in, so that the Left Socialist Revolutionaries ("more than half") spill over the centre aisle; one gallery, on the far long wall, 4.2 m up and 2.2 m deep; two portraits, either side of the platform; a step of 0.45 m from row to row in the Nicolai Hall; the Duma drawn as 30 (as many as its side's benches hold) and the Bolsheviki as 10 there, with no count from Reed, and the Bolsheviki on the left; the Committee and the Peasants' Congress drawn about one figure to six people; that all but the Bolsheviki hoot Zinoviev (Reed: "most of the delegates were hostile"; the scene's `house` says `all`), and that the workers in the gallery take no part. The left is drawn in soldiers' uniforms from Reed's "on the left almost all the delegates wore the uniforms of common soldiers"; the Bolsheviki, the right and the centre in the map's mixes for their factions, with Reed's officers and peasants among them. Not drawn: Reed's own place in the hall. The Bolshevik benches' "ironic laughter" is drawn as a laugh (leaning back, the hands at the belly, a five-second shake); Zinoviev's leaving "amid laughter" is not. Out of Reed's order: the old Executive Committee walks out while Zinoviev is being hooted, where Reed has it leave first ("Whereupon the old Executive Committee left the hall.... Almost immediately"); both are in one scene.
  - *Fontanka 6.* The Imperial Law School's "great meeting-hall" is drawn for the Peasants' Congress's last two sessions there, and Tchernov's earlier exit from the Alexander Hall is a scene of its own. Reed's: Tchernov "interrupted by a great burst of laughter" who "left the platform and the room"; the extraordinary session and the "arrival of a delegation from Smolny, accompanied by representatives of the Red Army, greeted with a rising ovation"; after Tchernov's arrival "On the afternoon of November 25th", the Bolsheviki "on their feet all at once, shaking their fists and yelling" and his "This is an outrage, not a session!" as he "left the hall". The map's: the hall's place in the building's west wing along the Fontanka, its size (32 by 18 m) and its platform at the south end; the delegates drawn as 60, about one figure to six of Reed's "about four hundred", filling the hall from the front, and the delegation as eight, seated in the middle of the front rows; that Tchernov's return was the same day and in the Alexander Hall (Reed says only "Tchernov entered the hall"), and its seating, carried over from the first session; the laughter as the whole hall's but the speaker's party's; an empty tribune in the extraordinary session, whose speakers (Ustinov, Nathanson, Reinstein) are not in the Faction Map. Not drawn: the old Executive Committee's rump convention in another room, the agreement "received by the delegates with the wildest joy", Tchernov's walk in "welcomed with great applause by the majority", Zinoviev's heckling, "some of the Left Socialist Revolutionaries" on their feet with the Bolsheviki (a pose is a whole body's, and `part` is for a walk-out), "the rest of the assembly tried to yell them down", and the Executive Committee he brought back.
  - *The Mariinsky Palace and the Riding School.* The Council of the Republic's "high, cold hall" is drawn for Reed's two visits: on 5 November Karelin reading "The remedy for Bolshevism is bullets!", the Cadets to the right, "the truculent Left", and "the rows of Bolshevik seats--empty", kept empty and labelled; on 6 November Kerensky's last speech, the "Uproar from the Left", and his leaving with "his suite of officers", who follow him out in file. The Riding School is a hall with no benches: Reed's arc-light, the armoured cars round the walls and one in the middle with "a dozen men ... perched on top", Krylenko on its bonnet, the vote by walking "to the left", the "victorious roaring", and the "about fifty men" who "rapidly walked out of the building". The map's: the halls' places, sizes and shapes (Reed does not describe the Council's hall), the numbers (a figure to about six in the Council, the suite as five, to twenty in the Riding School, the "dozen" on the car as six), where the suite stands and that it follows Kerensky in file, the Left as Left Socialist Revolutionaries, the 6 November seating carried over from the 5th, the cars round the walls, "left" as the men on the car saw it, and the order of the crossing. Not drawn: the diplomats in the Council ("All the diplomats present except the Italian ambassador"), Khanjunov and the other Riding School speakers who are not in the Faction Map, and the claque that "went flying".
  - *The Cirque Moderne.* Not drawn inside: its site is not known (the pin is a guess within 300 m and no source found gives it), and a circus drawn there would be the map's invention on an unverified spot. The scene keeps its label.
  - *Told moves.* A move Reed is told of after it is over ("So finally we marched them up to the Finland Station") is drawn as a finished trail with nobody on it, not acted out in the scene.
  - *Vehicles.* Cars, trucks, cabs, trams and armoured cars stop for the people in their way and go on when they have passed or stepped aside; people standing in its lane step out of the way as it comes and back when it has gone by, which Reed describes nowhere; where a car starts among people (Reed's car at Smolny's door) they are inside its outline for the second or two it takes them to step out. A vehicle keeps a lane straight ahead of it, so on a bend it may stop for someone at the roadside; it does not steer round people, only round things in the road (guns, barricades, other vehicles), and it judges those at the size they are drawn close up, so from far off, where everything is drawn larger, a car can seem to brush them. The machine guns wheeled aside at Smolny's door and the sailors' barricade pulled open for the Red Cross car are the map's; Reed says only that "an automobile passed in and out". Held up for more than eight seconds past its walk, it is put at its journey's end (until this was reviewed it never was: it crawled on behind its own route). A crowd that throws itself flat as a vehicle comes lies off the vehicle's way, as Reed has it ("piled in the gutters, heaped up behind telephone-poles").

**What review found.** An independent reviewer checked a sample of 20 events and 20 places against the text and OSM. Every finding was re-read against the text before anything changed, and all but one held up:
- Reed left the palace "through a door opening onto the Neva quay", not across the square.
- The town "held for Kerensky" was a control change with no basis: the Colonel takes it back two sentences later.
- One place misquoted Reed: the "Pulkovo fork" stood on "where the road divided", but Reed's words are "At Pulkovo the road divided".
- Some moves had no support in the text: the yunkers' march to the Grebetskaya corner (the corner was where the Soviet fire came from), the sailors' march on the Morskaya, and Reed walking out to the yunker sortie, which he watched from a window.
- Some witness types were wrong, and one cab ride was recorded as a car.
- The exception: the reviewer would have made the Morskaya `named`. It stays `identified`, because Reed never says which Morskaya.

Checking the findings turned up more: a paraphrase in our own notes printed as a Reed quote ("a day and two nights" on the Moscow train), and the Vladimir school's demolition. All are fixed.

**Following Reed.** After review, the project settled that the map follows Reed authoritatively (§1). The claim checks against other sources were removed from the data and the tooling. That includes the dates they had brought in for the Moscow trip and for Kerensky's departure point.

 The lesson for the next round is that the validator catches what can be checked mechanically (quotes, dates, chains, footprints), not what has been misread.

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
- [IANA tz database, `europe`](https://github.com/eggert/tz/blob/main/europe) (Rule Russia 1917); [tz mailing list, March 2021](https://mm.icann.org/pipermail/tz/2021-March/054958.html).
- To locate places only: [TASS, "History"](https://tass.com/history) (the PTA building on Pochtamtskaya); Russian Wikipedia, [Павловское военное училище](https://ru.wikipedia.org/wiki/Павловское_военное_училище), [Малая Гребецкая улица](https://ru.wikipedia.org/wiki/Малая_Гребецкая_улица) and [Дом Союзов](https://ru.wikipedia.org/wiki/Дом_Союзов); the [Encyclopaedia of St Petersburg, "Красного Курсанта улица"](https://encspb.ru/object/2804017850) (the Pavlovsk school at no. 21 from 1894).
- [Suvorin, *Plan of Petrograd*, 1916](https://commons.wikimedia.org/wiki/File:Plan_Petrograd_Suvorin_1916.jpg) (Wikimedia Commons).
- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL): every pin, footprint and distance.
