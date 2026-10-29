"""Check the Ten Days data against its schema, Reed's text, the calendar, the map and itself.

The data follows Reed authoritatively: every event, time, move and change of control comes from his
text. Outside sources only locate his places and set the 1917 clock, so nothing here checks Reed
against other accounts; it checks that the data says what Reed says.

usage: python3 -I tools/check_story.py [--data data] [--text cache/sections.json] [--report] [--strict]
                                       [--osm] [--cache cache] [--pdf PDF] [--only CODE[,CODE…]]

Unlike the Raskolnikov build, this fails: every finding below ERROR level makes the exit status 1.
  0  no errors (warnings allowed; with --strict, warnings count as errors)
  1  data errors
  2  environment problem: no sections.json (run tools/text.py cache), the text's hash differs from
     meta.text.body_sha256, a network failure under --osm, or no PDF reader under --pdf

--report prints the measurements (speeds, sun, weekday/date pairs, Reed's walks, coverage, control
timelines) as Markdown. --osm fetches every OSM element named in places.json from the OSM API (one request a
second, cached in CACHE/osm) and checks the pin against its footprint. --pdf checks the convenience
page numbers `p` against the marxists.org PDF.
"""
import sys, os, re, json, time, hashlib, argparse, urllib.request, urllib.error, datetime as dt
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib as L

UA = 'ten-days-that-shook-the-world/0.1 (+https://github.com/altf4m88/ten-days-that-shook-the-world)'
OSM_API = 'https://api.openstreetmap.org/api/0.6'


class EnvError(Exception):
    pass


class Findings:
    def __init__(self):
        self.items = []

    def err(self, code, where, msg):
        self.items.append(('ERROR', code, where, msg))

    def warn(self, code, where, msg):
        self.items.append(('WARN', code, where, msg))

    def info(self, code, where, msg):
        self.items.append(('INFO', code, where, msg))

    def codes(self, level='ERROR'):
        return [c for lv, c, _, _ in self.items if lv == level]


# ---------- field types ----------
STR, INT, BOOL, LIST, DICT, NUM = str, int, bool, list, dict, (int, float)
TYPES = {
    'title': STR, 'note': STR, 'id': STR, 'kind': STR, 'url': STR, 'cite': STR, 'bloc': STR, 'track': BOOL,
    'part_of': STR, 'seat': STR, 'wd': STR, 'name': STR, 'reed': LIST, 'ru': STR, 'stance': LIST,
    'from': STR, 's': STR, 'ev': STR, 'src': LIST, 'ref': DICT, 'zone': STR, 'in': STR, 'acc': INT,
    'conf': STR, 'osm': STR, 'site_osm': STR, 'geo': DICT, 'ctl0': DICT, 'addr1917': STR, 'addr_now': STR,
    'ident': STR, 'today': STR, 'm': STR, 'at': STR, 'osm_v': INT, 'on': STR, 'state': STR, 'holder': STR,
    'by': STR, 'as_of': STR, 't': STR, 'tq': STR, 'tr': LIST, 'tp': STR, 'cal': STR, 'dp': STR, 'sec': STR,
    'p': INT, 'loc': STR, 'witness': STR, 'tags': LIST, 'why': STR, 'sum': STR, 'also': LIST, 'doc': DICT,
    'moves': LIST, 'ctl': LIST, 'who': STR, 'with': LIST, 'size': STR, 'via': LIST, 'to': STR,
    'mode': STR, 'rc': STR, 't0': STR, 'gap': BOOL, 'ack': STR, 'place': STR,
    'd': STR, 'os': STR, 'label': STR, 'actors': LIST, 'city': STR,
    'present': LIST, 'gone': LIST, 'n': INT, 'kit': LIST, 'brief': BOOL, 'stay': BOOL, 'say': LIST, 'form': STR, 'march': BOOL, 'fire': (BOOL, STR), 'at': STR, 'pose': STR, 'run': BOOL, 'assault': STR, 'patrol': BOOL, 'face': STR, 'inside': BOOL,
    'file': STR, 'w': INT, 'h': INT, 'scenes': LIST, 'license': STR, 'author': STR, 'date': STR, 'page': INT, 'caption': STR,
}


def typed(rec, k):
    """rec[k] has the type TYPES gives the field"""
    want = TYPES.get(k)
    return want is None or isinstance(rec.get(k), want)


def fields(F, rec, kind, where):
    if not isinstance(rec, dict):
        F.err('field.type', where, f'expected an object, got {type(rec).__name__}')
        return False
    for k in rec:
        if k not in L.FIELDS[kind]:
            F.err('field.unknown', where, f'unknown field {k!r}')
    for k in L.REQUIRED.get(kind, []):
        if k not in rec:
            F.err('field.missing', where, f'missing {k!r}')
    for k, v in rec.items():
        want = TYPES.get(k)
        if k == 'q' and kind == 'event':
            ok = isinstance(v, str) or (isinstance(v, list) and v and all(isinstance(x, str) for x in v))
        elif k == 'q':
            ok = isinstance(v, str)
        elif k in ('ll', 'stage'):
            ok = (v is None and k == 'll') or (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v))
        elif k == 'exists':
            ok = v is None or isinstance(v, bool)
        elif want is INT:
            ok = isinstance(v, int) and not isinstance(v, bool)
        elif want is None:
            continue
        else:
            ok = isinstance(v, want)
        if not ok:
            F.err('field.type', where, f'{k!r} has the wrong type ({type(v).__name__})')
        elif k in L.LIMITS:
            for seg in (v if isinstance(v, list) else [v]):
                if isinstance(seg, str) and len(seg) > L.LIMITS[k]:
                    F.err('field.length', where, f'{k!r} is {len(seg)} characters, limit {L.LIMITS[k]}')
    return True


def enum(F, rec, key, ename, where):
    if key in rec and isinstance(rec[key], str) and rec[key] not in L.ENUM[ename]:
        F.err('field.enum', where, f'{key}={rec[key]!r} is not one of {sorted(L.ENUM[ename])}')


def tparse(s):
    try:
        if L.T_RE.match(s):
            return L.parse_t(s)
        if L.D_RE.match(s):
            return dt.datetime.strptime(s, '%Y-%m-%d')
    except ValueError:
        pass
    return None


