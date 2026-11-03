#!/usr/bin/env python3
"""Portraits for the who's who, from Wikimedia Commons, public domain only.

    python3 tools/fetch_portraits.py [--fetch | --templates] [--data data] [--cache cache/portraits]

For each person in data/people.json with a `wp` (English Wikipedia) title: the article's lead image, its
Commons licence, author and date. With --fetch these are asked of the Wikipedia and Commons APIs (politely:
one request every 1.5 s, an identifying User-Agent) and kept in cache/portraits/meta.json; without it the
cache is used. A picture is kept only if Commons marks it public domain (or CC0, a public-domain
dedication); its 250-pixel-wide copy is written to media/portrait-<id>.jpg and its record to
data/pictures.json (kind "portrait", no scenes), with the licence rule in words from the file's Commons
templates, and the person gets `pic`. Pictures that are not public
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


# Commons' licence templates, and the rule each states, in words
RULES = [
    (r'PD-RusEmpire', 'published in the Russian Empire before 1917'),
    (r'PD-Russia(-expired|-2008)?$', 'published in Russia, its author dead or unknown before 1943 (Russian law)'),
    (r'PD-Russia-1996', 'published in Russia before 1946, with no author named or the author dead before 1946'),
    (r'PD-USSR', 'published in the Soviet Union, its author dead or unknown before 1943'),
    (r'PD-old-100', 'its author died more than 100 years ago'),
    (r'PD-old-70', 'its author died more than 70 years ago'),
    (r'PD-old-80', 'its author died more than 80 years ago'),
    (r'PD-old$', 'its author died long enough ago for it to be out of copyright'),
    (r'PD-EU-no author disclosure|PD-anon-70', 'published anonymously more than 70 years ago'),
    (r'PD-US-expired|PD-1923|PD-US-1923', 'published in the United States more than 95 years ago'),
    (r'PD-US-no notice|PD-US-not renewed', 'published in the United States without a copyright notice or renewal'),
    (r'PD-US-?gov', 'a work of the United States government'),
    (r'PD-old-auto', 'its author died more than 70 years ago'),
    (r'PD-anon-expired|PD-anon-1923', 'published anonymously more than 95 years ago'),
    (r'PD-Ukraine', 'published in Ukraine, its author dead more than 70 years ago or unknown'),
    (r'PD-Finland', 'a photograph taken in Finland more than 50 years ago'),
    (r'PD-Norway50', 'a photograph taken in Norway more than 50 years ago, before 1969'),
    (r'PD-Sweden-photo', 'a photograph taken in Sweden before 1969'),
    (r'PD-scan', 'a faithful scan of a public-domain work'),
    (r'PD-Art', 'a faithful reproduction of a public-domain painting or drawing'),
    (r'PD-US$', 'out of copyright in the United States, by a rule Commons does not name'),
    (r'CC-zero|Cc-zero', 'dedicated to the public domain by its author (CC0)'),
]
TEMPLATE = re.compile(r'^Template:(PD-[^/]+|CC-zero|Cc-zero)$', re.I)   # not their /en, /lang and /layout parts
NOT_RULES = {'pd-layout', 'pd-notice', 'pd-because', 'pd-textlogo', 'pd-art-category'}
OWN_WORK = re.compile(r'^PD-(self|author|user)', re.I)   # an uploader's claim to have made it: not credible for a 1917 photograph


def licence_templates(templates):
    """the licence templates themselves, not the helpers they call ({{PD-old-text}}, {{PD-old-warning-text}},
    {{PD-US-expired-max-year}}): a helper named after its template stands for it"""
    real = [t for t in templates if not re.search(r'-(text|warning-text|max-year)$|warning|-X-', t, re.I) and t.lower() not in NOT_RULES]
    if not real:   # only the helpers: the template each is named after
        real = [re.sub(r'-(text|warning-text|max-year)$', '', t, flags=re.I) for t in templates if not re.search(r'warning|-X-', t, re.I)]
    out = []
    for t in real:
        if t.lower() not in [o.lower() for o in out]:
            out.append(t)
    if any(re.match(r'PD-old-\d', t, re.I) for t in out):   # the plain {{PD-old}} says less than {{PD-old-70}}
        out = [t for t in out if t.lower() != 'pd-old']
    return out


def rule_of(templates):
    """the licence line: the rule in words, then Commons' own templates"""
    templates = licence_templates(templates)
    words = []
    for pat, text in RULES:
        if any(re.match(pat, t, re.I) for t in templates) and text not in words:
            words.append(text)
    tags = ', '.join('{{' + t + '}}' for t in templates)
    return (f'Public domain: {"; ".join(words)} (Wikimedia Commons: {tags})' if words else
            f'Public domain (Wikimedia Commons: {tags})' if tags else None)


