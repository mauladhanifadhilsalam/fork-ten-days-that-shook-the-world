"""Turn the checked data into what the page draws: scenes, places in local metres, routes, control.

usage: python3 -I tools/build_story.py DATA_DIR MAP_JSON GRAPH_PKL OUT_JSON
Run tools/check_story.py first: this script trusts the data and only shapes it for the page.
Needs Shapely (for the shortcut test, as in Raskolnikov Wandering).

Routes. A move's points are its `from`, its `via` and its `to`.
- rc "stated" or "inferred", by foot, march, cab, car, truck, armoured car, cavalry or tram, inside
  the city core: routed along today's streets, minus the bridges built after 1917. The routing
  helpers (snapping onto street segments, Dijkstra, loop and hairpin removal, rounded corners) are
  Raskolnikov Wandering's.
- rail, ship, a mode Reed does not give, rc "none", or anything leaving the core: straight lines
  through the points. The page draws those as arcs, so nobody mistakes them for a street route.

The tour is Petrograd's: scenes Reed sets at the front, in Moscow or further off stay in the data
(and in the checks) but are left out of the page. Moves that leave the city are still drawn.

Presence. Who stands where between scenes comes from storylib.presence_spans; here each span gets
what the page needs to draw it: which figures, how many, and what kit. Those are display rules, not
data: the body (a unit, a crowd, a ship) and Reed's phrase for its size decide the figures.
"""
import sys, os, re, json, math, heapq, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib as L
from mapconf import P
from shapely.geometry import Polygon as _Poly, LineString as _Line
from shapely.strtree import STRtree

DATA, MAP, GRAPH, OUT = sys.argv[1:5]
meta = L.load_json(os.path.join(DATA, 'meta.json'))
T = {k: L.load_json(os.path.join(DATA, k + '.json')) for k in ('sources', 'actors', 'places', 'events')}
PICS = L.load_json(os.path.join(DATA, 'pictures.json')) if os.path.exists(os.path.join(DATA, 'pictures.json')) else []
with open(MAP, encoding='utf-8') as f:
    M = json.load(f)
with open(GRAPH, 'rb') as f:
    G = pickle.load(f)
x0, y0, x1, y1 = M['ext']
FAR_KM = 60   # beyond this a place is an off-map card, not a pin on the plain

# ---------- routing (Raskolnikov Wandering's helpers) ----------
adj, gnodes, enames = G['adj'], G['nodes'], G.get('names', {})
pts = {n: P(*ll) for n, ll in gnodes.items()}
CELL = 50.0
edges = {}
for u, lst in adj.items():
    for v, w, d in lst:
        k = (u, v) if u < v else (v, u)
        if k not in edges and d > 0:
            edges[k] = (w / d, d)
# snap only onto the main street network: a courtyard path that touches nothing else would leave
# the router stranded (the Duma's pin sits inside the building, nearest to such a path)
main, best = set(), set()
for start in adj:
    if start in main:
        continue
    comp, stack = {start}, [start]
    while stack:
        u = stack.pop()
        for v, _, _ in adj.get(u, ()):
            if v not in comp:
                comp.add(v)
                stack.append(v)
    main |= comp
    if len(comp) > len(best):
        best = comp
