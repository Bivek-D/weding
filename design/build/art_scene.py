"""Sculpted scene elements for the opened hero (round 3): banana plants, areca palms, marigolds, garland strands.

Each element is drawn as a height map and lit by the same top-left light as the rest of the card
(art_bodo2.light), so everything reads as one clay-like stage. Writes WebP into site/public/art/.
Run with the scratch venv:  python art_scene.py
"""
import numpy as np
from scipy import ndimage as nd

from art_bodo2 import PAL, light, rgb, save

RNG = np.random.default_rng(7)


class Canvas:
    """Painter's-order canvas: later strokes cover earlier ones; keeps colour, height and alpha."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.col = np.zeros((h, w, 3))
        self.hgt = np.zeros((h, w))
        self.a = np.zeros((h, w))

    def splat(self, xs, ys, col, hgt):
        xi, yi = np.round(xs).astype(int), np.round(ys).astype(int)
        ok = (xi >= 0) & (xi < self.w) & (yi >= 0) & (yi < self.h)
        xi, yi = xi[ok], yi[ok]
        self.col[yi, xi] = col[ok] if np.ndim(col) > 1 else col
        self.hgt[yi, xi] = hgt[ok] if np.ndim(hgt) else hgt
        self.a[yi, xi] = 1

    def render(self, k=1.0, spec=.25, amb=.55, blur=.8):
        a = nd.binary_closing(self.a > 0, iterations=1)
        h = nd.gaussian_filter(self.hgt, blur)
        mul, hl = light(h, k, spec, amb)
        out = self.col * mul[..., None] + hl[..., None]
        return np.clip(out, 0, 1), nd.gaussian_filter(a.astype(float), .6)


def bezier(p0, p1, p2, t):
    t = t[..., None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def leaf(cv, p0, p1, p2, width, base_col, tip_col, tears=0, droop_shade=0.0):
    """A long leaf along a quadratic curve, convex across its width, with a raised midrib and optional tears."""
    nt, ns = 520, 90
    t = np.linspace(0, 1, nt)[:, None].repeat(ns, 1)
    sgrid = np.linspace(-1, 1, ns)[None, :].repeat(nt, 0)
    c = bezier(np.array(p0, float), np.array(p1, float), np.array(p2, float), t)          # (nt, ns, 2)
    d = np.gradient(c[:, 0, :], axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    wprof = width * np.sin(np.pi * np.clip(t, 0, 1)) ** .55 * (1 - .25 * t)
    pts = c + n[:, None, :] * (sgrid * wprof)[..., None]
    keep = np.ones_like(t, bool)
    crease = np.zeros_like(t, bool)
    for _ in range(tears):                                     # banana leaves tear along their veins
        tc = RNG.uniform(.25, .9)
        side = RNG.choice([-1, 1])
        crease |= (np.abs(t - tc - sgrid * side * .02) < .004) & (sgrid * side > .2)
    hgt = (1 - sgrid ** 2) * 4 + np.exp(-(sgrid / .06) ** 2) * 1.6 + (np.abs((t * 60) % 1 - .5) < .08) * .25
    mix = np.clip(t * 1.1, 0, 1)[..., None]
    col = rgb(base_col) * (1 - mix) + rgb(tip_col) * mix
    col = col * (1 - droop_shade * (sgrid[..., None] < 0))
    rib = np.abs(sgrid) < .05
    col = np.where(rib[..., None], col * 1.18 + .03, col)
    col = np.where(crease[..., None], col * .72, col)
    hgt = hgt - crease * 1.5
    for i in range(nt):                                         # paint back to front along the leaf
        k = keep[i]
        cv.splat(pts[i, k, 0], pts[i, k, 1], col[i, k], hgt[i, k])


def banana(w=320, h=640, flip=False):
    cv = Canvas(w, h)
    cx, top = w * .5, h * .5
    # long paddle leaves that rise and droop, back leaves first; a young rolled leaf stands upright
    specs = [((-.98, -.05), (-.45, -.85), 36, 3), ((.98, -.08), (.5, -.85), 36, 3), ((-.55, -.8), (-.1, -.98), 32, 2),
             ((.6, -.78), (.15, -.98), 32, 2), ((-.98, .35), (-.75, -.35), 34, 4), ((.98, .3), (.75, -.4), 34, 4),
             ((.05, -.98), (.0, -.6), 9, 0)]
    for (tx, ty), (mx, my), wd, tears in specs:
        p0 = (cx + RNG.uniform(-4, 4), top)
        p2 = (cx + tx * w * .5, top + ty * h * .5)
        p1 = (cx + mx * w * .5, top + my * h * .5)
        leaf(cv, p0, p1, p2, wd, "#3E8A2E", "#7DB83E", tears, .2)
    # pseudostem, tapered, with brown-purple streaks
    ys = np.arange(int(top - 10), h)
    for y in ys:
        r = 13 + 9 * (y - top) / (h - top)
        xs = np.arange(int(cx - r), int(cx + r) + 1)
        u = (xs - cx) / r
        streak = (np.sin(xs * .9 + y * .03) > .7)
        col = np.where(streak[:, None], rgb("#6E5A2E"), rgb("#6FA03A") * (1 - .25 * (y - top) / (h - top)))
        cv.splat(xs.astype(float), np.full(xs.shape, y, float), col, np.sqrt(np.clip(1 - u ** 2, 0, 1)) * 7)
    out, a = cv.render(.9, .22, .55)
    if flip:
        out, a = out[:, ::-1], a[:, ::-1]
    return out, a


def palm(w=260, h=700):
    """Areca palm far behind the stage: slim ringed trunk and a crown of arching fronds, softened for distance."""
    cv = Canvas(w, h)
    cx = w * .5
    crown = h * .16
    for y in range(int(crown), h):
        lean = (y - crown) / (h - crown)
        x0 = cx + 10 * np.sin(lean * 2.2)
        r = 6 + 4 * lean
        xs = np.arange(int(x0 - r), int(x0 + r) + 1)
        ring = (int(y) % 11) < 2
        col = rgb("#8C8466") * (0.8 if ring else 1)
        cv.splat(xs.astype(float), np.full(xs.shape, y, float), np.tile(col, (xs.size, 1)), np.sqrt(np.clip(1 - ((xs - x0) / r) ** 2, 0, 1)) * 5)
    for ang in np.linspace(-2.9, -.25, 10):
        L = RNG.uniform(.42, .52) * w
        p0 = np.array([cx, crown])
        p2 = p0 + L * np.array([np.cos(ang), np.sin(ang) + 1.25])
        p1 = p0 + L * .6 * np.array([np.cos(ang), np.sin(ang) - .2])
        t = np.linspace(0, 1, 160)
        c = bezier(p0, p1, p2, t)
        d = np.gradient(c, axis=0)
        n = np.stack([-d[:, 1], d[:, 0]], 1)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        for i in range(0, 160, 3):                               # leaflets along the frond
            ll = 26 * np.sin(np.pi * t[i]) + 4
            for side in (-1, 1):
                s = np.linspace(0, 1, 30)
                pts = c[i] + n[i] * side * s[:, None] * ll + d[i] / (np.linalg.norm(d[i]) + 1e-9) * s[:, None] * ll * .5
                cv.splat(pts[:, 0], pts[:, 1], np.tile(rgb("#5E8A4A"), (30, 1)), np.full(30, 1.5))
        cv.splat(c[:, 0], c[:, 1], np.tile(rgb("#4E7A3A"), (160, 1)), np.full(160, 2.5))
    out, a = cv.render(.6, .1, .7, 1.0)
    haze = rgb("#E9E2CF")
    out = out * .55 + haze * .45                                   # aerial perspective
    return out, a


def marigold(cv, x, y, r, warm=0.0):
    yy, xx = np.mgrid[int(y - r) - 1:int(y + r) + 2, int(x - r) - 1:int(x + r) + 2].astype(float)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
    ang = np.arctan2(yy - y, xx - x)
    frill = .07 * np.sin(ang * 14 + d * 9) + .05 * np.sin(ang * 23 - d * 13)
    inside = d < 1 + frill
    hgt = np.sqrt(np.clip(1 - d ** 2, 0, 1)) * r * .55 + np.abs(np.sin(d * 9 + ang * 3)) * r * .08
    c1, c2 = rgb("#F7B32B"), rgb("#E8701A")
    col = c1 * (1 - d[..., None]) + c2 * d[..., None]
    col = col * (1 - warm) + rgb(PAL["scarlet"]) * warm * .5 + col * warm * .5
    cv.splat(xx[inside], yy[inside], col[inside], hgt[inside])


def bush(w=340, h=260, flip=False):
    """Foreground marigold bush: a mound of leaves with flowers, for the front corners."""
    cv = Canvas(w, h)
    for _ in range(70):                                        # leaves
        x, y = RNG.uniform(.05, .95) * w, RNG.uniform(.35, 1.0) * h
        ang = RNG.uniform(-2.6, -.5)
        L = RNG.uniform(26, 46)
        p0 = np.array([x, y])
        p2 = p0 + L * np.array([np.cos(ang), np.sin(ang)])
        leaf(cv, p0, (p0 + p2) / 2 + RNG.normal(0, 4, 2), p2, RNG.uniform(7, 11), "#2F6B2A", "#4F8E36")
    pts = sorted([(RNG.uniform(.08, .92) * w, RNG.uniform(.18, .8) * h, RNG.uniform(20, 31)) for _ in range(13)],
                 key=lambda p: p[1])
    for x, y, r in pts:
        marigold(cv, x, y, r, RNG.uniform(0, .5))
    out, a = cv.render(1.1, .25, .55)
    if flip:
        out, a = out[:, ::-1], a[:, ::-1]
    return out, a


def strand(w=40, h=300):
    """Marigold garland strand: alternating orange and yellow flowers, a leaf pair every few, a small tassel."""
    cv = Canvas(w, h)
    y = 10
    i = 0
    while y < h - 40:
        if i % 5 == 4:
            for side in (-1, 1):
                leaf(cv, (w / 2, y), (w / 2 + side * 8, y + 4), (w / 2 + side * 17, y + 12), 4, "#2F6B2A", "#5C9A3A")
        marigold(cv, w / 2 + np.sin(i * 1.3) * 1.5, y, 9.5, .35 if i % 2 else 0)
        y += 15
        i += 1
    for j in range(9):                                        # thread tassel
        xs = np.full(30, w / 2 + (j - 4) * 1.6)
        ys = np.linspace(y, y + 28, 30)
        cv.splat(xs, ys, np.tile(rgb(PAL["scarlet"] if j % 2 else PAL["gold"]), (30, 1)), np.full(30, 1.0))
    return cv.render(1.0, .3, .55)


if __name__ == "__main__" and "--bow" not in __import__("sys").argv:
    for name, (img, a) in {"banana-l": banana(), "banana-r": banana(flip=True), "palm": palm(),
                           "bush-l": bush(), "bush-r": bush(flip=True), "strand": strand()}.items():
        save(f"{name}.webp", img, a)
        print("wrote", name, img.shape[1], "x", img.shape[0])


# ------------------------------------------------------------------ the bow tied around the cover
def ribbon_tex(width_px=56, length_px=900):
    """Yellow aronai ribbon (scarlet agor), squeezed to ribbon width."""
    from art_bodo2 import aronai_band
    col, hgt = aronai_band(length_px, PAL["yellow"], PAL["scarlet"])
    rows = np.linspace(0, col.shape[0] - 1, width_px).astype(int)
    return col[rows], hgt[rows]


def ribbon_along(cv, pts_fn, n, width, tex, thgt, shade_fn=None, cut=None, t0=0.0):
    """Paint a ribbon along a curve: pts_fn(t) -> (x, y) for t in [0, 1]; texture runs along its length.
    shade_fn(t) -> multiplier (the back of a loop is darker); cut(t, s) -> keep mask (V-notched ends)."""
    t = np.linspace(0, 1, n)
    c = np.array([pts_fn(v) for v in t])
    d = np.gradient(c, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    L = np.cumsum(np.r_[0, np.linalg.norm(np.diff(c, axis=0), axis=1)])
    ns = int(width * 1.6)
    s = np.linspace(-1, 1, ns)
    for i in range(n):
        keep = np.ones(ns, bool) if cut is None else cut(t[i], s)
        if not keep.any():
            continue
        row = np.clip(((s + 1) / 2 * (tex.shape[0] - 1)).astype(int), 0, tex.shape[0] - 1)
        colx = int((L[i] + t0) % tex.shape[1])
        col = tex[row, colx]
        h = thgt[row, colx] * 1.5 + (1 - s ** 2) * 5
        if shade_fn is not None:
            col = col * shade_fn(t[i])
        p = c[i] + nrm[i] * (s[:, None] * width / 2)
        cv.splat(p[keep, 0], p[keep, 1], col[keep], h[keep])


def bow_parts():
    tex, thgt = ribbon_tex()
    W = 56                                                  # ribbon width (2x px)
    # loop (left; the right one is mirrored): a teardrop from the knot out to the left and back
    cv = Canvas(300, 230)
    kx, ky = 286, 118
    A, B = 250, 82

    def loop(t, back):
        th = np.pi + t * np.pi if back else t * np.pi        # back half first, then the front half over it
        x = kx - A * (1 - np.cos(th)) / 2
        y = ky - B * np.sin(th) * (0.55 + 0.45 * (1 - np.cos(th)) / 2) - 26 * (1 - np.cos(th)) / 2
        return x, y
    ribbon_along(cv, lambda t: loop(t, True), 700, W, tex, thgt, shade_fn=lambda t: .62 + .2 * t, t0=400)
    ribbon_along(cv, lambda t: loop(t, False), 700, W, tex, thgt, shade_fn=lambda t: 1.05 - .15 * np.sin(np.pi * t))
    img, a = cv.render(1.1, .3, .55)
    save("bow-loop.webp", img, a)

    # tail (left; mirrored for the right): falls from the knot with a soft S, V-cut end
    cv = Canvas(200, 330)
    p0, p1, p2 = np.array([186., 12.]), np.array([150., 140.]), np.array([70., 300.])
    ribbon_along(cv, lambda t: tuple(bezier(p0, p1, p2, np.array(t))), 600, W, tex, thgt,
                 shade_fn=lambda t: .95 - .15 * t, cut=lambda t, s: t < 1 - .09 * (1 - np.abs(s)), t0=200)
    img, a = cv.render(1.1, .3, .55)
    save("bow-tail.webp", img, a)

    # the knot: a short wrapped band
    cv = Canvas(90, 110)
    ribbon_along(cv, lambda t: (45, 8 + t * 94), 200, 70, tex, thgt, shade_fn=lambda t: 1 - .25 * abs(t - .4))
    img, a = cv.render(1.2, .35, .5)
    save("bow-knot.webp", img, a)

    # the straight ribbon across the doors (tiles along x)
    col, hgt = tex[:, :900], thgt[:, :900]
    hgt = hgt * 1.5 + (1 - np.linspace(-1, 1, W) ** 2)[:, None] * 5
    from art_bodo2 import lit
    save("ribbon.webp", lit(col, hgt, 1.2, .3, .6))


if __name__ == "__main__" and "--bow" in __import__("sys").argv:
    bow_parts()
