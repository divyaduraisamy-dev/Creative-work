# /// script
# dependencies = ["pillow", "numpy", "scipy", "potracer", "fonttools", "brotli"]
# ///
"""Build "Neat Handwriting" from the drawn guide sheet (sheet.png).

    uv run ui-scrapbook/custom-features/assets/fonts/neat-handwriting/build_font.py

sheet.png is the guide sheet from make_sheet.py with one character drawn in each box (it may be
scaled; the builder finds the boxes by their blue lines). Each box's ink becomes that character.
Letters are set on the guide baseline (small wobbles are snapped onto it, so text lines up), and
the space between letters and words is measured from the two "write naturally" lines.

Writes neat-handwriting.otf (install on a computer), neat-handwriting.woff2 (web) and
specimen.png (every letter as cut, to check).
"""
import sys
from pathlib import Path

import numpy as np
import potrace
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_sheet as guide  # noqa: E402  (the sheet layout: boxes, guide lines, sample strips)

FAMILY = "Neat Handwriting"
PS_NAME = "NeatHandwriting-Regular"
CAP_HEIGHT = 700           # font units for a capital
UPSCALE = 6                # letters are enlarged before tracing for smoother outlines
BOLDEN = 14                # font units added around every stroke so it holds up at reading size
EXTRA_SPACE = 22            # font units added each side of a letter, a touch roomier than the samples, for reading
DESCENDERS = set("gjpqy,;")
CENTRE_ON_X = set("-–")    # dashes sit at the middle of the small letters


def load():
    """The drawn sheet on white, as (rgb, ink mask)."""
    im = Image.open(HERE / "sheet.png").convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    rgb = np.asarray(flat.convert("RGB")).astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    bluish = (b - r) > 35                      # guides and labels
    return rgb, (lum < 130) & ~bluish


def blue_profile(rgb, axis):
    r, b = rgb[..., 0], rgb[..., 2]
    blue = ((b - r) > 20) & (b > 170)
    return blue.sum(axis=axis).astype(float)


def fit(profile, expected, lo, hi, n):
    """Scale and offset that best put the guide's lines (expected, sheet px) on the drawn sheet's."""
    best = (-1, 0, 0)
    prof = ndimage.uniform_filter1d(profile, 3)
    ex = np.asarray(expected, float)
    for s in np.linspace(lo, hi, n):
        span = int(len(profile) - ex.max() * s)
        for o in range(min(0, span), max(1, span + 1)):
            idx = np.round(ex * s + o).astype(int)
            ok = (idx >= 0) & (idx < len(prof))
            score = prof[idx[ok]].sum()
            if score > best[0]:
                best = (score, s, o)
    return best[1], best[2]


def locate(rgb):
    """How the guide sheet was scaled and placed: (scale, x offset, y offset)."""
    h, w = rgb.shape[:2]
    s0 = min(w / guide.W, h / guide.H)
    ys, xs = [], []
    for _, (x0, y0, x1, y1) in guide.CELLS:
        ys += [round(y0 + share * (y1 - y0)) for share in guide.LINES.values()] + [y0 + 8, y1 - 8]
        xs += [x0 + 8, x1 - 8]
    s, oy = fit(blue_profile(rgb, 1), sorted(set(ys)), s0 * 0.96, s0 * 1.0001, 160)
    _, ox = fit(blue_profile(rgb, 0), sorted(set(xs)), s, s, 1)
    return s, ox, oy


