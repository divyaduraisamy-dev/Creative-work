# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy", "scipy", "potracer", "fonttools", "brotli"]
# ///
"""Build "Divya's Handwriting" from the handwriting sheet.

    uv run ui-scrapbook/custom-features/assets/fonts/divya-handwriting/build_font.py

(The tools above load only for this script; they are not site dependencies.)

Reads sheet.png (the handwriting sheet: white ink = 255 on black) and writes, next to this file:
    divya-handwriting.woff2   the web font (the site uses this)
    divya-handwriting.otf     the same font to install on a computer (double-click it)
    specimen.png              every letter cut from the sheet with its character, to check the cutting

How it works: the sheet is cut into separate marks, marks are grouped into letters (dots and
accents join the letter under or over them), each row is matched to its list of characters
below, and each letter is traced into smooth outlines. Rows 1-2 (lowercase) and 3-4 (capitals)
are two versions of the same letters: typing alternates between them, so double letters differ.

To change a letter: redraw it on the sheet (same place, same order), export the sheet again as
sheet.png, rerun this script, then rebuild the site (uv run python build_static.py).
To add characters: add a row to the sheet and to ROWS below.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import potrace
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
FAMILY = "Divya's Handwriting"
PS_NAME = "DivyasHandwriting-Regular"
UNITS_PER_PX = 10          # font units per sheet pixel (capitals come out about 700 units tall)
UPSCALE = 4                # letters are enlarged before tracing for smoother outlines
SIDE_BEARING = 70          # space left and right of each letter, in font units
SPACE_WIDTH = 330

# Each row of the sheet: the characters in reading order, and the line through the row's middle
# as (x, y) at its left and right end (sheet pixels; the rows on the sheet slope a little).
# x_range limits a row to part of the sheet. "base" lists characters that sit on the baseline,
# used to find each row's baseline. "size" scales a row to match another (the accented letters
# were written smaller than the alphabet rows).


@dataclass
class Row:
    name: str
    chars: list[str]
    left: tuple[float, float]
    right: tuple[float, float]
    base: str
    x_range: tuple[float, float] = (0, 10_000)
    suffix: str = ""           # glyph-name suffix (".alt" for the second alphabet rows)
    size_like: str | None = None  # scale this row so its letters match that row's height
    glyphs: list = field(default_factory=list)


LOWER = list("abcdefghijklmnopqrstuvwxyz")
UPPER = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ROWS = [
    Row("lower", LOWER, (60, 384), (2060, 344), "acemnorsuvwxz"),
    Row("lower2", LOWER, (60, 500), (2060, 432), "acemnorsuvwxz", suffix=".alt"),
    Row("upper", UPPER, (50, 641), (2060, 528), "ABCDEFHIKLMNPRSTUVWXZ"),
    Row("upper2", UPPER, (50, 766), (2060, 642), "ABCDEFHIKLMNPRSTUVWXZ", suffix=".alt"),
    Row("figures", list("0123456789%$¢£&*@#“°”<>"), (50, 905), (2140, 790), "0123456789"),
    Row("symbols", list("?!¿¡()[]{}/\\©+×=_…"), (30, 1000), (2010, 987), "?!+="),
    Row("punct", list(",:;-—.‘’"), (30, 1180), (800, 1150), ":", x_range=(0, 820)),
    Row("accents", list("áâàäåãéêèëíîìïıñóôöõøšúûù"), (840, 1150), (2430, 1088), "áâàäåãéêèëóôöõúûù",
        x_range=(820, 10_000), size_like="lower"),
    Row("accents_upper", list("ÁÂÀÄÅÃÉÊÈËÍÎÌÏÑÓÔÖÕØŠÚÛÙ"), (840, 1280), (2430, 1140), "ÁÂÀÄÅÃÉÊÈËÍÎÌÏÑÓÔÖÕØŠÚÛÙ",
        x_range=(820, 10_000), size_like="upper"),
]

# Characters that need moving after cutting: the degree sign sits at the top of the figures,
# the asterisk is raised like a footnote star.
RAISE_TO_CAP = {"°", "*"}
# Extra keys that share a drawing: straight quotes use the curly closing ones.
SHARED = {"”": ['"'], "’": ["'"]}


@dataclass
class Mark:
    y0: int
    y1: int
    x0: int
    x1: int
    area: int
    label: int

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


def row_y(row: Row, x: float) -> float:
    (xa, ya), (xb, yb) = row.left, row.right
    return ya + (yb - ya) * (x - xa) / (xb - xa)


def x_overlap(a, b, tol=8) -> bool:
    return a.x0 - tol < b.x1 and b.x0 - tol < a.x1


def cut(ink: np.ndarray):
    """Cut the sheet into letters: a list of (row, [marks]) per character, in reading order."""
    labels, _ = ndimage.label(ink, structure=np.ones((3, 3)))
    marks = []
    for i, sl in enumerate(ndimage.find_objects(labels)):
        m = Mark(sl[0].start, sl[0].stop, sl[1].start, sl[1].stop, int((labels[sl] == i + 1).sum()), i + 1)
        if m.x1 - m.x0 > 1000:  # the line drawn across the sheet
            continue
        marks.append(m)
    def is_body(m):  # a letter's main stroke (short i stems count; dots and accents don't)
        h, w = m.y1 - m.y0, m.x1 - m.x0
        return m.area >= 300 or h >= 35 or (h >= 20 and h > 1.8 * w)

    big = [m for m in marks if is_body(m)]
    small = [m for m in marks if not is_body(m)]

    def inside(s, b, pad=4):
        return s.x0 < b.x1 + pad and b.x0 - pad < s.x1 and s.y0 < b.y1 + pad and b.y0 - pad < s.y1

    groups = [[m] for m in big]
    loose = []
    for s in small:
        # Marks inside a letter's box belong to it (the circles of %); accents and dots join the
        # letter under them; failing that, the letter over them (! ?).
        within = [g for g in groups if inside(s, g[0])]
        if within:
            within[0].append(s)
            continue
        below = [g for g in groups if x_overlap(s, g[0]) and 0 <= g[0].y0 - s.y1 <= 45]
        above = [g for g in groups if x_overlap(s, g[0]) and 0 <= s.y0 - g[0].y1 <= 45]
        if below:
            min(below, key=lambda g: g[0].y0 - s.y1).append(s)
        elif above:
            min(above, key=lambda g: s.y0 - g[0].y1).append(s)
        else:
            loose.append(s)
    # Loose marks that belong together (i and its dot, = : and quote marks) become one letter.
    loose_groups: list[list[Mark]] = []
    for s in loose:
        for g in loose_groups:
            if any((x_overlap(s, o) and abs(s.cy - o.cy) <= 60)
                   or (abs(s.cy - o.cy) <= 15 and min(abs(s.x0 - o.x1), abs(o.x0 - s.x1)) <= 14
                       and min(s.y1 - s.y0, o.y1 - o.y0) >= 12) for o in g):  # quote-mark ticks
                g.append(s)
                break
        else:
            loose_groups.append([s])
    groups += loose_groups

    def box(g):
        return Mark(min(m.y0 for m in g), max(m.y1 for m in g), min(m.x0 for m in g), max(m.x1 for m in g),
                    sum(m.area for m in g), 0)

    per_row: dict[str, list] = {r.name: [] for r in ROWS}
    for g in groups:
        main = max(g, key=lambda m: m.area)
        b = box(g)
        options = [r for r in ROWS if r.x_range[0] <= b.cx < r.x_range[1]]
        row = min(options, key=lambda r: abs(row_y(r, main.cx) - main.cy))
        per_row[row.name].append(g)

    out = []
    for row in ROWS:
        found = sorted(per_row[row.name], key=lambda g: box(g).cx)
        # Letters drawn in strokes that don't touch (G, 5, ©, %, quote marks): overlapping side to side.
        merged: list[list[Mark]] = []
        for g in found:
            if merged:
                a, b = box(merged[-1]), box(g)
                overlap = min(a.x1, b.x1) - max(a.x0, b.x0)
                ticks = (a.x1 - a.x0 <= 16 and b.x1 - b.x0 <= 16 and -14 <= overlap
                         and min(a.y1, b.y1) - max(a.y0, b.y0) > 10)  # the two strokes of a quote mark
                if overlap >= 0.3 * min(a.x1 - a.x0, b.x1 - b.x0) or ticks:
                    merged[-1] = merged[-1] + g
                    continue
            merged.append(g)
        found = merged
        if row.name == "symbols" and len(found) == len(row.chars) + 2:
            found = found[:-3] + [sum(found[-3:], [])]  # the three dots of …
        if row.name == "figures":
            # The degree sign sits low between the quote marks: order by size, not position.
            pass
        if len(found) != len(row.chars):
            print(f"row {row.name}: found {len(found)} letters, expected {len(row.chars)}", file=sys.stderr)
        row.glyphs = list(zip(row.chars, found))
        out.append(row)
    return labels, out


def specimen(ink: np.ndarray, labels: np.ndarray, rows: list[Row], path: Path) -> None:
    """A sheet of every cut letter with its character, to check the cutting."""
    cell = 90
    width = max(len(r.chars) for r in rows) * cell
    img = Image.new("L", (width, cell * len(rows) * 2), 255)
    draw = ImageDraw.Draw(img)
    for ri, row in enumerate(rows):
        for ci, (ch, g) in enumerate(row.glyphs):
            y0, y1 = min(m.y0 for m in g), max(m.y1 for m in g)
            x0, x1 = min(m.x0 for m in g), max(m.x1 for m in g)
            keep = np.isin(labels[y0:y1, x0:x1], [m.label for m in g])
            crop = Image.fromarray(np.where(keep, 0, 255).astype(np.uint8))
            crop.thumbnail((cell - 10, cell - 10))
            img.paste(crop, (ci * cell + 5, ri * cell * 2 + 5))
            draw.text((ci * cell + 30, ri * cell * 2 + cell + 10), ch, fill=0)
    img.save(path)


def baseline(row: Row):
    """The row's baseline as y(x), following the row's curve: near each letter, a line through the
    bottoms of nearby letters that sit on the baseline (closer letters count more)."""
    pts = [(np.mean([(m.x0 + m.x1) / 2 for m in g]), max(m.y1 for m in g)) for ch, g in row.glyphs if ch in row.base]
    xs, ys = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
    (xa, ya), (xb, yb) = row.left, row.right
    slope = (yb - ya) / (xb - xa)
    if len(pts) < 4:
        icpt = float(np.median(ys - slope * xs))
        return lambda x: slope * x + icpt

    def y_at(x: float) -> float:
        w = np.exp(-(((xs - x) / 250) ** 2)) + 1e-6
        a, b = np.polyfit(xs, ys, 1, w=np.sqrt(w))
        resid = np.abs(ys - (a * xs + b))
        keep = resid <= max(8, np.median(resid) * 2)  # ignore letters that dip or float
        a, b = np.polyfit(xs[keep], ys[keep], 1, w=np.sqrt(w[keep]))
        return a * x + b
    return y_at


def body_height(row: Row, chars: str) -> float:
    """Typical height of the main stroke of these letters in a row (sheet pixels)."""
    hs = [max(m.y1 - m.y0 for m in g) for ch, g in row.glyphs if ch in chars]
    return float(np.median(hs))


def trace(gray: np.ndarray, labels: np.ndarray, g: list[Mark]):
    """Outlines of one letter, as closed paths of ("line"|"curve", points) in sheet pixels."""
    pad = 6
    y0, y1 = max(min(m.y0 for m in g) - pad, 0), max(m.y1 for m in g) + pad
    x0, x1 = max(min(m.x0 for m in g) - pad, 0), max(m.x1 for m in g) + pad
    own = ndimage.binary_dilation(np.isin(labels[y0:y1, x0:x1], [m.label for m in g]), iterations=2)
    crop = Image.fromarray((gray[y0:y1, x0:x1] * own).astype(np.uint8))
    big = crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.BICUBIC)
    bm = potrace.Bitmap(np.array(big) <= 127)  # the tracer fills the False areas: ink = False
    paths = []
    for curve in bm.trace(turdsize=40, alphamax=1.0, opticurve=True, opttolerance=0.3):
        def pt(p):
            return (x0 + p.x / UPSCALE, y0 + p.y / UPSCALE)
        segs = []
        for seg in curve.segments:
            if seg.is_corner:
                segs.append(("line", [pt(seg.c), pt(seg.end_point)]))
            else:
                segs.append(("curve", [pt(seg.c1), pt(seg.c2), pt(seg.end_point)]))
        paths.append((pt(curve.start_point), segs))
    return paths


def glyph_name(ch: str, suffix: str = "") -> str:
    return f"uni{ord(ch):04X}{suffix}"


def build(gray: np.ndarray, labels: np.ndarray, rows: list[Row]) -> None:
    by_name = {r.name: r for r in rows}
    scale = {}
    for row in rows:
        k = UNITS_PER_PX
        if row.size_like:
            ref = by_name[row.size_like]
            ref_chars = ref.base
            k *= body_height(ref, ref_chars) / body_height(row, row.base)
        scale[row.name] = k

    outlines = {}   # glyph name -> (paths in font units, advance)
    cmap = {}
    for row in rows:
        base_y = baseline(row)
        k = scale[row.name]
        for ch, g in row.glyphs:
            gx0 = min(m.x0 for m in g)
            cx = np.mean([(m.x0 + m.x1) / 2 for m in g])
            by = base_y(cx)
            width = (max(m.x1 for m in g) - gx0) * k
            raw = trace(gray, labels, g)
            paths = [([((x - gx0) * k + SIDE_BEARING, (by - y) * k)
                       for x, y in [start]][0],
                      [(kind, [((x - gx0) * k + SIDE_BEARING, (by - y) * k) for x, y in pts]) for kind, pts in segs])
                     for start, segs in raw]
            name = glyph_name(ch, row.suffix)
            outlines[name] = (paths, round(width + 2 * SIDE_BEARING))
            if not row.suffix:
                cmap[ord(ch)] = name
                for extra in SHARED.get(ch, []):
                    cmap[ord(extra)] = name

    def top(name):
        return max(y for start, segs in outlines[name][0] for _, pts in segs for _, y in pts)

    def bottom(name):
        return min(y for start, segs in outlines[name][0] for _, pts in segs for _, y in pts)

    cap = float(np.median([top(glyph_name(c)) for c in "HIKLMNTXZ"]))
    xheight = float(np.median([top(glyph_name(c)) for c in "xvwz"]))
    for ch in RAISE_TO_CAP:
        name = glyph_name(ch)
        dy = cap - top(name)
        paths, adv = outlines[name]
        outlines[name] = ([((sx, sy + dy), [(kind, [(x, y + dy) for x, y in pts]) for kind, pts in segs])
                           for (sx, sy), segs in paths], adv)

    order = [".notdef", "space"] + list(outlines)
    char_strings, metrics = {}, {}
    for name in order:
        if name in (".notdef", "space"):
            pen = T2CharStringPen(SPACE_WIDTH, None)
            metrics[name] = (SPACE_WIDTH, 0)
        else:
            paths, adv = outlines[name]
            pen = T2CharStringPen(adv, None)
            for start, segs in paths:
                pen.moveTo(start)
                for kind, pts in segs:
                    if kind == "line":
                        for p in pts:
                            pen.lineTo(p)
                    else:
                        pen.curveTo(*pts)
                pen.closePath()
            xs = [x for start, segs in paths for _, pts in segs for x, _ in pts] or [0]
            metrics[name] = (adv, round(min(xs)))
        char_strings[name] = pen.getCharString()
    cmap[0x20] = "space"
    cmap[0xA0] = "space"

    ascent = round(max(top(n) for n in outlines)) + 20
    descent = round(min(bottom(n) for n in outlines)) - 20
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(PS_NAME, {"FullName": f"{FAMILY} Regular"}, char_strings, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupNameTable({
        "familyName": FAMILY, "styleName": "Regular", "fullName": f"{FAMILY} Regular",
        "psName": PS_NAME, "version": "Version 1.000", "uniqueFontIdentifier": f"{PS_NAME};1.000",
        "copyright": "Handwriting by Divya Duraisamy",
    })
    fb.setupOS2(sTypoAscender=ascent, sTypoDescender=descent, sTypoLineGap=0,
                usWinAscent=ascent, usWinDescent=-descent, sxHeight=round(xheight), sCapHeight=round(cap),
                achVendID="NONE", fsType=0)
    fb.setupPost()
    # Typing alternates between the two versions of each letter: a letter right after a
    # first-version letter takes its second version, so double letters never look the same.
    pairs = [(glyph_name(c), glyph_name(c, ".alt")) for c in LOWER + UPPER]
    addOpenTypeFeaturesFromString(fb.font, f"""
languagesystem DFLT dflt;
languagesystem latn dflt;
@first = [{" ".join(a for a, _ in pairs)}];
@second = [{" ".join(b for _, b in pairs)}];
feature calt {{
    sub @first @first' by @second;
}} calt;
""")
    fb.save(HERE / "divya-handwriting.otf")
    fb.font.flavor = "woff2"
    fb.save(HERE / "divya-handwriting.woff2")
    print(f"wrote divya-handwriting.otf and .woff2: {len(outlines)} letters, cap height {cap:.0f}, x-height {xheight:.0f}")


if __name__ == "__main__":
    sheet = np.array(Image.open(HERE / "sheet.png").convert("L"))
    labels, rows = cut(sheet > 100)
    specimen(sheet, labels, rows, HERE / "specimen.png")
    build(sheet, labels, rows)
    for row in rows:  # --show ROW: where each letter of a row was cut from
        if "--show" in sys.argv and row.name in sys.argv:
            for ch, g in row.glyphs:
                print(row.name, ch, [(m.x0, m.x1, m.y0, m.y1, m.area) for m in g])
