"""Draw the stand-in pictures for Keep or Toss, until Divya's own drawings replace them.

    uv run python ui-scrapbook/custom-features/assets/keep-or-toss/stand-ins/make_stand_ins.py

Each food gets two SVG layers, like the Recipe Finder art:
    <slug>-ink.svg     thick black marker lines (the page shows them in its text colour, so they
                       turn cream on the dark page)
    <slug>-color.svg   loose looping scribbles in two or three shades of one colour, a little
                       uneven, sitting under the lines
Made in the style of Divya's can, fish and bowl: one even, round-ended marker line that wobbles
and sometimes runs past a corner; bright crayon colour filled with loops; no gradients or shadows.

A drawing of yours with the same name (bananas-color.webp + bananas-ink.webp, or bananas.png)
in the folder above this one is used instead, automatically.
"""

from __future__ import annotations

import math
import random
import zlib
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIZE = 600
INK_W = 13

# Colour sets: (colour, line width, row gap, loop size, opacity), lightest first.
def shades(light, mid, dark):
    return [(light, 9, 16, 22, 1), (mid, 7, 22, 18, 0.95), (dark, 5, 34, 14, 0.85)]

YELLOW = shades("#ffe14d", "#ffc21a", "#f5a300")
RED = shades("#ff5a52", "#e8243c", "#a3122a")
GREEN = shades("#a6e35a", "#4cbb3a", "#1f7a2e")
DARK_GREEN = shades("#5fae3c", "#2f7d2a", "#174f1d")
PALE_GREEN = shades("#e4f5a1", "#c9e76b", "#9ccc45")
BLUE = shades("#49b6f2", "#4f6bd8", "#1e2a8a")
PALE_BLUE = shades("#d6eefc", "#bfe3fb", "#8fcdf5")
ORANGE = shades("#ffb14d", "#ff8a1f", "#d9590b")
PINK = shades("#ffb3d1", "#ff6fae", "#d62f80")
PURPLE = shades("#c79bff", "#8f4fe0", "#55208f")
BROWN = shades("#e6b27a", "#b5763a", "#7a4a1d")
TAN = shades("#fbe3b0", "#efc275", "#cf9443")
CREAM = [("#fff4d4", 8, 18, 22, 1), ("#f6e2ac", 5, 28, 16, 0.85)]
GREY = shades("#e3e8ec", "#b9c2cb", "#8a949e")
SALMON = shades("#ffc9b0", "#ff9a7a", "#e0674a")
MEAT = shades("#ff9aa2", "#e04e5c", "#a8243a")


# ---------- shapes ----------
def ellipse(cx, cy, rx, ry, n=28, start=0.0):
    return [(cx + rx * math.cos(start + 2 * math.pi * k / n), cy + ry * math.sin(start + 2 * math.pi * k / n)) for k in range(n)]


