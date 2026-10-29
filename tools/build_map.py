"""Build the 3D map's geometry (local metres, see mapconf) and a street graph from the OSM tiles.

usage: python3 -I tools/build_map.py CACHE_DIR DATA_DIR OUT_JSON
Reads CACHE_DIR/osm_raw, CACHE_DIR/osm_rel and DATA_DIR/places.json; writes OUT_JSON and
CACHE_DIR/build/graph.pkl. Needs Shapely.

Adapted from Raskolnikov Wandering's build_map.py, with these changes:
- the extent and origin come from mapconf;
- bridges are back-dated to November 1917 (mapconf.NOT_IN_1917). Only ways and relations tagged as
  bridges are matched by name, so ordinary streets with a similar name stay in the streets and the
  graph, and the street centre-lines on a removed bridge are dropped too;
- every building that is one of Reed's places (its `osm` element in places.json) is taken out of
  the merged mesh and written separately under `key`, so the page can light it up and tint it by
  who holds it;
- rings lose consecutive duplicate vertices after rounding to whole metres;
- railway lines are kept, faintly, for the trains Reed takes.
"""
import sys, os, glob, json, math, pickle
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osmload import load
import mapconf
from mapconf import P
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union, polygonize
from shapely.validation import make_valid

S, DATA, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
x0, y0, x1, y1 = mapconf.extent_m()
EXT = box(x0, y0, x1, y1)
print('extent m', round(x0), round(y0), round(x1), round(y1), f'= {(x1 - x0) / 1000:.1f} x {(y1 - y0) / 1000:.1f} km')

os.makedirs(os.path.join(S, 'build'), exist_ok=True)
nodes, ways, rels = load(os.path.join(S, 'osm_raw'), os.path.join(S, 'build/osm_all.pkl'))
for f in glob.glob(os.path.join(S, 'osm_rel/*.osm')):   # full water relations win over the tiles' cut ones
    for ev, el in ET.iterparse(f):
        if el.tag == 'node':
            nodes[int(el.get('id'))] = (float(el.get('lat')), float(el.get('lon')))
        elif el.tag == 'way':
            ways.setdefault(int(el.get('id')), {'n': [int(n.get('ref')) for n in el.findall('nd')], 't': {t.get('k'): t.get('v') for t in el.findall('tag')}})
        elif el.tag == 'relation':
            rels[int(el.get('id'))] = {'m': [(m.get('type'), int(m.get('ref')), m.get('role')) for m in el.findall('member')], 't': {t.get('k'): t.get('v') for t in el.findall('tag')}}

with open(os.path.join(DATA, 'places.json'), encoding='utf-8') as f:
    PLACES = json.load(f)
KEY = {}   # 'way/123' -> place id, for Reed's buildings inside the core
for p in PLACES:
    ref = p.get('osm')
    if ref and p.get('kind') in ('building', 'station', 'complex') and p.get('zone') == 'city' and p.get('ll'):
        x, y = P(*p['ll'])
        if EXT.contains(box(x - 1, y - 1, x + 1, y + 1)):
            KEY[ref] = p


def coords(nids):
    return [P(*nodes[n]) for n in nids if n in nodes]


def mp_polygon(rel):
    """Assemble a multipolygon by polygonizing its member linework (robust to touching rings)."""
    def faces(role_ok):
        lines = []
        for t, r, role in rel['m']:
            if t == 'way' and r in ways and role_ok(role):
                c = coords(ways[r]['n'])
                if len(c) >= 2:
                    lines.append(LineString(c))
        if not lines:
            return None
        polys = list(polygonize(unary_union(lines)))
        return unary_union([make_valid(p) for p in polys]) if polys else None
    outs = faces(lambda role: role in ('outer', ''))
    if outs is None or outs.is_empty:
        return None
    ins = faces(lambda role: role == 'inner')
    if ins is not None and not ins.is_empty:
        outs = outs.difference(ins)
    return outs


def way_polygon(w):
    if len(w['n']) < 4 or w['n'][0] != w['n'][-1]:
        return None
    c = coords(w['n'])
    if len(c) < 4:
        return None
    return make_valid(Polygon(c))


