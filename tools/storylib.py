"""Shared helpers for the Ten Days data tools.

What lives here:
- the schema: allowed fields per record type, in canonical order, and their enums
- strict JSON loading, which rejects duplicate keys
- the canonical file layout (one header line of short fields, then one line per prose field
  or nested item)
- quote normalisation and lookup in Reed's text
- the date and time-phrase parsers
- small geometry helpers and a sun-elevation formula

Standard library only. The tools import it with sys.path.insert(0, os.path.dirname(__file__)),
because python3 -I leaves the script's own directory off sys.path.
"""
import json, math, re, datetime as dt
from collections import OrderedDict

TABLES = ['sources', 'actors', 'places', 'events']   # plus meta.json, which has its own shape

# ---------- schema ----------
# Field order here is the canonical order on disk. PROSE fields get a line of their own.
FIELDS = {
    'meta': ['title', 'text', 'pdf', 'calendar', 'clock', 'range', 'zones', 'speed_kmh', 'blocs', 'tags', 'note'],
    'day': ['d', 'os', 'label', 'name'],
    'source': ['id', 'kind', 'url', 'cite', 'note'],
    'actor': ['id', 'kind', 'bloc', 'track', 'part_of', 'seat', 'wd', 'name', 'reed', 'ru', 'stance', 'note'],
    'stance': ['from', 's', 'ev', 'src', 'ref', 'note'],
    'place': ['id', 'kind', 'zone', 'in', 'll', 'acc', 'conf', 'exists', 'osm', 'site_osm', 'wd', 'geo', 'ctl0',
              'name', 'reed', 'ru', 'addr1917', 'addr_now', 'ident', 'today', 'note'],
    'geo': ['m', 'at', 'q', 'osm_v', 'on', 'src', 'note'],
    'ctl0': ['state', 'holder', 'by', 'as_of', 'ev', 'src', 'ref'],
    'event': ['id', 't', 'tq', 'tr', 'tp', 'cal', 'dp', 'sec', 'p', 'loc', 'witness', 'by', 'actors', 'tags', 'src',
              'title', 'why', 'sum', 'q', 'also', 'doc', 'moves', 'ctl', 'check'],
    'ref': ['sec', 'q'],
    'doc': ['at', 't', 'tp', 'cal', 'dp', 'q'],
    'move': ['who', 'with', 'size', 'from', 'via', 'to', 'mode', 'rc', 't0', 'gap', 'ack'],
    'ctl': ['place', 'state', 'holder', 'by', 'basis'],
    'check': ['claim', 'v', 'src', 'rec', 'cf', 'note'],
}
REQUIRED = {
    'day': ['d', 'os', 'label', 'name'],
    'source': ['id', 'kind', 'cite'],
    'actor': ['id', 'kind', 'bloc', 'name', 'reed'],
    'stance': ['from', 's'],
    'place': ['id', 'kind', 'zone', 'conf', 'geo', 'name', 'reed'],
    'geo': ['m'],
    'ctl0': ['state', 'as_of'],
    'event': ['id', 't', 'tq', 'cal', 'loc', 'witness', 'title', 'sum'],
    'ref': ['sec', 'q'],
    'doc': ['at', 't', 'tp', 'cal', 'q'],
    'move': ['who', 'from', 'to', 'mode', 'rc'],
    'ctl': ['place', 'state'],
    'check': ['claim', 'v'],
}
PROSE = {'cite', 'name', 'note', 'title', 'why', 'sum', 'q', 'ident', 'today', 'rec', 'ru', 'reed',
         'addr1917', 'addr_now'}
NESTED_LIST = {'stance', 'also', 'moves', 'ctl', 'check'}   # one line per item
NESTED_ONE = {'geo', 'ctl0', 'doc'}                         # one line for the whole object