def templates_for(files, done=None):
    """{file: [licence templates]}, asked of Commons for ten files at a time, slowly; `done(out)` after each
    ten, so what came in is kept if Commons refuses the rest (it limits requests: HTTP 429)"""
    out = {}
    for s in range(0, len(files), 10):
        if s:
            time.sleep(10)
        part = files[s:s + 10]
        params = {'action': 'query', 'titles': '|'.join('File:' + f for f in part), 'prop': 'templates', 'tlnamespace': 10,
                  'tllimit': 'max', 'format': 'json'}
        norm, cont = {}, {}
        while True:
            q = get('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(params, **cont)))
            time.sleep(1.5)
            for n in (q.get('query') or {}).get('normalized', []):
                norm[n['to']] = n['from']
            for page in ((q.get('query') or {}).get('pages') or {}).values():
                title = norm.get(page.get('title'), page.get('title', ''))[5:]
                got = out.setdefault(title.replace(' ', '_'), [])
                for t in page.get('templates', []):
                    name = t['title'][9:]
                    if TEMPLATE.match(t['title']) and name.lower() not in NOT_RULES and name.lower() not in [g.lower() for g in got]:
                        got.append(name)
            if 'continue' not in q:
                break
            cont = q['continue']
        if done:
            done(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data')
    ap.add_argument('--cache', default='cache/portraits')
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--templates', action='store_true', help='ask Commons only for the licence templates missing from the cache')
    a = ap.parse_args()
    root = os.path.dirname(os.path.abspath(a.data))
    os.makedirs(a.cache, exist_ok=True)
    mpath = os.path.join(a.cache, 'meta.json')
    meta = json.load(open(mpath)) if os.path.exists(mpath) else {}
    people = L.load_json(os.path.join(a.data, 'people.json'))
    pics = L.load_json(os.path.join(a.data, 'pictures.json'))
    old_lic = {p['id']: p['license'] for p in pics if p['id'].startswith('portrait-')}
    pics = [p for p in pics if not p['id'].startswith('portrait-')]
    from PIL import Image
    # a portrait a scene card already shows, chosen and dated by hand, comes first ("Lenin, clean-shaven, as
    # Reed saw him"); a fetched one only where there is none
    curated = {q['id']: q for q in pics if q['kind'] == 'portrait'}
    alias = {'lenin': 'lenin-1917', 'trotzky': 'trotsky', 'dybenko': 'dybenko-1920', 'avksentiev': 'avksentiev-reed', 'schreider': 'schreider-reed'}
    kept, left, reused = [], [], []
    need = [m['file'] for m in meta.values() if m.get('file') and 'templates' not in m and public_domain(m.get('license'))]
    if need and (a.fetch or a.templates):   # the licence rule: Commons' templates for each file
        def keep(got):
            for m in meta.values():
                if m.get('file') in got:
                    m['templates'] = got[m['file']]
            json.dump(meta, open(mpath, 'w'), ensure_ascii=False, indent=1)
        try:
            templates_for(need, keep)
        except RuntimeError as e:
            print(f'licence templates not fetched ({str(e)[-160:]}); try again later')
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
            try:   # one renamed or missing article is reported, not the end of the run
                meta[pid] = meta_for(title)
            except RuntimeError as e:
                left.append((pid, f'lookup failed ({str(e)[:80]})'))
                continue
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
        lt = licence_templates(m.get('templates') or [])
        if lt and all(OWN_WORK.match(t) for t in lt):
            left.append((pid, f'only an own-work claim ({", ".join(lt)}), not credible for a photograph of 1917'))
            continue
        label = rule_of(m.get('templates') or []) or old_lic.get(f'portrait-{pid}')
        if not rule_of(m.get('templates') or []):   # kept as it was; the checker asks for the rule
            print(f'  {pid}: no licence templates in the cache yet; its licence is left as it was')
        if not label:
            left.append((pid, 'no licence templates in the cache; run with --templates'))
            continue
        pics.append({'id': f'portrait-{pid}', 'kind': 'portrait', 'from': 'commons', 'file': f'media/portrait-{pid}.jpg', 'w': w, 'h': h,
                     'scenes': [], 'license': label,
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
