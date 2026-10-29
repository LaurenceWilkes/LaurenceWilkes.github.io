#!/usr/bin/env python3
"""
-- LLM generated code --

Generate a static, HTML-based ASCII rendering of a Julia set.

The output is plain HTML/CSS containing precomputed characters (no canvas or runtime JS).
"""

from __future__ import annotations

import argparse
import html
import math
from pathlib import Path

# Resolution chosen to fit a 1200 x 628 logo-shaped container with relatively large glyphs.
WIDTH = 110
HEIGHT = 34

# Julia-set parameter c = c_real + c_imag*i. A real c gives the figure symmetry
# across both axes, similar to the supplied reference.
C_REAL = -0.745
C_IMAG = 0.0
MAX_ITERATIONS = 100
BAILOUT_RADIUS = 16.0

# View window. Its aspect ratio accounts for the narrower width of monospace characters.
X_MIN, X_MAX = -1.74, 1.74
Y_MIN, Y_MAX = -0.90, 0.90

# Escape-time bands: red outside, moving through orange to yellow near the set boundary.
PALETTE = [
    "#ff1400", "#ff1900", "#ff2500", "#ff3700", "#ff4e00",
    "#ff6600", "#ff8400", "#ffa100", "#ffc100", "#ffe000", "#fff200",
]
ASCII_CHARS = ".,:;-~=+*#%@"


def julia_value(x: float, y: float, c_real: float, c_imag: float,
                max_iterations: int) -> tuple[bool, float]:
    """Return (is_inside, smooth_escape_iteration) for z <- z*z + c."""
    zx, zy = x, y
    bailout_squared = BAILOUT_RADIUS * BAILOUT_RADIUS

    for iteration in range(max_iterations):
        zx, zy = zx * zx - zy * zy + c_real, 2.0 * zx * zy + c_imag
        magnitude_squared = zx * zx + zy * zy
        if magnitude_squared > bailout_squared:
            # Smooth iteration count gives a less jagged colour transition than raw counts.
            magnitude = math.sqrt(magnitude_squared)
            smooth = iteration + 1 - math.log(math.log(magnitude)) / math.log(2.0)
            return False, max(0.0, smooth)

    return True, float(max_iterations)


def classify(x: float, y: float, c_real: float, c_imag: float,
             max_iterations: int) -> tuple[str, str]:
    """Choose a glyph and colour class from the calculated Julia-set value."""
    inside, smooth = julia_value(x, y, c_real, c_imag, max_iterations)
    if inside:
        return "inside", "@"

    # Logarithmic quantisation creates visible red/orange/yellow contour bands.
    band = min(len(PALETTE) - 1, int(math.log2(smooth + 1.0) * 2.4))
    char_index = min(
        len(ASCII_CHARS) - 1,
        int(math.log(smooth + 1.0) / math.log(max_iterations + 1.0) * len(ASCII_CHARS)),
    )
    return f"b{band}", ASCII_CHARS[char_index]


def make_row(y: float, width: int, x_min: float, x_max: float,
             c_real: float, c_imag: float, max_iterations: int) -> str:
    """Build one HTML row, grouping adjacent glyphs with the same colour class."""
    cells: list[tuple[str, str]] = []
    for column in range(width):
        x = x_min + (x_max - x_min) * column / (width - 1)
        cells.append(classify(x, y, c_real, c_imag, max_iterations))

    runs: list[str] = []
    run_class = cells[0][0]
    run_chars: list[str] = []
    for css_class, char in cells:
        if css_class != run_class:
            runs.append(f'<span class="{run_class}">{html.escape("".join(run_chars))}</span>')
            run_class, run_chars = css_class, []
        run_chars.append(char)
    runs.append(f'<span class="{run_class}">{html.escape("".join(run_chars))}</span>')
    return "".join(runs)


def build_html(c_real: float, c_imag: float, max_iterations: int) -> str:
    rows = []
    for row in range(HEIGHT):
        y = Y_MAX - (Y_MAX - Y_MIN) * row / (HEIGHT - 1)
        rows.append(make_row(y, WIDTH, X_MIN, X_MAX, c_real, c_imag, max_iterations))

    palette_css = "\n".join(
        f"    .b{i} {{ color: {colour}; }}" for i, colour in enumerate(PALETTE)
    )
    ascii_rows = "\n".join(rows)

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Julia Set ASCII Art</title>
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ width: 100%; height: 100%; margin: 0; }}
    body {{ display: grid; place-items: center; overflow: hidden; background: #ff1400; }}

    /* Same image-like dimensions as the Advent of Code logo: 1200 x 628. */
    .julia-logo {{
      container-type: inline-size;
      width: min(100%, 1200px);
      aspect-ratio: 1200 / 628;
      overflow: hidden;
      display: grid;
      place-items: center;
      background: #ff1400;
    }}
    .julia-logo pre {{
      margin: 0;
      padding: 0;
      white-space: pre;
      font-family: Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: min(1.45cqw, 18px);
      line-height: 1;
      font-weight: 700;
      letter-spacing: 0;
      font-variant-ligatures: none;
    }}
{palette_css}
    .inside {{ color: #000000; }}
  </style>
</head>
<body>
  <main class="julia-logo" role="img" aria-label="ASCII rendering of a Julia set, with a black centre and red, orange and yellow contour bands.">
    <pre aria-hidden="true">{ascii_rows}</pre>
  </main>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).with_name("julia-set-ascii.html"),
        help="Output HTML file (default: julia-set-ascii.html beside this script)",
    )
    parser.add_argument("--c-real", type=float, default=C_REAL, help="Real part of Julia parameter c")
    parser.add_argument("--c-imag", type=float, default=C_IMAG, help="Imaginary part of Julia parameter c")
    parser.add_argument("--iterations", type=int, default=MAX_ITERATIONS, help="Maximum iterations per character")
    args = parser.parse_args()

    if args.iterations < 2:
        parser.error("--iterations must be at least 2")

    html_document = build_html(args.c_real, args.c_imag, args.iterations)
    args.output.write_text(html_document, encoding="utf-8")
    print(f"Wrote {args.output} ({WIDTH} columns x {HEIGHT} rows; c={args.c_real}{args.c_imag:+}i)")


if __name__ == "__main__":
    main()
