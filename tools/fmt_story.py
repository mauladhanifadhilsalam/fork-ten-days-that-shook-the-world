"""Rewrite the data files in their canonical layout and order.

usage: python3 -I tools/fmt_story.py [--check] [--pages PDF] [DATA_DIR]

Layout: one header line of short fields per record, then a line for each prose field and for each
nested item (moves, control changes, checks). Events are sorted by time, places by zone then id,
actors by kind then id, sources by id.

--check   change nothing; exit 1 and list the files that would change
--pages   also fill each event's convenience page number `p` from the marxists.org PDF (needs pypdf)
          and record the PDF's SHA-256 in meta.pdf.sha256
"""
import sys, os, json, hashlib, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data', nargs='?', default='data')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--pages')
    a = ap.parse_args()
    objs = {n: L.load_json(os.path.join(a.data, n + '.json')) for n in ['meta'] + L.TABLES}
    if a.pages:
        from pypdf import PdfReader
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from check_story import page_of, pdf_pages
        raw = L.read_bytes(a.pages)
        pages = pdf_pages(PdfReader(a.pages))
        objs['meta']['meta'].setdefault('pdf', {})['sha256'] = hashlib.sha256(raw).hexdigest()
        missing = []
        for e in objs['events']:
            if 'q' in e:
                p = page_of(pages, e['q'])
                if p:
                    e['p'] = p
                else:
                    e.pop('p', None)
                    missing.append(e['id'])
        if missing:
            print('no PDF page found for:', ', '.join(missing))
    changed = []
    for n, obj in objs.items():
        path = os.path.join(a.data, n + '.json')
        text = L.canonical(n, obj if n == 'meta' else L.sort_table(n, obj))
        if L.read_text(path) != text:
            changed.append(path)
            if not a.check:
                L.write_text(path, text)
    if a.check:
        for p in changed:
            print('would reformat', p)
        sys.exit(1 if changed else 0)
    for p in changed:
        print('reformatted', p)


if __name__ == '__main__':
    main()
