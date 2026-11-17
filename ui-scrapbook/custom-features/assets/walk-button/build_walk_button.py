"""Build walk-button.webp (the hand-drawn "What time should we go on a walk?" button on the Kovu page).

The drawing comes in two files from the drawing app: bubble.svg (the speech bubble) and
walking-kovu.svg (Divya walking KOVU, which sits on the bubble's top-left bump). Each "SVG" is
really a 1904x2500 picture (grey lines on black) inside an SVG wrapper, so this script takes the
picture out of each, turns the lines into a transparent mask, and places both pieces where they
were in the first, lower-resolution walk-button.webp (900x796), at twice that size.

    uv run python ui-scrapbook/custom-features/assets/walk-button/build_walk_button.py

The page uses the result as a CSS mask, so only its transparency matters: lines are solid,
everything else is clear. Keep the 900:796 shape; walk-drawing.html sets aspect-ratio 900 / 796.
"""

import base64
import io
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "walk-button.webp"

LAYOUT = (900, 796)  # the original button's size; every placement below is measured in it
SCALE = 2            # output is 1800x1592

# Each piece: the drawn area of its picture (left, top, right, bottom in source pixels), how much
# it shrinks to fit the 900x796 layout, and where its top-left corner lands there. Found by
# matching each piece against the original button.
PIECES = [
    ("bubble.svg", (17, 249, 1902, 1608), 0.46, (18, 157)),
    ("walking-kovu.svg", (77, 210, 1555, 1651), 0.206, (40, 13)),
]

LINE = 36.0  # the grey of a drawn line in the source; anything this bright or brighter is solid


def picture(svg: Path) -> Image.Image:
    """The picture inside the drawing app's SVG wrapper (the last embedded PNG)."""
    data = re.findall(r"base64,([A-Za-z0-9+/=]+)", svg.read_text())[-1]
    return Image.open(io.BytesIO(base64.b64decode(data))).convert("L")


def lines(grey: Image.Image) -> Image.Image:
    """Grey lines on black -> a mask with solid lines."""
    mask = Image.fromarray((np.clip(np.asarray(grey, float) / LINE, 0, 1) * 255).astype("uint8"))
    # The export leaves a thin dark ring inside the edge of every line; close it up.
    return mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))


def main() -> None:
    width, height = LAYOUT[0] * SCALE, LAYOUT[1] * SCALE
    canvas = np.zeros((height, width))
    for name, box, shrink, (x, y) in PIECES:
        mask = lines(picture(HERE / name).crop(box))
        w, h = round(mask.width * shrink * SCALE), round(mask.height * shrink * SCALE)
        part = np.asarray(mask.resize((w, h), Image.LANCZOS), float)
        x, y = x * SCALE, y * SCALE
        part = part[: height - y, : width - x]
        area = canvas[y : y + part.shape[0], x : x + part.shape[1]]
        np.maximum(area, part, out=area)
    button = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    button.putalpha(Image.fromarray(np.clip(canvas, 0, 255).astype("uint8")))
    button.save(OUT, lossless=True, method=6)
    print(f"wrote {OUT} ({width}x{height})")


if __name__ == "__main__":
    main()
