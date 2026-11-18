"""Bodo art, round 2: built from references/bodo-research.md.

Agor is drawn the way it is woven: fine extra-weft thread floats in one contrast colour on a solid ground,
on a thread grid (cell = CW x CH px). Real structures: diamond chains, Hajw (hill) sawtooth with fern
hatching, peacock-eye medallions (concentric dotted rings), small butis. Lit from the top left.

Writes WebP/PNG into site/public/art/ (and the curtain opening sequence into site/public/art/curtain/).
Run with the scratch venv (numpy, pillow, scipy):  python art_bodo2.py [--frames]
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(PRJ, "site", "public", "art")
os.makedirs(OUT, exist_ok=True)

PAL = {  # bodo-research.md
    "yellow": "#F2C318", "marigold": "#EE8A1E", "scarlet": "#D7332B", "scarlet_d": "#A8221D",
    "emerald": "#0F7A4A", "emerald_d": "#0A5534", "parrot": "#6DBE45", "magenta": "#B0287A",
    "navy": "#1E2457", "gold": "#D9A84A", "ivory": "#FBF6EC", "beige": "#D8CDB8", "brass": "#B98A3A",
    "bamboo": "#C9A063", "ink": "#3A2618",
}
CW, CH = 3, 2   # one woven cell (a short horizontal float) in px


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def save(name, img, alpha=None, q=90):
    img = np.clip(img, 0, 1)
    arr = (np.dstack([img, np.clip(alpha, 0, 1)]) if alpha is not None else img)
    im = Image.fromarray((arr * 255).astype(np.uint8), "RGBA" if alpha is not None else "RGB")
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if name.endswith(".webp"):
        im.save(path, quality=q, method=5)
    else:
        im.save(path)
    return path


def light(height, k=1.0, spec=.2, amb=.7):
    gy, gx = np.gradient(height)
    nx, ny = -gx * k, -gy * k
    n = np.sqrt(nx * nx + ny * ny + 1)
    L = np.array([-1.0, -1.0, 1.5])
    L /= np.linalg.norm(L)
    d = (nx * L[0] + ny * L[1] + L[2]) / n
    mul = amb + (1 - amb) * d / L[2]
    hl = np.clip(d - L[2], 0, None) ** 1.5 * spec * 6
    return mul, hl


# ------------------------------------------------------------------ thread grid motifs (boolean, rows x cols)
def diamond_chain(cols, r=2):
    g = np.zeros((2 * r + 1, cols), bool)
    y, x = np.mgrid[0:2 * r + 1, 0:cols]
    p = 2 * r + 2
    dx = np.abs((x % p) - r)
    d = dx + np.abs(y - r)
    g[(d == r)] = True
    g[(d == 0)] = True
    g[(x % p == p - 1) & (y == r)] = True       # link between diamonds
    return g


def hills(cols, h=7, period=8, down=True):
    """Hajw agor: sawtooth hills with fern hatching inside each tooth."""
    y, x = np.mgrid[0:h, 0:cols]
    t = np.abs((x % period) - period / 2) / (period / 2)          # 0 at apex, 1 at base corners
    yy = y if down else (h - 1 - y)
    height = (1 - t) * h                                          # tooth height at this column
    inside = yy < height
    edge = inside & ~(yy + 1 < height - .2)
    fern = inside & (((x + yy) % 3 == 0) | ((x - yy) % 3 == 0)) & (yy < height - 1)
    base = yy == 0
    return edge | fern | base


def medallion(r=6):
    s = 2 * r + 1
    y, x = np.mgrid[0:s, 0:s] - r
    d = np.sqrt((x * CW / CH) ** 2 * .45 + y ** 2)              # compensate the float aspect
    a = np.arctan2(y, x)
    g = np.zeros((s, s), bool)
    g |= (np.abs(d - r) < .55) & ((np.round(a / (np.pi / 10)) % 2) == 0)    # dotted outer ring
    g |= np.abs(d - (r - 1.6)) < .5                                          # solid ring
    g |= (np.abs(d - (r - 3.2)) < .5) & ((np.round(a / (np.pi / 6)) % 2) == 0)
    md = np.abs(x) + np.abs(y)
    g |= (np.abs(d - (r - 4.8)) < .5)
    g |= (md == 2) | (md == 0) | ((md == 3) & ((x == 0) | (y == 0)))     # centre flower
    return g


def buti(r=2):
    s = 2 * r + 3
    y, x = np.mgrid[0:s, 0:s] - (r + 1)
    md = np.abs(x) + np.abs(y)
    return (md == r) | (md == 0) | ((md == r + 1) & ((x == 0) | (y == 0)))


def paste(g, m, y0, x0):
    h, w = m.shape
    ys, xs = slice(max(y0, 0), min(y0 + h, g.shape[0])), slice(max(x0, 0), min(x0 + w, g.shape[1]))
    if ys.stop <= ys.start or xs.stop <= xs.start:
        return
    g[ys, xs] |= m[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]


def band_grid(cols, kind="full"):
    """Aronai anatomy across the band: chain, hills (down), rule, medallions + butis, rule, hills (up), chain."""
    if kind == "slim":
        parts = [diamond_chain(cols), np.zeros((1, cols), bool), hills(cols, 9, 10, True)]
    else:
        mid = np.zeros((17, cols), bool)
        for i, cx in enumerate(range(12, cols, 24)):
            paste(mid, medallion(8), 0, cx - 8)
            paste(mid, buti(3), 4, cx + 12 - 4)
        rule = np.ones((1, cols), bool)
        gap = np.zeros((1, cols), bool)
        parts = [diamond_chain(cols), gap, hills(cols, 11, 10, True), gap, rule, gap, mid, gap, rule, gap,
                 hills(cols, 11, 10, False), gap, diamond_chain(cols)]
    return np.vstack(parts)


def weave_px(h, w):
    y, x = np.mgrid[0:h, 0:w]
    chk = ((x // 2 + y // 2) % 2).astype(float)
    return chk * np.abs(np.sin(np.pi * (x + .5) / 2)) + (1 - chk) * np.abs(np.sin(np.pi * (y + .5) / 2))


def render_grid(g, ground, thread, pad_rows=2, accent=None):
    """Turn a thread grid into a lit woven image. Returns (rgb, height)."""
    g = np.pad(g, ((pad_rows, pad_rows), (0, 0)))
    h, w = g.shape[0] * CH, g.shape[1] * CW
    m = np.kron(g, np.ones((CH, CW), bool))
    # each float is a little raised lozenge along x
    xs = (np.arange(w) % CW + .5) / CW
    prof = np.sin(np.pi * xs)[None, :] * np.ones((h, 1))
    hgt = weave_px(h, w) * .25 + m * (.7 + .5 * prof)
    col = np.zeros((h, w, 3)) + rgb(ground)
    col[m] = rgb(thread)
    if accent is not None:
        acc = np.kron(accent[0], np.ones((CH, CW), bool))
        acc = np.pad(acc, ((pad_rows * CH, h - acc.shape[0] - pad_rows * CH), (0, w - acc.shape[1])))
        col[acc] = rgb(accent[1])
    hgt = nd.gaussian_filter(hgt, .6)
    return col, hgt


def lit(col, hgt, k=1.6, spec=.25, amb=.72):
    mul, hl = light(hgt, k, spec, amb)
    return col * mul[..., None] + hl[..., None]


def aronai_band(length_px, ground, thread, kind="full"):
    g = band_grid(length_px // CW + 1, kind)
    col, hgt = render_grid(g, ground, thread)
    return col[:, :length_px], hgt[:, :length_px]


# ------------------------------------------------------------------ assets
def bands():
    for name, ground, thread in (("band-scarlet", "scarlet", "gold"), ("band-emerald", "emerald", "ivory"),
                                 ("band-navy", "navy", "gold"), ("band-yellow", "yellow", "scarlet"),
                                 ("band-magenta", "magenta", "ivory")):
        col, hgt = aronai_band(1200, PAL[ground], PAL[thread])
        save(f"{name}.webp", lit(col, hgt))
    col, hgt = aronai_band(1200, PAL["scarlet"], PAL["gold"], "slim")
    img = lit(col, hgt)
    save("edge-scarlet.webp", np.transpose(img, (1, 0, 2))[::-1])
    col, hgt = aronai_band(1200, PAL["emerald"], PAL["ivory"], "slim")
    save("edge-emerald.webp", np.transpose(lit(col, hgt), (1, 0, 2))[::-1])


def door(w=393 * 2 // 2 * 2 // 2, h=852 * 2):
    """One door leaf (the left one; the right is mirrored in CSS): emerald dokhona, gold butis,
    scarlet agor column at the seam, scarlet hem panel."""
    w = 393
    gw, gh = w // CW + 1, h // CH + 1
    g = np.zeros((gh, gw), bool)
    # designed all over (Mwdwm Gongse agor): rows of peacock-eye medallions, butis between,
    # a diamond chain between rows, and a Hajw border down the hinge edge
    row_h = 40
    for j, yy in enumerate(range(4, gh, row_h)):
        off = 0 if j % 2 else 19
        for xx in range(16 + off, gw - 26, 38):
            paste(g, medallion(12), yy, xx - 12)
        for xx in range(35 + off - 38, gw - 26, 38):
            paste(g, buti(4), yy + 7, xx - 5)
        paste(g, diamond_chain(gw), yy + 28, 0)
    hb = hills(gh, 9, 10, True).T                      # hills pointing inward from the hinge
    g[:, :hb.shape[1]] |= hb[:gh]
    g[:, hb.shape[1]] = True
    col, hgt = render_grid(g, PAL["emerald"], PAL["gold"], pad_rows=0)
    col, hgt = col[:h, :w], hgt[:h, :w]
    out = lit(col, hgt, 1.6, .25, .74)
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    out *= (1.05 - .12 * yy - .1 * (1 - xx) ** 3)[..., None]     # hinge side a touch darker
    save("door-base.webp", out)
    # the scarlet column and hem are separate layers, sewn on top of the cloth (raised in the page)
    bc, bh = aronai_band(h, PAL["scarlet"], PAL["gold"])
    save("door-column.webp", lit(np.transpose(bc, (1, 0, 2)), bh.T, 1.6, .25, .74))
    hc, hh = aronai_band(w, PAL["scarlet"], PAL["gold"])
    save("door-hem.webp", lit(hc, hh, 1.6, .25, .74))
    print("door column", bc.shape[0], "px wide; hem", hc.shape[0], "px tall")


def plaque_shadow(w=400, h=460, pad=60):
    """Soft shadow the plaque casts on the doors (dark, blurred silhouette with room around it)."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    nx, ny = np.abs(x - w / 2) / (w / 2 - 4), np.abs(y - h / 2) / (h / 2 - 4)
    inside = ((nx ** 4 + ny ** 4) < 1) & ~(((nx - 1) ** 2 + (ny - 1) ** 2) < .09)
    a = np.pad(inside.astype(float), pad)
    a = nd.gaussian_filter(a, 16) * .75
    save("plaque-shadow.webp", np.zeros(a.shape + (3,)) + rgb("#0B1F14"), a)


