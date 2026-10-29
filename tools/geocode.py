"""Find the OSM element and a pin for places whose coordinates are still pending, straight from OSM.

usage: python3 -I tools/geocode.py [--data data] [--cache cache] [--ids ID,…] [--radius M]
       python3 -I tools/geocode.py --accept ID=way/123,ID=relation/456 [--data data] [--cache cache]

A pending place carries a rough hint in `ll` (typed by hand, or a Wikidata P625) and, optionally,
a search string in `geo.q`: an address ("Невский проспект, 33") or a name. Without --accept the
tool fetches the OSM data in a small box around the hint from the OSM API (map call, cached in
CACHE/osm-map) and ranks the buildings, stations, bridges and complexes in it:
  - its footprint contains the hint;
  - its wikidata tag equals the place's wd;
  - its name matches the place's Russian name, or its address matches geo.q;
  - its outline is close to the hint.
A person then picks one. There is no free-text search on purpose: a name searched city-wide finds
the wrong building ("Смольный институт" turns up a modern institute 3 km away).

--accept writes the chosen element into the place (osm if the 1917 building survives, site_osm if
not), moves the pin well inside the footprint if the hint was outside, and records
geo = {m: "osm", at, q, osm_v, on}. Then run check_story.py --osm.

The OSM API is an editing API: keep to small boxes, one request a second, and cache everything.
"""
import sys, os, re, json, time, argparse, urllib.request, urllib.error, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib as L
import check_story as C

LOOKUP_KINDS = {'building', 'station', 'complex', 'bridge'}
WANT = ('building', 'railway', 'bridge', 'man_made', 'historic', 'amenity', 'tourism', 'landuse', 'military')
LINES = ('subway', 'tram', 'rail', 'light_rail', 'narrow_gauge', 'platform')


def osm_map(cache, ll, radius):
    """All OSM elements in a box of +-radius metres around ll, from the API's map call."""
    dlat = radius / 111320.0
    dlon = radius / (111320.0 * max(0.2, abs(__import__('math').cos(__import__('math').radians(ll[0])))))
    w, s, e, n = ll[1] - dlon, ll[0] - dlat, ll[1] + dlon, ll[0] + dlat
    key = f'{w:.5f},{s:.5f},{e:.5f},{n:.5f}'
    path = os.path.join(cache, 'osm-map', key + '.json')
    if os.path.exists(path):
        return json.loads(L.read_text(path))
    url = f'{C.OSM_API}/map.json?bbox={key}'
    req = urllib.request.Request(url, headers={'User-Agent': C.UA})
    for wait in (30, 120, None):
        time.sleep(1.0)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode('utf-8'))
            break
        except urllib.error.HTTPError as ex:
            if ex.code not in (429, 509) or wait is None:
                raise
            print(f'  (HTTP {ex.code} from the OSM API; waiting {wait} s)', file=sys.stderr)
            time.sleep(wait)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    L.write_text(path, json.dumps(data))
    return data


def address(q):
    """'Невский проспект, 33' -> ('невский проспект', '33'); anything else -> None."""
    m = re.match(r'^\s*(.+?),\s*(\d+[а-яА-Я]?(?:[/-]\d+)?)\s*$', q or '')
    return (m.group(1).lower(), m.group(2).lower()) if m else None


def candidates(cache, p, radius):
    data = osm_map(cache, p['ll'], radius)
    els = data['elements']
    nodes = {e['id']: (e['lat'], e['lon']) for e in els if e['type'] == 'node'}
    ways = {e['id']: e for e in els if e['type'] == 'way'}
    ru = (p.get('ru') or '').lower()
    addr = address(p.get('geo', {}).get('q'))
    out = []
    for e in els:
        if e['type'] not in ('way', 'relation'):
            continue
        t = e.get('tags', {})
        if not any(k in t for k in WANT) or (t.get('railway') in LINES and 'building' not in t):
            continue
        if e['type'] == 'relation' and t.get('type') not in ('multipolygon', 'building', None):
            continue
        ref = f'{e["type"]}/{e["id"]}'
        if e['type'] == 'way':
            if len(e.get('nodes', [])) < 4 or e['nodes'][0] != e['nodes'][-1]:
                continue   # an open way is a line, not a footprint
            rings = [[nodes[n] for n in e.get('nodes', []) if n in nodes]]
        else:   # the map call may cut a relation's outline at the box edge, so fetch it whole
            full = C.osm_fetch(cache, ref, C.Findings(), p['id'])
            if full is None:
                continue
            _, rings, _ = C.rings_of(full, ref)
        rings = [r for r in rings if len(r) > 2]
        if not rings:
            continue
        xy = lambda r: [L.local_xy(p['ll'], q) for q in r]
        inside = any(L.in_ring((0.0, 0.0), xy(r)) for r in rings)
        d = 0.0 if inside else min(L.ring_dist((0.0, 0.0), xy(r)) for r in rings)
        name = (t.get('name') or '').lower()
        why, score = [], 0
        if inside:
            why.append('contains hint'); score += 3
        if any(k in t for k in ('building', 'man_made', 'historic')) or t.get('railway') == 'station':
            score += 1
        if p.get('wd') and t.get('wikidata') == p['wd']:
            why.append('wikidata'); score += 5
        if ru and name and (ru in name or name in ru):
            why.append('name'); score += 3
        hn = re.match(r'\d+', t.get('addr:housenumber', ''))
        if addr and t.get('addr:street', '').lower() == addr[0] and hn and hn.group() == re.match(r'\d+', addr[1]).group():
            why.append('address'); score += 4
        score -= d / 100.0
        out.append((score, ref, d, t, why))
    return sorted(out, key=lambda x: -x[0])[:6]