ENUM = {
    'source.kind': {'primary', 'secondary', 'reference', 'map', 'data'},
    'actor.kind': {'person', 'party', 'organ', 'unit', 'school', 'ship', 'crowd', 'press', 'foreign'},
    'actor.bloc': {'soviet', 'government', 'opposition', 'neutral', 'foreign', 'observer', 'public'},
    'stance.s': {'support', 'oppose', 'neutral', 'divided', 'unknown'},
    'place.kind': {'building', 'room', 'complex', 'square', 'street', 'bridge', 'station', 'district', 'town',
                   'area', 'offmap'},
    'place.zone': {'city', 'front', 'moscow', 'offmap'},
    'place.conf': {'named', 'identified', 'conjectural', 'unlocated'},
    'geo.m': {'osm', 'wikidata', 'plan1916', 'secondary', 'hand', 'pending'},
    'state': {'held', 'besieged', 'contested', 'neutral', 'unknown'},
    'event.tq': {'stated', 'doc', 'approx', 'day', 'inferred', 'secondary'},
    'cal': {'NS', 'OS', 'none'},
    'event.witness': {'seen', 'told', 'reported', 'document', 'context'},
    'move.mode': {'foot', 'march', 'cavalry', 'tram', 'car', 'truck', 'armoured', 'rail', 'ship', 'air', 'unknown'},
    'move.rc': {'stated', 'inferred', 'none'},
    'ctl.basis': {'text', 'record'},
    'check.v': {'agrees', 'partly', 'differs', 'disputed', 'unchecked'},
}
HOLDABLE = {'building', 'complex', 'square', 'bridge', 'station', 'district', 'town', 'area'}
LIMITS = {'title': 60, 'sum': 350, 'q': 320, 'note': 500, 'rec': 400, 'why': 300, 'ident': 400}
ID_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
OSM_RE = re.compile(r'^(node|way|relation)/\d+$')
WD_RE = re.compile(r'^Q\d+$')
T_RE = re.compile(r'^1917-(0[1-9]|1[0-2])-([0-2]\d|3[01])T([01]\d|2[0-3]):[0-5]\d$')
D_RE = re.compile(r'^1917-(0[1-9]|1[0-2])-([0-2]\d|3[01])$')


# ---------- strict JSON ----------
class DuplicateKey(ValueError):
    pass


def _no_dups(pairs):
    d = OrderedDict()
    for k, v in pairs:
        if k in d:
            raise DuplicateKey(k)
        d[k] = v
    return d


def load_json(path):
    return json.loads(read_text(path), object_pairs_hook=_no_dups)