def cut(rgb, ink, s, ox, oy):
    """{char: (mask crop, (x0, y0) of the crop, baseline y, x-height line y)} in drawn-sheet pixels."""
    found, missing = {}, []
    lab, _ = ndimage.label(ink, structure=np.ones((3, 3)))
    for ch, (x0, y0, x1, y1) in guide.CELLS:
        X0, X1 = round(x0 * s + ox + 12 * s), round(x1 * s + ox - 12 * s)
        Y0, Y1 = round(y0 * s + oy + 12 * s), round(y1 * s + oy - 12 * s)
        base = (y0 + guide.LINES["base"] * (y1 - y0)) * s + oy
        xline = (y0 + guide.LINES["x"] * (y1 - y0)) * s + oy
        # the ink of this box: every mark that is mostly inside it (strokes may stray over the edge)
        inside = lab[Y0:Y1, X0:X1]
        ids = [i for i in np.unique(inside) if i and (inside == i).sum() >= 4]
        if not ids:
            missing.append(ch)
            continue
        mask = np.isin(lab, ids)
        yy, xx = np.where(mask)
        found[ch] = (mask[yy.min():yy.max() + 1, xx.min():xx.max() + 1], (xx.min(), yy.min()), base, xline)
    if missing:
        print("empty boxes:", " ".join(missing))
    return found