def show(p, cands):
    print(f'\n== {p["id"]} ({p["kind"]}, exists={p.get("exists")}) hint {p["ll"]}  wd={p.get("wd")}  q={p.get("geo", {}).get("q")!r}')
    if not cands:
        print('  no building-like element near the hint; widen --radius or place it by hand')
    for score, ref, d, t, why in cands:
        kind = next((f'{k}={t[k]}' for k in WANT if k in t), '')
        adr = ' '.join(x for x in (t.get('addr:street', ''), t.get('addr:housenumber', '')) if x)
        print(f'  {score:5.1f} {ref:20} {kind:28} {d:5.0f} m  {t.get("wikidata", ""):10} {t.get("name", "")[:34]:34} {adr[:30]}  [{", ".join(why)}]')


def inside_point(hint, rings):
    """A point well inside the footprint: on a 40×40 grid over the ring nearest the hint, the grid
    point farthest from any edge. (A vertex average can fall outside an L- or U-shaped building.)"""
    best = None
    for r in rings:
        if len(r) < 3:
            continue
        la, lo = [q[0] for q in r], [q[1] for q in r]
        xy = [L.local_xy(hint, q) for q in r]
        near = L.ring_dist((0.0, 0.0), xy)
        for i in range(1, 40):
            for j in range(1, 40):
                p = (min(la) + (max(la) - min(la)) * i / 40, min(lo) + (max(lo) - min(lo)) * j / 40)
                pxy = L.local_xy(hint, p)
                if L.in_ring(pxy, xy):
                    score = (near, -L.ring_dist(pxy, xy))   # prefer the ring nearest the hint, then depth
                    if best is None or score < best[0]:
                        best = (score, [round(p[0], 6), round(p[1], 6)])
    return best[1] if best else None


def accept(args):
    places = L.load_json(os.path.join(args.data, 'places.json'))
    byid = {p['id']: p for p in places}
    F = C.Findings()
    for pair in args.accept.split(','):
        pid, ref = pair.split('=')
        p = byid[pid]
        data = C.osm_fetch(args.cache, ref, F, pid)
        if data is None:
            print('missing', ref)
            continue
        me, rings, points = C.rings_of(data, ref)
        ll, at = p['ll'], 'hint'
        if rings:
            inside = any(L.in_ring((0.0, 0.0), [L.local_xy(ll, q) for q in r]) for r in rings if len(r) > 2)
            if not inside:
                ll = inside_point(ll, rings)
                if ll is None:
                    print(f'{pid}: could not find a point inside {ref}; left unchanged')
                    continue
                at = ref
        elif points:
            ll, at = [round(points[0][0], 6), round(points[0][1], 6)], ref
        key = 'osm' if p.get('exists') is not False else 'site_osm'
        p.pop('osm', None)
        p.pop('site_osm', None)
        p[key] = ref
        p['ll'] = [round(ll[0], 6), round(ll[1], 6)]
        g = {'m': 'osm', 'at': at}
        if p.get('geo', {}).get('q'):
            g['q'] = p['geo']['q']
        g['osm_v'] = me.get('version')
        g['on'] = str(dt.date.today())
        p['geo'] = g
        print(f'{pid}: {key}={ref} ll={p["ll"]} (pin {"kept: the hint lies inside" if at == "hint" else "moved inside the footprint"})')
    L.write_text(os.path.join(args.data, 'places.json'), L.canonical('places', L.sort_table('places', places)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data')
    ap.add_argument('--cache', default='cache')
    ap.add_argument('--ids')
    ap.add_argument('--radius', type=float, default=250.0, help='half-width of the box around the hint, metres')
    ap.add_argument('--accept')
    args = ap.parse_args()
    if args.accept:
        return accept(args)
    places = L.load_json(os.path.join(args.data, 'places.json'))
    want = set(args.ids.split(',')) if args.ids else None
    for p in places:
        if want is not None and p['id'] not in want:
            continue
        if want is None and p.get('geo', {}).get('m') != 'pending':
            continue
        if not p.get('ll') or p.get('kind') not in LOOKUP_KINDS:
            print(f'\n== {p["id"]}: {p.get("kind")} — no lookup; place it by hand (geo.m "hand")')
            continue
        show(p, candidates(args.cache, p, args.radius))


if __name__ == '__main__':
    main()