# ---------- the checker ----------
class Checker:
    def __init__(self, data_dir, book, F):
        self.dir, self.book, self.F = data_dir, book, F
        self.meta = self.days = None
        self.sources, self.actors, self.places, self.events, self.pictures = [], [], [], [], []

    # -- loading --
    def load(self):
        F, ok = self.F, True
        raw = {}
        for name in ['meta'] + L.TABLES + L.OPTIONAL:
            path = os.path.join(self.dir, name + '.json')
            where = f'{name}.json'
            if not os.path.exists(path):
                if name in L.OPTIONAL:
                    raw[name] = []
                    continue
                F.err('file.missing', where, 'file not found')
                ok = False
                continue
            try:
                raw[name] = L.load_json(path)
            except L.DuplicateKey as e:
                F.err('json.duplicate-key', where, f'duplicate key {e}')
                ok = False
                continue
            except json.JSONDecodeError as e:
                F.err('json.syntax', where, str(e))
                ok = False
                continue
            obj = raw[name]
            if name == 'meta':
                if not isinstance(obj, dict) or 'meta' not in obj:
                    F.err('field.type', where, 'expected {"meta": …, "days": […]}')
                    ok = False
                    continue
            elif not isinstance(obj, list):
                F.err('field.type', where, 'expected a list of records')
                ok = False
                continue
            text = L.read_text(path)
            want = L.canonical(name, obj if name == 'meta' else L.sort_table(name, obj))
            if text != want:
                a, b = text.split('\n'), want.split('\n')
                n = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                F.err('fmt.layout', where, f'not in canonical layout or order from line {n + 1}; run tools/fmt_story.py')
        if not ok:
            return False
        m = raw['meta']
        for k in m:
            if k not in ('meta', 'days'):
                F.err('field.unknown', 'meta.json', f'unknown top-level key {k!r}')
        self.meta, self.days = m['meta'], m.get('days', [])
        self.sources, self.actors, self.places, self.events = (raw[n] for n in L.TABLES)
        self.pictures = raw.get('pictures', [])
        return True

    # -- helpers --
    def quote_ok(self, sec, q, where, what='q'):
        """Each segment must occur exactly once in the section, in order, close together."""
        F = self.F
        if sec not in self.book.secs:
            F.err('text.section-unknown', where, f'no section {sec!r}')
            return None
        last, first = None, None
        for i, seg in enumerate(L.segments(q)):
            hits = self.book.find(sec, seg)
            tag = f'{what}[{i}]' if isinstance(q, list) else what
            if not hits:
                F.err('quote.not-found', where, f'{tag} not in {sec}: "{seg[:70]}"')
                return None
            if len(hits) > 1:
                F.err('quote.not-unique', where, f'{tag} occurs {len(hits)} times in {sec}; quote more of it')
                return None
            pos = hits[0]
            if last is not None and (pos < last or pos - last > 600 + 320):
                F.err('quote.order', where, f'{tag} is out of order or more than 600 characters after the previous segment')
            last = pos + len(L.norm(seg))
            first = pos if first is None else first
        return first

    def ids(self, recs, table):
        F, seen = self.F, set()
        for r in recs:
            i = r.get('id') if isinstance(r, dict) else None
            if not isinstance(i, str):
                continue
            if not L.ID_RE.match(i):
                F.err('field.pattern', f'{table}/{i}', 'ids are lower-case slugs: a-z, 0-9, single hyphens')
            if i in seen:
                F.err('id.duplicate', f'{table}/{i}', 'duplicate id')
            seen.add(i)
        return seen

    def spelled(self, names, where):
        for n in names:
            if not isinstance(n, str) or not n:
                self.F.err('field.type', where, 'reed[] holds non-empty strings')
            elif L.norm(n) not in self.book.all:
                self.F.err('spelling.not-in-book', where, f'Reed never writes {n!r}')

    def in_range(self, s, where, what):
        t = tparse(s) if isinstance(s, str) else None
        if t is None:
            self.F.err('time.format', where, f'{what}={s!r} is not YYYY-MM-DDTHH:MM (or YYYY-MM-DD)')
            return None
        lo = dt.datetime.strptime(self.meta['range'][0], '%Y-%m-%d')
        hi = dt.datetime.strptime(self.meta['range'][1], '%Y-%m-%d') + dt.timedelta(hours=23, minutes=59)
        if not lo <= t <= hi:
            self.F.err('time.range', where, f'{what}={s} is outside {self.meta["range"]}')
        return t

    def evidence(self, rec, where):
        """stance and ctl0 entries must point at Reed: an event, or a passage of his."""
        F = self.F
        if not any(k in rec for k in ('ev', 'ref')):
            F.err('evidence.missing', where, 'needs ev or ref')
        if 'ev' in rec and rec['ev'] not in self.E:
            F.err('ref.unknown', where, f'no event {rec["ev"]!r}')
        if 'ref' in rec and isinstance(rec['ref'], dict):
            if fields(F, rec['ref'], 'ref', where + '.ref'):
                if isinstance(rec['ref'].get('sec'), str) and isinstance(rec['ref'].get('q'), str):
                    self.quote_ok(rec['ref']['sec'], rec['ref']['q'], where + '.ref')

    def related(self, a, b):
        """Same place, or one contains the other (through `in`)."""
        def chain(x):
            out, seen = [], set()
            while x and x not in seen:
                seen.add(x)
                out.append(x)
                x = self.P.get(x, {}).get('in')
            return out
        return a in chain(b) or b in chain(a)

    # -- the checks --
    def run(self):
        if not self.load():
            return
        F, meta = self.F, self.meta
        # meta
        for k in meta:
            if k not in L.FIELDS['meta']:
                F.err('field.unknown', 'meta.json', f'unknown meta field {k!r}')
        for k in ('text', 'calendar', 'clock', 'range', 'zones', 'speed_kmh', 'blocs'):
            if k not in meta:
                F.err('field.missing', 'meta.json', f'missing meta.{k}')
        if F.codes():
            return
        if meta['text'].get('body_sha256') != self.book.sha256:
            raise EnvError(f'sections.json was built from a text with SHA-256 {self.book.sha256}, '
                           f'but meta.text.body_sha256 is {meta["text"].get("body_sha256")}')
        if isinstance(meta['calendar'].get('ref'), dict):
            self.quote_ok(meta['calendar']['ref'].get('sec'), meta['calendar']['ref'].get('q', ''), 'meta.calendar.ref')
        for i, d in enumerate(self.days):
            w = f'meta.days[{i}]'
            if fields(F, d, 'day', w):
                a, b = (tparse(d.get(x, '')) for x in ('d', 'os'))
                if a is None or b is None or not L.D_RE.match(d.get('d', '')) or not L.D_RE.match(d.get('os', '')):
                    F.err('time.format', w, 'd and os are YYYY-MM-DD')
                elif a - b != dt.timedelta(days=13):
                    F.err('days.os', w, f'os should be {(a - dt.timedelta(days=13)).date()} (New Style minus 13 days)')
        self.zones = meta['zones']

        self.S = self.ids(self.sources, 'sources')
        self.A = {a['id']: a for a in self.actors if isinstance(a, dict) and 'id' in a}
        self.ids(self.actors, 'actors')
        self.P = {p['id']: p for p in self.places if isinstance(p, dict) and 'id' in p}
        self.ids(self.places, 'places')
        self.E = {e['id']: e for e in self.events if isinstance(e, dict) and 'id' in e}
        self.ids(self.events, 'events')
        used = {'source': Counter(), 'actor': Counter(), 'place': Counter()}
        self.used = used
        for k, c in meta['clock'].items():
            if not isinstance(c, dict) or not isinstance(c.get('offset_min'), (int, float)):
                F.err('field.type', f'meta.clock.{k}', 'each clock is {"offset_min": minutes east of UTC, …}')
                continue
            for s in c.get('src', []):
                if s not in self.S:
                    F.err('ref.unknown', f'meta.clock.{k}', f'no source {s!r}')
                used['source'][s] += 1
        if 'petrograd' not in meta['clock']:
            F.err('field.missing', 'meta.clock', 'needs a petrograd clock')

        for s in self.sources:
            w = f'sources/{s.get("id")}'
            if fields(F, s, 'source', w):
                enum(F, s, 'kind', 'source.kind', w)

        for a in self.actors:
            w = f'actors/{a.get("id")}'
            if not fields(F, a, 'actor', w):
                continue
            enum(F, a, 'kind', 'actor.kind', w)
            enum(F, a, 'bloc', 'actor.bloc', w)
            self.spelled(a.get('reed', []), w)
            if not a.get('reed'):
                F.err('field.missing', w, 'reed[] needs at least one spelling from the book')
            if 'part_of' in a:
                if a['part_of'] not in self.A:
                    F.err('ref.unknown', w, f'no actor {a["part_of"]!r}')
                used['actor'][a['part_of']] += 1
            if 'seat' in a:
                if a['seat'] not in self.P:
                    F.err('ref.unknown', w, f'no place {a["seat"]!r}')
                used['place'][a['seat']] += 1
            if 'wd' in a and not L.WD_RE.match(a['wd']):
                F.err('field.pattern', w, 'wd is a Wikidata id like Q123')
            last = None
            for i, st in enumerate(a.get('stance', [])):
                sw = f'{w}.stance[{i}]'
                if not fields(F, st, 'stance', sw):
                    continue
                enum(F, st, 's', 'stance.s', sw)
                t = self.in_range(st.get('from', ''), sw, 'from')
                if t and last and t < last:
                    F.err('stance.order', sw, 'stance entries must be in time order')
                last = t or last
                self.evidence(st, sw)

        for p in self.places:
            w = f'places/{p.get("id")}'
            if not fields(F, p, 'place', w):
                continue
            for k, e in (('kind', 'place.kind'), ('zone', 'place.zone'), ('conf', 'place.conf')):
                enum(F, p, k, e, w)
            self.spelled(p.get('reed', []), w)
            if not p.get('reed'):
                F.err('field.missing', w, 'reed[] needs at least one spelling or phrase from the book')
            ll = p.get('ll')
            if p.get('conf') == 'unlocated':
                if ll is not None:
                    F.err('geo.ll-forbidden', w, 'an unlocated place has ll: null')
            elif ll is None:
                F.err('geo.ll-required', w, 'needs ll (only conf "unlocated" may have ll: null)')
            else:
                if any(len(repr(float(x)).split('.')[-1]) > 6 for x in ll):
                    F.err('geo.precision', w, 'coordinates take at most 6 decimals')
                z = self.zones.get(p.get('zone'))
                if z and not (z[0] <= ll[0] <= z[2] and z[1] <= ll[1] <= z[3]):
                    F.err('geo.zone', w, f'{ll} is outside the {p.get("zone")} box {z}')
                if 'acc' not in p:
                    F.err('field.missing', w, 'a located place needs acc (metres)')
                elif p.get('conf') == 'conjectural' and p['acc'] < 50:
                    F.warn('geo.acc-small', w, f'conjectural pin with acc {p["acc"]} m; is it really that precise?')
            if 'stage' in p and isinstance(p['stage'], list) and len(p['stage']) == 2:
                if not ll:
                    F.err('geo.stage', w, 'stage (where its figures stand) needs a located place')
                elif L.dist_m(ll, p['stage']) > 400:
                    F.err('geo.stage', w, f'stage is {L.dist_m(ll, p["stage"]):.0f} m from the pin; keep it within 400 m')
                if any(len(repr(float(x)).split('.')[-1]) > 6 for x in p['stage']):
                    F.err('geo.precision', w, 'stage takes at most 6 decimals')
            if p.get('conf') in ('identified', 'conjectural') and not p.get('ident'):
                F.err('field.missing', w, f'conf {p["conf"]!r} needs ident (how the place was identified)')
            if 'in' in p:
                par = self.P.get(p['in'])
                if par is None:
                    F.err('ref.unknown', w, f'no place {p["in"]!r}')
                else:
                    used['place'][p['in']] += 1
                    if ll and par.get('ll') and L.dist_m(ll, par['ll']) > 400:
                        F.err('geo.parent-distance', w, f'{L.dist_m(ll, par["ll"]):.0f} m from its parent {p["in"]}')
            ex = p.get('exists')
            for k in ('osm', 'site_osm'):
                if k in p and not L.OSM_RE.match(p[k]):
                    F.err('field.pattern', w, f'{k} is like way/123')
            if p.get('kind') in ('building', 'station', 'complex') and ex is True and 'osm' not in p:
                F.err('geo.osm-required', w, f'a surviving {p["kind"]} needs its OSM element in osm')
            if ex is False and 'osm' in p:
                F.err('geo.osm-forbidden', w, 'exists:false: put what stands on the site now in site_osm, not osm')
            if ex is True and 'site_osm' in p:
                F.err('geo.osm-forbidden', w, 'exists:true: use osm, not site_osm')
            if 'wd' in p and not L.WD_RE.match(p['wd']):
                F.err('field.pattern', w, 'wd is a Wikidata id like Q123')
            for s in p.get('src', []):   # sources for the identification, the 1917 address, survival
                if s not in self.S:
                    F.err('ref.unknown', w, f'no source {s!r}')
                used['source'][s] += 1
            g = p.get('geo')
            if isinstance(g, dict) and fields(F, g, 'geo', w + '.geo'):
                enum(F, g, 'm', 'geo.m', w + '.geo')
                if g.get('m') == 'osm':   # an OSM-derived pin cites the OSM source
                    if 'osm' not in self.S:
                        F.err('ref.unknown', w + '.geo', 'geo.m "osm" needs the source "osm" in sources.json')
                    used['source']['osm'] += 1
                if g.get('m') == 'pending':
                    F.err('geo.pending', w, 'coordinates still pending; run tools/geocode.py')
                for s in g.get('src', []):
                    if s not in self.S:
                        F.err('ref.unknown', w + '.geo', f'no source {s!r}')
                    used['source'][s] += 1
            c0 = p.get('ctl0')
            if isinstance(c0, dict) and fields(F, c0, 'ctl0', w + '.ctl0'):
                self.control_state(c0, w + '.ctl0')
                if p.get('kind') not in L.HOLDABLE:
                    F.err('ctl.kind', w, f'a {p.get("kind")} cannot be held')
                self.in_range(c0.get('as_of', ''), w + '.ctl0', 'as_of')
                self.evidence(c0, w + '.ctl0')
        self.cycles()

        tags = set(meta.get('tags', []))
        for e in self.events:
            self.event(e, tags)
        self.tracks()
        self.control()
        self.presence()
        self.ids(self.pictures, 'pictures')
        for pic in self.pictures:
            self.picture(pic)
        for k, table in (('source', self.S), ('actor', self.A), ('place', self.P)):
            for i in table:
                if not used[k][i]:
                    F.warn(f'unused.{k}', f'{k}s/{i}', 'never referenced')

    def cycles(self):
        for pid in self.P:
            seen, x = set(), pid
            while x in self.P and 'in' in self.P[x]:
                if x in seen:
                    self.F.err('ref.cycle', f'places/{pid}', 'its `in` chain loops')
                    break
                seen.add(x)
                x = self.P[x]['in']

    def control_state(self, c, where):
        F = self.F
        enum(F, c, 'state', 'state', where)
        st = c.get('state')
        for k in ('holder', 'by'):
            if k in c:
                if c[k] not in self.A:
                    F.err('ref.unknown', where, f'no actor {c[k]!r}')
                self.used['actor'][c[k]] += 1
        if st in ('held', 'besieged') and 'holder' not in c:
            F.err('ctl.state', where, f'state {st!r} needs a holder')
        if st == 'besieged' and 'by' not in c:
            F.err('ctl.state', where, 'besieged needs by (the besieger)')
        if st in ('contested', 'unknown') and 'holder' in c:
            F.err('ctl.state', where, f'state {st!r} has no holder')
        if st != 'besieged' and 'by' in c:
            F.err('ctl.state', where, 'only besieged takes by')

    def event(self, e, tags):
        F = self.F
        w = f'events/{e.get("id")}'
        if not fields(F, e, 'event', w):
            return
        used = self.used
        for k, en in (('tq', 'event.tq'), ('cal', 'cal'), ('witness', 'event.witness')):
            enum(F, e, k, en, w)
        t = self.in_range(e.get('t', ''), w, 't')
        tq = e.get('tq')
        tr = e.get('tr')
        if tr is not None:
            if len(tr) != 2:
                F.err('field.type', w, 'tr is [earliest, latest]')
            else:
                a, b = (self.in_range(x, w, 'tr') for x in tr)
                if a and b and t and not a <= t <= b:
                    F.err('time.bounds', w, f't {e["t"]} is outside tr {tr}')
        elif tq not in ('stated', 'doc'):
            F.err('field.missing', w, f'tq {tq!r} needs tr (earliest and latest)')
        if tq in ('stated', 'doc', 'approx') and 'tp' not in e:
            F.err('field.missing', w, f'tq {tq!r} needs tp, the time phrase as Reed writes it')
        if tq == 'inferred' and 'why' not in e:
            F.err('field.missing', w, 'tq "inferred" needs why')
        if t and tq in ('stated', 'doc') and 'tp' in e:
            c = L.parse_tp(e['tp'])
            if not c:
                F.err('time.tp-unparsed', w, f'no clock time in tp {e["tp"]!r}')
            elif (t.hour, t.minute) not in c:
                F.err('time.tp-mismatch', w, f'tp {e["tp"]!r} means {sorted(c)}, but t is {e["t"]}')
        if t and 'dp' in e:
            self.date_phrase(e['dp'], e.get('cal'), t, w)
        for g in e.get('tags', []):
            if g not in tags:
                F.err('field.enum', w, f'tag {g!r} is not in meta.tags')
        if e.get('loc') not in self.P:
            F.err('ref.unknown', w, f'no place {e.get("loc")!r}')
        used['place'][e.get('loc')] += 1
        for a in e.get('actors', []):
            if a not in self.A:
                F.err('ref.unknown', w, f'actors: no actor {a!r}')
            used['actor'][a] += 1
        if 'by' in e:
            if e.get('witness') != 'told':
                F.err('field.enum', w, 'by (the informant) goes with witness "told"')
            if e['by'] not in self.A:
                F.err('ref.unknown', w, f'no actor {e["by"]!r}')
            used['actor'][e['by']] += 1

        # the text
        pos = None
        if 'sec' in e and 'q' in e:   # both required: an event that is not in Reed has no place here
            pos = self.quote_ok(e['sec'], e['q'], w)
        if pos is not None:
            for k in ('tp', 'dp'):
                if k in e and not self.book.near(e['sec'], pos, e[k]):
                    F.err('phrase.not-near', w, f'{k} {e[k]!r} is not within 1,500 characters of the quote')
        for i, r in enumerate(e.get('also', [])):
            if fields(F, r, 'ref', f'{w}.also[{i}]') and isinstance(r.get('q'), str):
                self.quote_ok(r.get('sec'), r['q'], f'{w}.also[{i}]')
        d = e.get('doc')
        if isinstance(d, dict) and fields(F, d, 'doc', w + '.doc'):
            enum(F, d, 'cal', 'cal', w + '.doc')
            if d.get('at') not in self.P:
                F.err('ref.unknown', w + '.doc', f'no place {d.get("at")!r}')
            used['place'][d.get('at')] += 1
            dtm = self.in_range(d.get('t', ''), w + '.doc', 't')
            if dtm and t and dtm > t:
                F.err('doc.after-event', w, f'the document ({d["t"]}) is dated after the scene that reads it ({e["t"]})')
            if dtm and 'tp' in d:
                c = L.parse_tp(d['tp'])
                if not c:
                    F.err('time.tp-unparsed', w + '.doc', f'no clock time in tp {d["tp"]!r}')
                elif (dtm.hour, dtm.minute) not in c:
                    F.err('time.tp-mismatch', w + '.doc', f'tp {d["tp"]!r} means {sorted(c)}, but t is {d["t"]}')
            if dtm and 'dp' in d:
                self.date_phrase(d['dp'], d.get('cal'), dtm, w + '.doc')
            if 'sec' in e and isinstance(d.get('q'), str):
                dpos = self.quote_ok(e['sec'], d['q'], w + '.doc')
                for k in ('tp', 'dp'):
                    if dpos is not None and k in d and not self.book.near(e['sec'], dpos, d[k]):
                        F.err('phrase.not-near', w + '.doc', f'{k} {d[k]!r} is not near the document quote')

        # moves
        for i, m in enumerate(e.get('moves', [])):
            mw = f'{w}.moves[{i}]'
            if not fields(F, m, 'move', mw):
                continue
            enum(F, m, 'mode', 'move.mode', mw)
            enum(F, m, 'rc', 'move.rc', mw)
            for a in [m.get('who')] + m.get('with', []):
                if a not in self.A:
                    F.err('ref.unknown', mw, f'no actor {a!r}')
                used['actor'][a] += 1
            for k in ('from', 'to'):
                if m.get(k) not in self.P:
                    F.err('ref.unknown', mw, f'{k}: no place {m.get(k)!r}')
                used['place'][m.get(k)] += 1
            for v in m.get('via', []):
                if isinstance(v, str):
                    if v not in self.P:
                        F.err('ref.unknown', mw, f'via: no place {v!r}')
                    elif self.P[v].get('zone') == 'offmap':
                        F.err('track.offmap-waypoint', mw, f'{v} is off the map; it can only start or end a move')
                    used['place'][v] += 1
                elif not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
                    F.err('field.type', mw, 'via holds place ids or [lat, lon]')
            if 't0' in m:
                t0 = self.in_range(m['t0'], mw, 't0')
                if t0 and t and t0 > t:
                    F.err('time.bounds', mw, 't0 (departure) is after the event')
            if 'size' in m and pos is not None and not self.book.near(e['sec'], pos, m['size']):
                F.err('phrase.not-near', mw, f'size {m["size"]!r} is not within 1,500 characters of the quote')
            if 'ack' in m and not m['ack'].strip():
                F.err('field.type', mw, 'ack explains the anomaly')
            self.count_n(m, mw)
            if m.get('run') and pos is not None and not re.search(L.RUN_WORDS, self.scene_text(e) + ' ' + (m.get('size') or ''), re.I):
                F.err('fight.not-in-text', mw, f'run: the passage has no word for running at the enemy ({L.RUN_WORDS})')
            if 'kit' in m and pos is not None:
                self.kit(m['kit'], self.scene_text(e), mw)
            if 'say' in m and pos is not None:
                self.say(m, e['sec'], pos, mw)
            if m.get('stay'):
                to = self.P.get(m.get('to'), {})
                if to and not to.get('ll'):
                    F.err('presence.unlocated', mw, f'stay: {m.get("to")} has no position')
                elif to.get('zone') == 'offmap':
                    F.err('presence.unlocated', mw, f'stay: {m.get("to")} is off the map')
                if self.A.get(m.get('who'), {}).get('kind') not in L.PRESENT_KINDS:
                    F.err('presence.kind', mw, f'stay: a {self.A.get(m.get("who"), {}).get("kind")} does not stay; only bodies of people and ships do')

        # presence: who is there from this scene on, and who is gone after it
        for key in ('present', 'gone'):
            for i, r in enumerate(e.get(key, [])):
                rw = f'{w}.{key}[{i}]'
                if not fields(F, r, 'presence' if key == 'present' else 'gone', rw):
                    continue
                a = self.A.get(r.get('who'))
                if a is None:
                    F.err('ref.unknown', rw, f'no actor {r.get("who")!r}')
                elif a.get('kind') not in L.PRESENT_KINDS:
                    F.err('presence.kind', rw, f'a {a.get("kind")} is not drawn as a standing body; only {sorted(L.PRESENT_KINDS)}')
                used['actor'][r.get('who')] += 1
                pid = r.get('place', e.get('loc'))
                if pid not in self.P:
                    F.err('ref.unknown', rw, f'no place {pid!r}')
                elif not self.P[pid].get('ll'):
                    F.err('presence.unlocated', rw, f'{pid} has no position')
                used['place'][pid] += 1
                sup = self.support(e, r, rw, pos)
                if sup is None:
                    continue
                if a is not None:
                    self.named(a, sup, rw)
                if key == 'present':
                    if 'size' in r and sup[1] is not None and not self.book.near(sup[0], sup[1], r['size']):
                        F.err('phrase.not-near', rw, f'size {r["size"]!r} is not within 1,500 characters of the quote')
                    self.count_n(r, rw)
                    if 'kit' in r:
                        self.kit(r['kit'], sup[2], rw)
                    if 'say' in r:
                        self.say(r, sup[0], sup[1], rw)
                    # the word checks read only fields of the right type (a wrong type is reported above)
                    if any(k in r and not typed(r, k) for k in ('form', 'march', 'face', 'inside', 'fire', 'at', 'pose', 'assault', 'patrol')):
                        continue
                    here = r.get('place', e.get('loc'))
                    if 'form' in r or 'march' in r:
                        self.formation(r, sup[2], rw, here)
                    if any(k in r for k in ('fire', 'at', 'pose', 'assault', 'patrol')):
                        self.fighting(e, r, sup[2], rw)
                    if 'face' in r:
                        self.facing(r, sup[2], rw, here)
                    if r.get('inside'):
                        self.indoors(r, sup[2], rw, here)
        if 'shooting' in e.get('tags', []) and pos is not None and not re.search(L.SHOOTING_WORDS, self.scene_text(e), re.I):
            F.err('tag.shooting', w, 'tagged shooting, but the quotes say nothing of firing')

        # control
        for i, c in enumerate(e.get('ctl', [])):
            cw = f'{w}.ctl[{i}]'
            if not fields(F, c, 'ctl', cw):
                continue
            pl = self.P.get(c.get('place'))
            if pl is None:
                F.err('ref.unknown', cw, f'no place {c.get("place")!r}')
            elif pl.get('kind') not in L.HOLDABLE:
                F.err('ctl.kind', cw, f'a {pl.get("kind")} cannot be held')
            used['place'][c.get('place')] += 1
            self.control_state(c, cw)

    def scene_text(self, e):
        """The scene's own words: its quote and its other passages, normalised and joined."""
        parts = [L.norm(x) for x in L.segments(e.get('q', '')) if isinstance(x, str)]
        parts += [L.norm(r['q']) for r in e.get('also', []) if isinstance(r, dict) and isinstance(r.get('q'), str)]
        return ' '.join(parts)

    def support(self, e, r, where, pos):
        """What backs a presence: its own passage (ref), or else the scene's quotes.
        Returns (section, position of the passage, its text), or None if the passage is broken."""
        ref = r.get('ref')
        if ref is None:
            return (e.get('sec'), pos, self.scene_text(e)) if pos is not None else None
        if not fields(self.F, ref, 'ref', where + '.ref') or not isinstance(ref.get('q'), str):
            return None
        at = self.quote_ok(ref.get('sec'), ref['q'], where + '.ref')
        return None if at is None else (ref['sec'], at, L.norm(ref['q']))

    def named(self, a, sup, where):
        """The body must be in the passage, or within 1,500 characters of it, under one of Reed's spellings."""
        sec, at, text = sup
        names = [L.norm(n).lower() for n in a.get('reed', []) if isinstance(n, str)]
        if any(n in text.lower() for n in names):
            return
        t = self.book.secs.get(sec, '').lower()
        if at is not None and any(n in t[max(0, at - 1500): at + 1500] for n in names):
            return
        self.F.err('presence.unnamed', where, f'Reed does not name {a.get("id")} near this passage (as {", ".join(a.get("reed", []))})')

    def kit(self, kit, text, where):
        for k in kit:
            name, n = L.kit_item(k) if isinstance(k, str) else (None, None)
            if name not in L.KIT_WORDS:
                self.F.err('field.enum', where, f'kit {k!r} is not one of {sorted(L.ENUM["kit"])} (optionally with :count)')
            elif not re.search(L.KIT_WORDS[name], text, re.I):
                self.F.err('kit.not-in-text', where, f'kit {name!r}: the passage has no word for it ({L.KIT_WORDS[name]})')

    def say(self, r, sec, pos, where):
        """words on a banner or a flag: Reed's, verbatim, within 1,500 characters of the passage, no more
        of them than the banners and flags the kit has"""
        carry = [L.kit_item(k) for k in r.get('kit', []) if isinstance(k, str) and k.split(':')[0] in ('banner', 'flag')]
        if not carry:
            self.F.err('field.missing', where, 'say (the words on a banner or a flag) needs a banner or a flag in kit')
        elif all(n is not None for _, n in carry) and isinstance(r['say'], list) and len(r['say']) > sum(n for _, n in carry):
            self.F.err('field.range', where, f'say has {len(r["say"])} texts for {sum(n for _, n in carry)} banners and flags')
        for t in r['say']:
            if not isinstance(t, str) or not t.strip():
                self.F.err('field.type', where, 'say holds the words on each banner')
            elif not self.book.near(sec, pos, t):
                self.F.err('phrase.not-near', where, f'say {t!r} is not within 1,500 characters of the passage')

    def formation(self, r, text, where, place=None):
        """a column, a line or ranks, and a body on the move: each needs its word in the passage or in
        the size phrase (itself Reed's, near the passage). On the move means passing: a brief column."""
        F, words = self.F, text + ' ' + (r.get('size') or '')
        if 'form' in r:
            if r['form'] not in L.ENUM['form']:
                F.err('field.enum', where, f'form {r["form"]!r} is not one of {sorted(L.ENUM["form"])}')
            elif not re.search(L.FORM_WORDS[r['form']], words, re.I):
                F.err('form.not-in-text', where, f'form {r["form"]!r}: the passage has no word for it ({L.FORM_WORDS[r["form"]]})')
            elif r['form'] == 'ring' and (self.P.get(place) or {}).get('kind') not in ('building', 'station', 'complex'):
                F.err('form.ring-place', where, 'form "ring" surrounds a building: the place is a building, station or complex')
        if r.get('march'):
            if r.get('form') != 'column' or not r.get('brief'):
                F.err('field.missing', where, 'march (a body passing) needs form: column and brief')
            if not re.search(L.MARCH_WORDS, words, re.I):
                F.err('form.not-in-text', where, f'march: the passage has no word for it ({L.MARCH_WORDS})')

    def fighting(self, e, r, text, where):
        """who fires (in the open, or from the windows), at whom or what, who assaults (and is thrown
        back, or gets in), whose cars cruise up and down, and who lies dead or flat: each needs its
        words in the passage or the size phrase, and a scene where anyone fires is tagged shooting"""
        F, words = self.F, text + ' ' + (r.get('size') or '')
        if 'fire' in r:
            if r['fire'] not in (True, 'windows'):
                F.err('field.enum', where, 'fire is true, or "windows" for firing from inside the building')
            elif not re.search(L.SHOOTING_WORDS, words, re.I):
                F.err('fight.not-in-text', where, f'fire: the passage has no word for firing ({L.SHOOTING_WORDS})')
            elif r['fire'] == 'windows' and not re.search(L.WINDOW_WORDS, words, re.I):
                F.err('fight.not-in-text', where, 'fire: "windows", but the passage says nothing of windows')
            if 'shooting' not in e.get('tags', []):
                F.err('tag.shooting', where, 'a body fires here, so the scene is tagged shooting')
        if 'at' in r:
            if 'fire' not in r:
                F.err('field.missing', where, 'at (what the body fires at) needs fire')
            if r['at'] not in self.A and r['at'] not in self.P:
                F.err('ref.unknown', where, f'at: no actor or place {r["at"]!r}')
            self.count_ref(r['at'])
        if 'assault' in r:
            if r['assault'] not in L.ENUM['assault']:
                F.err('field.enum', where, f'assault {r["assault"]!r} is not one of {sorted(L.ENUM["assault"])}')
            elif r['assault'] == 'repulsed' and not (re.search(L.ATTACK_WORDS, words, re.I) and re.search(L.REPULSE_WORDS, words, re.I)):
                F.err('fight.not-in-text', where, f'assault "repulsed": the passage needs words for the attack ({L.ATTACK_WORDS}) and for its failing ({L.REPULSE_WORDS})')
            elif r['assault'] == 'carried' and not re.search(L.ENTRY_WORDS, words, re.I):
                F.err('fight.not-in-text', where, f'assault "carried": the passage has no words for going in ({L.ENTRY_WORDS})')
        if r.get('patrol'):
            if not re.search(L.PATROL_WORDS, words, re.I):
                F.err('fight.not-in-text', where, f'patrol: the passage has no words for cruising ({L.PATROL_WORDS})')
            if not any(L.kit_item(k)[0] in ('armoured', 'car', 'truck') for k in r.get('kit', [])):
                F.err('field.missing', where, 'patrol: the body has no armoured car, car or truck in its kit to cruise in')
        if 'pose' in r:
            if r['pose'] not in L.ENUM['pose']:
                F.err('field.enum', where, f'pose {r["pose"]!r} is not one of {sorted(L.ENUM["pose"])}')
            elif not re.search(L.POSE_WORDS[r['pose']], words, re.I):
                F.err('fight.not-in-text', where, f'pose {r["pose"]!r}: the passage has no word for it ({L.POSE_WORDS[r["pose"]]})')

    def indoors(self, r, text, where, place=None):
        """a body Reed puts inside its building ("in the back rooms", "inside"): the place is a building,
        and the passage says so; a body inside neither forms up nor fires in the open"""
        F, words = self.F, text + ' ' + (r.get('size') or '')
        if (self.P.get(place) or {}).get('kind') not in ('building', 'station', 'complex', 'room'):
            F.err('field.range', where, 'inside: the place is a building, station, complex or room')
        if not re.search(L.INSIDE_WORDS, words, re.I):
            F.err('form.not-in-text', where, f'inside: the passage has no word for indoors ({L.INSIDE_WORDS})')
        if any(k in r for k in ('form', 'march', 'assault', 'patrol')) or r.get('fire') is True:
            F.err('field.range', where, 'inside: a body indoors does not form up, march, assault, patrol or fire in the open')

    def facing(self, r, text, where, place=None):
        """what the body looks at, or trains its guns on ("staring at the hotel roof", "all the guns
        trained toward St. Isaac's"): a place or a body, with Reed's word for looking in the passage"""
        F, words = self.F, text + ' ' + (r.get('size') or '')
        if r['face'] not in self.A and r['face'] not in self.P:
            F.err('ref.unknown', where, f'face: no actor or place {r["face"]!r}')
        elif r['face'] == (place or r.get('place')):
            F.err('field.range', where, 'face: a body faces something other than the place it stands at')
        self.count_ref(r['face'])
        if not re.search(L.FACE_WORDS, words, re.I):
            F.err('form.not-in-text', where, f'face: the passage has no word for looking or training guns ({L.FACE_WORDS})')

    def count_n(self, r, where):
        if 'n' in r:
            if 'size' not in r:
                self.F.err('field.missing', where, 'n (how many to draw) needs size, the phrase it reads')
            elif isinstance(r['n'], int) and not 1 <= r['n'] <= 400:
                self.F.err('field.range', where, 'n is between 1 and 400')

    def picture(self, pic):
        """A picture shown with a scene: a file in the repo, of the stated size, public domain, with its
        provenance. Reed's own facsimiles carry his caption (ref), quote-checked like everything else."""
        F = self.F
        w = f'pictures/{pic.get("id")}'
        if not fields(F, pic, 'picture', w):
            return
        enum(F, pic, 'kind', 'picture.kind', w)
        enum(F, pic, 'from', 'picture.from', w)
        path = os.path.join(os.path.dirname(os.path.abspath(self.dir)), pic.get('file', ''))
        if not isinstance(pic.get('file'), str) or not pic['file'].startswith('media/'):
            F.err('picture.file', w, 'file is a path under media/')
        elif not os.path.exists(path):
            F.err('picture.file', w, f'no file {pic["file"]}')
        else:
            size = L.image_size(path)
            if size is None:
                F.err('picture.file', w, 'not a JPEG or PNG')
            elif size != (pic.get('w'), pic.get('h')):
                F.err('picture.size', w, f'the file is {size[0]}x{size[1]}, not {pic.get("w")}x{pic.get("h")}')
        if not str(pic.get('license', '')).startswith('Public domain'):
            F.err('picture.license', w, 'only public-domain pictures are shown; say which rule ("Public domain (PD-…)")')
        if not re.match(r'^https://', str(pic.get('url', ''))):
            F.err('field.pattern', w, 'url is the https page the picture comes from')
        for e in pic.get('scenes', []):
            if e not in self.E:
                F.err('ref.unknown', w, f'scenes: no event {e!r}')
        if pic.get('from') == 'reed-1919':
            # Reed's own facsimile: his caption is the evidence, and the page says where in the edition
            if 'ref' not in pic:
                F.err('field.missing', w, "a facsimile from Reed's book carries his caption in ref")
            if 'page' not in pic:
                F.err('field.missing', w, 'page: where the facsimile is in the edition the scan comes from')
        else:
            for k in ('caption', 'author', 'date'):
                if k not in pic:
                    F.err('field.missing', w, f'a picture from {pic.get("from")} needs {k}')
        ref = pic.get('ref')
        if isinstance(ref, dict) and fields(F, ref, 'ref', w + '.ref') and isinstance(ref.get('q'), str):
            self.quote_ok(ref.get('sec'), ref['q'], w + '.ref')

    def presence(self):
        """Who stays where between scenes (storylib.presence_spans). A `gone` must find someone, and a
        body indoors (`inside`, which a later entry inherits) does not form up, march, assault, patrol or
        fire in the open."""
        spans, misses = L.presence_spans(self.events, self.actors, self.places)
        self.spans = spans
        for eid, who, pid in misses:
            self.F.err('presence.not-there', f'events/{eid}', f'gone: {who} is not at {pid} at this point')
        for sp in spans:
            if sp.get('inside') and (any(sp.get(k) for k in ('form', 'march', 'assault', 'patrol')) or sp.get('fire') is True):
                self.F.err('field.range', f'events/{sp["ev"]}', f'{sp["who"]} at {sp["place"]} is inside (from an earlier entry): it does not form up, march, assault, patrol or fire in the open')

    def count_ref(self, x):
        """a place or an actor named by `at` or `face` is in use"""
        if isinstance(x, str):
            if x in self.P:
                self.used['place'][x] += 1
            elif x in self.A:
                self.used['actor'][x] += 1

    def date_phrase(self, dp, cal, t, w):
        F = self.F
        if cal == 'none':
            F.err('date.cal-none', w, 'a date phrase needs cal NS or OS')
            return
        cands, wd = L.parse_dp(dp, cal, t.date())
        if not cands:
            F.err('date.dp-unparsed', w, f'no date in dp {dp!r}')
            return
        if t.date() not in cands:
            F.err('date.dp-mismatch', w, f'dp {dp!r} read as {cal} is {", ".join(map(str, cands))} (New Style), but t is {t.date()}')
        if wd is not None and not any(c.weekday() == wd for c in cands):
            F.err('date.weekday', w, f'dp {dp!r} names a {L.WEEKDAYS[wd].title()}, but {cands[0]} ({cal}) was a {L.WEEKDAYS[cands[0].weekday()].title()}')

    # -- tracks: Reed, Kerensky, the Cossacks --
    def track_moves(self, aid):
        out = []
        for i, e in enumerate(self.events):
            for m in e.get('moves', []):
                if isinstance(m, dict) and m.get('who') == aid:
                    out.append((i, e, m))
        return out

    def tracks(self):
        F = self.F
        self.reed_path = []
        for aid, a in self.A.items():
            if not a.get('track'):
                continue
            prev = None
            for i, e, m in self.track_moves(aid):
                if prev and m.get('from') != prev[2].get('to') and not m.get('gap'):
                    F.err('track.chain', f'events/{e["id"]}',
                          f'{aid} leaves from {m.get("from")} but the previous move ({prev[1]["id"]}) ended at {prev[2].get("to")}; mark gap if the text skips')
                prev = (i, e, m)
            if aid == 'reed':
                self.reed_path = self.track_moves(aid)
        if 'reed' not in self.A:
            return
        # Where Reed is: the end of his last move before an event, and every point he passes in it.
        moves = self.reed_path
        for i, e in enumerate(self.events):
            if e.get('witness') != 'seen' or e.get('loc') not in self.P:
                continue
            before = [m for j, ee, m in moves if j < i]
            here = [m for j, ee, m in moves if j == i]
            spots = set()
            if before:
                spots.add(before[-1].get('to'))
            for m in here:
                spots |= {m.get('from'), m.get('to')} | {v for v in m.get('via', []) if isinstance(v, str)}
            if not any(s and self.related(s, e['loc']) for s in spots):
                at = before[-1].get('to') if before else 'nowhere yet'
                F.err('track.seen-elsewhere', f'events/{e["id"]}',
                      f'witness "seen" at {e["loc"]}, but Reed is at {at}; add his move or change the witness type')

    def control(self):
        F = self.F
        tl = defaultdict(list)
        for e in self.events:
            for c in e.get('ctl', []):
                if isinstance(c, dict):
                    tl[c.get('place')].append((e.get('t', ''), e.get('id'), c))
        self.timelines = {}
        for pid, changes in tl.items():
            p = self.P.get(pid)
            if not p:
                continue
            c0 = p.get('ctl0')
            if c0 and changes and isinstance(c0.get('as_of'), str) and c0['as_of'] > changes[0][0]:
                F.err('ctl0.after-first', f'places/{pid}', f'ctl0 is as of {c0["as_of"]}, after the first change ({changes[0][0]})')
            cur = (c0.get('state'), c0.get('holder'), c0.get('by')) if c0 else None
            for t, eid, c in changes:
                new = (c.get('state'), c.get('holder'), c.get('by'))
                if new == cur:
                    F.warn('ctl.redundant', f'events/{eid}', f'{pid} is already {new[0]} by {new[1]}')
                cur = new
            self.timelines[pid] = ([('ctl0', c0)] if c0 else []) + [(eid, c) for t, eid, c in changes]

    # -- measurements --
    def speeds(self):
        """Feasible speed of each tracked move: straight-line distance through its points over the
        widest time window the data allows (previous event's earliest bound to this one's latest)."""
        F, out = self.F, []
        sp = self.meta['speed_kmh']
        for aid, a in self.A.items():
            if not a.get('track'):
                continue
            prev_e = None
            for i, e, m in self.track_moves(aid):
                pts = [self.P.get(m.get('from'), {}).get('ll')]
                pts += [self.P.get(v, {}).get('ll') if isinstance(v, str) else v for v in m.get('via', [])]
                pts.append(self.P.get(m.get('to'), {}).get('ll'))
                pts = [x for x in pts if x]
                km = sum(L.dist_m(x, y) for x, y in zip(pts, pts[1:])) / 1000
                end = tparse(e['tr'][1]) if e.get('tr') else tparse(e['t'])
                if m.get('t0'):
                    start = tparse(m['t0'])
                elif prev_e is not None:
                    start = tparse(prev_e['tr'][0]) if prev_e.get('tr') else tparse(prev_e['t'])
                else:
                    start = None
                prev_e = e
                if start is None or end is None or km == 0:
                    continue
                hours = (end - start).total_seconds() / 3600
                if hours <= 0:
                    hours = 1 / 60
                kmh = km / hours
                vmax = sp.get(m.get('mode'), max(sp.values()))
                out.append((aid, e['id'], m.get('mode'), km, hours, kmh, vmax))
                where = f'events/{e["id"]}'
                if kmh > 3 * vmax and not m.get('ack'):
                    F.err('speed.implausible', where, f'{aid}: {km:.1f} km in at most {hours * 60:.0f} min = {kmh:.0f} km/h by {m.get("mode")} (limit {vmax}); fix the times or add ack')
                elif kmh > vmax and not m.get('ack'):
                    F.warn('speed.fast', where, f'{aid}: {kmh:.0f} km/h by {m.get("mode")} (limit {vmax})')
        return out


