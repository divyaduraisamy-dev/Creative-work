# /// script
# dependencies = ["pillow"]
# ///
"""Guide sheet for "Neat Handwriting": one box per character, with four guide lines in each.

Draw each character in its box (on a layer above the sheet), then upload the full-size image.
The guides and labels are blue so the font builder can tell them apart from your ink: draw in
white on the dark sheet, or black on the light one.

    uv run make_sheet.py        -> guide-sheet-dark.png, guide-sheet-light.png

The layout (CELLS, LINES, SAMPLES) is what the font builder uses to cut letters out by box, so
keep it in step with any sheet you've drawn on.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
W = 3600
COLS = 10
CELL_W = W // COLS            # 360
CELL_H = 440
TOP = 520                     # header height
# guide lines as shares of a box's height, top to bottom
LINES = {"tall": 0.24, "x": 0.47, "base": 0.73, "tail": 0.91}

GROUPS = [
    ("lowercase", list("abcdefghijklmnopqrstuvwxyz")),
    ("capitals", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
    ("figures", list("0123456789")),
    ("punctuation", list(".,'’\"“”?!:;-–()/&")),
]
# small name tags for marks that look alike
HINTS = {"'": "straight", "’": "curly", '"': "straight", "“": "opening", "”": "closing",
         "-": "hyphen", "–": "dash", ".": "full stop", ",": "comma", ":": "colon", ";": "semicolon"}
SAMPLES = [
    "The quick brown fox jumps over the lazy dog.",
    "Fish swim past 0123456789 bowls & cans!",
]
SAMPLE_H = 500

THEMES = {
    "dark": {"bg": (0, 0, 0), "guide": (52, 96, 150), "soft": (34, 62, 98), "label": (88, 140, 200)},
    "light": {"bg": (255, 255, 255), "guide": (150, 190, 230), "soft": (200, 222, 244), "label": (90, 140, 200)},
}


def layout():
    """[(char, (x0, y0, x1, y1))] for every box, and the sample strips' boxes."""
    cells, y = [], TOP
    for _, chars in GROUPS:
        for i, ch in enumerate(chars):
            r, c = divmod(i, COLS)
            cells.append((ch, (c * CELL_W, y + r * CELL_H, (c + 1) * CELL_W, y + (r + 1) * CELL_H)))
        y += -(-len(chars) // COLS) * CELL_H
    samples = [(text, (0, y + i * SAMPLE_H, W, y + (i + 1) * SAMPLE_H)) for i, text in enumerate(SAMPLES)]
    return cells, samples, y + len(SAMPLES) * SAMPLE_H + 60


CELLS, SAMPLE_BOXES, H = layout()


def font(size, bold=False):
    path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default(size)


def dashed(d, x0, x1, y, fill, width, dash=18, gap=14):
    x = x0
    while x < x1:
        d.line([(x, y), (min(x + dash, x1), y)], fill=fill, width=width)
        x += dash + gap


def guides(d, box, t, pad=26):
    x0, y0, x1, y1 = box
    h = y1 - y0
    for name, share in LINES.items():
        y = round(y0 + share * h)
        if name == "x":
            dashed(d, x0 + pad, x1 - pad, y, t["guide"], 3)
        else:
            d.line([(x0 + pad, y), (x1 - pad, y)], fill=t["guide"], width=6 if name == "base" else 3)


def draw(theme):
    t = THEMES[theme]
    im = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(im)
    # header: title, how to use it, and what the four lines mean
    d.text((60, 50), "Neat Handwriting  ·  guide sheet", font=font(84, True), fill=t["label"])
    tip = ("One character per box, inside the lines. Letters sit on the thick baseline; small letters reach the "
           "dashed line; capitals and tall letters (b d f h k l t) reach the top line; tails (g j p q y) reach the bottom line.")
    tip += " Same pen and thickness throughout. Print, don't join letters. Upload the full-size image."
    words, line, y = tip.split(), "", 168
    for w in words:  # wrap at word breaks
        if d.textlength(line + " " + w, font=font(40)) > W - 120:
            d.text((60, y), line, font=font(40), fill=t["label"]); line, y = w, y + 52
        else:
            line = (line + " " + w).strip()
    d.text((60, y), line, font=font(40), fill=t["label"])
    lx, ly = 60, y + 80
    for i, name in enumerate(LINES):
        y = ly + i * 40
        if name == "x":
            dashed(d, lx, lx + 420, y, t["guide"], 3)
        else:
            d.line([(lx, y), (lx + 420, y)], fill=t["guide"], width=6 if name == "base" else 3)
        word = {"tall": "capitals & tall letters", "x": "small letters", "base": "baseline (letters sit here)",
                "tail": "tails"}[name]
        d.text((lx + 450, y - 18), word, font=font(32), fill=t["label"])
    # character boxes
    for ch, (x0, y0, x1, y1) in CELLS:
        d.rectangle([x0 + 8, y0 + 8, x1 - 8, y1 - 8], outline=t["soft"], width=2)
        guides(d, (x0, y0, x1, y1), t)
        d.text((x0 + 24, y0 + 18), ch, font=font(46), fill=t["label"])
        if ch in HINTS:
            d.text((x0 + 70, y0 + 30), HINTS[ch], font=font(30), fill=t["label"])
    # spacing samples: write the line naturally, across the strip
    for text, (x0, y0, x1, y1) in SAMPLE_BOXES:
        d.rectangle([x0 + 8, y0 + 8, x1 - 8, y1 - 8], outline=t["soft"], width=2)
        guides(d, (x0, y0 + 40, x1, y1), t, pad=40)
        d.text((x0 + 40, y0 + 26), "write naturally:  " + text, font=font(40), fill=t["label"])
    out = HERE / f"guide-sheet-{theme}.png"
    im.save(out, optimize=True)
    print(out.name, im.size)


if __name__ == "__main__":
    for theme in THEMES:
        draw(theme)
