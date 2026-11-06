# Plan: the congress and meeting halls, and the walkouts

Status: phases 1 to 4 done (Smolny's great hall: the Second Congress, and the other sessions there, from the Petrograd Soviet of 30 October to the Peasants' Congress coming in on 29 November; the City Duma's Alexander and Nicolai Halls; Fontanka 6); phase 5, optional, not started. Scope, as asked: the scenes of the congresses and meetings, so that the
walkouts can be shown. Not the Winter Palace's rooms, the Military Revolutionary Committee's offices or the
State Bank.

## What is there now

A congress is one body of 14 figures with `inside: true`. It is drawn as a label on the roof of
Smolny, the City Duma or Fontanka 6, and the close camera ends on a wall. The walkouts are in the scene
cards' text only.

## The scenes

| Hall | Scenes in the tour | Walkouts Reed gives |
|---|---|---|
| Smolny, the great meeting-hall | `trotzky-oct30`, `smolny-night-nov6`, `dan-after-midnight`, `bolsheviki-leave-old-cec`, `congress-opens`, `bund-leaves-congress`, `internationalists-leave`, `krylenko-telegram`, `lenin-enters`, `peace-carried`, `land-decree`, `sovnarkom-formed`, `trotzky-report-nov12`, `holtzman-telegram`, `press-decree-night`, `banners-intertwined` (16) | "all the Bolsheviki left the hall" (the old _Tsay-ee-kah_, 6 Nov); the Mensheviki, the Socialist Revolutionaries, the Front group and the _Bund_ ("I call upon all delegates to leave this hall"; "As he went down the aisle in the midst of a deafening noise, people surged in upon him"; "will leave the Congress"); the Mensheviki Internationalists, "in a Whirlwind of Jocular insults", only part of them ("only part of the Mensheviki Internationalists left the Congress") |
| The City Duma: the Alexander Hall and the Nicolai Hall | `salvation-formed`, `peasants-first-session`, `duma-in-permanence`, `schreider-neutral` (4) | the Bolsheviki "left the chamber, followed by cries of 'German agents! Down with the traitors!'" (8 Nov); at the Peasants' Congress, reported, "the old Executive Committee left the hall" |
| Fontanka 6, the Peasants' Congress | `tchernov-leaves`, `peasants-extraordinary-session` (2) | Tchernov "left the platform and the room"; the old Executive Committee "had withdrawn" before the session (its walk-out is the Alexander Hall's). Tchernov's other exit ("'This is an outrage, not a session!' cried Tchernov, and he left the hall") is in the Alexander Hall on 25 November: `tchernov-outrage`, added in phase 4 |
| Optional: the Cirque Moderne, the Mariinsky Palace (the Council of the Republic), the Mikhailovsky Riding School | `cirque-moderne-meeting`, `council-of-republic-nov5`, `kerensky-council-nov6`, `riding-school` (4) | at the Riding School "about fifty men … turned and rapidly walked out of the building" |

## What Reed gives, and what he does not

- **The halls.** Smolny: "the great meeting-hall", "the rows of seats, under the white chandeliers, packed
  immovably in the aisles and on the sides, perched on every window-sill, and even the edge of the
  platform"; the platform, the presidium table, the tribune, the press table; "the white wall … the empty
  frame from which the Tsar's picture had been torn"; "a foul blue cloud of cigarette smoke"; "no heat in
  the hall". The Duma: "the galleried Alexander Hall, hung with its great, gold-framed, red-shrouded Imperial
  portraits"; "About a hundred people were grouped around the platform". The Cirque Moderne: "the bare,
  gloomy amphitheatre, lit by five tiny lights hanging from a thin wire, … packed from the ring up the steep
  sweep of grimy benches".
- **Where the factions sat.** Only at the Peasants' Congress: "the Bolshevik benches", "the right
  benches … but the centre and left". At the City Duma: "all benches except those of the Bolsheviki".
- **How many.** The presidium of the Second Congress: "14 Bolsheviki, 7 Socialist Revolutionaries, 3
  Mensheviki and 1 Internationalist". The Peasants' Congress: "about four hundred". No count of the Second
  Congress's delegates by party.
