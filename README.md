# ten-days-that-shook-the-world

A future 3D map of John Reed's *Ten Days That Shook the World* (1919): Reed's own path through Petrograd in October–December 1917, the factions, who held which building when, and the movements he reports. It is the sister project of [Raskolnikov Wandering](https://github.com/mauladhanifadhilsalam/raskolnikov-wandering).

**Status: data first, no 3D yet.** This repo holds:
- the assessment of whether, and how, the Raskolnikov treatment fits Reed: [docs/assessment.md](docs/assessment.md);
- a checked seed dataset;
- the tools that check it.

The rendering comes next, once the data has been reviewed.

## What is here

```
docs/assessment.md     the critical assessment: verdict, what the book gives, Reed as a source, the plan
docs/schema.md         field reference for the data files
data/meta.json         text and PDF pins, calendar rule, clock, map zones, move speeds, timeline days
data/sources.json      the sources actually consulted
data/actors.json       64 factions, bodies, units, people and crowds, with stance over time
data/places.json       75 places in the city, at the front, off-map, and in Moscow (text only)
data/events.json       138 scenes: time and its quality, verbatim quote, witness type, moves, control changes, claim checks
tools/text.py          downloads Gutenberg #3076 and splits it into sections (pinned by SHA-256)
tools/check_story.py   the validator; fails hard. --report, --osm, --pdf
tools/fmt_story.py     writes the canonical layout; --check, --pages
tools/geocode.py       finds OSM buildings around a hint (OSM API only), --accept writes them
tools/storylib.py      shared schema, layout, quote normalisation, date and time parsers, geometry, sun
tests/test_check.py    one failing fixture per error code, plus mutation tests on the real data
```

## What the data asserts, and how far to trust it

Every scene quotes Reed verbatim, and the validator proves each quote occurs exactly once in the named section of Gutenberg #3076. Each scene also says:

- **how Reed knows it** (`witness`):
  - `seen`: he was there;
  - `told`: an informant, named in `by`;
  - `reported`: news, rumour, or his own compiled chronology;
  - `document`: something he prints.
- **how its time is known** (`tq`): stated, on a document, a part-of-day phrase, the day only, inferred with a reason, or from another source. Times carry bounds (`tr`). Reed gives about sixty clock times in 121,000 words, so most times are estimates and are labelled as such.
- **which calendar its dates use** (`cal`). Reed keeps to New Style, but the documents he prints sometimes use Old Style, and the validator catches the difference (weekdays included).
- **where Reed contradicts himself or the record** (`check`), quoting both passages. Verdicts other than `unchecked` cite a source that was actually read. Three of them rest on reference works (Russian Wikipedia, the Encyclopaedia of St Petersburg) and are marked as such in `data/sources.json`.

Places carry three separate things:
- the identification (`conf`: named, identified, conjectural or unlocated, with the reasoning in `ident` and any source read for it in `src`);
- where the pin came from (`geo`);
- how precise it is (`acc`, metres).

A surviving building is tied to its OSM element, and `check_story.py --osm` tests that the pin lies inside the footprint.

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

The measurement tables (speeds, Reed's daily distances, sun against "dusk" and "twilight", every weekday–date pair, control timelines, claims):

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
- Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). The coordinates and element ids in `data/places.json` are derived from OSM and are available under the [Open Database License](https://opendatacommons.org/licenses/odbl/).
- The other sources consulted are listed in `data/sources.json` and cited in the assessment.
