"""Turns assets/stino.png into the colored ASCII portrait in assets/portrait.json.

Run it again when the photo changes:  python scripts/portrait.py
Needs Pillow. The daily card generator only reads the JSON file: one list of
[character, color] pairs per row.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
WIDTH = 64  # characters
# Light-on-dark: brighter pixels get denser characters.
RAMP = ' .,:;i1tfLCG08@'

src = Image.open(ROOT / 'assets' / 'stino.png').convert('RGB')
w, h = src.size
# Head and shoulders, without the window on the right.
img = src.crop((int(w * 0.15), 0, int(w * 0.72), int(h * 0.80)))
img = ImageEnhance.Color(img).enhance(1.3)
img = ImageEnhance.Brightness(img).enhance(1.25)
img = ImageEnhance.Contrast(img).enhance(1.2)
# Characters are about twice as tall as they are wide.
rows = int(WIDTH * img.size[1] / img.size[0] * 0.5)
small = img.resize((WIDTH, rows), Image.LANCZOS)
gray = ImageOps.autocontrast(small.convert('L'), cutoff=1)

cells = []
for y in range(rows):
    row = []
    for x in range(WIDTH):
        # Keep the head and shoulders bright and let the bright wall fall back.
        head = math.hypot((x / WIDTH - 0.50) / 0.40, (y / rows - 0.40) / 0.42)
        shoulders = 0.6 if y / rows > 0.62 and 0.15 < x / WIDTH < 0.98 else 0.0
        light = 0.18 + 0.82 * max(shoulders, max(0.0, min(1.0, (1.15 - head) / 0.3)))
        v = gray.getpixel((x, y)) / 255
        char = RAMP[min(len(RAMP) - 1, int((0.3 + 0.7 * v) * light * len(RAMP)))]
        r, g, b = (int(c * light) for c in small.getpixel((x, y)))
        row.append([char, f'#{r:02x}{g:02x}{b:02x}'])
    cells.append(row)

(ROOT / 'assets' / 'portrait.json').write_text(json.dumps(cells, separators=(',', ':')), encoding='utf-8')
print(f'{WIDTH} x {rows} characters')