# ---------- OSM footprint check ----------
def osm_fetch(cache, ref, F, where):
    path = os.path.join(cache, 'osm', ref.replace('/', '-') + '.json')
    if os.path.exists(path):
        return json.loads(L.read_text(path))
    kind, num = ref.split('/')
    url = f'{OSM_API}/{kind}/{num}' + ('' if kind == 'node' else '/full') + '.json'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    time.sleep(1.0)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            F.err('osm.missing', where, f'{ref} is gone from OSM (HTTP {e.code})')
            return None
        raise EnvError(f'OSM API: HTTP {e.code} for {ref}')
    except (urllib.error.URLError, TimeoutError) as e:
        raise EnvError(f'OSM API unreachable for {ref}: {e}')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    L.write_text(path, json.dumps(data))
    return data


def rings_of(data, ref):
    els = data['elements']
    nodes = {e['id']: (e['lat'], e['lon']) for e in els if e['type'] == 'node'}
    ways = {e['id']: [nodes[n] for n in e['nodes'] if n in nodes] for e in els if e['type'] == 'way'}
    kind, num = ref.split('/')
    me = next(e for e in els if e['type'] == kind and e['id'] == int(num))
    if kind == 'node':
        return me, [], [nodes[int(num)]]
    if kind == 'way':
        return me, [ways[int(num)]], []
    # relation: join member ways into closed rings (outer and inner alike; we only need the outline)
    parts = [list(ways[m['ref']]) for m in me.get('members', []) if m['type'] == 'way' and m['ref'] in ways]
    rings = []
    while parts:
        r = parts.pop(0)
        grown = True
        while grown and r[0] != r[-1]:
            grown = False
            for i, q in enumerate(parts):
                if q[0] == r[-1]:
                    r += q[1:]
                elif q[-1] == r[-1]:
                    r += q[-2::-1]
                elif q[-1] == r[0]:
                    r = q[:-1] + r
                elif q[0] == r[0]:
                    r = q[:0:-1] + r
                else:
                    continue
                parts.pop(i)
                grown = True
                break
        rings.append(r)
    points = [nodes[m['ref']] for m in me.get('members', []) if m['type'] == 'node' and m['ref'] in nodes]
    return me, rings, points


