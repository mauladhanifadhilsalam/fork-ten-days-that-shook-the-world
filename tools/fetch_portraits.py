#!/usr/bin/env python3
"""Portraits for the who's who, from Wikimedia Commons, public domain only.

    python3 tools/fetch_portraits.py [--fetch] [--data data] [--cache cache/portraits]

For each person in data/people.json with a `wp` (English Wikipedia) title: the article's lead image, its
Commons licence, author and date. With --fetch these are asked of the Wikipedia and Commons APIs (politely:
one request every 1.5 s, an identifying User-Agent) and kept in cache/portraits/meta.json; without it the
cache is used. A picture is kept only if Commons marks it public domain (or CC0, a public-domain
dedication); its 240-pixel-wide copy is written to media/portrait-<id>.jpg and its record to
data/pictures.json (kind "portrait", no scenes), and the person gets `pic`. Pictures that are not public
domain are reported and left out: the map shows only public-domain pictures.
"""
import argparse, io, json, os, re, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib as L

UA = 'TenDaysMap/1.0 (who\'s who portraits; https://github.com/mauladhanifadhilsalam/raskolnikov-wandering)'
WIDTH = 250   # one of the thumbnail sizes Wikimedia keeps ready (https://w.wiki/GHai); others are made on demand and limited


def get(url, raw=False):
    for k in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=40)
            return r.read() if raw else json.load(r)
        except Exception as e:
            err = e
            time.sleep(5 * (k + 1))
    raise RuntimeError(f'{url}: {err}')


def meta_for(title):
    s = get('https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title))
    time.sleep(1.5)
    img = (s.get('originalimage') or {}).get('source', '')
    if not img:
        return {'title': s.get('title')}
    fn = urllib.parse.unquote(img.split('/')[-1].split('?')[0])
    q = get('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
        'action': 'query', 'titles': 'File:' + fn, 'prop': 'imageinfo', 'iiprop': 'extmetadata|url', 'iiurlwidth': WIDTH, 'format': 'json'}))
    time.sleep(1.5)
    page = list(((q.get('query') or {}).get('pages') or {'-': {}}).values())[0]
    ii = (page.get('imageinfo') or [{}])[0]
    m = ii.get('extmetadata', {})
    strip = lambda k: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', (m.get(k) or {}).get('value', ''))).strip()
    return {'title': s.get('title'), 'file': fn, 'license': strip('LicenseShortName'), 'artist': strip('Artist'),
            'date': strip('DateTimeOriginal'), 'page': ii.get('descriptionurl'), 'thumb': ii.get('thumburl')}


def public_domain(lic):
    return bool(re.match(r'(public domain|pd\b|pd-|cc0)', lic or '', re.I))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data')
    ap.add_argument('--cache', default='cache/portraits')
    ap.add_argument('--fetch', action='store_true')
    a = ap.parse_args()
    root = os.path.dirname(os.path.abspath(a.data))
    os.makedirs(a.cache, exist_ok=True)
    mpath = os.path.join(a.cache, 'meta.json')
    meta = json.load(open(mpath)) if os.path.exists(mpath) else {}
    people = L.load_json(os.path.join(a.data, 'people.json'))
    pics = L.load_json(os.path.join(a.data, 'pictures.json'))
    pics = [p for p in pics if not p['id'].startswith('portrait-')]
    from PIL import Image
    # a portrait a scene card already shows, chosen and dated by hand, comes first ("Lenin, clean-shaven, as
    # Reed saw him"); a fetched one only where there is none
    curated = {q['id']: q for q in pics if q['kind'] == 'portrait'}
    alias = {'lenin': 'lenin-1917', 'trotzky': 'trotsky', 'dybenko': 'dybenko-1920', 'avksentiev': 'avksentiev-reed', 'schreider': 'schreider-reed'}
    kept, left, reused = [], [], []
    for person in people:
        pid, title = person['id'], person.get('wp')
        person.pop('pic', None)
        if alias.get(pid, pid) in curated:
            person['pic'] = alias.get(pid, pid)
            reused.append(pid)
            continue
        if not title and pid not in meta:   # a person with only a Russian article is portrayed from the cache
            continue
        if (a.fetch and title) or pid not in meta:
            if not a.fetch:
                left.append((pid, 'not in the cache; run with --fetch'))
                continue
            meta[pid] = meta_for(title)
            json.dump(meta, open(mpath, 'w'), ensure_ascii=False, indent=1)
        m = meta[pid]
        if not m.get('thumb'):
            left.append((pid, 'no lead image'))
            continue
        if not public_domain(m.get('license')):
            left.append((pid, f'not public domain ({m.get("license") or "no licence given"})'))
            continue
        out = os.path.join(root, 'media', f'portrait-{pid}.jpg')
        if not os.path.exists(out):
            url = re.sub(r'/\d+px-', f'/{WIDTH}px-', m['thumb'])
            try:
                im = Image.open(io.BytesIO(get(url, raw=True))).convert('RGB')
            except Exception as e:
                left.append((pid, f'download failed, try again later ({str(e)[:60]})'))
                continue
            if im.width > WIDTH:
                im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
            im.save(out, 'JPEG', quality=84, optimize=True)
            time.sleep(4)
        w, h = Image.open(out).size
        lic = m['license']
        label = lic if lic.lower().startswith('public domain') else f'Public domain ({lic})'
        pics.append({'id': f'portrait-{pid}', 'kind': 'portrait', 'from': 'commons', 'file': f'media/portrait-{pid}.jpg', 'w': w, 'h': h,
                     'scenes': [], 'license': f'{label} (Wikimedia Commons)',
                     'author': m.get('artist') or 'Unknown', 'date': m.get('date') or 'unknown', 'url': m['page'],
                     'title': person['name'], 'caption': f'{person["name"]}, from the photograph on Wikimedia Commons'})
        person['pic'] = f'portrait-{pid}'
        kept.append(pid)
    with open(os.path.join(a.data, 'pictures.json'), 'w') as fh:
        fh.write(L.canonical('pictures', L.sort_table('pictures', pics)))
    with open(os.path.join(a.data, 'people.json'), 'w') as fh:
        fh.write(L.canonical('people', L.sort_table('people', people)))
    print(f'{len(reused)} portraits from the scene cards, {len(kept)} fetched; {len(left)} left out')
    for pid, why in left:
        print(f'  {pid}: {why}')


if __name__ == '__main__':
    main()
