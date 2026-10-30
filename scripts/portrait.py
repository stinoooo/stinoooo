"""Turns assets/stino.png into the ASCII portrait in assets/portrait.txt.

Run it again when the photo changes:  python scripts/portrait.py
Needs Pillow. The daily card generator only reads the text file.
"""
import math
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
WIDTH = 44  # characters
# Light-on-dark: brighter pixels get denser characters.
RAMP = ' .:-=+*#%@'

img = Image.open(ROOT / 'assets' / 'stino.png').convert('L')
w, h = img.size
# Head and shoulders, without the window on the right.
img = img.crop((int(w * 0.17), int(h * 0.03), int(w * 0.70), int(h * 0.70)))
img = ImageOps.autocontrast(img, cutoff=1)
# Characters are about twice as tall as they are wide.
rows = int(WIDTH * img.size[1] / img.size[0] * 0.5)
img = img.resize((WIDTH, rows), Image.LANCZOS)

lines = []
for y in range(rows):
    line = ''
    for x in range(WIDTH):
        # Fade out towards the edges so the bright wall does not swallow the face.
        dx = (x / WIDTH - 0.50) / 0.50
        dy = (y / rows - 0.48) / 0.58
        fade = max(0.0, min(1.0, (1.05 - math.hypot(dx, dy)) / 0.25))
        v = img.getpixel((x, y)) / 255 * fade
        line += RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
    lines.append(line.rstrip())

(ROOT / 'assets' / 'portrait.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(lines))