def tassel(w=64, h=230):
    """A tassel on a twisted cord: scarlet cord, gold bead, scarlet cap, gold and scarlet fringe."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    cx = w / 2
    col = np.zeros((h, w, 3))
    hgt = np.zeros((h, w))
    a = np.zeros((h, w))
    cord = (y < 70) & (np.abs(x - cx) < 4)
    twist = (np.sin((y + (x - cx) * 2) / 3.2) > 0)
    col[cord] = np.where(twist[cord][:, None], rgb(PAL["scarlet"]), rgb(PAL["scarlet_d"]))
    hgt[cord] = 1 - ((x[cord] - cx) / 4) ** 2
    bead = ((x - cx) ** 2 + (y - 80) ** 2) < 13 ** 2
    col[bead] = rgb(PAL["gold"])
    hgt[bead] = np.sqrt(np.clip(1 - ((x[bead] - cx) ** 2 + (y[bead] - 80) ** 2) / 169, 0, 1)) * 3
    cap_w = 8 + (y - 92) * .55
    cap = (y >= 92) & (y < 118) & (np.abs(x - cx) < cap_w)
    col[cap] = rgb(PAL["scarlet"])
    col[cap & (((y - 92) // 5) % 2 == 1)] = rgb(PAL["gold"])
    hgt[cap] = np.sqrt(np.clip(1 - ((x[cap] - cx) / cap_w[cap]) ** 2, 0, 1)) * 2.5
    spread = 22 + (y - 118) * .1
    fr = (y >= 118) & (y < h - 4) & (np.abs(x - cx) < spread)
    strand = (np.floor((x - cx + 40) / 2.2) % 3)
    col[fr] = np.where((strand[fr] == 0)[:, None], rgb(PAL["scarlet"]), rgb(PAL["gold"]))
    hgt[fr] = .6 + .4 * np.sin((x[fr] - cx) * 1.4)
    ends = fr & (y > h - 4 - 10 * np.abs(np.sin((x - cx) * .7)))
    a = (cord | bead | cap | (fr & ~ends)).astype(float)
    out = lit(col, nd.gaussian_filter(hgt * 3, .8), 1.2, .35, .6)
    save("tassel.webp", out, nd.gaussian_filter(a, .5))


def plaque(w=400, h=460):
    """The cover badge: a lashed bamboo frame around a recessed ivory face with gold agor borders.
    A column of small scarlet diamonds runs down the centre, where the badge splits between the doors;
    a gold peacock-eye medallion crowns it and Hajw teeth run along the foot. Names are added in HTML."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = w / 2, h / 2
    nx, ny = np.abs(x - cx) / (w / 2 - 4), np.abs(y - cy) / (h / 2 - 4)
    notch = ((nx - 1) ** 2 + (ny - 1) ** 2) < .09
    inside = ((nx ** 4 + ny ** 4) < 1) & ~notch
    dist = nd.distance_transform_edt(inside)
    R = 26                                                   # bamboo rim width
    rim = inside & (dist < R)
    face = inside & (dist >= R)
    ang = np.arctan2(y - cy, x - cx)
    col = np.zeros((h, w, 3)) + rgb(PAL["ivory"])
    hgt = np.zeros((h, w))
    # bamboo: a rounded culm, warm tan with fine fibres, darker node rings with a raised lip
    across = np.clip(dist / R, 0, 1)
    culm = np.sin(across * np.pi)
    fib = .04 * np.sin(ang * 420 + dist * .8)
    col[rim] = (rgb(PAL["bamboo"]) * (.9 + .2 * culm[rim, None]) + fib[rim, None])
    hgt[rim] = culm[rim] * 7
    node = rim & (np.abs(((ang / (2 * np.pi)) * 22) % 1 - .5) < .028)
    col[node] = rgb("#8E6A36")
    hgt[node] += 1.2
    # cane lashings wrapped diagonally where the bamboo meets at the four notched corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            ccx, ccy = cx + sx * (w / 2 - 34), cy + sy * (h / 2 - 34)
            near = rim & (((x - ccx) ** 2 + (y - ccy) ** 2) < 30 ** 2)
            wrap = near & ((((x - ccx) * sx + (y - ccy) * sy) // 4) % 2 == 0)
            col[wrap] = rgb("#7A5426")
            hgt[wrap] += 1.6
            col[near & ~wrap] = rgb("#B98E52")
    # recessed face: the ivory sits below the rim, shadowed along its top-left edge
    depth = np.clip((dist - R) / 10, 0, 1)
    hgt[face] = -4 + 2 * depth[face]
    linen = .025 * (np.sin(x * 2.1) * np.sin(y * 1.7))
    col[face] = col[face] * (1 + linen[face, None])
    # gold border: double rule and small diamonds stepping around the face
    ring1 = face & (np.abs(dist - (R + 9)) < 1.1)
    ring2 = face & (np.abs(dist - (R + 15)) < .9)
    dia = face & (np.abs(dist - (R + 12)) < 3.2) & (np.abs(((ang / (2 * np.pi)) * 64) % 1 - .5) < .14)
    gold = ring1 | ring2 | dia
    col[gold] = rgb(PAL["gold"])
    hgt[gold] += .9
    # centre column of scarlet diamonds: where the badge parts
    gy = (y // 12)
    cyy = (y % 12) - 6
    dcol = face & (np.abs(x - cx) + np.abs(cyy) * .8 < 4.2) & (dist > R + 20)
    col[dcol] = rgb(PAL["scarlet"])
    hgt[dcol] += .8
    # peacock-eye medallion at the top, Hajw teeth along the foot
    m = np.kron(medallion(8), np.ones((CH, CW), bool))
    my, mx = int(R + 24), int(cx) - m.shape[1] // 2
    sub = np.zeros((h, w), bool)
    sub[my:my + m.shape[0], mx:mx + m.shape[1]] = m
    col[sub] = rgb(PAL["gold"])
    hgt += sub * 1.0
    tg = np.kron(hills(46, 6, 8, False), np.ones((CH, CW), bool))
    ty0, tx0 = h - R - 24 - tg.shape[0], int(cx) - tg.shape[1] // 2
    sub = np.zeros((h, w), bool)
    sub[ty0:ty0 + tg.shape[0], tx0:tx0 + tg.shape[1]] = tg
    sub &= face
    col[sub] = rgb(PAL["scarlet"])
    hgt += sub * .8
    hgt = nd.gaussian_filter(hgt, 1.0)
    out = lit(col, hgt, 1.6, .35, .62)
    save("plaque.webp", out, nd.gaussian_filter(inside.astype(float), .8))


def swag(w=420, h=230):
    """One scarlet jwmgra swag with a gold Hajw border on its lower edge and a short fringe."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    t = x / w
    depth = (h - 46) * np.sin(np.pi * t) ** .9 + 20
    s = y / depth
    cloth = s <= 1
    # agor border following the lower edge: sample a hills band by distance from the edge
    gb = np.vstack([hills(w // CW + 1, 7, 8, False), np.zeros((1, w // CW + 1), bool), diamond_chain(w // CW + 1)])
    bm = np.kron(gb, np.ones((CH, CW), bool))[:, :w]
    bh = bm.shape[0]
    dist_from_edge = (depth - y).astype(int)
    on = cloth & (dist_from_edge < bh) & (dist_from_edge >= 0)
    col = np.zeros((h, w, 3)) + rgb(PAL["scarlet"])
    idx = np.clip(bh - 1 - dist_from_edge, 0, bh - 1)
    thread = np.zeros((h, w), bool)
    thread[on] = bm[idx[on], x[on].astype(int)]
    col[thread] = rgb(PAL["gold"])
    folds = np.cos(2 * np.pi * 3.6 * np.clip(s, 0, 1)) * 2.4 * np.sin(np.pi * t)
    hgt = nd.gaussian_filter(folds + weave_px(h, w) * .15 + thread * .6, 1.0)
    ao = 1 - .22 * (.5 - .5 * np.cos(2 * np.pi * 3.6 * np.clip(s, 0, 1)))
    mul, hl = light(hgt, .9, .15, .66)
    out = col * (mul * ao)[..., None] + hl[..., None]
    # fringe below the edge
    fr = (s > 1) & (y < depth + 16) & ((x.astype(int) % 4) < 2)
    out[fr] = rgb(PAL["gold"]) * (1 - (y[fr] - depth[fr]) / 30)[:, None]
    alpha = (cloth | fr).astype(float)
    save("swag.webp", out, nd.gaussian_filter(alpha, .6))


def header(w=1200, h=None):
    col, hgt = aronai_band(w, PAL["navy"], PAL["gold"])
    save("header.webp", lit(col, hgt))


def wing(w=130, h=150):
    """One butterfly wing (right side): scarlet jwmgra with a gold Hajw edge and small gold butis."""
    y, x = np.mgrid[0:h, 0:w].astype(float)

    def lobe(cx, cy, rx, ry, ang):
        c, s_ = np.cos(ang), np.sin(ang)
        u, v = (x - cx) * c + (y - cy) * s_, -(x - cx) * s_ + (y - cy) * c
        return (u / rx) ** 2 + (v / ry) ** 2 < 1
    up = lobe(w * .5, h * .34, w * .5, h * .25, -.55)
    lo = lobe(w * .36, h * .72, w * .3, h * .2, .5)
    wg = (up | lo) & (x > 3)
    dist = nd.distance_transform_edt(wg)
    col = np.zeros((h, w, 3)) + rgb(PAL["scarlet"])
    teeth = wg & (dist < 10) & (dist > 2) & ((((x + y) // 4) % 2) == 0)
    rim = wg & (dist <= 2)
    col[teeth | rim] = rgb(PAL["gold"])
    g = np.zeros((h // CH + 1, w // CW + 1), bool)
    for cy, cx in ((int(h * .3 / CH), int(w * .55 / CW)), (int(h * .72 / CH), int(w * .36 / CW))):
        paste(g, buti(3), cy - 4, cx - 4)
    bm = np.kron(g, np.ones((CH, CW), bool))[:h, :w] & wg & (dist > 10)
    col[bm] = rgb(PAL["gold"])
    body = (np.abs(x - 2) < 3) & (y > h * .15) & (y < h * .9)
    col[body] = rgb(PAL["ink"])
    hgt = nd.gaussian_filter(np.clip(dist, 0, 14) / 14 + (teeth | bm) * .35, 1.2)
    save("wing.webp", lit(col, hgt, 2.0, .3, .62), nd.gaussian_filter((wg | body).astype(float), .7))


def kham(w=96, h=96):
    """Kham drum for the sound toggle: wooden barrel with zigzag leather lacing."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = w / 2, h / 2
    body = (np.abs(y - cy) < h * .22 * (1 + .25 * np.cos(np.pi * (x - cx) / (w * .9)))) & (np.abs(x - cx) < w * .42)
    heads = body & (np.abs(np.abs(x - cx) - w * .4) < 3)
    col = np.zeros((h, w, 3)) + rgb("#8A5A2B")
    zz = (np.abs(((x - cx) / 6) % 2 - 1) * h * .36 + cy - h * .18)
    lace = body & (np.abs(y - zz) < 1.3)
    col[lace] = rgb(PAL["ivory"])
    col[heads] = rgb(PAL["beige"])
    yy = (y - cy) / (h * .25)
    hgt = np.sqrt(np.clip(1 - yy ** 2, 0, 1)) * 6 * body + lace * 1.2
    save("kham.webp", lit(col, nd.gaussian_filter(hgt, 1), 1.0, .3, .55), nd.gaussian_filter(body.astype(float), .6))


def crest():
    """Large gold peacock-eye medallion for section headings (thread only, transparent)."""
    g = np.pad(medallion(12), 2)
    m = np.kron(g, np.ones((CH * 2, CW * 2), bool))
    hgt = nd.gaussian_filter(m.astype(float), 1)
    col = np.zeros(m.shape + (3,)) + rgb(PAL["gold"])
    save("crest.webp", lit(col, hgt, 2.0, .35, .7), m.astype(float))


def linen(size=512):
    rng = np.random.default_rng(3)
    fx = nd.gaussian_filter(rng.normal(size=(size, size)), (0, 5), mode="wrap")
    fy = nd.gaussian_filter(rng.normal(size=(size, size)), (5, 0), mode="wrap")
    mul, _ = light(fx + fy, 1.0, 0, .85)
    blot = nd.gaussian_filter(rng.normal(size=(size, size)), 40, mode="wrap")
    col = rgb(PAL["ivory"])[None, None] * (mul + blot / np.abs(blot).max() * .02)[..., None]
    save("linen.webp", col, q=82)


# ------------------------------------------------------------------ curtain opening sequence
def curtain_texture(H, Wc):
    """Flat (unfolded) left curtain: gwmw yellow with sparse scarlet butis, scarlet agor column at the inner edge,
    scarlet hem panel. Wc = flat cloth width in px (wider than the half screen, it gathers)."""
    gw, gh = Wc // CW + 1, H // CH + 1
    g = np.zeros((gh, gw), bool)
    for j, yy in enumerate(range(10, gh, 30)):
        for xx in range(6 + (15 if j % 2 else 0), gw - 40, 30):
            paste(g, buti(2), yy, xx)
    col, hgt = render_grid(g, PAL["yellow"], PAL["scarlet"], pad_rows=0)
    col, hgt = col[:H, :Wc], hgt[:H, :Wc]
    bc, bh = aronai_band(H, PAL["scarlet"], PAL["gold"])
    bc, bh = np.transpose(bc, (1, 0, 2)), bh.T
    bw = bc.shape[1]
    col[:, Wc - bw:], hgt[:, Wc - bw:] = bc, bh
    hc, hh = aronai_band(Wc, PAL["scarlet"], PAL["gold"])
    y0 = H - hc.shape[0] - int(H * .025)
    col[y0:y0 + hc.shape[0]], hgt[y0:y0 + hc.shape[0]] = hc, hh
    return col, hgt


def curtain_frames(n=36, W=640, H=1388):
    half = W // 2
    Wc = int(half * 1.5)
    tex, thgt = curtain_texture(H, Wc)
    y = np.arange(H)
    yt = int(H * .6)
    e_open = np.where(y < yt, .10 + .2 * np.cos(np.pi / 2 * np.clip(y / yt, 0, 1)) ** 1.3, .10 + .09 * np.clip((y - yt) / (H - yt), 0, 1) ** .75) * W
    os.makedirs(os.path.join(OUT, "curtain"), exist_ok=True)
    tie_c, _ = aronai_band(int(W * .3), PAL["emerald"], PAL["ivory"], "slim")
    for i in range(n):
        t = i / (n - 1)
        # zip: the middle rows open first
        s = np.clip((t - np.abs(y / H - .48) * .55) / .6, 0, 1)
        s = s * s * (3 - 2 * s)
        e = half + 6 + (e_open - half - 6) * s                     # inner edge x of the left curtain
        X = np.arange(half)[None, :].repeat(H, 0)
        E = e[:, None]
        inside = X < E
        u = np.clip(X / E, 0, 1)                                    # 0 outer edge .. 1 inner edge
        sx = np.clip((u * (Wc - 1)).astype(int), 0, Wc - 1)
        col = tex[y[:, None].repeat(half, 1), sx]
        th = thgt[y[:, None].repeat(half, 1), sx]
        squeeze = np.clip(1 - E / half, 0, 1)                       # 0 closed .. ~.8 open
        folds = 10
        ph = 2 * np.pi * folds * u ** .92 + y[:, None] / 260 * (1 - squeeze)
        hgt = np.cos(ph) * (3 + 17 * squeeze) + th * 2
        # a rolled hem gives the inner edge thickness
        dpx = E - X
        hgt += 7 * np.exp(-(dpx / 7) ** 2) * inside
        ao = 1 - (.12 + .34 * squeeze) * (.5 - .5 * np.cos(ph))
        ao *= 1 - .35 * np.exp(-((dpx - 2) / 2.5) ** 2) * inside       # dark underside of the hem roll
        ao *= (1 - .25 * np.exp(-y / (H * .07)))[:, None]
        alpha = inside.astype(float)
        # aronai tie-back fades in at the end (flat colour now, lit with the cloth below)
        k = np.clip((t - .8) / .2, 0, 1)
        if k > 0:
            th_ = tie_c.shape[0]
            et = int(e[yt])
            y0 = yt - th_ // 2
            col[y0:y0 + th_, :et + 6] = col[y0:y0 + th_, :et + 6] * (1 - k) + tie_c[:, :et + 6] * k
            hgt[y0:y0 + th_, :et + 6] += 6 * k * np.sin(np.linspace(0, np.pi, th_))[:, None]
            ao[y0:y0 + th_, :et + 6] = ao[y0:y0 + th_, :et + 6] * (1 - k) + k
            alpha[y0:y0 + th_, :et + 6] = np.maximum(alpha[y0:y0 + th_, :et + 6], k)
        # mirror into the right curtain, then light the whole stage at once so both sides share the top-left light
        Hf = np.zeros((H, W))
        Cf = np.zeros((H, W, 3))
        Af = np.zeros((H, W))
        AOf = np.ones((H, W))
        Hf[:, :half], Hf[:, half:] = hgt, hgt[:, ::-1]
        Cf[:, :half], Cf[:, half:] = col, col[:, ::-1]
        Af[:, :half], Af[:, half:] = alpha, alpha[:, ::-1]
        AOf[:, :half], AOf[:, half:] = ao, ao[:, ::-1]
        mul, hl = light(nd.gaussian_filter(Hf, 1.3), .8, .28, .52)
        out = Cf * (mul * AOf)[..., None] + hl[..., None]
        Af = nd.gaussian_filter(Af, .7)
        # the curtains cast a soft shadow on the stage behind them: down and right, plus a contact shadow
        cast = nd.gaussian_filter(nd.shift(Af, (14, 20), order=0), 16) * .5
        contact = nd.gaussian_filter(Af, 6) * .3
        sa = np.clip(np.maximum(cast, contact), 0, 1) * (1 - Af)
        fa = Af + sa
        full = (out * Af[..., None] + rgb("#2A1608") * sa[..., None]) / np.maximum(fa, 1e-4)[..., None]
        save(f"curtain/{i:02d}.webp", full, fa, q=78)
    print("curtain frames", n)


if __name__ == "__main__":
    bands()
    door()
    plaque()
    plaque_shadow()
    tassel()
    swag()
    header()
    wing()
    kham()
    crest()
    linen()
    if "--frames" in sys.argv:
        curtain_frames()
    print("art written to", OUT)