- **Not in Reed.** The size and shape of each hall, and where in the building it is. Smolny's footprint on
  the map is the whole complex, 281 × 629 m. Under the project's rule, outside sources may fill this gap and
  are marked as such: Smolny's great hall survives, and public-domain photographs and plans of it exist.

## The work

### 1. Data and checker

- **A hall** on a room place (`smolny-hall`, `duma-alexander-hall`, `duma-nicolai-hall`, `fontanka-6-hall`;
  new rooms for the optional halls): its plan (rows facing a platform; an amphitheatre; a chamber with a
  gallery), where it sits in its building and its size, each from Reed's words or, failing them, an outside
  source with its quote (`outside: {source, q}`). Features only where Reed names them: chandeliers,
  columns, gallery, portraits, the torn frame, the banners.
- **The congress by faction.** In place of one `congress` body, a body per faction in the hall (Bolsheviki,
  Left SRs, SRs, Mensheviki, Mensheviki Internationalists, the _Bund_, the Front group, the old _Tsay-ee-kah_
  on the platform). Each has a `seat`: `left | centre | right | platform | press | aisles | sills`. A seat
  is Reed's where he says ("on the platform sat the leaders of the old _Tsay-ee-kah_"; "the Bolshevik
  benches"); elsewhere it is ours and the card says so. Sizes as with the crowds: a figure stands for
  several delegates, in proportions marked as ours, since Reed gives none.
- **The speaker:** `speaker` on a scene, a person from the Faction Map (Dan ringing the bell, Trotzky,
  Lenin, Krylenko with the telegram, Abramovitch for the _Bund_, Tchernov), only where Reed puts that person
  at the tribune or on the platform in the scene.
- **The walkout:** a move with `walkout: true` from a hall body's seats out of the hall's door. It needs
  Reed's words ("left the hall", "leave the Congress", "walked out", "left the platform and the room"), and
  `part` where he says only some went. The body is gone from the hall after it.