def read_text(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write_text(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


# ---------- canonical layout ----------
def _j(v):
    return json.dumps(v, ensure_ascii=False)


def _order(rec, kind):
    keys = FIELDS[kind]
    out = [(k, rec[k]) for k in keys if k in rec]
    out += [(k, v) for k, v in rec.items() if k not in keys]   # unknown fields keep their place at the end
    return out


def _sub(kind_of, key):
    return {'stance': 'stance', 'also': 'ref', 'moves': 'move', 'ctl': 'ctl', 'check': 'check',
            'geo': 'geo', 'ctl0': 'ctl0', 'doc': 'doc'}.get(key)


def _flat(obj, kind):
    """One-line JSON for a nested object, with its keys in canonical order."""
    if not isinstance(obj, dict):
        return _j(obj)
    parts = []
    for k, v in _order(obj, kind):
        if k == 'cf' and isinstance(v, list):
            v = [OrderedDict(_order(x, 'ref')) if isinstance(x, dict) else x for x in v]
        parts.append(f'{_j(k)}: {_j(v)}')
    return '{' + ', '.join(parts) + '}'


def dump_record(rec, kind):
    head, tail = [], []
    for k, v in _order(rec, kind):
        if k in NESTED_LIST and isinstance(v, list):
            sub = _sub(kind, k)
            items = ',\n  '.join(_flat(x, sub) for x in v)
            tail.append(f'{_j(k)}: [\n  {items}]' if v else f'{_j(k)}: []')
        elif k in NESTED_ONE and isinstance(v, dict):
            tail.append(f'{_j(k)}: {_flat(v, _sub(kind, k))}')
        elif k in PROSE:
            tail.append(f'{_j(k)}: {_j(v)}')
        else:
            head.append(f'{_j(k)}: {_j(v)}')
    lines = ['{' + ', '.join(head)] if head else ['{']
    if tail:
        lines[0] += ','
        lines += [' ' + x + ',' for x in tail[:-1]] + [' ' + tail[-1] + '}']
    else:
        lines[0] += '}'
    return '\n'.join(lines)


def dump_table(records, kind):
    if not records:
        return '[]\n'
    return '[\n' + ',\n'.join(dump_record(r, kind) for r in records) + '\n]\n'


def dump_meta(obj):
    meta = OrderedDict(_order(obj.get('meta', {}), 'meta'))
    out = ['{', ' "meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace('\n', '\n ') + ',']
    days = obj.get('days', [])
    out.append(' "days": [\n  ' + ',\n  '.join(_flat(d, 'day') for d in days) + ']' if days else ' "days": []')
    extra = [k for k in obj if k not in ('meta', 'days')]
    for k in extra:   # unknown top-level keys survive formatting so the validator can report them
        out[-1] += ','
        out.append(f' {_j(k)}: {_j(obj[k])}')
    out.append('}')
    return '\n'.join(out) + '\n'


def canonical(name, obj):
    """The exact text a data file must contain."""
    if name == 'meta':
        return dump_meta(obj)
    kind = {'sources': 'source', 'actors': 'actor', 'places': 'place', 'events': 'event'}[name]
    return dump_table(obj, kind)


def sort_table(name, recs):
    if name == 'events':
        return sorted(recs, key=lambda e: (e.get('t', ''), e.get('id', '')))
    if name == 'places':
        zo = {'city': 0, 'front': 1, 'moscow': 2, 'offmap': 3}
        return sorted(recs, key=lambda p: (zo.get(p.get('zone'), 9), p.get('id', '')))
    if name == 'actors':
        ko = {k: i for i, k in enumerate(['person', 'party', 'organ', 'unit', 'school', 'ship', 'crowd', 'press', 'foreign'])}
        return sorted(recs, key=lambda a: (ko.get(a.get('kind'), 99), a.get('id', '')))
    return sorted(recs, key=lambda s: s.get('id', ''))


# ---------- quotes ----------
def norm(s):
    """The old Raskolnikov norm(), plus ellipsis, en dash and no-break space."""
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('—', '--').replace('–', '-').replace('…', '...').replace('\xa0', ' ')
    s = s.replace('_', '').replace('ï', 'i')
    return re.sub(r'\s+', ' ', s).strip()


def segments(q):
    return q if isinstance(q, list) else [q]


class Book:
    """Reed's text from cache/sections.json: section ids -> normalised text."""

    def __init__(self, data):
        self.data = data
        self.sha256 = data['source']['sha256']
        self.secs = OrderedDict()
        for s in data['sections']:
            self.secs[s['id']] = norm(' '.join(s['paras']))
        self.all = ' '.join(self.secs.values())

    def find(self, sec, q):
        """Positions of q in section sec (both normalised)."""
        t, n = self.secs.get(sec), norm(q)
        if t is None or not n:
            return []
        out, i = [], t.find(n)
        while i != -1:
            out.append(i)
            i = t.find(n, i + 1)
        return out

    def near(self, sec, pos, phrase, span=1500):
        t = self.secs.get(sec, '')
        return norm(phrase) in t[max(0, pos - span): pos + span]


# ---------- dates ----------
MONTHS = {m: i + 1 for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july',
                                          'august', 'september', 'october', 'november', 'december'])}
MONTHS.update({'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9,
               'oct': 10, 'nov': 11, 'dec': 12})
WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
_MON = r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\.?'
_WD = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
_ORD = r'(\d{1,2})(?:st|nd|rd|th|d)?'


def os_to_ns(d):
    return d + dt.timedelta(days=13)   # valid 1900-03-01 .. 2100-02-28


def parse_t(s):
    return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M')


def parse_dp(phrase, cal, ref_date=None):
    """Parse a date phrase. Returns (candidate New Style dates, weekday or None).

    'cal' is the calendar the phrase is written in. A phrase without a month ('the 5th') takes the
    month of ref_date, and the month before, in that calendar. 'Night of X to Y' and any phrase
    mentioning night allow the following day too."""
    p = phrase.lower().replace('\n', ' ')
    wd = re.search(_WD, p)
    weekday = WEEKDAYS.index(wd.group(1)) if wd else None
    year = 1917
    y = re.search(r'\b(191[78])\b', p)
    if y:
        year = int(y.group(1))
    cands = []
    m = re.search(_MON + r'\s+' + _ORD + r'(?:\s*(?:to|-|and)\s*(?:the\s+)?' + _ORD + r')?', p)
    if m:
        mon, d1, d2 = MONTHS[m.group(1)], int(m.group(2)), m.group(3)
        days = [d1] + ([int(d2)] if d2 else [])
        cands = [(year, mon, d) for d in days]
    else:
        m = re.search(_ORD + r'\s+(?:of\s+)?' + _MON, p)
        if m:
            cands = [(year, MONTHS[m.group(2)], int(m.group(1)))]
        else:
            m = re.search(r'\bthe\s+' + _ORD + r'\b', p)
            if m and ref_date is not None:
                base = ref_date - dt.timedelta(days=13) if cal == 'OS' else ref_date
                for mon in (base.month, base.month - 1):
                    if 1 <= mon <= 12:
                        cands.append((year, mon, int(m.group(1))))
    out = []
    for (yy, mm, dd) in cands:
        try:
            d = dt.date(yy, mm, dd)
        except ValueError:
            continue
        d = os_to_ns(d) if cal == 'OS' else d
        out.append(d)
        if 'night' in p:
            out.append(d + dt.timedelta(days=1))
    return sorted(set(out)), weekday


# ---------- time phrases ----------
WORDNUM = {w: i + 1 for i, w in enumerate(['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
                                           'nine', 'ten', 'eleven', 'twelve'])}
_AMPM = r'(a\.?\s?m\.?|p\.?\s?m\.?)'
_NUMW = r'(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)'


def _hour(tok):
    return WORDNUM[tok] if tok in WORDNUM else int(tok)


def _apply(h, mm, ampm, ctx):
    """Candidate 24-hour (h, m) for a 12-hour reading, given an a.m./p.m. marker or context words."""
    if ampm:
        pm = ampm.startswith('p')
        h24 = (h % 12) + (12 if pm else 0)
        return {(h24, mm)}
    if ctx:
        if re.search(r'in the morning|before dawn', ctx):
            return {(h % 12, mm)}
        if re.search(r'in the afternoon|in the evening|p\.?\s?m', ctx):
            return {((h % 12) + 12, mm)}
        if re.search(r'at night|in the night', ctx):
            return {((h % 12) + 12, mm)} if h >= 6 and h != 12 else {(h % 12, mm)}
    if h > 12:
        return {(h, mm)}
    return {(h % 12, mm), ((h % 12) + 12, mm)}


def parse_tp(phrase):
    """Candidate clock times (h, m) a time phrase can mean. Empty set if no clock time is found."""
    p = phrase.lower().replace('\n', ' ')
    ctx = p
    if re.search(r'\bmidnight\b', p):
        return {(0, 0)}
    if re.search(r'\bnoon\b|\bmidday\b', p):
        return {(12, 0)}
    m = re.search(r'(\d{1,2}) minutes (past|after|to) ' + _NUMW + r'(?:\s*' + _AMPM + r')?', p)
    if m:
        mins, h = int(m.group(1)), _hour(m.group(3))
        if m.group(2) == 'to':
            h, mins = h - 1, 60 - mins
        return _apply(h, mins, m.group(4), ctx)
    m = re.search(r'(half|a quarter|quarter)[- ](past|to) ' + _NUMW, p)
    if m:
        h = _hour(m.group(3))
        mins = 30 if m.group(1) == 'half' else 15
        if m.group(2) == 'to':
            h, mins = h - 1, 60 - mins
        return _apply(h, mins, None, ctx)
    m = re.search(r'\b(\d{1,2})[.:](\d{2})\s*' + _AMPM + r'?', p)
    if m:
        return _apply(int(m.group(1)), int(m.group(2)), m.group(3), ctx)
    m = re.search(r'\b(\d{1,2})\s*' + _AMPM, p)
    if m:
        return _apply(int(m.group(1)), 0, m.group(2), ctx)
    m = re.search(r'\b' + _NUMW + r"\s+o['’]?\s?clock", p)
    if m:
        return _apply(_hour(m.group(1)), 0, None, ctx)
    m = re.search(r'\b(?:at|about|toward|towards|by)\s+' + _NUMW + r'\s+(?=in the morning|in the afternoon|in the evening|at night)', p)
    if m:
        return _apply(_hour(m.group(1)), 0, None, ctx)
    return set()


# ---------- geometry ----------
R_EARTH = 6371008.8


def dist_m(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))


def local_xy(origin, p):
    k = math.cos(math.radians(origin[0]))
    return ((p[1] - origin[1]) * 111319.49 * k, (p[0] - origin[0]) * 111319.49)


def in_ring(pt, ring):
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1:
            inside = not inside
    return inside


def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def ring_dist(pt, ring):
    return min(seg_dist(pt, a, b) for a, b in zip(ring, ring[1:] + ring[:1]))


# ---------- sun ----------
def sun_elevation(lat, lon, utc):
    """Solar elevation in degrees (low-precision almanac formula, good to a few hundredths of a
    degree, which is plenty for 'was it dark yet')."""
    n = (utc - dt.datetime(2000, 1, 1, 12)).total_seconds() / 86400.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (280.46061837 + 360.98564736629 * n) % 360
    ha = math.radians(gmst + lon) - ra
    la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha)))