CLASS_KEYS = {
    'building': ('building', 'building:part', 'historic', 'amenity', 'tourism', 'office', 'military'),
    'station': ('railway', 'public_transport', 'building'),
    'bridge': ('bridge', 'man_made', 'highway'),
    'complex': ('building', 'historic', 'amenity', 'tourism', 'landuse', 'leisure', 'military', 'place'),
    'square': ('place', 'highway', 'area', 'leisure'),
    'town': ('place', 'boundary', 'admin_level'),
    'district': ('place', 'boundary', 'landuse'),
    'street': ('highway', 'name'),
    'area': (), 'room': (), 'offmap': ('place',),
}


def check_osm(C, F, cache):
    for p in C.places:
        ref = p.get('osm') or p.get('site_osm')
        if not ref or not L.OSM_RE.match(ref):
            continue
        where = f'places/{p["id"]}'
        data = osm_fetch(cache, ref, F, where)
        if data is None:
            continue
        me, rings, points = rings_of(data, ref)
        tags = me.get('tags', {})
        if p.get('osm'):
            keys = CLASS_KEYS.get(p.get('kind'), ())
            has = set(tags)
            if ref.startswith('relation'):
                for e in data['elements']:
                    if e['type'] == 'way':
                        has |= set(e.get('tags', {}))
            if keys and not has & set(keys):
                F.err('osm.class', where, f'{ref} has none of {keys} for a {p.get("kind")}')
        if p.get('wd') and tags.get('wikidata') and tags['wikidata'] != p['wd']:
            F.err('osm.wikidata', where, f'{ref} says wikidata={tags["wikidata"]}, the place says {p["wd"]}')
        g = p.get('geo', {})
        if g.get('osm_v') and me.get('version') and me['version'] != g['osm_v']:
            F.info('osm.version', where, f'{ref} is now version {me["version"]} (looked up at {g["osm_v"]})')
        ll = p.get('ll')
        if not ll:
            continue
        if rings:
            xy = lambda q: L.local_xy(ll, q)
            pt = (0.0, 0.0)
            inside = any(L.in_ring(pt, [xy(q) for q in r]) for r in rings if len(r) > 2)
            if not inside:
                d = min(L.ring_dist(pt, [xy(q) for q in r]) for r in rings if len(r) > 1)
                lim = 25 if p.get('kind') in ('building', 'station', 'room') else max(25, p.get('acc', 25))
                if d > lim:
                    F.err('osm.outside', where, f'the pin is {d:.0f} m outside {ref} (limit {lim} m)')
        elif points:
            d = min(L.dist_m(ll, q) for q in points)
            if d > max(p.get('acc', 100), 100):
                F.err('osm.outside', where, f'the pin is {d:.0f} m from {ref}')


