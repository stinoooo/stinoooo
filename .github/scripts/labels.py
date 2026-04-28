"""Decorate Platane/snk snake SVGs with month/day axis labels and a
contribution-count header — without touching the snake animation itself.

Layout strategy: the source SVG already has padding around the grid for
the snake's animation entry/exit (viewBox -16 -32 880 192). We expand
the viewBox further into negative space, and place all decorations in
that *new* band so they sit safely outside the snake's animation range.

Geometry is sourced directly from Platane/snk v3 conventions:
  - grid origin at (2, 2)
  - cell pitch 16 (12px cell + 2px stroke margin + 2px gap)
  - 7 rows × 53 weeks
"""

import datetime
import os
import re
from pathlib import Path

GRID_ORIGIN_X = 2
GRID_ORIGIN_Y = 2
CELL_PITCH = 16

PAD_LEFT = 30
PAD_TOP = 40

today = datetime.date.today()
start = today - datetime.timedelta(days=364)
while start.weekday() != 6:  # back up to Sunday (Mon=0..Sun=6)
    start -= datetime.timedelta(days=1)

month_positions = []
d = start
while d <= today:
    if d.day == 1:
        col = (d - start).days // 7
        month_positions.append((d.strftime("%b"), col))
    d += datetime.timedelta(days=1)

VARIANTS = [
    ("dist/github-contribution-grid-snake.svg",       "#57606a"),
    ("dist/github-contribution-grid-snake-dark.svg",  "#7d8590"),
]

FONT_BASE = (
    'font-family="-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,'
    'Helvetica,Arial,sans-serif"'
)
FONT_LABEL = f'{FONT_BASE} font-size="9"'
FONT_TITLE = f'{FONT_BASE} font-size="13" font-weight="600"'

count_raw = os.environ.get("CONTRIB_COUNT", "").strip()
count_str = ""
if count_raw:
    try:
        count_str = f"{int(count_raw):,}"
    except ValueError:
        count_str = count_raw  # use as-is if non-numeric


def update_attr(src: str, attr: str, value: str) -> str:
    """Replace an attribute on the root <svg> tag (first occurrence)."""
    pattern = rf'(<svg\b[^>]*?\s){attr}="[^"]*"'
    return re.sub(pattern, lambda m: m.group(1) + f'{attr}="{value}"', src, count=1)


for path_str, label_color in VARIANTS:
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

    title_svg = ""
    if count_str:
        title_svg = (
            f'<text x="{GRID_ORIGIN_X}" y="{vy - 22:.0f}" '
            f'fill="{label_color}" {FONT_TITLE}>'
            f'{count_str} contributions in the last year'
            f"</text>"
        )

    months_svg = "\n  ".join(
        f'<text x="{GRID_ORIGIN_X + col * CELL_PITCH:.0f}" '
        f'y="{vy - 6:.0f}" fill="{label_color}" {FONT_LABEL}>{name}</text>'
        for name, col in month_positions
    )

    days_svg = "\n  ".join(
        f'<text x="{vx - 6:.0f}" '
        f'y="{GRID_ORIGIN_Y + row * CELL_PITCH + 11:.0f}" '
        f'fill="{label_color}" {FONT_LABEL} text-anchor="end">{label}</text>'
        for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    )

    label_block = (
        f'\n<g class="decorations">\n'
        f"  {title_svg}\n  {months_svg}\n  {days_svg}\n"
        f"</g>\n"
    )

    src2 = re.sub(
        r'viewBox="[^"]+"',
        f'viewBox="{new_vx:.0f} {new_vy:.0f} {new_vw:.0f} {new_vh:.0f}"',
        src,
        count=1,
    )

    # Keep width/height attrs on the root <svg> in sync with the new viewBox.
    w_match = re.search(r'<svg\b[^>]*?\swidth="([\d.]+)"', src2)
    h_match = re.search(r'<svg\b[^>]*?\sheight="([\d.]+)"', src2)
    if w_match:
        src2 = update_attr(src2, "width", f"{float(w_match.group(1)) + PAD_LEFT:.0f}")
    if h_match:
        src2 = update_attr(src2, "height", f"{float(h_match.group(1)) + PAD_TOP:.0f}")

    src3 = re.sub(
        r"(<svg\b[^>]*>)",
        lambda m: m.group(1) + label_block,
        src2,
        count=1,
        flags=re.DOTALL,
    )
    path.write_text(src3, encoding="utf-8")
    print(f"decorated: {path_str}  (count={count_str or 'n/a'})")
