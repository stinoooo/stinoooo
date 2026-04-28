"""Wrap Platane/snk snake SVGs with GitHub-style month and day labels.

Reads each generated SVG, expands its viewBox to make room for axis labels,
and injects month names along the top and Mon/Wed/Fri labels along the left.
Preserves the snake animation untouched — labels are added in a sibling <g>.
"""

import datetime
import re
from pathlib import Path

PAD_LEFT = 34
PAD_TOP = 22
CELL = 14  # Platane/snk default: dotSize 12 + dotPadding 2

today = datetime.date.today()
start = today - datetime.timedelta(days=364)
while start.weekday() != 6:  # back up to Sunday (Python: Mon=0..Sun=6)
    start -= datetime.timedelta(days=1)

month_positions = []
d = start
while d <= today:
    if d.day == 1:
        col = (d - start).days // 7
        month_positions.append((d.strftime("%b"), col))
    d += datetime.timedelta(days=1)

VARIANTS = [
    ("dist/snake.svg", "#57606a"),
    ("dist/snake-dark.svg", "#7d8590"),
]

FONT = (
    'font-family="-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,sans-serif" '
    'font-size="9"'
)

for path_str, color in VARIANTS:
    path = Path(path_str)
    if not path.exists():
        print(f"skip: {path_str} not found")
        continue

    src = path.read_text(encoding="utf-8")

    vb_match = re.search(r'viewBox="([^"]+)"', src)
    if not vb_match:
        print(f"skip: no viewBox in {path_str}")
        continue
    vx, vy, vw, vh = map(float, vb_match.group(1).split())

    new_vx = vx - PAD_LEFT
    new_vy = vy - PAD_TOP
    new_vw = vw + PAD_LEFT
    new_vh = vh + PAD_TOP

    months_svg = "\n  ".join(
        f'<text x="{col * CELL + 2}" y="{vy - 8:.0f}" fill="{color}" {FONT}>{name}</text>'
        for name, col in month_positions
    )

    days_svg = "\n  ".join(
        f'<text x="{vx - 6:.0f}" y="{row * CELL + 11:.0f}" '
        f'fill="{color}" {FONT} text-anchor="end">{label}</text>'
        for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    )

    new_src = re.sub(
        r'viewBox="[^"]+"',
        f'viewBox="{new_vx:.0f} {new_vy:.0f} {new_vw:.0f} {new_vh:.0f}"',
        src,
        count=1,
    )

    label_block = (
        f'\n<g class="date-labels">\n  {months_svg}\n  {days_svg}\n</g>\n'
    )
    new_src = re.sub(
        r"(<svg\b[^>]*>)",
        lambda m: m.group(1) + label_block,
        new_src,
        count=1,
        flags=re.DOTALL,
    )

    path.write_text(new_src, encoding="utf-8")
    print(f"labeled: {path_str}")