edges = {k: v for k, v in edges.items() if k[0] in best}
egrid = {}
for (u, v) in edges:
    (ax, ay), (bx, by) = pts[u], pts[v]
    for cx in range(int(min(ax, bx) // CELL), int(max(ax, bx) // CELL) + 1):
        for cy in range(int(min(ay, by) // CELL), int(max(ay, by) // CELL) + 1):
            egrid.setdefault((cx, cy), []).append((u, v))


def snap(x, y, name=None):
    """nearest point on any street segment, or on the street called `name`: (u, v, t, (px, py), distance)"""
    cx, cy = int(x // CELL), int(y // CELL)
    best = None
    for r in range(0, 40 if name else 12):
        for i in range(cx - r, cx + r + 1):
            for j in range(cy - r, cy + r + 1):
                if max(abs(i - cx), abs(j - cy)) != r:
                    continue
                for (u, v) in egrid.get((i, j), ()):
                    if name and enames.get((u, v) if u < v else (v, u)) != name:
                        continue
                    (ax, ay), (bx, by) = pts[u], pts[v]
                    dx, dy = bx - ax, by - ay
                    L2 = dx * dx + dy * dy or 1e-9
                    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
                    px, py = ax + t * dx, ay + t * dy
                    d = math.hypot(px - x, py - y)
                    if best is None or d < best[4]:
                        best = (u, v, t, (px, py), d)
        if best is not None and best[4] < r * CELL:
            break
    return best


def route(pa, pb):
    """shortest street path between two arbitrary points, entering and leaving the graph mid-edge"""
    ua, va, ta, qa, _ = snap(*pa)
    ub, vb, tb, qb, _ = snap(*pb)
    return route_from(ua, va, ta, qa, ub, vb, tb, qb)


def route_from(ua, va, ta, qa, ub, vb, tb, qb):
    pen_a, La = edges[(ua, va) if ua < va else (va, ua)]
    pen_b, Lb = edges[(ub, vb) if ub < vb else (vb, ub)]
    dist, prev = {ua: ta * La * pen_a, va: (1 - ta) * La * pen_a}, {ua: None, va: None}
    h = [(dist[ua], ua), (dist[va], va)]
    heapq.heapify(h)
    done = set()
    while h and not (ub in done and vb in done):
        d, u = heapq.heappop(h)
        if u in done:
            continue
        done.add(u)
        for v, w, l in adj.get(u, ()):
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v], prev[v] = nd, u
                heapq.heappush(h, (nd, v))
    options = []
    if ub in dist:
        options.append((dist[ub] + tb * Lb * pen_b, ub))
    if vb in dist:
        options.append((dist[vb] + (1 - tb) * Lb * pen_b, vb))
    if {ua, va} == {ub, vb}:
        tb2 = tb if (ua, va) == (ub, vb) else 1 - tb
        options.append((abs(ta - tb2) * La * pen_a, None))
    if not options:
        return None
    cost, endn = min(options)
    if endn is None:
        return [qa, qb]
    chain = [endn]
    while prev[chain[-1]] is not None:
        chain.append(prev[chain[-1]])
    return [qa] + [pts[n] for n in chain[::-1]] + [qb]


def plen(p):
    return sum(math.dist(a, b) for a, b in zip(p, p[1:]))


def rdp(p, eps):
    if len(p) < 3:
        return p
    (ax, ay), (bx, by) = p[0], p[-1]
    dx, dy = bx - ax, by - ay
    Ln = math.hypot(dx, dy)
    dmax, idx = 0, 0
    for i in range(1, len(p) - 1):
        d = math.dist(p[i], p[0]) if Ln < 1e-6 else abs(dy * p[i][0] - dx * p[i][1] + bx * ay - by * ax) / Ln
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(p[:idx + 1], eps)[:-1] + rdp(p[idx:], eps)
    return [p[0], p[-1]]


def dedupe(p):
    out = [p[0]]
    for q in p[1:]:
        if math.dist(q, out[-1]) > 0.3:
            out.append(q)
    return out


def cut_loops(p):
    """drop short out-and-back excursions: the path returns to a point it already visited"""
    limit = min(80.0, 0.3 * plen(p))
    changed = True
    while changed:
        changed = False
        cum = [0.0]
        for a, b in zip(p, p[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        cells = {}
        for i, q in enumerate(p):
            cells.setdefault((int(q[0] // 4), int(q[1] // 4)), []).append(i)
        for i, q in enumerate(p):
            cx, cy = int(q[0] // 4), int(q[1] // 4)
            far = None
            for a in (cx - 1, cx, cx + 1):
                for b in (cy - 1, cy, cy + 1):
                    for j in cells.get((a, b), ()):
                        if j > i + 1 and math.dist(q, p[j]) < 3.0 and 6 < cum[j] - cum[i] < limit:
                            far = j if far is None else max(far, j)
            if far is not None:
                p = p[:i + 1] + p[far + 1:]
                changed = True
                break
    return p


def turn(a, b, c):
    v1 = (b[0] - a[0], b[1] - a[1]); v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return 0.0, n1, n2
    cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cosv)), n1, n2


def cut_uturns(p, keep):
    changed = True
    while changed and len(p) > 2:
        changed = False
        for i in range(1, len(p) - 1):
            if i in keep:
                continue
            ang, n1, n2 = turn(p[i - 1], p[i], p[i + 1])
            if ang > 150 and min(n1, n2) < 40:
                p = p[:i] + p[i + 1:]
                keep = {k - 1 if k > i else k for k in keep}
                changed = True
                break
    return p


_obst = []
for bld in M['b'] + M['key']:
    if len(bld['o']) >= 3 and bld.get('k') != 2:
        _obst.append(_Poly(bld['o']).buffer(-0.5))
for poly in M['water']:
    if len(poly[0]) >= 3:
        _obst.append(_Poly(poly[0], [h for h in poly[1:] if len(h) >= 3]).buffer(-0.5))
_obst = [g for g in _obst if not g.is_empty and g.is_valid]
_tree = STRtree(_obst)


def clear(a, b):
    ln = _Line([a, b])
    return not any(_obst[i].intersects(ln) for i in _tree.query(ln))


def shortcuts(p):
    changed = True
    while changed:
        changed = False
        cum = [0.0]
        for a, b in zip(p, p[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        for i in range(1, len(p) - 2):
            for j in range(min(len(p) - 2, i + 80), i + 1, -1):
                d = math.dist(p[i], p[j])
                if d < 35 and cum[j] - cum[i] > 3 * d + 40 and clear(p[i], p[j]):
                    p = p[:i + 1] + p[j:]
                    changed = True
                    break
            if changed:
                break
    return p


def round_corners(p, rmax=9.0, steps=5):
    if len(p) < 3:
        return p
    out = [p[0]]
    for i in range(1, len(p) - 1):
        a, b, c = p[i - 1], p[i], p[i + 1]
        ang, n1, n2 = turn(a, b, c)
        if ang < 12:
            out.append(b)
            continue
        r = min(rmax, 0.4 * n1, 0.4 * n2)
        s0 = (b[0] - (b[0] - a[0]) / n1 * r, b[1] - (b[1] - a[1]) / n1 * r)
        s1 = (b[0] + (c[0] - b[0]) / n2 * r, b[1] + (c[1] - b[1]) / n2 * r)
        for k in range(steps + 1):
            t = k / steps
            out.append(((1 - t) ** 2 * s0[0] + 2 * (1 - t) * t * b[0] + t * t * s1[0],
                        (1 - t) ** 2 * s0[1] + 2 * (1 - t) * t * b[1] + t * t * s1[1]))
    out.append(p[-1])
    return dedupe(out)


def in_core(xy):
    return xy is not None and x0 <= xy[0] <= x1 and y0 <= xy[1] <= y1


# ---------- places ----------
PL = {}
for p in T['places']:
    xy = P(*p['ll']) if p.get('ll') else None
    rec = {k: p[k] for k in ('name', 'kind', 'zone', 'conf', 'acc', 'exists', 'ru', 'addr1917', 'addr_now', 'ident', 'today', 'note', 'in') if k in p}
    rec['reed'] = p['reed'][0]
    if p.get('stage'):
        sx, sy = P(*p['stage'])
        rec['stage'] = [round(sx, 1), round(sy, 1)]
    if xy:
        dist = math.hypot(*xy) / 1000
        rec['p'] = [round(xy[0], 1), round(xy[1], 1)]
        rec['core'] = in_core(xy)
        if dist > FAR_KM:
            rec['far'] = True
        if not rec['core']:
            bearing = (math.degrees(math.atan2(xy[0], xy[1])) + 360) % 360
            rec['off'] = {'km': round(dist), 'dir': ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'][int((bearing + 22.5) // 45) % 8]}
    PL[p['id']] = rec

# ---------- moves ----------
STREET_MODES = {'foot', 'march', 'cab', 'car', 'truck', 'armoured', 'cavalry', 'tram'}


def point(ref):
    if isinstance(ref, str):
        return P(*T_places[ref]['ll']) if T_places[ref].get('ll') else None
    return P(*ref)


T_places = {p['id']: p for p in T['places']}
stats = {'routed': 0, 'straight': 0, 'unlocated': 0, 'routed_m': 0.0}


PASSED = {'building', 'complex', 'station', 'room'}   # landmarks a route goes by, not into


def shape(m):
    seq = [m['from']] + list(m.get('via', [])) + [m['to']]
    xy = [point(r) for r in seq]
    if any(q is None for q in xy):
        stats['unlocated'] += 1
        return None, 'unlocated'
    if m['from'] == m['to'] and not m.get('via'):
        return None, 'stays'
    routed = m['rc'] in ('stated', 'inferred') and m['mode'] in STREET_MODES and all(in_core(q) for q in xy)
    if not routed:
        stats['straight'] += 1
        return [[round(a, 1), round(b, 1)] for a, b in xy], 'straight'
    # a building named as a waypoint ("in front of the Kazan Cathedral") is passed, not entered: the
    # street route between its neighbours goes by it, while its pin would pull the route round its back
    keep = [0] + [i for i in range(1, len(seq) - 1) if not (isinstance(seq[i], str) and T_places[seq[i]].get('kind') in PASSED)] + [len(seq) - 1]
    seq, xy = [seq[i] for i in keep], [xy[i] for i in keep]
    # a street named as a waypoint ("up the Morskaya") is entered at its nearest point to its pin
    for i, r in enumerate(seq):
        pl = T_places.get(r) if isinstance(r, str) else None
        if pl and pl.get('kind') == 'street' and pl.get('ru'):
            s = snap(*xy[i], name=pl['ru'])
            if s and s[4] < 400:
                xy[i] = s[3]
    full = [xy[0]]
    for a, b in zip(xy, xy[1:]):
        leg = route(a, b)
        if leg is None:
            print(f"  no street route for {m['who']} {m['from']} -> {m['to']}: leg {[round(v) for v in a]} -> {[round(v) for v in b]}")
            stats['straight'] += 1
            return [[round(a, 1), round(b, 1)] for a, b in xy], 'straight'
        full += leg
    full.append(xy[-1])
    full = dedupe(full)
    full = cut_loops(full)
    full = rdp(full, 2.0)
    roundtrip = m['from'] == m['to']
    if not roundtrip:
        full = shortcuts(full)
    full = cut_uturns(full, keep=set(range(1, len(full) - 1)) if roundtrip else set())
    full = round_corners(full)
    stats['routed'] += 1
    stats['routed_m'] += plen(full)
    return [[round(a, 1), round(b, 1)] for a, b in full], 'street'


# ---------- figures ----------
# what each body is drawn as: figure types and their shares (the page models each type)
ACTOR_FIG = {
    'red-guards': [('redguard', 1)], 'sailors': [('sailor', 1)], 'cyclists': [('soldier', 1)],
    'garrison': [('soldier', 1)], 'pavlovsky': [('soldier', 1)], 'semionovsky': [('soldier', 1)],
    'peter-paul-garrison': [('soldier', 1)], 'tsarskoye-rifles': [('soldier', 1)],
    'pulkovo-detachment': [('redguard', .4), ('sailor', .3), ('soldier', .3)],
    'petrograd-cossacks': [('cossack', 1)], 'krasnov-cossacks': [('cossack', 1)], 'armoured-cars': [('soldier', 1)],
    'womens-battalion': [('womansoldier', 1)],
    'yunkers': [('yunker', 1)], 'vladimir-yunkers': [('yunker', 1)], 'engineers-yunkers': [('yunker', 1)],
    'pavlovsk-yunkers': [('yunker', 1)],
    'workers': [('worker', .5), ('workerwoman', .35), ('child', .15)],
    'duma-procession': [('bourgeois', .5), ('bourgeoiswoman', .2), ('intelligent', .3)],
    'peasants-congress': [('peasant', .75), ('soldier', .25)],
}
BLOC_FIG = {
    'soviet': [('soldier', .35), ('sailor', .25), ('redguard', .25), ('worker', .15)],
    'government': [('officer', .5), ('bourgeois', .5)],
    'opposition': [('bourgeois', .5), ('intelligent', .4), ('bourgeoiswoman', .1)],
    'neutral': [('soldier', 1)],
    'public': [('worker', .3), ('workerwoman', .25), ('bourgeois', .2), ('bourgeoiswoman', .1), ('intelligent', .1), ('child', .05)],
}
# Reed's own words for a body, when he gives them, override the default figures: the specific words
# name who they are; the generic ones (women, children) only add to the mix
SIZE_FIG = [(r'sailor', 'sailor'), (r'soldier|troops|regiment|infantry', 'soldier'), (r'red guard', 'redguard'),
            (r'yunker', 'yunker'), (r'cossack', 'cossack'), (r'workmen|workers', 'worker'), (r'peasant', 'peasant'),
            (r'officer', 'officer'), (r'student', 'intelligent'), (r'bourgeois|fifth avenue|fur coat|shop-keeper|clerk', 'bourgeois')]
SIZE_ADD = [(r"\bwomen\b(?!.s battalion)", 'workerwoman'), (r'child', 'child')]
DEFAULT_N = {'unit': 24, 'school': 28, 'crowd': 60, 'organ': 14, 'party': 12, 'ship': 1, 'person': 1, 'press': 4, 'foreign': 3}
NUMW = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'fifteen': 15, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
        'seventy': 70, 'eighty': 80, 'ninety': 90, 'several': 3, 'few': 3, 'dozen': 12, 'hundreds': 300, 'thousands': 3000}


def size_number(phrase):
    """'about two thousand citizens' -> 2000; 'two or three hundred' -> 250; 'five or six' -> 5.5; None if no number"""
    p = phrase.lower().replace('-', ' ')
    vals, cur, mult = [], None, 1
    for w in re.findall(r"[a-z]+|\d+", p):
        if w.isdigit():
            cur = int(w)
            vals.append(cur)
        elif w in NUMW:
            vals.append(NUMW[w])
        elif w in ('hundred', 'thousand'):
            m = 100 if w == 'hundred' else 1000
            if vals:
                vals = [v * m if v < m else v for v in vals]
            else:
                vals = [m]
        elif w in ('company', 'companies'):
            mult = 100
    if not vals:
        return None
    return sum(vals) / len(vals) * (mult if mult > 1 else 1)


def figures(who, size=None, n=None):
    """(composition [[type, share]], how many to draw) for a body of people"""
    a = T_actors.get(who, {})
    comp = ACTOR_FIG.get(who) or BLOC_FIG.get(a.get('bloc'), BLOC_FIG['public'])
    if size:
        low = size.lower()
        hits = [fig for rx, fig in SIZE_FIG if re.search(rx, low)]
        if hits and not (who in ACTOR_FIG and set(hits) <= {f for f, _ in ACTOR_FIG[who]}):
            comp = [(f, 1 / len(hits)) for f in dict.fromkeys(hits)]
        extra = [fig for rx, fig in SIZE_ADD if re.search(rx, low) and fig not in {f for f, _ in comp}]
        if extra:
            comp = [(f, w * 0.75) for f, w in comp] + [(f, 0.25 / len(extra)) for f in extra]
    if n is None:
        num = size_number(size) if size else None
        n = round(min(150, max(4, 3.2 * math.sqrt(num)))) if num else DEFAULT_N.get(a.get('kind'), 12)
    return [[f, round(w, 3)] for f, w in comp], n


T_actors = {a['id']: a for a in T['actors']}
events_all = L.sort_table('events', T['events'])
spans, _ = L.presence_spans(events_all, T['actors'], T['places'])
in_tour = [T_places[e['loc']]['zone'] == 'city' for e in events_all]
tour_ix = {}   # full index -> tour index
for i, ok in enumerate(in_tour):
    if ok:
        tour_ix[i] = len(tour_ix)


def to_tour(i):
    """the first tour scene at or after full index i (None past the end)"""
    if i is None:
        return None
    for j in range(i, len(events_all)):
        if j in tour_ix:
            return tour_ix[j]
    return None


presence = []
for sp in spans:
    pl = T_places.get(sp['place'], {})
    if pl.get('zone') != 'city' or not pl.get('ll'):
        continue
    a, b = to_tour(sp['start']), to_tour(sp['end'])
    if a is None or (b is not None and b <= a):
        continue
    kind = T_actors.get(sp['who'], {}).get('kind')
    rec = {'who': sp['who'], 'place': sp['place'], 'from': a, 'to': b, 'ev': sp['ev']}
    if kind == 'ship':
        rec['ship'] = True
    else:
        rec['fig'], rec['n'] = figures(sp['who'], sp.get('size'), sp.get('n'))
    for k in ('size', 'kit'):
        if k in sp:
            rec[k] = sp[k]
    presence.append(rec)

events = []
for e in [e for e, ok in zip(events_all, in_tour) if ok]:
    rec = {k: e[k] for k in ('id', 't', 'tq', 'tr', 'tp', 'cal', 'dp', 'sec', 'p', 'loc', 'witness', 'by', 'actors', 'tags', 'title', 'why', 'sum') if k in e}
    rec['q'] = ' … '.join(L.segments(e['q']))
    if e.get('also'):
        rec['also'] = [{'sec': a['sec'], 'q': ' … '.join(L.segments(a['q']))} for a in e['also']]
    if e.get('doc'):
        rec['doc'] = e['doc']
    mv = []
    for m in e.get('moves', []):
        r = {k: m[k] for k in ('who', 'with', 'size', 'from', 'via', 'to', 'mode', 'rc', 'gap', 'stay', 'kit') if k in m}
        if T_actors.get(m['who'], {}).get('kind') not in ('person', 'ship'):
            r['fig'], r['n'] = figures(m['who'], m.get('size'), m.get('n'))
        wf = [list(figures(w)) for w in m.get('with', []) if T_actors.get(w, {}).get('kind') not in ('person', 'ship')]
        if wf:
            r['wfig'] = wf
        line, kind = shape(m)
        r['line'], r['draw'] = line, kind
        if line:
            r['len'] = round(plen(line))
        mv.append(r)
    if mv:
        rec['moves'] = mv
    if e.get('ctl'):
        rec['ctl'] = e['ctl']
    # pictures for the card: Reed's own facsimiles carry his caption; the rest, ours, with a credit
    pics = []
    for p in PICS:
        if e['id'] not in p.get('scenes', []):
            continue
        r = {'f': p['file'], 'w': p['w'], 'h': p['h'], 'k': p['kind'], 't': p.get('title', ''), 'lic': p['license'], 'url': p['url']}
        if p.get('ref'):
            r['cap'], r['sec'] = p['ref']['q'], p['ref']['sec']
        else:
            r['cap'], r['by'], r['date'] = p['caption'], p.get('author', ''), p.get('date', '')
        pics.append(r)
    if pics:
        rec['pics'] = pics
    events.append(rec)
print(f"tour: {len(events)} of {len(events_all)} scenes (Petrograd only); presence spans {len(presence)} of {len(spans)}")

# ---------- control timelines ----------
control = {}
for p in T['places']:
    if p.get('ctl0'):
        c = p['ctl0']
        control[p['id']] = [{'t': c['as_of'] + ('T00:00' if len(c['as_of']) == 10 else ''), 'ev': c.get('ev'), **{k: c[k] for k in ('state', 'holder', 'by') if k in c}}]
for e in T['events']:
    for c in e.get('ctl', []):
        control.setdefault(c['place'], []).append({'t': e['t'], 'ev': e['id'], **{k: c[k] for k in ('state', 'holder', 'by') if k in c}})
for tl in control.values():
    tl.sort(key=lambda c: c['t'])

actors = {}
for a in T['actors']:
    actors[a['id']] = {k: a[k] for k in ('name', 'kind', 'bloc', 'track', 'ru', 'note') if k in a}
    actors[a['id']]['reed'] = a['reed'][0]
    if a.get('stance'):
        actors[a['id']]['stance'] = [{'from': s['from'], 's': s['s']} for s in a['stance']]

story = {
    'meta': {'title': meta['meta']['title'], 'clock': {k: v['offset_min'] for k, v in meta['meta']['clock'].items()},
             'blocs': meta['meta']['blocs'], 'pdf': meta['meta'].get('pdf', {}).get('url'),
             'text': meta['meta']['text']['url']},
    'days': [{k: (d.get('city') or d['name']) if k == 'name' else d[k] for k in ('d', 'os', 'label', 'name')} for d in meta['days']],
    'places': PL, 'actors': actors, 'events': events, 'control': control, 'presence': presence,
}
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(story, f, ensure_ascii=False, separators=(',', ':'))
print(f"events {len(events)}, moves routed {stats['routed']} ({stats['routed_m'] / 1000:.1f} km), straight {stats['straight']}, "
      f"unlocated {stats['unlocated']}; control timelines {len(control)}")
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