def clean(ring):
    """whole metres, without consecutive duplicates or a closing repeat"""
    out = []
    for x, y in ring:
        q = [round(x), round(y)]
        if not out or q != out[-1]:
            out.append(q)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def polys_of(g):
    return [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']


def q(g, min_area=40):
    out = []
    for p in polys_of(g):
        if p.area < min_area:
            continue
        ext = clean(list(p.exterior.coords))
        if len(ext) < 3:
            continue
        holes = [h for h in (clean(list(r.coords)) for r in p.interiors) if len(h) >= 3 and Polygon(h).area > min_area]
        out.append([ext] + holes)
    return out


def is_removed_bridge(t):
    return (t.get('bridge') not in (None, 'no') or t.get('man_made') == 'bridge') and any(b in t.get('name', '') for b in mapconf.NOT_IN_1917)


# ---------------- water ----------------
water = []
for rid, r in rels.items():
    t = r['t']
    if t.get('type') == 'multipolygon' and (t.get('natural') == 'water' or t.get('waterway') == 'riverbank' or t.get('water')):
        g = mp_polygon(r)
        if g is not None and not g.is_empty:
            water.append(g)
for wid, w in ways.items():
    t = w['t']
    if t.get('natural') == 'water' or t.get('waterway') == 'riverbank':
        g = way_polygon(w)
        if g is not None:
            water.append(g)
WATER = unary_union([g.buffer(0) for g in water]).intersection(EXT.buffer(5))
WATER = WATER.buffer(0.6).buffer(-0.6).simplify(1.2)
LAND = EXT.difference(WATER).buffer(0)
print('water km2', round(WATER.area / 1e6, 3), 'land', round(LAND.area / 1e6, 3))

# ---------------- parks ----------------
parks = []
for rid, r in rels.items():
    t = r['t']
    if t.get('type') == 'multipolygon' and (t.get('leisure') in ('park', 'garden') or t.get('landuse') in ('grass',)):
        g = mp_polygon(r)
        if g is not None:
            parks.append(g)
for wid, w in ways.items():
    t = w['t']
    if t.get('leisure') in ('park', 'garden') or t.get('landuse') in ('grass',) or t.get('natural') == 'wood':
        g = way_polygon(w)
        if g is not None:
            parks.append(g)
PARKS = unary_union([p.buffer(0) for p in parks]).intersection(LAND).simplify(1.5)
PARKS = PARKS.buffer(-0.5).buffer(0.5)


# ---------------- buildings ----------------
def levels(t, area):
    try:
        lv = float(t.get('building:levels', '').split(';')[0])
    except ValueError:
        lv = 4 if area > 300 else 3
    return max(1, min(lv, 6))   # capped: the 1917 skyline had few tall buildings


blds = []
for wid, w in ways.items():
    t = w['t']
    if 'building' not in t or t.get('building') in ('no', 'roof', 'construction', 'ruins'):
        continue
    if t.get('location') == 'underground' or t.get('layer', '0').startswith('-'):
        continue
    g = way_polygon(w)
    if g is not None:
        blds.append((f'way/{wid}', g, t))
for rid, r in rels.items():
    t = r['t']
    if t.get('type') == 'multipolygon' and 'building' in t and t.get('building') not in ('no', 'roof'):
        g = mp_polygon(r)
        if g is not None:
            blds.append((f'relation/{rid}', g, t))

out_b, key = [], []
found = set()
for ref, g, t in blds:
    g = g.intersection(EXT)
    if g.is_empty or g.area < 25:
        continue
    g = g.simplify(0.9, preserve_topology=True)
    kind = 1 if t.get('building') in ('church', 'cathedral', 'chapel') or t.get('amenity') == 'place_of_worship' else 0
    for poly in q(g, 25):
        lv = levels(t, Polygon(poly[0]).area)
        rec = {'o': poly[0], 'h': poly[1:], 'l': lv, 'k': kind}
        if ref in KEY:
            rec['id'] = KEY[ref]['id']
            key.append(rec)
            found.add(ref)
        else:
            out_b.append(rec)

# complexes (Peter-Paul) and buildings whose element is not a building in OSM: their outline
for ref, p in KEY.items():
    if ref in found:
        continue
    typ, num = ref.split('/')
    g = None
    if typ == 'way' and int(num) in ways:
        g = way_polygon(ways[int(num)])
    elif typ == 'relation' and int(num) in rels:
        g = mp_polygon(rels[int(num)])
    if g is None or g.is_empty:
        print('  no footprint in the tiles for', p['id'], ref)
        continue
    for poly in q(g.intersection(EXT).simplify(1.2, preserve_topology=True), 25):
        key.append({'o': poly[0], 'h': poly[1:], 'l': 0, 'k': 2, 'id': p['id']})   # k 2: an area, drawn flat
print('buildings', len(out_b), '; Reed\'s buildings', len(key), 'parts for', len({k['id'] for k in key}), 'places')

# ---------------- bridges standing in 1917 ----------------
brs = []
for rid, r in rels.items():
    t = r['t']
    if t.get('man_made') == 'bridge' and t.get('type') == 'multipolygon' and not is_removed_bridge(t):
        g = mp_polygon(r)
        if g is not None:
            brs.append(g)
for wid, w in ways.items():
    t = w['t']
    if t.get('man_made') == 'bridge' and not is_removed_bridge(t):
        g = way_polygon(w)
        if g is not None:
            brs.append(g)
BRIDGES = unary_union([b.buffer(0) for b in brs]).intersection(EXT).simplify(0.8)

# ---------------- streets and railways ----------------
DRAW = {'primary': 3, 'secondary': 3, 'tertiary': 2, 'residential': 1, 'unclassified': 1, 'living_street': 1, 'pedestrian': 1,
        'primary_link': 2, 'secondary_link': 2, 'tertiary_link': 1}


def lines_in(c):
    ls = LineString(c).intersection(EXT)
    if ls.is_empty:
        return []
    return [ls] if ls.geom_type == 'LineString' else [p for p in getattr(ls, 'geoms', []) if p.geom_type == 'LineString']


streets, rail = [], []
for wid, w in ways.items():
    t = w['t']
    c = coords(w['n'])
    if len(c) < 2:
        continue
    if t.get('highway') in DRAW and t.get('area') != 'yes' and not is_removed_bridge(t):
        for p in lines_in(c):
            streets.append({'c': clean(p.simplify(1.5).coords), 'r': DRAW[t['highway']]})
    elif t.get('railway') == 'rail' and t.get('service') not in ('yard', 'siding', 'spur') and t.get('tunnel') != 'yes':
        for p in lines_in(c):
            rail.append(clean(p.simplify(2.0).coords))
streets = [s for s in streets if len(s['c']) >= 2]
rail = [r for r in rail if len(r) >= 2]
print('street segs', len(streets), 'rail segs', len(rail))

# ---------------- street graph, for foot, cab and motor routes ----------------
WALK = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street', 'pedestrian', 'primary_link',
        'secondary_link', 'tertiary_link', 'service', 'footway', 'path', 'steps', 'track', 'cycleway'}
