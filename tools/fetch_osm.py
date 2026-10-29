"""Download the OpenStreetMap data the 3D map is built from.

usage: python3 -I tools/fetch_osm.py CACHE_DIR
Writes CACHE_DIR/osm_raw/*.osm (bbox tiles over mapconf.CORE) and CACHE_DIR/osm_rel/*.osm (the full
versions of every water relation the tiles touch, so rivers and canals close properly).

Adapted from Raskolnikov Wandering's fetcher. It uses the OSM editing API (Overpass and Geofabrik
are not reachable from the build environment), so it is deliberately slow and polite: small tiles,
a pause after every request, and a re-run skips files already present. A tile with too many nodes
(HTTP 400) is split in four.
"""
import sys, os, time, glob, urllib.request, urllib.error
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapconf

CACHE = sys.argv[1]
RAW = os.path.join(CACHE, 'osm_raw')
REL = os.path.join(CACHE, 'osm_rel')
os.makedirs(RAW, exist_ok=True)
os.makedirs(REL, exist_ok=True)
UA = {'User-Agent': 'ten-days-that-shook-the-world/0.2 (literary map; low volume)'}
API = 'https://api.openstreetmap.org/api/0.6'


def get(url, path):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                data = r.read()
            with open(path, 'wb') as f:
                f.write(data)
            print(os.path.basename(path), len(data), flush=True)
            time.sleep(2)
            return True
        except urllib.error.HTTPError as ex:
            if ex.code == 400:
                return False   # too many nodes: the caller splits the tile
            print(os.path.basename(path), 'HTTP', ex.code, flush=True)
            time.sleep(8 * (attempt + 1))   # 509 = bandwidth limit, back off
        except Exception as ex:
            print(os.path.basename(path), 'ERR', ex, flush=True)
            time.sleep(8 * (attempt + 1))
    raise SystemExit('giving up on ' + url)


def tile(name, w, s, e, n):
    path = os.path.join(RAW, name + '.osm')
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    if not get(f'{API}/map?bbox={w:.5f},{s:.5f},{e:.5f},{n:.5f}', path):
        mx, my = (w + e) / 2, (s + n) / 2
        for i, b in enumerate([(w, s, mx, my), (mx, s, e, my), (w, my, mx, n), (mx, my, e, n)]):
            tile(f'{name}_{i}', *b)


def grid(prefix, w, s, e, n, dx, dy):
    i, x = 0, w
    while x < e - 1e-9:
        j, y = 0, s
        while y < n - 1e-9:
            tile(f'{prefix}_{i:02d}_{j:02d}', x, y, min(x + dx, e), min(y + dy, n))
            y += dy
            j += 1
        x += dx
        i += 1


W, S, E, N = mapconf.CORE
grid('core', W, S, E, N, 0.0075, 0.005)

# every water multipolygon the tiles touch, fetched whole
WATER = {'water', 'riverbank'}
rels = set()
for f in sorted(glob.glob(os.path.join(RAW, '*.osm'))):
    for _, el in ET.iterparse(f):
        if el.tag == 'relation':
            t = {x.get('k'): x.get('v') for x in el.findall('tag')}
            if t.get('type') == 'multipolygon' and (t.get('natural') == 'water' or t.get('waterway') == 'riverbank' or 'water' in t):
                rels.add(int(el.get('id')))
            el.clear()
print('water relations:', len(rels), flush=True)
for rid in sorted(rels):
    path = os.path.join(REL, f'r{rid}.osm')
    if not (os.path.exists(path) and os.path.getsize(path) > 1000):
        get(f'{API}/relation/{rid}/full', path)
print('done')