def spacing(ink, s, ox, oy):
    """Typical gap between letters and between words in the sample lines, as shares of the x-height."""
    letter, word = [], []
    for _, (x0, y0, x1, y1) in guide.SAMPLE_BOXES:
        Y0, Y1 = round((y0 + 70) * s + oy), round(y1 * s + oy)
        strip = ink[Y0:Y1, :]
        lab, n = ndimage.label(strip, structure=np.ones((3, 3)))
        boxes = [b for b in ndimage.find_objects(lab) if b is not None]
        spans = sorted([[b[1].start, b[1].stop, b[0].start, b[0].stop] for b in boxes
                        if (b[1].stop - b[1].start) * (b[0].stop - b[0].start) > 12])
        letters = []  # marks that overlap sideways (an i and its dot) are one letter
        for sp in spans:
            if letters and sp[0] < letters[-1][1] - 2:
                letters[-1] = [letters[-1][0], max(letters[-1][1], sp[1]),
                               min(letters[-1][2], sp[2]), max(letters[-1][3], sp[3])]
            else:
                letters.append(sp)
        heights = sorted(l[3] - l[2] for l in letters)
        xh = float(np.median(heights[: max(3, len(heights) // 2)]))   # the shorter half: small letters
        gaps = np.array([b[0] - a[1] for a, b in zip(letters, letters[1:])], float) / xh
        cut_at = (np.median(gaps) + gaps.max()) / 2
        for _ in range(10):                                            # two groups: letters, words
            lo, hi = gaps[gaps <= cut_at], gaps[gaps > cut_at]
            if not len(lo) or not len(hi):
                break
            cut_at = (lo.mean() + hi.mean()) / 2
        letter += list(gaps[gaps <= cut_at])
        word += list(gaps[gaps > cut_at])
    return float(np.median(letter)), float(np.median(word))


def trace(mask):
    """Outlines of a mask as closed paths of ("line"|"curve", points), in mask pixels."""
    pad = 4
    img = Image.fromarray(np.pad(mask, pad).astype(np.uint8) * 255)
    big = np.array(img.resize((img.width * UPSCALE, img.height * UPSCALE), Image.BICUBIC)) > 110
    big = ndimage.binary_dilation(big, iterations=max(1, round(BOLDEN * UPSCALE / UNITS_PX[0])))
    bm = potrace.Bitmap(~big)  # the tracer fills the False areas: ink = False
    paths = []
    for curve in bm.trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.25):
        def pt(p):
            return (p.x / UPSCALE - pad, p.y / UPSCALE - pad)
        segs = [("line", [pt(sg.c), pt(sg.end_point)]) if sg.is_corner else
                ("curve", [pt(sg.c1), pt(sg.c2), pt(sg.end_point)]) for sg in curve.segments]
        paths.append((pt(curve.start_point), segs))
    return paths


UNITS_PX = [10.0]  # font units per drawn-sheet pixel (set once the capitals are measured)


def glyph_name(ch):
    return f"uni{ord(ch):04X}"


def build():
    rgb, ink = load()
    s, ox, oy = locate(rgb)
    print(f"sheet found at {s:.4f}x, offset ({ox}, {oy})")
    cells = cut(rgb, ink, s, ox, oy)
    caps = [m.shape[0] for c, (m, *_rest) in cells.items() if c in "EFHIKLMNTXZ"]
    UNITS_PX[0] = CAP_HEIGHT / float(np.median(caps))
    k = UNITS_PX[0]
    xh_px = float(np.median([cells[c][2] - cells[c][1][1] for c in "acemnorsuvwxz" if c in cells]))
    letter_gap, word_gap = spacing(ink, s, ox, oy)
    side = round(letter_gap * xh_px * k / 2) + EXTRA_SPACE
    space = round(word_gap * xh_px * k - 2 * (side - EXTRA_SPACE))  # word gaps stay as wide as yours
    print(f"x-height {xh_px * k:.0f} units, side bearing {side}, space {space}")

    outlines, cmap = {}, {}
    for ch, (mask, (mx, my), base, xline) in cells.items():
        bottom = my + mask.shape[0]
        # snap small wobbles onto the baseline so letters line up (not tails, not raised marks)
        if ch not in DESCENDERS and abs(bottom - base) < 0.18 * xh_px:
            base = bottom
        if ch in CENTRE_ON_X:
            base = my + mask.shape[0] / 2 + xh_px / 2
        paths = trace(mask)
        width = mask.shape[1] * k
        conv = lambda x, y: (x * k + side, (base - (my + y)) * k)  # noqa: E731
        outlines[glyph_name(ch)] = ([(conv(*st), [(kind, [conv(*p) for p in pts]) for kind, pts in segs])
                                     for st, segs in paths], round(width + 2 * side))
        cmap[ord(ch)] = glyph_name(ch)

    def ys(name):
        return [y for _, segs in outlines[name][0] for _, pts in segs for _, y in pts]

    cap = float(np.median([max(ys(glyph_name(c))) for c in "HIKLMNTXZ"]))
    xheight = float(np.median([max(ys(glyph_name(c))) for c in "xvwz"]))
    order = [".notdef", "space"] + list(outlines)
    char_strings, metrics = {}, {}
    for name in order:
        if name in (".notdef", "space"):
            pen = T2CharStringPen(space, None)
            metrics[name] = (space, 0)
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
            xs = [x for _, segs in paths for _, pts in segs for x, _ in pts] or [0]
            metrics[name] = (adv, round(min(xs)))
        char_strings[name] = pen.getCharString()
    cmap[0x20] = cmap[0xA0] = "space"

    ascent = round(max(max(ys(n)) for n in outlines)) + 30
    descent = round(min(min(ys(n)) for n in outlines)) - 30
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
    fb.save(HERE / "neat-handwriting.otf")
    fb.font.flavor = "woff2"
    fb.save(HERE / "neat-handwriting.woff2")
    print(f"wrote neat-handwriting.otf and .woff2: {len(outlines)} characters, cap {cap:.0f}, x-height {xheight:.0f}")
    specimen()


def specimen():
    """Every character set in the finished font, plus a paragraph, to check by eye."""
    f = ImageFont.truetype(str(HERE / "neat-handwriting.otf"), 64)
    small = ImageFont.truetype(str(HERE / "neat-handwriting.otf"), 30)
    im = Image.new("RGB", (1800, 760), "white")
    d = ImageDraw.Draw(im)
    lines = ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789 .,'’\"“”?!:;-–()/&"]
    for i, t in enumerate(lines):
        d.line([(40, 110 + i * 110), (1760, 110 + i * 110)], fill=(170, 200, 235), width=2)
        d.text((40, 110 + i * 110), t, font=f, fill="black", anchor="ls")
    para = ("Food pantry clients pick the ingredients they received, and the app shows recipes that",
            "match, sorted by how quickly they can be made. It works with a full kitchen or a microwave.")
    for i, t in enumerate(para):
        d.text((40, 480 + i * 52), t, font=small, fill="black", anchor="ls")
    d.text((40, 650), "The quick brown fox jumps over the lazy dog.", font=f, fill="black", anchor="ls")
    im.save(HERE / "specimen.png")


if __name__ == "__main__":
    build()
