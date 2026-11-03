#!/usr/bin/env python3
"""Contact sheets of scene screenshots, six to a sheet, the map part only (the card cropped off), each labelled.

    python3 -I tools/audit/sheet.py SHOTDIR OUTDIR [ID ...]

SHOTDIR holds <id>.png from shot.js or crowds.js --shots; without IDs every scene of build/story.json that
has a shot is laid out, in tour order. Needs Pillow.
"""
import json, os, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H, COLS = 430, 360, 3


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    shots, out, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
    if not ids:
        with open(os.path.join(ROOT, 'build', 'story.json')) as fh:
            ids = [e['id'] for e in json.load(fh)['events']]
    ids = [i for i in ids if os.path.exists(os.path.join(shots, i + '.png'))]
    os.makedirs(out, exist_ok=True)
    for s in range(0, len(ids), 6):
        part = ids[s:s + 6]
        rows = (len(part) + COLS - 1) // COLS
        sheet = Image.new('RGB', (COLS * W, rows * (H + 40)), 'white')
        draw = ImageDraw.Draw(sheet)
        for k, i in enumerate(part):
            im = Image.open(os.path.join(shots, i + '.png'))
            im = im.crop((0, 90, min(860, im.width), im.height - 90)).resize((W, H))
            x, y = (k % COLS) * W, (k // COLS) * (H + 40)
            sheet.paste(im, (x, y + 40))
            draw.rectangle([x, y, x + W, y + 40], fill='black')
            draw.text((x + 6, y + 12), f'{s + k + 1}. {i}', fill='white')
        path = os.path.join(out, f'sheet-{s // 6 + 1:02d}.png')
        sheet.save(path)
        print(path)


if __name__ == '__main__':
    main()
