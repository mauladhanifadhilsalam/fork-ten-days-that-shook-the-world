"""Download Reed's *Ten Days That Shook the World* (Project Gutenberg #3076) and split it into sections.

usage: python3 -I tools/text.py CACHE_DIR

Writes CACHE_DIR/sections.json:
  {"source": {"url", "sha256"},
   "sections": [{"id", "kind", "parent"?, "title", "paras": [...]}, ...],
   "graphics": [{"sec", "page", "caption"}, ...]}

Section ids are "Preface", "Notes", "I".."XII", the appendix containers "App.I".."App.XII", and
their numbered sub-sections "App.I.1".."App.XII.2". It prints words, explicit clock times and
first-person movements per section, so the numbers in docs/assessment.md can be reproduced.

The body (between Gutenberg's START and END lines) is pinned by SHA-256. If Gutenberg changes
the text, this stops, and the quotes in data/ must be re-checked before the pin is moved.
"""
import sys, os, re, json, hashlib, urllib.request

URL = 'https://www.gutenberg.org/cache/epub/3076/pg3076.txt'
UA = 'ten-days-that-shook-the-world/0.1 (+https://github.com/altf4m88/ten-days-that-shook-the-world)'
BODY_SHA256 = 'e82c94fbbc9ec113aeb91e0f28ac1432aa6be142307ed4e516f9869af7ec4cf2'
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
TITLES = ['Background', 'The Coming Storm', 'On the Eve', 'The Fall of the Provisional Government',
          'Plunging Ahead', 'The Committee for Salvation', 'The Revolutionary Front', 'Counter-Revolution',
          'Victory', 'Moscow', 'The Conquest of Power', 'The Peasants’ Congress']
APP_SECTS = [5, 13, 7, 4, 5, 1, 2, 5, 5, 4, 20, 2]
XREF = re.compile(r'App\.\s*([IVX]+),\s*Sect\.\s*(\d+)')
CLOCK = re.compile(r"\b\d{1,2}[.:]\d{2}\s*[AaPp]\.?\s?[Mm]\.?|\b[Aa]t \d{1,2}[.:]\d{2}\b|\b\d{1,2}\s*[AaPp]\.\s?[Mm]\."
                   r"|o[’']clock|\bmidnight\b|\bnoon\b|minutes (?:past|to) \w+")
MOVE = re.compile(r"\b(?:I|we|We)\s+(?:went|walked|drove|hurried|ran|rode|crossed|turned|climbed|made for|"
                  r"took|left|reached|got|passed|came|slipped|plunged|poured|swung|followed)\b")


def fail(msg):
    print('text.py:', msg, file=sys.stderr)
    sys.exit(1)


def capitals(line):
    """A sub-section title line: letters at least 90% capitals ("TRUCE. KRASNOV’s ANSWER …" counts)."""
    letters = [c for c in line if c.isalpha()]
    return len(letters) >= 3 and sum(c.isupper() for c in letters) >= 0.9 * len(letters)