# ---------- PDF page check ----------
def check_pdf(C, F, path):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise EnvError('--pdf needs pypdf (pip install pypdf)')
    if not os.path.exists(path):
        raise EnvError(f'no PDF at {path}')
    sha = hashlib.sha256(L.read_bytes(path)).hexdigest()
    want = C.meta.get('pdf', {}).get('sha256')
    if want and sha != want:
        raise EnvError(f'the PDF is not the one the page numbers were taken from ({sha[:12]}…, expected {want[:12]}…)')
    pages = pdf_pages(PdfReader(path))
    for e in C.events:
        if 'p' not in e or 'q' not in e:
            continue
        p = page_of(pages, e['q'])
        if p is None:
            F.warn('pdf.not-found', f'events/{e["id"]}', 'quote not found in the PDF text (that edition’s wording differs?)')
        elif e['p'] != p:
            F.err('pdf.page', f'events/{e["id"]}', f'p is {e["p"]}, but the quote starts on PDF page {p}')


def pdf_pages(reader):
    """Each page's text as bare lower-case letters and digits: the PDF breaks lines, hyphenates and
    spaces "A. M." differently from Gutenberg, so only the letters are compared."""
    return [re.sub(r'[^a-z0-9]', '', L.norm(pg.extract_text() or '').lower()) for pg in reader.pages]