adj, names = {}, {}   # names: edge -> street name, so a route "up the Morskaya" can stay on it
for wid, w in ways.items():
    t = w['t']
    if t.get('highway') not in WALK or t.get('area') == 'yes' or t.get('indoor') == 'yes' or t.get('access') == 'private':
        continue
    if is_removed_bridge(t):
        continue
    pen = 1.0
    if t.get('highway') in ('service', 'track'):
        if t.get('service') in ('parking_aisle', 'driveway', 'drive-through'):
            continue
        pen = 2.2
    if t.get('highway') in ('footway', 'path', 'cycleway', 'steps'):
        pen = 1.05 if t.get('footway') in ('sidewalk', 'crossing') else 1.8
    if t.get('tunnel') == 'building_passage' or t.get('covered') == 'yes':
        pen = 3.0
    ns = [n for n in w['n'] if n in nodes]
    for a, b in zip(ns, ns[1:]):
        pa, pb = P(*nodes[a]), P(*nodes[b])
        d = math.dist(pa, pb)
        adj.setdefault(a, []).append((b, d * pen, d))
        adj.setdefault(b, []).append((a, d * pen, d))
        if t.get('name') and t.get('highway') not in ('footway', 'path', 'cycleway', 'steps', 'service'):
            names[(a, b) if a < b else (b, a)] = t['name']
print('graph nodes', len(adj), 'named edges', len(names))
with open(os.path.join(S, 'build/graph.pkl'), 'wb') as f:
    pickle.dump({'adj': adj, 'nodes': {n: nodes[n] for n in adj}, 'names': names}, f)

data = {
    'origin': list(mapconf.ORIGIN), 'k': [mapconf.KX, mapconf.KY],
    'ext': [round(x0), round(y0), round(x1), round(y1)],
    'land': q(LAND), 'water': q(WATER), 'parks': q(PARKS),
    'b': out_b, 'key': key, 's': streets, 'rail': rail, 'br': q(BRIDGES),
}
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, separators=(',', ':'))
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
