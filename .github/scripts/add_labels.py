"""Finalize Platane/snk snake SVGs into a complete labeled GitHub-style graph.

Two transformations:
  1. Fill the entire 53-week × 7-day grid with empty cells, so the raster
     is always visually complete — including days with no commits and the
     unrendered future days at the trailing edge of the current week.
  2. Inject month names along the top and Mon/Wed/Fri labels down the left,
     mimicking GitHub's native contribution graph.

Snake animations from the source SVG are left untouched: the background
grid sits in a sibling <g> placed first (renders beneath the snake), and
label text is injected in negative coordinate space outside the original
viewBox so it never collides with the animation.
"""

import datetime
import re
from pathlib import Path

PAD_LEFT = 34
PAD_TOP = 22
CELL = 14          # Platane/snk default: dotSize 12 + dotPadding 2
DOT_SIZE = 12
DOT_RADIUS = 2

today = datetime.date.today()
start = today - datetime.timedelta(days=364)
while start.weekday() != 6:  # back up to Sunday (Mon=0..Sun=6)
    start -= datetime.timedelta(days=1)

total_weeks = ((today - start).days // 7) + 1

month_positions = []
d = start
while d <= today:
    if d.day == 1:
        col = (d - start).days // 7
        month_positions.append((d.strftime("%b"), col))
    d += datetime.timedelta(days=1)

VARIANTS = [
    # path,                  label color, empty cell color
    ("dist/snake.svg",       "#57606a",   "#ebedf0"),
    ("dist/snake-dark.svg",  "#7d8590",   "#161b22"),
]

FONT = (
    'font-family="-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,sans-serif" '
    'font-size="9"'
)


def detect_grid_origin(src: str) -> tuple[float, float]:
    """Find top-left dot position by scanning rects with width=height=12."""
    xs, ys = [], []
    for m in re.finditer(r"<rect\b[^>]*?>", src):
        rect = m.group(0)
        w = re.search(r'\swidth="([\d.]+)"', rect)
        h = re.search(r'\sheight="([\d.]+)"', rect)
        x = re.search(r'\sx="([\d.\-]+)"', rect)
        y = re.search(r'\sy="([\d.\-]+)"', rect)
        if not (w and h and x and y):
            continue
        if abs(float(w.group(1)) - DOT_SIZE) > 0.5:
            continue
        if abs(float(h.group(1)) - DOT_SIZE) > 0.5:
            continue
        xv, yv = float(x.group(1)), float(y.group(1))
        # Skip snake animation rects entering from off-grid.
        if xv < 0 or yv < 0:
            continue
        xs.append(xv)
        ys.append(yv)
    if xs and ys:
        return min(xs), min(ys)
    return 0.0, 0.0


for path_str, label_color, empty_color in VARIANTS:
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

    origin_x, origin_y = detect_grid_origin(src)

    # Full raster: 53 (or 54) weeks × 7 days, no gaps anywhere.
    bg_rects = []
    for col in range(total_weeks):
        for row in range(7):
            x = origin_x + col * CELL
            y = origin_y + row * CELL
            bg_rects.append(
                f'<rect x="{x:.0f}" y="{y:.0f}" '
                f'width="{DOT_SIZE}" height="{DOT_SIZE}" '
                f'fill="{empty_color}" rx="{DOT_RADIUS}" />'
            )
    bg_block = '\n<g class="grid-bg">\n  ' + "\n  ".join(bg_rects) + "\n</g>\n"

    months_svg = "\n  ".join(
        f'<text x="{origin_x + col * CELL + 2:.0f}" '
        f'y="{origin_y - 8:.0f}" fill="{label_color}" {FONT}>{name}</text>'
        for name, col in month_positions
    )

    days_svg = "\n  ".join(
        f'<text x="{origin_x - 6:.0f}" '
        f'y="{origin_y + row * CELL + 11:.0f}" '
        f'fill="{label_color}" {FONT} text-anchor="end">{label}</text>'
        for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    )

    label_block = (
        f'\n<g class="date-labels">\n  {months_svg}\n  {days_svg}\n</g>\n'
    )

    new_vx = vx - PAD_LEFT
    new_vy = vy - PAD_TOP
    new_vw = vw + PAD_LEFT
    new_vh = vh + PAD_TOP

    new_src = re.sub(
        r'viewBox="[^"]+"',
        f'viewBox="{new_vx:.0f} {new_vy:.0f} {new_vw:.0f} {new_vh:.0f}"',
        src,
        count=1,
    )

    new_src = re.sub(
        r"(<svg\b[^>]*>)",
        lambda m: m.group(1) + bg_block + label_block,
        new_src,
        count=1,
        flags=re.DOTALL,
    )

    path.write_text(new_src, encoding="utf-8")
    print(f"finalized: {path_str}  ({total_weeks} weeks × 7 days)")