def page_of(pages, q):
    """The PDF page where the quote starts. Long probes first; a shorter one is used only if it is
    found on exactly one page, which covers the editions' small differences ("bluffed our past")."""
    bare = re.sub(r'[^a-z0-9]', '', L.norm(L.segments(q)[0]).lower())
    for n in (60, 40, 25):
        probe = bare[:n]
        if len(probe) < 15:
            continue
        hits = [i + 1 for i, t in enumerate(pages) if probe in t]
        if not hits:
            hits = [i + 1 for i in range(len(pages) - 1) if probe in pages[i] + pages[i + 1]]
        if len(hits) == 1 or (hits and n == 60):
            return hits[0]
    return None


# ---------- report ----------
SUN_WORDS = re.compile(r'\b(dawn|daybreak|sunrise|twilight|dusk|nightfall|sunset|after dark|grew dark|it was dark|daylight)\b', re.I)
WEEKDAY_DATE = re.compile(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b[^.;]{0,25}?\b'
                          r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})')


def report(C, F):
    meta = C.meta
    off = meta['clock']['petrograd']['offset_min']
    print('# Check report\n')
    print(f'{len(C.sources)} sources, {len(C.actors)} actors, {len(C.places)} places, {len(C.events)} events, '
          f'{sum(len(e.get("moves", [])) for e in C.events)} moves, {len(C.timelines)} control timelines.\n')
    print('| witness | events |\n|---|---|')
    for k, v in Counter(e.get('witness') for e in C.events).most_common():
        print(f'| {k} | {v} |')
    print('\n| time quality | events |\n|---|---|')
    for k, v in Counter(e.get('tq') for e in C.events).most_common():
        print(f'| {k} | {v} |')
    print('\n| place confidence | places |\n|---|---|')
    for k, v in Counter(p.get('conf') for p in C.places).most_common():
        print(f'| {k} | {v} |')

    print('\n## Speeds (tracked actors; straight lines, widest window)\n')
    print('| actor | event | mode | km | hours (max) | km/h | limit |\n|---|---|---|---|---|---|---|')
    for aid, eid, mode, km, h, kmh, vmax in C.speeds():
        flag = ' **!**' if kmh > vmax else ''
        print(f'| {aid} | {eid} | {mode} | {km:.1f} | {h:.2f} | {kmh:.1f}{flag} | {vmax} |')

    print("\n## Reed's movements per day (a floor: straight lines between pins; legs to or from his unlocated lodging count as zero)\n")
    per = defaultdict(lambda: [0.0, 0.0])
    for i, e, m in getattr(C, 'reed_path', []):
        pts = [C.P.get(m.get('from'), {}).get('ll')] + [C.P.get(v, {}).get('ll') if isinstance(v, str) else v for v in m.get('via', [])] + [C.P.get(m.get('to'), {}).get('ll')]
        pts = [x for x in pts if x]
        km = sum(L.dist_m(x, y) for x, y in zip(pts, pts[1:])) / 1000
        per[e['t'][:10]][0 if m.get('mode') == 'foot' else 1] += km
    print('| date (NS) | on foot, km | other or unknown mode, km |\n|---|---|---|')
    for d in sorted(per):
        print(f'| {d} | {per[d][0]:.1f} | {per[d][1]:.1f} |')

    print('\n## Light: sun words against the sun (clock UTC+%s min)\n' % off)
    print('| event | words | t | sun elevation at t |\n|---|---|---|---|')
    for e in C.events:
        text = ' '.join([e.get('tp', '')] + L.segments(e.get('q', '')))
        ws = sorted({m.group(1).lower() for m in SUN_WORDS.finditer(text)})
        if not ws:
            continue
        ll = C.P.get(e.get('loc'), {}).get('ll') or [59.9398, 30.3146]
        t = tparse(e['t'])
        el = L.sun_elevation(ll[0], ll[1], t - dt.timedelta(minutes=off))
        print(f'| {e["id"]} | {", ".join(ws)} | {e["t"][11:]} ({e["tq"]}) | {el:+.1f}° |')

    print('\n## Weekday and date pairs in the whole book\n')
    print('| section | phrase | New Style | Old Style |\n|---|---|---|---|')
    for sid, text in C.book.secs.items():
        for m in WEEKDAY_DATE.finditer(text):
            wd = L.WEEKDAYS.index(m.group(1).lower())
            mon, day = L.MONTHS[m.group(2).lower()], int(m.group(3))
            try:
                d = dt.date(1917, mon, day)
            except ValueError:
                continue
            ns = 'fits' if d.weekday() == wd else L.WEEKDAYS[d.weekday()].title()
            o = L.os_to_ns(d)
            os_ = 'fits' if o.weekday() == wd else L.WEEKDAYS[o.weekday()].title()
            print(f'| {sid} | {m.group(0)[:50]} | {ns} | {os_} |')

    print('\n## Coverage by section\n')
    print('| section | events | of which Reed saw |\n|---|---|---|')
    cov = defaultdict(lambda: [0, 0])
    for e in C.events:
        k = e.get('sec')
        cov[k][0] += 1
        cov[k][1] += e.get('witness') == 'seen'
    order = list(C.book.secs)
    for k in sorted(cov, key=lambda x: order.index(x) if x in order else 999):
        print(f'| {k} | {cov[k][0]} | {cov[k][1]} |')

    print('\n## Presence: who stays where between scenes\n')
    print('| who | place | from | until | ended by |\n|---|---|---|---|---|')
    ids = [e.get('id') for e in C.events]
    for sp in getattr(C, 'spans', []):
        until = ids[sp['end']] if sp['end'] is not None and sp['end'] < len(ids) else ('the end' if sp['end'] is None else 'the last scene')
        print(f"| {sp['who']} | {sp['place']} | {ids[sp['start']] if sp['start'] < len(ids) else '-'} | {until} | {sp['end_by'] or ''}{' (' + sp['end_ev'] + ')' if sp['end_ev'] else ''} |")

    print('\n## Control timelines\n')
    for pid, tl in sorted(C.timelines.items()):
        steps = []
        for eid, c in tl:
            if c:
                s = c.get('state')
                who = c.get('holder', '')
                steps.append(f'{s}{":" + who if who else ""}{" by " + c["by"] if c.get("by") else ""} ({eid})')
        print(f'- **{pid}**: ' + ' → '.join(steps))
    print()


