"""Draw the placeholder artwork into assets/placeholders/.

These are simple flat illustrations that stand in for real photography. To use
your own pictures, overwrite the files of the same name (see README, section
"Placeholder images") - no code changes needed.

Run:  python scripts/make_placeholders.py
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

S = 2  # draw at 2x, then downscale for smooth edges
OUT = Path(__file__).resolve().parent.parent / "assets" / "placeholders"

TEAL = (11, 107, 99)
TEAL_D = (8, 74, 69)
TEAL_M = (86, 160, 152)
TEAL_L = (206, 230, 227)
TEAL_XL = (232, 244, 242)
AMBER = (199, 133, 26)
AMBER_D = (146, 96, 20)
AMBER_L = (246, 226, 186)
INK = (23, 32, 43)
SLATE = (92, 104, 119)
LINE = (214, 220, 228)
WHITE = (255, 255, 255)
PAPER = (247, 248, 250)


# ------------------------------------------------------------------ primitives
def canvas(w, h, top, bottom):
    img = Image.new("RGB", (w * S, h * S), top)
    d = ImageDraw.Draw(img)
    for y in range(h * S):
        t = y / (h * S - 1)
        d.line([(0, y), (w * S, y)], fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def rr(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle([round(v) for v in box], radius=round(r), fill=fill, outline=outline, width=round(width))


def circ(d, cx, cy, r, fill, outline=None, width=0):
    d.ellipse([round(cx - r), round(cy - r), round(cx + r), round(cy + r)], fill=fill, outline=outline, width=round(width))


def poly(d, pts, fill):
    d.polygon([(round(x), round(y)) for x, y in pts], fill=fill)


def backdrop(img):
    d = ImageDraw.Draw(img)
    w, h = img.size
    circ(d, w * 0.88, h * 0.1, h * 0.5, TEAL_L)
    circ(d, w * 0.04, h * 0.99, h * 0.3, AMBER_L)


def card(d, box, r):
    x0, y0, x1, y1 = box
    rr(d, (x0, y0 + r * 0.25, x1, y1 + r * 0.25), r, LINE)  # soft shadow
    rr(d, box, r, WHITE, outline=LINE, width=2)


def tag(d, x, y, u, fill=AMBER):
    poly(d, [(x, y), (x + 1.5 * u, y), (x + 2.0 * u, y + 0.5 * u), (x + 1.5 * u, y + u), (x, y + u)], fill)
    circ(d, x + 0.35 * u, y + 0.5 * u, 0.12 * u, WHITE)


def mountains(d, box, sun=True):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    rr(d, box, h * 0.08, TEAL_XL)
    if sun:
        circ(d, x0 + w * 0.72, y0 + h * 0.3, h * 0.11, AMBER)
    poly(d, [(x0, y1), (x0 + w * 0.32, y0 + h * 0.45), (x0 + w * 0.6, y1)], TEAL_M)
    poly(d, [(x0 + w * 0.35, y1), (x0 + w * 0.65, y0 + h * 0.55), (x1, y1)], TEAL)


def gavel(img, cx, cy, u, angle=35, head=TEAL_D, band=AMBER, handle=AMBER_D):
    size = round(6 * u)
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = size / 2
    rr(d, (c - 0.2 * u, c - 0.3 * u, c + 0.2 * u, c + 2.4 * u), 0.2 * u, handle)
    rr(d, (c - 1.3 * u, c - 1.3 * u, c + 1.3 * u, c - 0.3 * u), 0.3 * u, head)
    for dx in (-0.85, 0.65):
        d.rectangle([round(c + dx * u), round(c - 1.3 * u), round(c + (dx + 0.2) * u), round(c - 0.3 * u)], fill=band)
    layer = layer.rotate(angle, resample=Image.BICUBIC)
    img.paste(layer, (round(cx - size / 2), round(cy - size / 2)), layer)


def sound_block(d, cx, cy, u):
    rr(d, (cx - 1.7 * u, cy, cx + 1.7 * u, cy + 0.45 * u), 0.15 * u, AMBER_D)
    rr(d, (cx - 1.2 * u, cy - 0.4 * u, cx + 1.2 * u, cy + 0.05 * u), 0.15 * u, AMBER)


def person(d, cx, cy, u, color=TEAL):
    circ(d, cx, cy - 0.8 * u, 0.62 * u, color)
    d.pieslice([round(cx - 1.3 * u), round(cy - 0.05 * u), round(cx + 1.3 * u), round(cy + 2.6 * u)], 180, 360, fill=color)


# --------------------------------------------------------------------- motifs
def m_hero(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    # framed picture (left)
    x, y = cx - 4.6 * u, cy - 2.6 * u
    card(d, (x, y, x + 2.6 * u, y + 3.3 * u), 0.15 * u)
    mountains(d, (x + 0.25 * u, y + 0.25 * u, x + 2.35 * u, y + 3.05 * u))
    # vase (centre-left)
    vx, vy = cx - 1.4 * u, cy - 0.5 * u
    rr(d, (vx - 0.3 * u, vy - 1.5 * u, vx + 0.3 * u, vy - 0.4 * u), 0.15 * u, TEAL_M)
    circ(d, vx, vy + 0.35 * u, 1.0 * u, TEAL)
    d.arc([round(vx - 0.7 * u), round(vy - 0.05 * u), round(vx + 0.7 * u), round(vy + 0.75 * u)], 200, 340, fill=WHITE, width=round(0.08 * u))
    # clock (right)
    kx, ky = cx + 2.3 * u, cy - 1.2 * u
    circ(d, kx, ky, 1.25 * u, INK)
    circ(d, kx, ky, 1.0 * u, WHITE)
    d.line([(kx, ky), (kx, ky - 0.7 * u)], fill=INK, width=round(0.09 * u))
    d.line([(kx, ky), (kx + 0.5 * u, ky + 0.2 * u)], fill=AMBER, width=round(0.09 * u))
    # shelf
    rr(d, (cx - 5.2 * u, cy + 1.05 * u, cx + 4.4 * u, cy + 1.3 * u), 0.1 * u, LINE)
    # price tags hanging
    tag(d, cx - 3.4 * u, cy + 1.5 * u, 0.75 * u)
    tag(d, cx + 3.0 * u, cy + 0.0 * u, 0.75 * u, TEAL)
    # foreground: block and gavel, clear of the shelf items
    sound_block(d, cx + 1.9 * u, cy + 3.5 * u, 1.0 * u)
    gavel(img, cx + 1.3 * u, cy + 2.5 * u, 0.85 * u, angle=38)


def m_lock(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    d.arc([round(cx - 0.85 * u), round(cy - 2.1 * u), round(cx + 0.85 * u), round(cy - 0.1 * u)], 180, 360, fill=INK, width=round(0.3 * u))
    d.line([(cx - 0.85 * u, cy - 1.1 * u), (cx - 0.85 * u, cy - 0.3 * u)], fill=INK, width=round(0.3 * u))
    d.line([(cx + 0.85 * u, cy - 1.1 * u), (cx + 0.85 * u, cy - 0.3 * u)], fill=INK, width=round(0.3 * u))
    rr(d, (cx - 1.3 * u, cy - 0.4 * u, cx + 1.3 * u, cy + 1.7 * u), 0.35 * u, TEAL)
    circ(d, cx, cy + 0.55 * u, 0.26 * u, WHITE)
    rr(d, (cx - 0.08 * u, cy + 0.6 * u, cx + 0.08 * u, cy + 1.2 * u), 0.05 * u, WHITE)
    gavel(img, cx + 1.9 * u, cy + 1.6 * u, 0.55 * u, angle=40, head=AMBER_D, band=AMBER_L, handle=AMBER_D)


def m_person_plus(img, cx, cy, u, plus=True):
    d = ImageDraw.Draw(img)
    person(d, cx - 0.2 * u, cy, u)
    if plus:
        bx, by = cx + 1.5 * u, cy - 1.2 * u
        circ(d, bx, by, 0.6 * u, AMBER)
        d.line([(bx - 0.3 * u, by), (bx + 0.3 * u, by)], fill=WHITE, width=round(0.12 * u))
        d.line([(bx, by - 0.3 * u), (bx, by + 0.3 * u)], fill=WHITE, width=round(0.12 * u))
    else:
        circ(d, cx + 1.3 * u, cy + 1.3 * u, 0.55 * u, AMBER)
        rr(d, (cx + 1.05 * u, cy + 1.25 * u, cx + 1.55 * u, cy + 1.6 * u), 0.05 * u, WHITE)
        d.arc([round(cx + 1.12 * u), round(cy + 0.95 * u), round(cx + 1.48 * u), round(cy + 1.35 * u)], 180, 360, fill=WHITE, width=round(0.07 * u))


def m_shield(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    poly(d, [(cx - 1.5 * u, cy - 1.7 * u), (cx + 1.5 * u, cy - 1.7 * u), (cx + 1.5 * u, cy + 0.2 * u), (cx, cy + 2.0 * u), (cx - 1.5 * u, cy + 0.2 * u)], TEAL)
    poly(d, [(cx, cy - 1.7 * u), (cx + 1.5 * u, cy - 1.7 * u), (cx + 1.5 * u, cy + 0.2 * u), (cx, cy + 2.0 * u)], TEAL_D)
    d.line([(cx - 0.6 * u, cy), (cx - 0.15 * u, cy + 0.5 * u), (cx + 0.7 * u, cy - 0.5 * u)], fill=WHITE, width=round(0.22 * u), joint="curve")
    gavel(img, cx + 2.0 * u, cy + 1.2 * u, 0.55 * u, angle=40, head=AMBER_D, band=AMBER_L, handle=AMBER_D)


def m_cards(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    for dx, col in ((-2.5, TEAL_M), (0, AMBER), (2.5, TEAL)):
        x = cx + dx * u
        card(d, (x - 1.0 * u, cy - 1.5 * u, x + 1.0 * u, cy + 1.5 * u), 0.15 * u)
        rr(d, (x - 0.85 * u, cy - 1.35 * u, x + 0.85 * u, cy + 0.15 * u), 0.1 * u, col)
        circ(d, x + 0.35 * u, cy - 0.85 * u, 0.15 * u, WHITE)
        rr(d, (x - 0.8 * u, cy + 0.4 * u, x + 0.5 * u, cy + 0.55 * u), 0.05 * u, LINE)
        rr(d, (x - 0.8 * u, cy + 0.75 * u, x + 0.1 * u, cy + 0.9 * u), 0.05 * u, LINE)
        rr(d, (x - 0.8 * u, cy + 1.05 * u, x - 0.1 * u, cy + 1.3 * u), 0.12 * u, AMBER if col != AMBER else TEAL)


def m_sell(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    rr(d, (cx - 1.0 * u, cy - 1.3 * u, cx + 0.2 * u, cy - 0.9 * u), 0.1 * u, INK)
    rr(d, (cx - 1.9 * u, cy - 1.0 * u, cx + 1.0 * u, cy + 1.0 * u), 0.3 * u, INK)
    circ(d, cx - 0.45 * u, cy, 0.7 * u, TEAL_M)
    circ(d, cx - 0.45 * u, cy, 0.42 * u, TEAL_D)
    circ(d, cx - 0.55 * u, cy - 0.1 * u, 0.12 * u, WHITE)
    circ(d, cx + 0.65 * u, cy - 0.65 * u, 0.1 * u, AMBER)
    tag(d, cx + 0.9 * u, cy - 1.7 * u, 1.3 * u)
    tag(d, cx + 1.4 * u, cy + 0.3 * u, 1.0 * u, TEAL)


def m_boxes(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1, col) in ((-2.6, -0.1, -0.2, 1.7, TEAL), (0.2, -0.1, 2.6, 1.7, TEAL_M), (-1.2, -1.9, 1.2, -0.1, AMBER)):
        rr(d, (cx + x0 * u, cy + y0 * u, cx + x1 * u, cy + y1 * u), 0.15 * u, col)
        mid = cx + (x0 + x1) / 2 * u
        d.rectangle([round(mid - 0.12 * u), round(cy + y0 * u), round(mid + 0.12 * u), round(cy + y0 * u + 0.5 * u)], fill=WHITE)
    tag(d, cx + 1.6 * u, cy - 1.4 * u, 0.9 * u, TEAL_D)


def m_bids(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    shades = [TEAL_L, TEAL_M, TEAL_M, TEAL, TEAL_D]
    for i, col in enumerate(shades):
        h = (0.8 + i * 0.5) * u
        rr(d, (cx - 2.8 * u + i * 0.8 * u, cy + 1.5 * u - h, cx - 2.3 * u + i * 0.8 * u, cy + 1.5 * u), 0.1 * u, col)
    px, py = cx + 2.2 * u, cy - 0.5 * u
    rr(d, (px - 0.12 * u, py, px + 0.12 * u, py + 2.0 * u), 0.1 * u, AMBER_D)
    circ(d, px, py, 0.85 * u, AMBER)
    circ(d, px, py, 0.55 * u, AMBER_L)
    circ(d, px, py, 0.25 * u, AMBER)


def m_qr(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    card(d, (cx - 1.7 * u, cy - 1.9 * u, cx + 1.7 * u, cy + 1.9 * u), 0.2 * u)
    n, m = 9, 0.3 * u
    ox, oy = cx - n * m / 2, cy - n * m / 2
    rnd = random.Random(7)
    for i in range(n):
        for j in range(n):
            finder = (i < 3 and j < 3) or (i < 3 and j >= n - 3) or (i >= n - 3 and j < 3)
            if not finder and rnd.random() > 0.5:
                d.rectangle([round(ox + j * m), round(oy + i * m), round(ox + (j + 1) * m - 2), round(oy + (i + 1) * m - 2)], fill=INK)
    for (i, j) in ((0, 0), (0, n - 3), (n - 3, 0)):
        x, y = ox + j * m, oy + i * m
        d.rectangle([round(x), round(y), round(x + 3 * m - 2), round(y + 3 * m - 2)], fill=INK)
        d.rectangle([round(x + 0.4 * m), round(y + 0.4 * m), round(x + 2.6 * m - 2), round(y + 2.6 * m - 2)], fill=WHITE)
        d.rectangle([round(x + 1 * m), round(y + 1 * m), round(x + 2 * m - 2), round(y + 2 * m - 2)], fill=TEAL)
    for k, (dx, dy) in enumerate(((2.3, 1.2), (2.9, 0.6), (2.6, 1.9))):
        circ(d, cx + dx * u, cy + dy * u, 0.42 * u, AMBER if k != 1 else AMBER_D)


def m_dash(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    card(d, (cx - 3.0 * u, cy - 1.8 * u, cx + 3.0 * u, cy + 1.8 * u), 0.2 * u)
    rr(d, (cx - 3.0 * u, cy - 1.8 * u, cx + 3.0 * u, cy - 1.2 * u), 0.2 * u, LINE)
    for k in range(3):
        circ(d, cx - 2.6 * u + k * 0.35 * u, cy - 1.5 * u, 0.09 * u, SLATE)
    for k in range(3):
        rr(d, (cx - 2.7 * u + k * 1.85 * u, cy - 0.95 * u, cx - 1.05 * u + k * 1.85 * u, cy - 0.15 * u), 0.12 * u, (TEAL_XL, AMBER_L, TEAL_XL)[k])
    for i, h in enumerate((0.5, 0.9, 0.7, 1.2, 1.0, 1.4)):
        rr(d, (cx - 2.6 * u + i * 0.85 * u, cy + 1.5 * u - h * u, cx - 2.1 * u + i * 0.85 * u, cy + 1.5 * u), 0.08 * u, TEAL if i % 2 else TEAL_M)


def m_product(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    card(d, (cx - 3.0 * u, cy - 2.2 * u, cx + 3.0 * u, cy + 2.2 * u), 0.25 * u)
    mountains(d, (cx - 2.7 * u, cy - 1.9 * u, cx + 2.7 * u, cy + 1.9 * u))


def m_clock(img, cx, cy, u):
    import math
    d = ImageDraw.Draw(img)
    circ(d, cx, cy, 2.5 * u, AMBER_D)
    circ(d, cx, cy, 2.2 * u, WHITE)
    for k in range(12):
        a = math.radians(k * 30)
        r0, r1 = (1.75, 2.0) if k % 3 else (1.6, 2.0)
        d.line([(cx + math.sin(a) * r0 * u, cy - math.cos(a) * r0 * u), (cx + math.sin(a) * r1 * u, cy - math.cos(a) * r1 * u)], fill=INK, width=round(0.07 * u))
    d.line([(cx, cy), (cx + 0.1 * u, cy - 1.3 * u)], fill=INK, width=round(0.14 * u))
    d.line([(cx, cy), (cx + 0.95 * u, cy + 0.4 * u)], fill=INK, width=round(0.14 * u))
    d.line([(cx, cy), (cx - 0.6 * u, cy + 1.2 * u)], fill=AMBER, width=round(0.05 * u))
    circ(d, cx, cy, 0.14 * u, AMBER)


def m_vase(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    rr(d, (cx - 3.0 * u, cy + 2.0 * u, cx + 3.0 * u, cy + 2.25 * u), 0.1 * u, LINE)
    # large vase
    x = cx - 0.9 * u
    rr(d, (x - 0.35 * u, cy - 2.2 * u, x + 0.35 * u, cy - 0.9 * u), 0.12 * u, TEAL_M)
    d.ellipse([round(x - 1.2 * u), round(cy - 1.4 * u), round(x + 1.2 * u), round(cy + 2.0 * u)], fill=TEAL)
    d.arc([round(x - 0.8 * u), round(cy - 0.7 * u), round(x + 0.8 * u), round(cy + 1.5 * u)], 200, 330, fill=WHITE, width=round(0.1 * u))
    # small vase
    x2 = cx + 1.6 * u
    rr(d, (x2 - 0.3 * u, cy - 0.5 * u, x2 + 0.3 * u, cy + 0.2 * u), 0.1 * u, AMBER_D)
    d.ellipse([round(x2 - 0.95 * u), round(cy), round(x2 + 0.95 * u), round(cy + 2.0 * u)], fill=AMBER)
    rr(d, (x2 - 0.5 * u, cy + 0.7 * u, x2 + 0.5 * u, cy + 0.85 * u), 0.05 * u, AMBER_L)


def m_lamp(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    poly(d, [(cx - 1.4 * u, cy - 0.2 * u), (cx + 0.2 * u, cy - 1.9 * u), (cx + 1.6 * u, cy - 1.2 * u), (cx + 0.5 * u, cy + 0.4 * u)], AMBER)
    poly(d, [(cx - 1.4 * u, cy - 0.2 * u), (cx + 0.5 * u, cy + 0.4 * u), (cx - 0.3 * u, cy + 2.2 * u), (cx - 2.4 * u, cy + 1.4 * u)], AMBER_L)
    d.line([(cx + 0.5 * u, cy + 0.2 * u), (cx + 1.3 * u, cy + 1.2 * u), (cx + 0.9 * u, cy + 2.0 * u)], fill=INK, width=round(0.14 * u), joint="curve")
    d.ellipse([round(cx + 0.1 * u), round(cy + 1.95 * u), round(cx + 1.9 * u), round(cy + 2.4 * u)], fill=INK)
    circ(d, cx + 0.5 * u, cy + 0.3 * u, 0.16 * u, TEAL_D)


def m_books(img, cx, cy, u):
    d = ImageDraw.Draw(img)
    shelf = cy + 2.0 * u
    rr(d, (cx - 3.2 * u, shelf, cx + 3.2 * u, shelf + 0.25 * u), 0.1 * u, LINE)
    x = cx - 2.7 * u
    for w, h, col in ((0.55, 3.0, TEAL), (0.7, 3.4, AMBER), (0.5, 2.7, TEAL_D), (0.65, 3.2, TEAL_M), (0.55, 2.9, AMBER_D)):
        rr(d, (x, shelf - h * u, x + w * u, shelf), 0.06 * u, col)
        d.rectangle([round(x), round(shelf - h * u + 0.35 * u), round(x + w * u), round(shelf - h * u + 0.42 * u)], fill=WHITE)
        x += (w + 0.08) * u
    # a book lying flat on top of the stack to the right
    for k, col in enumerate((TEAL, AMBER, TEAL_M)):
        rr(d, (cx + 0.6 * u, shelf - (k + 1) * 0.55 * u, cx + 3.0 * u, shelf - k * 0.55 * u), 0.08 * u, col)
        d.rectangle([round(cx + 0.9 * u), round(shelf - (k + 1) * 0.55 * u + 0.18 * u), round(cx + 2.7 * u), round(shelf - (k + 1) * 0.55 * u + 0.24 * u)], fill=WHITE)


# ----------------------------------------------------------------------- jobs
def build(name, size, motif, unit, colors=(TEAL_XL, PAPER), offset=(0.5, 0.5)):
    w, h = size
    img = canvas(w, h, *colors)
    backdrop(img)
    motif(img, w * S * offset[0], h * S * offset[1], min(w, h) * S * unit)
    img.resize((w, h), Image.LANCZOS).save(OUT / name, quality=88)


def build_favicon():
    size = 64
    img = canvas(size, size, TEAL, TEAL_D)
    gavel(img, size * S / 2, size * S * 0.52, size * S * 0.105, angle=40, head=WHITE, band=AMBER, handle=AMBER_L)
    small = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=14, fill=255)
    small.putalpha(mask)
    small.save(OUT / "favicon.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    banner = (900, 360)
    build("hero_home.jpg", (1200, 900), m_hero, 0.098, offset=(0.52, 0.42))
    build("auth_login.jpg", (800, 1000), m_lock, 0.15)
    build("auth_register.jpg", (800, 1000), m_person_plus, 0.17)
    build("auth_admin.jpg", (800, 1000), m_shield, 0.15)
    build("banner_browse.jpg", banner, m_cards, 0.16)
    build("banner_sell.jpg", banner, m_sell, 0.17)
    build("banner_my_auctions.jpg", banner, m_boxes, 0.16)
    build("banner_my_bids.jpg", banner, m_bids, 0.16)
    build("banner_payment.jpg", banner, m_qr, 0.14)
    build("banner_admin.jpg", banner, m_shield, 0.15)
    build("banner_dashboard.jpg", banner, m_dash, 0.13)
    build("banner_account.jpg", banner, lambda i, x, y, u: m_person_plus(i, x, y, u, plus=False), 0.17)
    build("product_placeholder.jpg", (800, 600), m_product, 0.12, colors=((238, 241, 245), (250, 251, 252)))
    prod = ((238, 241, 245), (250, 251, 252))
    build("sample_camera.jpg", (800, 600), m_sell, 0.19, colors=prod)
    build("sample_print.jpg", (800, 600), m_product, 0.12, colors=prod)
    build("sample_clock.jpg", (800, 600), m_clock, 0.1, colors=prod)
    build("sample_vase.jpg", (800, 600), m_vase, 0.1, colors=prod)
    build("sample_lamp.jpg", (800, 600), m_lamp, 0.1, colors=prod)
    build("sample_books.jpg", (800, 600), m_books, 0.1, colors=prod)
    build("qr_placeholder.jpg", (600, 600), m_qr, 0.14, colors=((255, 255, 255), (246, 248, 250)))
    build_favicon()
    print("Placeholders written to", OUT)


if __name__ == "__main__":
    main()