def paragraphs(lines, sid, graphics):
    """Blank-line separated paragraphs, whitespace collapsed. Gutenberg's "[Graphic, page N: …]"
    markers are the transcriber's, not Reed's, so they move to `graphics`; the caption paragraph
    after a marker is Reed's and stays in the text."""
    out = []
    for p in '\n'.join(lines).split('\n\n'):
        p = re.sub(r'\s+', ' ', p).strip()
        if not p or p == 'Ten Days That Shook The World':   # a stray running head before Chapter I
            continue
        m = re.match(r'^\[Graphic, page (\d+)(?::\s*(.*?))?\]$', p)
        if m:
            graphics.append({'sec': sid, 'page': int(m.group(1)), 'caption': (m.group(2) or '').strip()})
        elif p.startswith('[Graphic'):
            fail(f'unparsed graphic marker in {sid}: {p[:60]}')
        else:
            out.append(p)
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    cache = sys.argv[1]
    os.makedirs(cache, exist_ok=True)
    src = os.path.join(cache, 'pg3076.txt')
    if not os.path.exists(src):
        req = urllib.request.Request(URL, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(src, 'wb') as f:
            f.write(r.read())

    with open(src, encoding='utf-8') as f:
        raw = f.read().replace('\r\n', '\n')
    lines = raw.split('\n')
    start = [i for i, l in enumerate(lines) if l.startswith('*** START OF THE PROJECT GUTENBERG EBOOK')]
    end = [i for i, l in enumerate(lines) if l.startswith('*** END OF THE PROJECT GUTENBERG EBOOK')]
    if len(start) != 1 or len(end) != 1:
        fail('START/END markers not found exactly once')
    body = lines[start[0] + 1:end[0]]
    sha = hashlib.sha256('\n'.join(body).encode('utf-8')).hexdigest()
    if BODY_SHA256 != '__PIN__' and sha != BODY_SHA256:
        fail(f'body SHA-256 is {sha}, pinned {BODY_SHA256}: Gutenberg changed the text; re-check data/ quotes, then move the pin')

    # Headings are flush-left lines; the contents list near the top is indented by one space.
    heads = [('Preface', 'Preface', 'front', 'Preface'), ('Notes and Explanations', 'Notes', 'front', 'Notes and Explanations')]
    heads += [(f'Chapter {r}', r, 'chapter', None) for r in ROMAN]
    heads += [(f'APPENDIX TO CHAPTER {r}', f'App.{r}', 'appendix', f'Appendix to Chapter {r}') for r in ROMAN]
    pos = []
    for line, sid, kind, title in heads:
        hits = [i for i, l in enumerate(body) if l == line]
        if len(hits) != 1:
            fail(f'heading {line!r} found {len(hits)} times')
        pos.append((hits[0], line, sid, kind, title))
    if [p[0] for p in pos] != sorted(p[0] for p in pos):
        fail('headings out of order')

    sections, graphics, xrefs = [], [], []
    for k, (i, line, sid, kind, title) in enumerate(pos):
        j = pos[k + 1][0] if k + 1 < len(pos) else len(body)
        chunk = body[i + 1:j]
        if kind == 'chapter':
            n = ROMAN.index(sid)
            first = next(x for x, l in enumerate(chunk) if l.strip())
            tline = chunk[first].strip()
            xrefs += XREF.findall(tline)
            title = re.sub(r'\s*\(See App\.[^)]*\)\s*$', '', tline)
            if title != TITLES[n]:
                fail(f'chapter {sid} title {title!r}, expected {TITLES[n]!r}')
            chunk = chunk[first + 1:]
        if kind != 'appendix':
            kept = paragraphs(chunk, sid, graphics)
            for p in kept:
                xrefs += XREF.findall(p)
            sections.append({'id': sid, 'kind': kind, 'title': title, 'paras': kept})
            continue
        # An appendix holds numbered sub-sections. A flush-left line that is just "N." opens one,
        # and the all-capitals lines right after it (if any) are its title.
        parent = {'id': sid, 'kind': 'appendix', 'title': title, 'paras': []}
        sections.append(parent)
        groups, subs = [(parent, [])], []
        x = 0
        while x < len(chunk):
            m = re.fullmatch(r'(\d+)\.', chunk[x])
            if not m:
                groups[-1][1].append(chunk[x])
                x += 1
                continue
            cur = {'id': f'{sid}.{m.group(1)}', 'kind': 'appsec', 'parent': sid, 'title': '', 'paras': []}
            subs.append(int(m.group(1)))
            sections.append(cur)
            x += 1
            while x < len(chunk) and not chunk[x].strip():
                x += 1
            tl = []
            while x < len(chunk) and chunk[x].strip() and capitals(chunk[x]):
                tl.append(chunk[x].strip())
                x += 1
            cur['title'] = ' '.join(tl)
            groups.append((cur, []))
        for sec, glines in groups:
            sec['paras'] = paragraphs(glines, sid, graphics)
            for p in sec['paras']:
                xrefs += XREF.findall(p)
        n = ROMAN.index(sid.split('.')[1])
        if subs != list(range(1, APP_SECTS[n] + 1)):
            fail(f'{sid} sub-sections {subs}, expected 1..{APP_SECTS[n]}')

    ids = {s['id'] for s in sections}
    bad = [f'App.{a}.{b}' for a, b in xrefs if f'App.{a}.{b}' not in ids]
    if bad:
        fail(f'unresolved cross-references: {bad}')
    top = [s for s in sections if s['kind'] != 'appsec']
    leaves = [s for s in sections if s['kind'] == 'appsec']
    if len(top) != 26 or len(leaves) != sum(APP_SECTS) or len(graphics) != 17:
        fail(f'{len(top)} sections, {len(leaves)} appendix sub-sections, {len(graphics)} graphics')

    out = {'source': {'url': URL, 'sha256': sha}, 'sections': sections, 'graphics': graphics}
    with open(os.path.join(cache, 'sections.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)

    # Stats, grouped by chapter (each appendix counted with its chapter's appendix total).
    print(f'body sha256 {sha}{"  (NOT PINNED)" if BODY_SHA256 == "__PIN__" else ""}')
    print(f'{len(top)} sections, {len(leaves)} appendix sub-sections, {len(xrefs)} cross-references, '
          f'{len(graphics)} graphics')
    print(f'{"section":12} {"words":>7} {"clock":>6} {"I/we moves":>10}')
    totals = {}
    for s in sections:
        key = s['parent'] if s['kind'] == 'appsec' else s['id']
        t = ' '.join(s['paras'])
        w, c, m = totals.get(key, (0, 0, 0))
        totals[key] = (w + len(t.split()), c + len(CLOCK.findall(t)), m + len(MOVE.findall(t)))
    for key, (w, c, m) in totals.items():
        print(f'{key:12} {w:7d} {c:6d} {m:10d}')
    main_w = sum(v[0] for k, v in totals.items() if not k.startswith('App.'))
    app_w = sum(v[0] for k, v in totals.items() if k.startswith('App.'))
    print(f'{"main text":12} {main_w:7d} {sum(v[1] for k, v in totals.items() if not k.startswith("App.")):6d}')
    print(f'{"appendices":12} {app_w:7d} {sum(v[1] for k, v in totals.items() if k.startswith("App.")):6d}')


if __name__ == '__main__':
    main()