# ---------- main ----------
def run(data_dir, text_path, osm=False, cache='cache', pdf=None):
    F = Findings()
    if not os.path.exists(text_path):
        raise EnvError(f'no {text_path}: run python3 -I tools/text.py cache')
    book = L.Book(json.loads(L.read_text(text_path)))
    C = Checker(data_dir, book, F)
    C.run()
    if C.meta and not F.codes():
        C.speeds()
        if osm:
            check_osm(C, F, cache)
        if pdf:
            check_pdf(C, F, pdf)
    return C, F


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default='data')
    ap.add_argument('--text', default='cache/sections.json')
    ap.add_argument('--cache', default='cache')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--osm', action='store_true')
    ap.add_argument('--pdf')
    ap.add_argument('--only', help='comma-separated code prefixes to show and count')
    a = ap.parse_args()
    try:
        C, F = run(a.data, a.text, a.osm, a.cache, a.pdf)
    except EnvError as e:
        print(f'ENV {e}', file=sys.stderr)
        sys.exit(2)
    items = F.items
    if a.only:
        pre = tuple(a.only.split(','))
        items = [x for x in items if x[1].startswith(pre)]
    rank = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
    for lv, code, where, msg in sorted(items, key=lambda x: (rank[x[0]], x[2])):
        print(f'{lv} {code} {where}: {msg}')
    n_err = sum(1 for x in items if x[0] == 'ERROR')
    n_warn = sum(1 for x in items if x[0] == 'WARN')
    if a.report and C.meta and not n_err:
        report(C, F)
    moves = sum(len(e.get('moves', [])) for e in C.events if isinstance(e, dict))
    tls = len(getattr(C, 'timelines', {}))
    pres = len(getattr(C, 'spans', []))
    print(f'checked {len(C.sources)} sources, {len(C.actors)} actors, {len(C.places)} places, {len(C.events)} events '
          f'({moves} moves, {tls} control timelines, {pres} presences), {len(C.pictures)} pictures: {n_err} errors, {n_warn} warnings')
    sys.exit(1 if n_err or (a.strict and n_warn) else 0)


if __name__ == '__main__':
    main()
