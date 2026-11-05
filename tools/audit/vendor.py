#!/usr/bin/env python3
"""Fetch the files the page loads from jsDelivr into cache/vendor/, each checked against its pinned SHA-256.

    python3 -I tools/audit/vendor.py [--check]

Also checks that tools/audit/vendor.json lists every external script src/app.html loads, so a new script or
a new three.js version cannot slip past the pins. --check only checks; it fetches nothing.
"""
import hashlib, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'cache', 'vendor')


def name(url):
    return url.split('/npm/', 1)[1].replace('/', '_')


def main():
    with open(os.path.join(ROOT, 'tools', 'audit', 'vendor.json')) as fh:
        files = json.load(fh)['files']
    with open(os.path.join(ROOT, 'src', 'app.html'), encoding='utf-8') as fh:
        loaded = re.findall(r'<script src="(https://[^"]+)"', fh.read())
    pinned = {f['url'] for f in files}
    missing = [u for u in loaded if u not in pinned]
    if missing:
        sys.exit('src/app.html loads scripts tools/audit/vendor.json does not pin:\n  ' + '\n  '.join(missing))
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for f in files:
        path = os.path.join(OUT, name(f['url']))
        if not os.path.exists(path) and '--check' not in sys.argv:
            with urllib.request.urlopen(urllib.request.Request(f['url'], headers={'User-Agent': 'TenDaysMap-audit/1.0'}), timeout=60) as r:
                data = r.read()
            with open(path, 'wb') as out:
                out.write(data)
        if not os.path.exists(path):
            print(f'missing {path}'); bad += 1; continue
        with open(path, 'rb') as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        if got != f['sha256']:
            print(f'{name(f["url"])}: SHA-256 {got}, pinned {f["sha256"]}'); os.remove(path); bad += 1
    print(f'{len(files) - bad} of {len(files)} files in {OUT}, as pinned')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