- **The hall's response, as poses tied to Reed's words:** standing ("a rising house", "the great crowd rose
  to him", "a rising ovation"); fists ("shaking their fists and yelling"); laughter or jeers ("a Whirlwind
  of Jocular insults", "a great burst of laughter"); the aisle closing on the one leaving ("people surged in
  upon him").

### 2. Drawing

- **The hall opened up.** Reed's buildings already have meshes of their own, so in a hall scene that
  building's roof is lifted off and its walls lowered round the hall, without touching the rest of the city.
  Inside: the floor, rows of benches, aisles, the platform with the presidium table and the tribune,
  windows, and the features the hall record names. Drawn from parts, like the guns and the barricades.
- **New figure poses** in `src/people.js`: seated on a bench, standing, a fist raised, an arm out at the
  tribune.
- **The walkout.** The faction's delegates rise row by row, file into the nearest aisle and out by the door,
  while the rest of the hall jeers or laughs as Reed has it. Where he says the aisle closed on a man
  leaving, it does.
- **Light.** At night the chandeliers, and the smoke over the rows where Reed gives it.
- **The card** names the speaker and the faction leaving, linked to the Faction Map.

### 3. Camera

In a hall scene the camera looks down into the opened hall over the rows to the platform. For a walkout it
follows the faction down the aisle to the door, then comes back to the tribune. The city frame opens the
scene briefly, as now.

### 4. Checks

- Checker and unit tests for each new field, each tied to Reed's words as the fight fields are.
- An audit: every delegate on a bench or standing where `seat` allows; walkers keep to the aisles (not
  through benches or people) and leave by the door; the speaker and the walkers on screen in the hall shots.
- One independent review per phase, as for the fights.

## Phases

1. **Smolny's great hall and the Second Congress:** `congress-opens`, `bund-leaves-congress`,
   `internationalists-leave`, `lenin-enters`, `peace-carried`, `land-decree`, `sovnarkom-formed`, and the
   Bolsheviki's walkout from the old _Tsay-ee-kah_ (`bolsheviki-leave-old-cec`). Most of the value, and every
   part of the machinery: hall, factions, speaker, walkout, poses, camera.
2. The other Smolny scenes: `trotzky-oct30`, `smolny-night-nov6`, `dan-after-midnight`, `krylenko-telegram`,
   `trotzky-report-nov12`, `holtzman-telegram`, `press-decree-night`, and `banners-intertwined` with the
   Peasants' procession coming in and the two presidiums embracing.
3. The City Duma's two halls.
4. Fontanka 6: the Peasants' Congress, the old Executive Committee and Tchernov leaving.
5. Optional: the Cirque Moderne (it needs a mesh of its own), the Mariinsky Palace, the Riding School.

## Left from phase 1

- The press table Reed sat at ("as we sat at the press table in the big hall"): not drawn, so `press` is not a bench yet.
- The Front group's walk-out ("The Front group will leave the Congress"), and Kutchin going "down the aisle in the midst of a deafening noise, people surged in upon him": the Front group is not a body in the data, and a single man walking out is not drawn.
- The "foul blue cloud of cigarette smoke" over the rows.
- land-decree: Reed's joy is "the peasant delegates'", but the house's cheering is drawn on the whole side of the rising.
- The chairman's place: Dan "ringing the bell" and Kameniev "reading" stand at the reading stand; the map has no separate place for the chair.
- A walk-in to the benches is used by the Peasants' Congress coming in; a body walking out from the platform is drawn but no scene uses it yet.
- Phase 2: Gotz "took the chair" and Sverdlov greeted the peasants, but there is one speaker per scene and no chairman, so neither is drawn; nor is Holtzman running down the corridor with the telegram (he is not in the Faction Map), nor the music that "blared down the corridor", nor Larin, whose resolution the press-decree scene's hooting and applause answer (he is not in the Faction Map either, so the scene has no speaker). Which two banners crossed on the wall Reed does not say; the map gives one to each presidium.

## Left from phase 4

- At Fontanka 6 nobody stands at the tribune in the extraordinary session: Ustinov, Nathanson and Reinstein, who speak, are not in the Faction Map. Sverdlov, who is, "greeted them" only at the end.
- The old Executive Committee's "rump convention ... in another room of the same building", where Tchernov first spoke, is not drawn; nor is the agreement Ustinov announced "received by the delegates with the wildest joy" before Tchernov came in.
- Tchernov's return to the Alexander Hall (25 Nov): his walk in, "welcomed with great applause by the majority", and Zinoviev's heckling are not drawn, only the uproar and his leaving; nor is the Executive Committee he brought back (the checker does not take "the Executive Committee" alone for its name).
- The laughter is a pose with a five-second shake: from far off it reads less than a raised fist.

## Left from phase 3

- The Peasants' Congress's first session: the old Executive Committee walks out while Zinoviev is hooted, where Reed has it leave first; one scene holds both. Zinoviev leaving the platform "amid laughter" is drawn, the laughter not.
- Where the Bolsheviki sat at the Duma, and the Duma's numbers: Reed gives "the Bolshevik benches" and "the right" only; the sides and the counts (30 and 10) are the map's.
- Layout seeds still follow the presence order, so adding records reshuffles unrelated scenes (the audit numbers move with them).

## Decisions taken

- **The hall's shape.** No outside source read gives where the great hall is in Smolny or its size (Russian Wikipedia names it the White or Assembly Hall; the rest came only from search summaries, not read). So the hall is schematic, 40 by 18 m in the main block south of the entrance, platform to the south, and marked as the map's in its record and on the card.
- **Seating.** Faction blocks, for the rising on the chair's left and against on its right, marked as the map's. Sizes from Reed's presidium "upon proportionality", four figures to a seat.
- **The hall's response** is the scene's (`house`), not a body's: Reed rarely names a faction beside the hooting or the cheering.

## Decisions before starting

- **The shape of a hall where Reed is silent.** Recommended: take it from outside sources (photographs and
  plans of the surviving Smolny hall; the Duma building's plans), marked as such. The alternative is a
  schematic hall sized to fit the building, clearly not the real room.
- **Seating where Reed does not say.** Recommended: faction blocks, those for the rising on the left and
  those against on the right, marked as the map's. The alternative is mixed seating, with factions told
  apart by colour only.