def egg(cx, cy, rx, ry, k=0.25, n=32):
    """Narrow at the top when k > 0, narrow at the bottom when k < 0."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        pts.append((cx + rx * math.sin(t) * (1 - k * math.cos(t)), cy - ry * math.cos(t)))
    return pts


def wavy(cx, cy, r, waves=9, depth=0.12, n=72, squash=1.0):
    return [(cx + r * (1 + depth * math.sin(waves * t)) * math.cos(t),
             cy + squash * r * (1 + depth * math.sin(waves * t)) * math.sin(t))
            for t in (2 * math.pi * i / n for i in range(n))]


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def star(cx, cy, r1, r2, points=5, turn=-math.pi / 2):
    out = []
    for i in range(points * 2):
        r = r1 if i % 2 == 0 else r2
        t = turn + math.pi * i / points
        out.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return out


def arc(cx, cy, rx, ry, a0, a1, n=16):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def move(points, dx=0, dy=0):
    return [(x + dx, y + dy) for x, y in points]


# ---------- drawing ----------
def smooth(points, closed=False):
    pts = points + points[:3] if closed else [points[0]] + points + [points[-1]]
    d = f"M{pts[1][0]:.1f},{pts[1][1]:.1f}"
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def densify(points, step=38, closed=False):
    out = []
    seq = points + [points[0]] if closed else points
    for (x1, y1), (x2, y2) in zip(seq, seq[1:]):
        n = max(1, int(math.dist((x1, y1), (x2, y2)) // step))
        out += [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n) for k in range(n)]
    if not closed:
        out.append(seq[-1])
    return out


def scribble(box, rng, gap, radius, speed=9, jitter=3):
    x0, y0, x1, y1 = box
    pts, y, row, theta, spin = [], y0, 0, rng.uniform(0, 6.3), 1
    while y <= y1 + gap:
        xs = (x0 - radius, x1 + radius) if row % 2 == 0 else (x1 + radius, x0 - radius)
        direction = 1 if xs[1] > xs[0] else -1
        x = xs[0]
        while (x - xs[1]) * direction < 0:
            r = radius * rng.uniform(0.5, 1.6)
            pts.append((x + r * math.cos(theta) + rng.uniform(-jitter, jitter),
                        y + r * math.sin(theta) * rng.uniform(0.6, 1.1) + rng.uniform(-jitter, jitter)))
            if rng.random() < 0.04:
                spin = -spin
            theta += spin * rng.uniform(0.35, 0.95)
            x += direction * speed * rng.uniform(0.3, 1.1)
        y += gap * rng.uniform(0.7, 1.25)
        row += 1
    return smooth(pts)


@dataclass
class Drawing:
    rng: random.Random
    ink: list[str] = field(default_factory=list)
    color: list[str] = field(default_factory=list)
    defs: list[str] = field(default_factory=list)

    def line(self, points, closed=False, wobble=3.5, overshoot=True, width=None):
        pts = [(x + self.rng.uniform(-wobble, wobble), y + self.rng.uniform(-wobble, wobble))
               for x, y in densify(points, closed=closed)]
        if closed and overshoot and len(pts) > 2:
            pts = pts + pts[:2]
            pts[-1] = (pts[-1][0] + self.rng.uniform(4, 9), pts[-1][1] + self.rng.uniform(-6, 6))
        w = f' stroke-width="{width}"' if width else ""
        self.ink.append(f'<path d="{smooth(pts)}"{w}/>')

    def fill(self, points, palette, straight=False, scale=1.0):
        """Loopy scribbles in a few shades, clipped to the shape."""
        cid = f"c{len(self.defs)}"
        outline = ("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z") if straight else smooth(points, closed=True)
        self.defs.append(f'<clipPath id="{cid}"><path d="{outline}"/></clipPath>')
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        box = (min(xs), min(ys), max(xs), max(ys))
        body = "".join(
            f'<path d="{scribble(box, self.rng, gap * scale, radius * scale)}" fill="none" stroke="{colour}" '
            f'stroke-width="{width * max(scale, 0.6):.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"/>'
            for colour, width, gap, radius, opacity in palette)
        self.color.append(f'<g clip-path="url(#{cid})">{body}</g>')

    def dot(self, cx, cy, r, colour):
        pts = ellipse(cx, cy, r * self.rng.uniform(0.85, 1.15), r * self.rng.uniform(0.85, 1.15), n=10)
        self.color.append(f'<path d="{smooth(pts, closed=True)}" fill="{colour}"/>')

    def shape(self, points, palette=None, closed=True, straight=False, scale=1.0):
        if palette:
            self.fill(points, palette, straight=straight, scale=scale)
        self.line(points, closed=closed)

    def svg(self, layer: str) -> str:
        if layer == "ink":
            body = (f'<g fill="none" stroke="#000" stroke-width="{INK_W}" stroke-linecap="round" '
                    f'stroke-linejoin="round">{"".join(self.ink)}</g>')
            defs = ""
        else:
            body = "".join(self.color)
            defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" '
                f'height="{SIZE}">{defs}{body}</svg>\n')


# ---------- the foods ----------
def bananas(d):
    body = [(48, 230), (73, 325), (143, 405), (253, 445), (368, 432), (458, 378), (513, 300), (530, 250),
            (488, 250), (443, 295), (363, 328), (263, 336), (175, 316), (115, 270), (86, 220)]
    d.shape(body, YELLOW)
    stem = [(495, 256), (510, 200), (520, 170), (544, 176), (538, 210), (526, 256)]
    d.shape(stem, BROWN)
    d.line([(48, 230), (42, 208), (68, 200), (86, 220)])
    d.line([(112, 312), (182, 378), (276, 410)])
    for x, y in [(200, 370), (247, 396), (323, 404), (393, 378), (290, 366), (150, 330), (440, 340)]:
        d.dot(x, y, 9, "#7a4a1d")
    d.dot(64, 214, 12, "#5b3a1a")


def apples(d):
    cx, cy, r = 300, 345, 190
    pts = []
    for i in range(48):
        t = -math.pi + 2 * math.pi * i / 48
        dip = 0.2 * math.exp(-(t / 0.45) ** 2) + 0.08 * math.exp(-((abs(t) - math.pi) / 0.4) ** 2)
        pts.append((cx + 1.06 * r * math.sin(t), cy - r * math.cos(t) * 0.95 + r * dip))
    d.shape(pts, RED)
    d.line([(298, 200), (306, 150), (322, 112)])
    leaf = [(318, 150), (360, 112), (420, 104), (392, 150), (340, 166)]
    d.shape(leaf, GREEN)
    d.line([(212, 290), (196, 350), (214, 420)], wobble=2)


def avocados(d):
    outer = egg(300, 330, 175, 235, k=0.38)
    d.shape(outer, DARK_GREEN)
    inner = egg(300, 345, 130, 190, k=0.36)
    d.shape(inner, PALE_GREEN)
    pit = ellipse(300, 410, 72, 78)
    d.shape(pit, BROWN)
    d.line(arc(285, 395, 36, 40, math.pi * 1.1, math.pi * 1.55), wobble=1.5)


def tomatoes(d):
    body = ellipse(300, 340, 205, 175, n=36)
    d.shape(body, RED)
    calyx = star(300, 190, 105, 30, points=5, turn=-math.pi / 2 + 0.3)
    d.shape(calyx, GREEN, straight=True)
    d.line([(300, 182), (304, 140), (316, 112)])
    d.line(arc(300, 340, 150, 120, math.pi * 1.15, math.pi * 1.4), wobble=1.5)


def berries(d):
    straw = egg(250, 320, 175, 200, k=-0.55)
    d.shape(straw, RED)
    leaves = [(110, 150), (160, 120), (200, 96), (250, 126), (300, 96), (340, 120), (390, 150), (330, 160), (250, 150), (170, 160)]
    d.shape(leaves, GREEN)
    for x, y in [(190, 230), (260, 220), (320, 240), (220, 300), (290, 310), (190, 370), (250, 390), (310, 360), (250, 460)]:
        d.dot(x, y, 8, "#ffe14d")
        d.line([(x - 4, y - 6), (x + 3, y + 6)], wobble=0.5, width=7)
    for cx, cy, r in [(470, 420, 62), (420, 500, 54), (520, 505, 50)]:
        b = ellipse(cx, cy, r, r * 0.95)
        d.shape(b, BLUE, scale=0.6)
        d.line(star(cx, cy - r * 0.2, 14, 6, points=5), closed=True, wobble=1, width=7)


def grapes(d):
    rows = [(5, 170), (4, 240), (3, 310), (2, 380), (1, 450)]
    r = 46
    for count, y in rows:
        x0 = 300 - (count - 1) * r
        for i in range(count):
            g = ellipse(x0 + 2 * r * i, y, r, r * 1.05, n=18)
            d.shape(g, PURPLE, scale=0.55)
    d.line([(300, 124), (310, 80), (330, 50)])
    leaf = [(318, 92), (380, 60), (440, 60), (420, 100), (452, 128), (390, 140), (340, 118)]
    d.shape(leaf, GREEN)


def citrus(d):
    lemon = ellipse(390, 250, 150, 105, n=32, start=0.0)
    lemon = [(x, y) for x, y in lemon]
    lemon[0] = (lemon[0][0] + 28, lemon[0][1])
    lemon[16] = (lemon[16][0] - 28, lemon[16][1])
    d.shape(lemon, YELLOW)
    orange = ellipse(255, 385, 175, 170, n=36)
    d.shape(orange, ORANGE)
    d.line([(255, 215), (262, 180)])
    leaf = [(262, 196), (300, 160), (360, 150), (330, 196), (286, 212)]
    d.shape(leaf, GREEN)
    for x, y in [(190, 330), (300, 450), (210, 460), (320, 330)]:
        d.dot(x, y, 6, "#d9590b")


def leafy_greens(d):
    outer = wavy(300, 330, 215, waves=11, depth=0.09, squash=0.9)
    d.shape(outer, GREEN)
    inner = wavy(300, 330, 140, waves=9, depth=0.12, squash=0.9)
    d.shape(inner, PALE_GREEN)
    for a in (-0.6, 0.0, 0.6, 2.5, 3.14, 3.8):
        d.line([(300 + 40 * math.cos(a), 330 + 36 * math.sin(a)), (300 + 175 * math.cos(a), 330 + 155 * math.sin(a))], wobble=2.5)


def carrots(d):
    for (bx, by, tx, ty, w) in [(190, 210, 330, 540, 62), (330, 170, 470, 500, 56)]:
        ang = math.atan2(ty - by, tx - bx)
        nx, ny = -math.sin(ang), math.cos(ang)
        body = [(bx + nx * w, by + ny * w), ((bx + tx) / 2 + nx * w * 0.6, (by + ty) / 2 + ny * w * 0.6), (tx, ty),
                ((bx + tx) / 2 - nx * w * 0.6, (by + ty) / 2 - ny * w * 0.6), (bx - nx * w, by - ny * w),
                (bx - math.cos(ang) * 20, by - math.sin(ang) * 20)]
        d.shape(body, ORANGE)
        for k in (0.25, 0.45, 0.65):
            px, py = bx + (tx - bx) * k, by + (ty - by) * k
            d.line([(px + nx * w * (0.7 - k * 0.6), py + ny * w * (0.7 - k * 0.6)), (px + nx * w * 0.1, py + ny * w * 0.1)], wobble=1.5)
        for spread in (-0.5, -0.15, 0.2):
            a = ang + math.pi + spread
            top = [(bx - math.cos(ang) * 15, by - math.sin(ang) * 15)]
            top.append((top[0][0] + 70 * math.cos(a), top[0][1] + 70 * math.sin(a)))
            top.append((top[0][0] + 140 * math.cos(a + 0.12), top[0][1] + 140 * math.sin(a + 0.12)))
            d.fill([(p[0] + dx, p[1] + dy) for p in top for dx, dy in ((0, 0),)] + [(top[-1][0] + 14, top[-1][1]), (top[1][0] + 14, top[1][1])], GREEN, scale=0.5)
            d.line(top)


def potatoes(d):
    rng = d.rng
    base = ellipse(300, 330, 225, 160, n=26)
    blob = [(x + rng.uniform(-14, 14), y + rng.uniform(-12, 12)) for x, y in base]
    d.shape(blob, BROWN)
    for x, y in [(210, 290), (330, 260), (400, 360), (260, 400)]:
        d.line(arc(x, y, 16, 10, 0.2, math.pi - 0.2, n=6), wobble=1)
        d.dot(x, y + 4, 6, "#7a4a1d")


def onions(d):
    body = egg(300, 360, 185, 190, k=0.42)
    d.shape(body, TAN)
    d.line([(285, 172), (292, 120), (300, 84), (312, 120), (318, 172)])
    for off in (-110, -50, 50, 110):
        d.line([(300 + off * 0.25, 190), (300 + off, 360), (300 + off * 0.4, 535)], wobble=2)
    for dx in (-30, -10, 12, 32):
        d.line([(300 + dx * 0.4, 548), (300 + dx, 585)], wobble=2, width=8)


def broccoli(d):
    stem = [(255, 330), (345, 330), (362, 545), (238, 545)]
    d.shape(stem, PALE_GREEN, straight=True)
    for cx, cy, r in [(200, 270, 95), (300, 210, 110), (405, 270, 95), (250, 330, 80), (355, 330, 80)]:
        d.fill(wavy(cx, cy, r, waves=7, depth=0.1, n=40), GREEN, scale=0.8)
    for cx, cy, r in [(200, 270, 95), (300, 210, 110), (405, 270, 95)]:
        d.line(arc(cx, cy, r, r * 0.95, math.pi * 0.85, math.pi * 2.15, n=14))
    d.line([(285, 400), (262, 350)], wobble=2)
    d.line([(318, 410), (340, 350)], wobble=2)


def milk(d):
    front = [(170, 236), (400, 236), (400, 548), (170, 548)]
    side = [(400, 236), (482, 200), (482, 512), (400, 548)]
    d.fill([(170, 236), (400, 236), (400, 384), (345, 404), (300, 382), (255, 405), (210, 380), (170, 400)], [("#d6eefc", 6, 30, 20, 0.9)], straight=True)
    d.fill([(170, 400), (210, 380), (255, 405), (300, 382), (345, 404), (400, 384), (400, 548), (170, 548)], BLUE, straight=True)
    d.fill([(400, 384), (440, 362), (482, 372), (482, 512), (400, 548)], BLUE[1:], straight=True)
    d.fill([(400, 236), (482, 200), (482, 372), (440, 362), (400, 384)], PALE_BLUE, straight=True)
    d.fill([(170, 236), (285, 146), (370, 112), (482, 200), (400, 236)], PALE_BLUE[:1], straight=True)
    d.line(front, closed=True)
    d.line(side, closed=True)
    d.line([(170, 236), (285, 146), (400, 236)])
    d.line([(285, 146), (370, 112), (482, 200)])
    d.line([(280, 150), (280, 116), (366, 84), (366, 116)])
    d.line([(170, 400), (210, 380), (255, 405), (300, 382), (345, 404), (400, 384), (440, 362), (482, 372)])
    cap = ellipse(270, 200, 22, 18, n=10)
    d.shape(cap, RED, scale=0.4)


def eggs(d):
    for cx, cy, rx, ry, tilt in [(220, 340, 120, 155, -0.15), (390, 360, 115, 150, 0.2)]:
        pts = egg(0, 0, rx, ry, k=0.18)
        pts = [(cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)) for x, y in pts]
        d.shape(pts, CREAM)
    d.line([(90, 510), (510, 520)], wobble=3)


def hard_cheese(d):
    top = [(100, 300), (470, 190), (520, 300), (150, 400)]
    front = [(150, 400), (520, 300), (520, 430), (150, 530)]
    side = [(100, 300), (150, 400), (150, 530), (100, 430)]
    d.shape(front, YELLOW, straight=True)
    d.shape(top, YELLOW[:2], straight=True)
    d.shape(side, ORANGE[:1] + YELLOW[1:], straight=True)
    for cx, cy, r in [(260, 440, 22), (390, 400, 30), (450, 360, 14), (320, 300, 18), (230, 330, 12)]:
        d.line(ellipse(cx, cy, r, r * 0.8, n=10), closed=True, wobble=1.5, overshoot=False)


def soft_cheese(d):
    d.fill(ellipse(300, 300, 210, 90), CREAM, scale=1)
    d.fill(rect(90, 300, 420, 130), CREAM, straight=True)
    d.line(arc(300, 300, 210, 90, 0, 2 * math.pi, n=30))
    d.line([(90, 300), (90, 430)])
    d.line([(510, 300), (510, 430)])
    d.line(arc(300, 430, 210, 90, 0, math.pi, n=18))
    wedge = [(300, 300), (500, 270), (480, 350)]
    d.fill(wedge, YELLOW[:2], straight=True)
    d.line(wedge, closed=True)
    for x, y in [(180, 290), (240, 330), (380, 320), (200, 260)]:
        d.dot(x, y, 5, "#e6d6a8")


def shredded_cheese(d):
    bag = [(150, 120), (450, 120), (470, 520), (130, 520)]
    d.fill(bag, PALE_BLUE[:2], straight=True)
    d.line(bag, closed=True)
    d.line([(150, 170), (450, 170)], wobble=2)
    d.fill(ellipse(300, 360, 120, 110), ORANGE[:2], scale=0.8)
    rng = d.rng
    for _ in range(16):
        x, y = rng.uniform(200, 400), rng.uniform(270, 450)
        a = rng.uniform(0, math.pi)
        d.line([(x, y), (x + 34 * math.cos(a), y + 34 * math.sin(a)), (x + 60 * math.cos(a + 0.4), y + 60 * math.sin(a + 0.4))], wobble=1.5, width=8)
    d.line(ellipse(300, 360, 120, 110, n=24), closed=True, wobble=4)
    for x, y, a in [(160, 560, 0.3), (430, 555, 2.7), (520, 470, 1.9)]:
        d.line([(x, y), (x + 40 * math.cos(a), y + 30 * math.sin(a))], wobble=1, width=8)


def yogurt(d):
    cup = [(150, 200), (450, 200), (410, 520), (190, 520)]
    d.fill(cup, CREAM[:1], straight=True)
    band = [(162, 300), (438, 300), (425, 400), (175, 400)]
    d.fill(band, PINK, straight=True)
    d.line(cup, closed=True)
    d.line([(162, 300), (438, 300)], wobble=2)
    d.line([(175, 400), (425, 400)], wobble=2)
    lid = ellipse(300, 200, 165, 42)
    d.shape(lid, PALE_BLUE)
    d.line([(455, 195), (520, 150), (540, 170)], wobble=2)


def butter(d):
    top = [(90, 300), (380, 210), (520, 260), (230, 350)]
    front = [(90, 300), (230, 350), (230, 450), (90, 400)]
    side = [(230, 350), (520, 260), (520, 360), (230, 450)]
    d.shape(top, [("#fff3a6", 9, 16, 22, 1), ("#ffe46b", 6, 24, 16, 0.9)], straight=True)
    d.shape(front, YELLOW[:2], straight=True)
    d.shape(side, YELLOW, straight=True)
    wrap = [(330, 225), (520, 260), (520, 360), (330, 418)]
    d.line(wrap[:1] + [(330, 418)], wobble=2)
    d.line([(160, 380), (190, 330)], wobble=2)


def raw_chicken(d):
    meat = egg(250, 290, 170, 190, k=-0.3)
    meat = [(x, y) for x, y in meat]
    d.shape(meat, SALMON)
    bone = [(330, 410), (440, 500), (470, 480), (500, 500), (505, 540), (470, 555), (455, 530), (420, 530), (310, 440)]
    d.shape(bone, CREAM[:1])
    d.line(arc(240, 260, 90, 100, math.pi * 1.1, math.pi * 1.5), wobble=1.5)


def ground_beef(d):
    tray = [(80, 360), (520, 360), (480, 500), (120, 500)]
    d.fill(tray, PALE_BLUE[:2], straight=True)
    d.line(tray, closed=True)
    mound = []
    for i in range(40):
        t = math.pi + math.pi * i / 39
        r = 180 * (1 + 0.06 * math.sin(9 * t))
        mound.append((300 + 1.15 * r * math.cos(t), 370 + 0.75 * r * math.sin(t)))
    d.fill(mound + [(507, 370), (93, 370)], MEAT)
    d.line(mound)
    for x, y in [(220, 300), (300, 260), (380, 300), (260, 340), (340, 330)]:
        d.line([(x - 18, y), (x - 6, y - 10), (x + 6, y), (x + 18, y - 10)], wobble=1, width=7)
    d.line([(60, 330), (300, 180), (540, 330)], wobble=4, width=6)


def fish(d):
    fillet = [(70, 330), (140, 250), (300, 215), (460, 235), (540, 290), (520, 370), (420, 410), (260, 420), (120, 400)]
    d.shape(fillet, SALMON)
    for x in (170, 250, 330, 410):
        d.line([(x, 240), (x + 30, 320), (x - 10, 400)], wobble=2, width=8)
    d.line([(120, 470), (480, 480)], wobble=3)


def deli_meat(d):
    for cx, cy, r in [(250, 360, 175), (330, 300, 165), (290, 240, 150)]:
        d.shape(wavy(cx, cy, r, waves=14, depth=0.035, squash=0.55), PINK[:2])
    for x, y in [(240, 230), (330, 250), (290, 210)]:
        d.dot(x, y, 7, "#ffe6ef")


def bread(d):
    top = []
    for i in range(30):
        t = math.pi + math.pi * i / 29
        top.append((300 + 230 * math.cos(t), 290 + 140 * math.sin(t)))
    loaf = top + [(530, 290), (520, 500), (80, 500), (70, 290)]
    d.fill(loaf, TAN)
    d.line(top + [(530, 290), (520, 500), (80, 500), (70, 290)], closed=True)
    for x in (190, 290, 390):
        d.line([(x - 30, 230), (x + 30, 180)], wobble=2)


def tortillas(d):
    for i, cy in enumerate((440, 400, 360)):
        e = ellipse(300, cy, 230, 70, n=30)
        d.shape(e, TAN[:2])
    half = arc(300, 330, 200, 150, math.pi, 2 * math.pi, n=20)
    d.fill(half + [(500, 330), (100, 330)], TAN)
    d.line(half + [(100, 330)], closed=True)
    for x, y in [(220, 260), (330, 230), (400, 290), (260, 300)]:
        d.dot(x, y, 8, "#b5763a")


def canned_vegetables(d):
    d.fill(rect(150, 170, 300, 370), GREY[:2], straight=True)
    d.fill(rect(150, 260, 300, 190), GREEN, straight=True)
    d.line(ellipse(300, 170, 150, 46), closed=True)
    d.line([(150, 170), (150, 540)])
    d.line([(450, 170), (450, 540)])
    d.line(arc(300, 540, 150, 46, 0, math.pi, n=18))
    d.line(arc(300, 260, 150, 40, 0, math.pi, n=18), wobble=2)
    d.line(arc(300, 450, 150, 40, 0, math.pi, n=18), wobble=2)
    for x, y in [(240, 330), (290, 360), (340, 330), (360, 390), (260, 395), (310, 410)]:
        d.dot(x, y, 14, "#ffd21a")
        d.line(ellipse(x, y, 14, 14, n=8), closed=True, wobble=0.5, overshoot=False, width=6)


def opened_canned_food(d):
    d.fill(rect(90, 260, 250, 280), GREY[:2], straight=True)
    d.fill(ellipse(215, 260, 125, 38), BROWN, scale=0.6)
    d.line(ellipse(215, 260, 125, 38), closed=True)
    d.line([(90, 260), (90, 540)])
    d.line([(340, 260), (340, 540)])
    d.line(arc(215, 540, 125, 38, 0, math.pi, n=16))
    lid = [(110, 240), (150, 120), (260, 80), (300, 110), (260, 220)]
    d.shape(lid, GREY[:1])
    box = [(370, 390), (550, 390), (540, 540), (380, 540)]
    d.fill(box, PALE_BLUE[:1], straight=True)
    d.fill([(380, 450), (545, 450), (540, 540), (380, 540)], BROWN, straight=True, scale=0.6)
    d.line(box, closed=True)
    d.line([(360, 370), (560, 370), (560, 392), (360, 392)], closed=True, overshoot=False)


def jam(d):
    jar = [(160, 220), (440, 220), (460, 300), (460, 520), (140, 520), (140, 300)]
    d.fill(jar, PURPLE)
    d.line(jar, closed=True)
    lid = [(170, 150), (430, 150), (440, 220), (160, 220)]
    d.shape(lid, RED, straight=True)
    for x in range(200, 430, 40):
        d.line([(x, 160), (x, 212)], wobble=1, width=7)
    label = [(190, 330), (410, 330), (410, 450), (190, 450)]
    d.fill(label, CREAM[:1], straight=True)
    d.line(label, closed=True)
    d.line([(225, 380), (300, 395), (375, 380)], wobble=2, width=9)


def cooked_rice(d):
    bowl = arc(300, 330, 230, 200, 0, math.pi, n=24)
    d.fill(bowl + [(70, 330)], BLUE)
    d.line(bowl + [(70, 330)], closed=True)
    mound = []
    for i in range(36):
        t = math.pi + math.pi * i / 35
        r = 205 * (1 + 0.05 * math.sin(16 * t))
        mound.append((300 + r * math.cos(t), 330 + 0.62 * r * math.sin(t)))
    d.fill(mound + [(505, 330), (95, 330)], CREAM)
    d.line(mound)
    for x, y in [(220, 280), (290, 250), (360, 280), (250, 310), (330, 300), (400, 310), (300, 220)]:
        d.line(ellipse(x, y, 11, 6, n=8), closed=True, wobble=0.5, overshoot=False, width=6)
    d.line([(380, 200), (560, 80)], wobble=1.5)
    d.line([(410, 215), (575, 115)], wobble=1.5)


def leftovers(d):
    box = [(110, 280), (490, 280), (470, 520), (130, 520)]
    d.fill(box, PALE_BLUE[:1], straight=True)
    food = [(140, 400), (200, 360), (280, 380), (350, 350), (430, 375), (470, 400), (460, 510), (140, 510)]
    d.fill(food, ORANGE)
    d.fill([(200, 400), (260, 390), (300, 430), (240, 450)], GREEN, scale=0.5)
    d.line(box, closed=True)
    d.line(food[:6], wobble=2)
    lid = [(90, 215), (510, 195), (515, 240), (95, 262)]
    d.shape(lid, PALE_BLUE, straight=True)
    d.line([(280, 205), (282, 180), (330, 178), (332, 203)], wobble=1.5)


def keep_or_toss(d):
    """The Work page entry: an open fridge with a banana and a milk carton inside."""
    body = [(140, 80), (400, 80), (400, 560), (140, 560)]
    d.fill(body, PALE_BLUE, straight=True)
    inside = [(168, 108), (372, 108), (372, 532), (168, 532)]
    d.fill(inside, CREAM[:1], straight=True)
    d.line(body, closed=True)
    d.line(inside, closed=True)
    for y in (250, 400):
        d.line([(168, y), (372, y)], wobble=2)
    door = [(400, 80), (540, 130), (540, 520), (400, 560)]
    d.shape(door, PALE_BLUE[:2], straight=True)
    d.line([(510, 270), (510, 340)], wobble=1.5)
    banana = [(190, 220), (215, 236), (260, 240), (300, 228), (325, 205), (312, 202), (290, 216), (258, 222), (218, 218), (198, 206)]
    d.shape(banana, YELLOW, scale=0.5)
    carton = [(290, 300), (345, 300), (345, 392), (290, 392)]
    d.shape(carton, BLUE, straight=True, scale=0.5)
    d.line([(290, 300), (318, 272), (345, 300)], wobble=1.5)
    apple = ellipse(220, 360, 34, 32, n=14)
    d.shape(apple, RED, scale=0.5)
    jar = [(200, 440), (250, 440), (255, 525), (195, 525)]
    d.shape(jar, PURPLE, straight=True, scale=0.5)
    box = [(275, 470), (355, 470), (350, 525), (280, 525)]
    d.shape(box, ORANGE, straight=True, scale=0.5)


DRAWINGS = {
    "bananas": bananas, "apples": apples, "avocados": avocados, "tomatoes": tomatoes, "berries": berries,
    "grapes": grapes, "citrus": citrus, "leafy-greens": leafy_greens, "carrots": carrots, "potatoes": potatoes,
    "onions": onions, "broccoli": broccoli, "milk": milk, "eggs": eggs, "hard-cheese": hard_cheese,
    "soft-cheese": soft_cheese, "shredded-cheese": shredded_cheese, "yogurt": yogurt, "butter": butter,
    "raw-chicken": raw_chicken, "ground-beef": ground_beef, "fish": fish, "deli-meat": deli_meat,
    "bread": bread, "tortillas": tortillas, "canned-vegetables": canned_vegetables,
    "opened-canned-food": opened_canned_food, "jam": jam, "cooked-rice": cooked_rice, "leftovers": leftovers,
    "keep-or-toss": keep_or_toss,
}


def main() -> None:
    for old in ("banana", ):  # the first sample, now named after the food's page
        for layer in ("ink", "color"):
            (HERE / f"{old}-{layer}.svg").unlink(missing_ok=True)
    for slug, draw in DRAWINGS.items():
        d = Drawing(random.Random(zlib.crc32(slug.encode())))
        draw(d)
        (HERE / f"{slug}-ink.svg").write_text(d.svg("ink"), encoding="utf-8")
        (HERE / f"{slug}-color.svg").write_text(d.svg("color"), encoding="utf-8")
    print(f"drew {len(DRAWINGS)} stand-ins in {HERE}")


if __name__ == "__main__":
    main()
