"""Raised embroidery (stumpwork) for the scroll sections: padded silk satin stitch, layered feathers and
petals, gold and pearl beads, lit from the top left, with no cast shadow baked in. The page adds a separate
shadow that shifts with tilt and scroll, so each piece looks lifted off the paper (like the beaded swans in
the user's reference).

Motifs from references/bodo-research.md: the paired peacocks facing each other in the agor centre column,
the peacock-eye medallion, marigold strands, leafy vines.

Writes site/public/art/relief/*.webp at 2x the CSS size.
Run with the project venv:  ..\\..\\..\\.cache\\venv\\Scripts\\python art_relief.py
"""
import numpy as np
from scipy import ndimage as nd

import art_bodo2 as A

S = 2                                   # px per CSS px
RNG = np.random.default_rng(7)
LIGHT_ANG = np.arctan2(-1, -1)          # light comes from the top left


def hexc(h, mute=.12):
    """A palette colour, softened a little toward warm ivory so silk reads refined, not plastic."""
    return A.rgb(h) * (1 - mute) + A.rgb("#EFE6D6") * mute


C = dict(
    teal=hexc("#2F6F7E"), teal_d=hexc("#1E4B5C"), peacock=hexc("#3A5F9E"), emerald=hexc("#2E7A55"),
    emerald_d=hexc("#1F5A3E"), leaf=hexc("#3C7F4E"), leaf_l=hexc("#86AE5A"), stem=hexc("#4C6B36"),
    scarlet=hexc("#B83A2E"), scarlet_d=hexc("#8E2620"), marigold=hexc("#E58A24"), yellow=hexc("#EDB828"),
    saffron=hexc("#F0A030"), gold=hexc("#C9A052", .05), pearl=A.rgb("#F2EADC"), ink=A.rgb("#2A1A10"),
    ivory=A.rgb("#FBF6EC"),
)


class Canvas:
    def __init__(s, w, h):
        H, W = h * S, w * S
        s.col = np.zeros((H, W, 3))
        s.hgt = np.zeros((H, W))
        s.a = np.zeros((H, W))
        s.gloss = np.zeros((H, W))

    def win(s, x0, y0, x1, y1):
        """Slices and CSS coordinates for a bounding box, so each shape only touches its own pixels."""
        H, W = s.a.shape
        r0, r1 = max(int(y0 * S) - 2, 0), min(int(np.ceil(y1 * S)) + 2, H)
        c0, c1 = max(int(x0 * S) - 2, 0), min(int(np.ceil(x1 * S)) + 2, W)
        if r1 <= r0 or c1 <= c0:
            return None
        Y, X = (np.mgrid[r0:r1, c0:c1] + .5) / S
        return (slice(r0, r1), slice(c0, c1)), X, Y

    def paint(s, sl, mask, color, height, gloss=0.0):
        """Lay a shape on top of whatever is there: it sits on the current surface (raised work stacks)."""
        m = mask > 0
        if not m.any():
            return
        hg, cl, al, gl = s.hgt[sl], s.col[sl], s.a[sl], s.gloss[sl]
        base = nd.maximum_filter(np.where(m, hg, 0), size=5)      # it rests on what is under it
        cl[m] = (color if np.ndim(color) == 3 else np.broadcast_to(color, cl.shape))[m]
        hg[m] = (base + height)[m]
        al[m] = 1
        gl[m] = (gloss if np.ndim(gloss) else np.full(m.shape, gloss))[m]

    def mirror(s):
        W = s.a.shape[1]
        half = W // 2
        for arr in (s.col, s.hgt, s.a, s.gloss):
            arr[:, W - half:] = arr[:, :half][:, ::-1]

    def flip(s):
        for arr in (s.col, s.hgt, s.a, s.gloss):
            arr[:] = arr[:, ::-1]

    def render(s, name):
        h = nd.gaussian_filter(s.hgt, .55) * S
        mul, hl = A.light(h, k=.38, spec=.16, amb=.66)
        ao = 1 - np.clip((nd.gaussian_filter(s.hgt, 3) - s.hgt) * .09, 0, .32)
        out = s.col * (mul * ao)[..., None] + (hl * (.6 + 2.2 * s.gloss))[..., None]
        # a whisper of silk sheen on top of the threads
        out = out + (s.gloss * .0)[..., None]
        a = nd.gaussian_filter(s.a, .55)
        ys, xs = np.where(a > .02)
        y0, y1, x0, x1 = max(ys.min() - 4, 0), ys.max() + 5, max(xs.min() - 4, 0), xs.max() + 5
        A.save(f"relief/{name}.webp", out[y0:y1, x0:x1], a[y0:y1, x0:x1], q=90)
        print(name, (x1 - x0) // S, "x", (y1 - y0) // S, "css px")


# ------------------------------------------------------------------ thread
def silk(X, Y, ang, color, pitch=.62, stitch=4.0, var=.07, seed=0):
    """Satin stitch in direction `ang`: fine parallel threads, staggered stitch ends, each thread a touch
    lighter or darker, and a sheen that depends on how the thread lies to the light.
    Returns (rgb, ridge height, gloss)."""
    c, s = np.cos(ang), np.sin(ang)
    q = X * c + Y * s                    # along the thread
    p = -X * s + Y * c                   # across the threads
    n = np.floor(p / pitch)
    fp = p / pitch - n
    rnd = np.sin(n * 12.9898 + seed * 78.233) * 43758.5453
    rnd = rnd - np.floor(rnd)
    ridge = np.sin(np.pi * fp) ** .7
    sq = (q / stitch + rnd) % 1.0
    ends = np.clip(np.minimum(sq, 1 - sq) * stitch / .35, 0, 1)        # tiny dips where stitches meet
    h = .32 * ridge * (.6 + .4 * ends)
    sheen = abs(np.cos(ang - LIGHT_ANG - np.pi / 2))                     # threads across the light glint
    tone = 1 + var * (rnd - .5) * 2
    rgb = color * tone[..., None] * (.9 + .1 * ridge)[..., None]
    gloss = (.25 + .5 * sheen) * ridge
    return rgb, h, gloss


def local(X, Y, x0, y0, ang):
    c, s = np.cos(ang), np.sin(ang)
    dx, dy = X - x0, Y - y0
    return dx * c + dy * s, -dx * s + dy * c


def dome(d, r, h, edge=None):
    """Padded profile from a normalised inside-distance d (0 at the rim .. 1 at the core)."""
    return h * np.sqrt(np.clip(1 - (1 - np.clip(d, 0, 1)) ** 2, 0, 1))


# ------------------------------------------------------------------ elements
def feather(cv, x0, y0, ang, L, w, color, h=2.2, stitch_dir=None, seed=0, tip_round=.55, rounded=False):
    """A padded teardrop (feather, petal or leaf body) from (x0, y0) along `ang`.
    rounded=True gives a petal: it widens from the base and ends in a round, ruffled cap."""
    r = L + w
    w_ = cv.win(x0 - r, y0 - r, x0 + r, y0 + r)
    if w_ is None:
        return
    sl, X, Y = w_
    u, v = local(X, Y, x0, y0, ang)
    t = np.clip(u / L, 0, 1)
    if rounded:
        cap = np.clip((t - .62) / .38, 0, 1)
        half = w * np.sin(np.pi / 2 * np.clip(t / .62, 0, 1)) * np.sqrt(1 - cap * cap)
        half *= 1 + .12 * np.cos(np.arctan2(v, np.maximum(u - .62 * L, 1e-3)) * 5) * cap   # ruffled edge
    else:
        half = w * np.sin(np.pi * np.clip(t, 0, 1) ** tip_round)
    m = (u >= 0) & (u <= L) & (np.abs(v) < half)
    d = np.where(m, np.minimum((half - np.abs(v)) / np.maximum(w * .5, .1), np.minimum(u, L - u) / 1.2), 0)
    sd = ang + .5 * np.sign(v) if stitch_dir is None else stitch_dir
    rgb, rh, gl = silk(X, Y, sd, color, seed=seed)
    cv.paint(sl, m, rgb, dome(d, 1, h) + rh, gl)


def blob(cv, x0, y0, rx, ry, ang, color, h, stitch, seed=0):
    r = max(rx, ry)
    w_ = cv.win(x0 - r, y0 - r, x0 + r, y0 + r)
    if w_ is None:
        return
    sl, X, Y = w_
    u, v = local(X, Y, x0, y0, ang)
    e = (u / rx) ** 2 + (v / ry) ** 2
    m = e <= 1
    rgb, rh, gl = silk(X, Y, stitch, color, seed=seed)
    cv.paint(sl, m, rgb, dome((1 - np.sqrt(np.clip(e, 0, 1))) * min(rx, ry) / 2.2, 1, h) + rh, gl)


def stroke(cv, pts, r0, r1, color, h, seed=0, twist=0.0):
    """A padded stroke along a path, stitched across its own direction (couched cord / neck / stem)."""
    pts = np.asarray(pts, float)
    R = max(r0, r1)
    w_ = cv.win(pts[:, 0].min() - R, pts[:, 1].min() - R, pts[:, 0].max() + R, pts[:, 1].max() + R)
    sl, X, Y = w_
    from scipy.spatial import cKDTree
    d, i = cKDTree(pts).query(np.dstack([X, Y]).reshape(-1, 2), distance_upper_bound=R + 1)
    d = d.reshape(X.shape)
    i = np.minimum(i.reshape(X.shape), len(pts) - 1)
    t = i / (len(pts) - 1)
    r = r0 + (r1 - r0) * t
    m = d <= r
    tan = np.gradient(pts, axis=0)
    ang = np.arctan2(tan[i, 1], tan[i, 0]) + np.pi / 2 + twist
    rgb, rh, gl = silk(X, Y, 0, color, seed=seed)
    # stitches lie across the stroke: recompute with the local direction (cheap approximation per pixel)
    c, s = np.cos(ang), np.sin(ang)
    p = -X * s + Y * c
    fp = (p / .62) % 1
    ridge = np.sin(np.pi * fp) ** .7
    rgb = color * (.9 + .1 * ridge)[..., None]
    gl = (.3 + .4 * np.abs(np.cos(ang - LIGHT_ANG - np.pi / 2))) * ridge
    cv.paint(sl, m, rgb, dome(1 - d / np.maximum(r, .1), 1, h) + .3 * ridge, gl)


def beads(cv, pts, r, color, gloss=1.0):
    for x, y in np.atleast_2d(pts):
        w_ = cv.win(x - r, y - r, x + r, y + r)
        if w_ is None:
            continue
        sl, X, Y = w_
        d2 = (X - x) ** 2 + (Y - y) ** 2
        m = d2 < r * r
        hh = np.sqrt(np.clip(r * r - d2, 0, None)) * .95
        cv.paint(sl, m, color, hh, gloss)


def bezier(p0, p1, p2, p3, n=300):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, float) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def along(pts, step, start=0.0):
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    s = np.arange(start, seg[-1], step)
    xy = np.c_[np.interp(s, seg, pts[:, 0]), np.interp(s, seg, pts[:, 1])]
    tan = np.c_[np.interp(s + .5, seg, pts[:, 0]) - xy[:, 0], np.interp(s + .5, seg, pts[:, 1]) - xy[:, 1]]
    return xy, np.arctan2(tan[:, 1], tan[:, 0])


def ring(cx, cy, R, n, phase=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + phase
    return np.c_[cx + R * np.cos(a), cy + R * np.sin(a)]


def marigold(cv, x, y, r, tone=0):
    """Three rings of padded petals, outer first, each ring lifted on the last: a ruffled marigold head."""
    base = [C["marigold"], C["yellow"], C["saffron"]][tone % 3]
    rot = RNG.uniform(0, 1)
    for k, (rr, n, L, w) in enumerate(((r * .15, 14, r * .85, r * .3), (r * .08, 11, r * .62, r * .3), (0, 8, r * .4, r * .27))):
        shade = np.clip(base * (1.0 + .06 * k), 0, 1)
        for j in range(n):
            a = 2 * np.pi * (j + rot + k * .37) / n
            feather(cv, x + rr * np.cos(a), y + rr * np.sin(a), a, L, w, shade, h=1.0 + .45 * k, seed=j + 9 * k,
                    stitch_dir=a, rounded=True)
    beads(cv, [(x, y)], r * .16, C["scarlet_d"] * .9 + base * .1, .4)


def leaf(cv, x, y, ang, L, w, seed=0):
    """Fishbone-stitched leaf: stitches slant into the midrib from both sides, darker at the base."""
    feather(cv, x, y, ang, L, w, C["leaf"] * .95 + C["leaf_l"] * .05, h=1.6, seed=seed)


# ------------------------------------------------------------------ the pieces
def peacock_half(cv):
    """The left peacock, facing right. Built back to front so later layers stack on earlier ones."""
    # tail: a fan of long feathers sweeping down and out behind the body, each ending in an eye
    for k in range(9):
        a = np.deg2rad(168 + k * 6.5)
        L = 62 + 14 * np.sin(k / 8 * np.pi)
        x0, y0 = 98 + k * .5, 160 + k * 1.4
        col = [C["emerald"], C["teal"], C["emerald_d"]][k % 3]
        feather(cv, x0, y0, a, L, 5.0 + k * .12, col, h=2.2, stitch_dir=a, seed=k, tip_round=.45)
        ex, ey = x0 + (L - 6) * np.cos(a), y0 + (L - 6) * np.sin(a)
        blob(cv, ex, ey, 5.0, 4.0, a, C["gold"], 1.2, a + 1.57, seed=k)
        blob(cv, ex, ey, 3.4, 2.7, a, C["teal_d"], 1.0, a, seed=k + 3)
        beads(cv, [(ex + .6 * np.cos(a), ey + .6 * np.sin(a))], 1.4, C["scarlet"], .8)
    # body: a full padded teardrop in deep teal, breast forward
    feather(cv, 90, 168, np.deg2rad(-24), 56, 20, C["teal_d"], h=5.2, stitch_dir=np.deg2rad(-24) + 1.2, seed=31, tip_round=.75)
    # neck and head: a short swan-like curve; the two heads meet over the medallion and make a heart
    neck = bezier((132, 146), (150, 124), (128, 100), (148, 86), 260)
    stroke(cv, neck, 8.0, 5.2, C["peacock"], 3.6, seed=4)
    blob(cv, 152, 82, 7.0, 6.2, -.2, C["peacock"], 3.6, .5, seed=5)
    stroke(cv, bezier((158, 82), (160.5, 83), (162, 84.5), (163.5, 86.5), 40), 1.8, .5, C["gold"], 1.2)
    beads(cv, [(154, 79.5)], 1.3, C["ink"], 1.6)
    # crest: fine gold threads tipped with beads
    for tx, ty in ((142, 62), (147, 59.5), (152.5, 60.5)):
        stroke(cv, bezier((150, 75), (149.5, 70), (tx + 1.5, ty + 4.5), (tx, ty), 40), .45, .4, C["gold"], .6)
        beads(cv, [(tx, ty)], 1.7, C["gold"], 1.4)
    # wing: three rows of scalloped feathers, scarlet edged with gold (the jwmgra held out in Bagurumba)
    for row, (n, L, w, col) in enumerate(((6, 26, 5.0, C["scarlet_d"]), (5, 19, 4.8, C["scarlet"]), (4, 12, 4.4, C["scarlet"]))):
        for j in range(n):
            a = np.deg2rad(172 + j * 5 - row * 3)
            bx = 126 - row * 8 + j * 1.0
            by = 148 + j * 3.6 + row * 2
            feather(cv, bx, by, a, L, w, col * (1 + .04 * row), h=1.5, seed=row * 10 + j, rounded=True)
    for x, y in along(bezier((128, 146), (114, 152), (102, 160), (92, 170), 100), 2.9)[0]:
        beads(cv, [(x, y)], .95, C["gold"], 1.3)


def peacocks():
    cv = Canvas(330, 250)
    peacock_half(cv)
    # the pearl string they stand on
    pts, _ = along(bezier((30, 192), (110, 200), (220, 200), (300, 192)), 5.4)
    beads(cv, pts, 2.6, C["pearl"], 1.1)
    cv.mirror()
    # the peacock-eye medallion between them, on the centre line
    cx, cy = 165, 170
    beads(cv, ring(cx, cy, 15, 18), 1.6, C["gold"], 1.3)
    beads(cv, ring(cx, cy, 10.5, 12, .26), 1.5, C["pearl"], 1.2)
    blob(cv, cx, cy, 7.4, 7.4, 0, C["scarlet"], 2.2, .8, seed=50)
    blob(cv, cx, cy, 4.2, 4.2, 0, C["emerald"], 1.6, -.6, seed=51)
    beads(cv, [(cx, cy)], 1.6, C["gold"], 1.4)
    cv.render("peacocks")


def garland():
    """A leafy bough across the top with marigold strands hanging at different lengths, tipped with tassels."""
    cv = Canvas(360, 250)
    for x, L in ((40, 160), (96, 112), (180, 196), (264, 112), (320, 160)):
        stroke(cv, np.c_[np.full(60, x), np.linspace(22, 22 + L, 60)], .5, .5, C["gold"], .5)
        y, r, k = 31.0, 7.2, 0
        while y < 22 + L - 5:
            marigold(cv, x + .7 * np.sin(y * .23), y, r, k)
            if k % 4 == 3:
                leaf(cv, x + 2, y + r * .9, .5, 7, 2.2, seed=k)
                leaf(cv, x - 2, y + r * .9, np.pi - .5, 7, 2.2, seed=k + 1)
            y += r * 1.62
            r = max(4.0, r * .955)
            k += 1
        beads(cv, [(x, 24 + L)], 2.3, C["scarlet"], 1)
        for dx in (-1.6, 0, 1.6):
            stroke(cv, np.c_[np.linspace(x, x + dx * 1.6, 20), np.linspace(26 + L, 38 + L, 20)], .7, .55, C["scarlet_d"], .7)
    bough = bezier((-4, 14), (100, 30), (260, 30), (364, 14), 600)
    stroke(cv, bough, 1.6, 1.6, C["stem"], 1.4)
    pts, angs = along(bough, 9.5, 3)
    for i, ((x, y), a) in enumerate(zip(pts, angs)):
        up = i % 2 == 0
        leaf(cv, x, y, a + (-1.0 if up else 1.0) + .2 * np.sin(i * 1.3), 12, 3.4, seed=i)
    pts, _ = along(bough, 30, 16)
    for i, (x, y) in enumerate(pts):
        marigold(cv, x, y + 1, 6.6, i + 1)
    cv.render("garland")


def vine(side):
    """A climbing vine for the edge of a section: fishbone leaves, small marigolds and scarlet buds."""
    cv = Canvas(70, 440)
    stem = bezier((40, -4), (10, 130), (60, 290), (28, 444), 900)
    stroke(cv, stem, 1.5, 1.2, C["stem"], 1.3)
    pts, angs = along(stem, 24, 10)
    for i, ((x, y), a) in enumerate(zip(pts, angs)):
        right = i % 2 == 0
        la = a + (-1.0 if right else 1.0)
        leaf(cv, x, y, la, 15, 4.2, seed=i)
        if i % 3 == 1:
            marigold(cv, x + 10 * np.cos(la - .6 * (1 if right else -1)), y + 10 * np.sin(la) - 4, 5.6, i)
        elif i % 3 == 2:
            stroke(cv, np.c_[np.linspace(x, x + (8 if right else -8), 20), np.linspace(y, y - 6, 20)], .6, .5, C["stem"], .6)
            beads(cv, [(x + (8 if right else -8), y - 7)], 2.3, C["scarlet"], .9)
    if side == "r":
        cv.flip()
    cv.render(f"vine-{side}")


def flipv(cv):
    for arr in (cv.col, cv.hgt, cv.a, cv.gloss):
        arr[:] = arr[::-1]


def butterfly(side):
    """A Bagurumba butterfly seen from above, a little turned: scarlet jwmgra wings with a gold agor border,
    yellow inner panels with tiny bead butis, an emerald body and gold antennae. side l faces right."""
    cv = Canvas(96, 80)
    cx, cy = 46, 44
    # lower wings first (they sit under the upper ones)
    for a, L, w in ((np.deg2rad(128), 26, 11), (np.deg2rad(62), 23, 10)):
        feather(cv, cx, cy + 2, a, L, w, C["scarlet_d"], h=1.8, stitch_dir=a, seed=3, rounded=True)
        feather(cv, cx + 2 * np.cos(a), cy + 2 + 2 * np.sin(a), a, L * .62, w * .55, C["yellow"], h=1.0, stitch_dir=a + 1.2, seed=4, rounded=True)
    # upper wings: large, held out like the jwmgra in the dance
    for a, L, w in ((np.deg2rad(212), 40, 16), (np.deg2rad(-32), 36, 15)):
        feather(cv, cx, cy - 2, a, L, w, C["scarlet"], h=2.4, stitch_dir=a, seed=5, rounded=True)
        feather(cv, cx + 3 * np.cos(a), cy - 2 + 3 * np.sin(a), a, L * .66, w * .56, C["yellow"], h=1.3, stitch_dir=a + 1.3, seed=6, rounded=True)
        # gold agor border: beads following the wing's outer edge
        for t in np.linspace(.18, .96, 12):
            half = w * np.sin(np.pi / 2 * min(t / .62, 1)) * np.sqrt(max(0.0, 1 - max(0.0, (t - .62) / .38) ** 2)) * .9
            for sgn in (-1, 1):
                ux, vy = L * t, sgn * half
                beads(cv, [(cx + ux * np.cos(a) - vy * np.sin(a), cy - 2 + ux * np.sin(a) + vy * np.cos(a))], .9, C["gold"], 1.3)
        # a small scarlet buti on the yellow panel
        beads(cv, [(cx + L * .42 * np.cos(a), cy - 2 + L * .42 * np.sin(a))], 1.5, C["scarlet_d"], .8)
    # body, head and antennae
    stroke(cv, bezier((cx - 2, cy + 16), (cx - 1, cy + 6), (cx, cy - 4), (cx + 1, cy - 12), 80), 2.0, 3.0, C["emerald_d"], 2.8)
    beads(cv, [(cx + 1.5, cy - 15)], 3.0, C["emerald"], .8)
    for ex, ey in ((cx - 8, cy - 31), (cx + 10, cy - 30)):
        stroke(cv, bezier((cx + 1, cy - 17), (cx + 1, cy - 24), ((cx + ex) / 2, ey + 2), (ex, ey), 40), .45, .4, C["gold"], .6)
        beads(cv, [(ex, ey)], 1.5, C["gold"], 1.3)
    if side == "r":
        cv.flip()
    cv.render(f"butterfly-{side}")


def sprig(corner):
    """A corner sprig to sit over a card's corner: a curved stem, fishbone leaves, two marigolds and a bud.
    corner tl/tr/bl/br says which corner it dresses."""
    cv = Canvas(96, 96)
    stem = bezier((8, 88), (14, 50), (44, 18), (88, 8), 300)
    stroke(cv, stem, 1.4, 1.0, C["stem"], 1.2)
    pts, angs = along(stem, 13, 8)
    for i, ((x, y), a) in enumerate(zip(pts, angs)):
        leaf(cv, x, y, a + (-.95 if i % 2 else .95), 13 - i * .6, 3.8, seed=i)
    marigold(cv, 26, 50, 8.2, 0)
    marigold(cv, 52, 24, 6.6, 1)
    stroke(cv, bezier((70, 13), (74, 16), (77, 20), (78, 25), 30), .6, .5, C["stem"], .6)
    beads(cv, [(78, 27)], 2.4, C["scarlet"], .9)
    beads(cv, [(14, 72), (36, 34)], 1.2, C["gold"], 1.2)
    if corner in ("tr", "br"):
        cv.flip()
    if corner in ("bl", "br"):
        flipv(cv)
    cv.render(f"sprig-{corner}")


def swag():
    """A short marigold swag for the top of an arch: a drape of marigolds and leaves, a strand at each end."""
    cv = Canvas(230, 80)
    drape = bezier((10, 10), (60, 52), (170, 52), (220, 10), 500)
    stroke(cv, drape, 1.0, 1.0, C["gold"], .8)
    pts, angs = along(drape, 9, 4)
    for i, ((x, y), a) in enumerate(zip(pts, angs)):
        leaf(cv, x, y, a + (-1.1 if i % 2 else 1.1), 9, 2.8, seed=i)
    pts, _ = along(drape, 12.5, 2)
    for i, (x, y) in enumerate(pts):
        r = 5.2 + 1.6 * np.sin(np.pi * i / max(len(pts) - 1, 1))
        marigold(cv, x, y, r, i)
    for x in (10, 220):
        for k, y in enumerate((18, 27, 35)):
            marigold(cv, x, y, 4.6 - k * .4, k + 2)
        beads(cv, [(x, 42)], 2.0, C["scarlet"], 1)
        stroke(cv, np.c_[np.linspace(x, x, 12), np.linspace(44, 52, 12)], .8, .5, C["scarlet_d"], .7)
    cv.render("swag")


def divider():
    """A raised divider: a marigold with a pair of leaves each side and gold beads tapering away."""
    cv = Canvas(220, 40)
    cx, cy = 110, 20
    for sgn in (-1, 1):
        for k in range(9):
            x = cx + sgn * (26 + k * 8.5)
            beads(cv, [(x, cy)], 2.0 - k * .17, C["gold"] if k % 2 == 0 else C["pearl"], 1.3)
        a = 0 if sgn > 0 else np.pi
        leaf(cv, cx + sgn * 7, cy - 1, a - .38 * sgn, 17, 4.4, seed=1)
        leaf(cv, cx + sgn * 7, cy + 1, a + .38 * sgn, 15, 4.0, seed=2)
    marigold(cv, cx, cy, 9.0, 0)
    cv.render("divider")


def bloom():
    """One marigold head, for the timeline."""
    cv = Canvas(30, 30)
    leaf(cv, 15, 17, np.deg2rad(150), 13, 3.4, seed=1)
    leaf(cv, 15, 17, np.deg2rad(30), 12, 3.2, seed=2)
    marigold(cv, 15, 14, 8.0, 0)
    cv.render("bloom")


PIECES = dict(
    peacocks=peacocks, garland=garland, vine=lambda: (vine("l"), vine("r")),
    butterfly=lambda: (butterfly("l"), butterfly("r")),
    sprig=lambda: [sprig(c) for c in ("tl", "tr", "bl", "br")],
    swag=swag, divider=divider, bloom=bloom,
)

if __name__ == "__main__":
    import sys
    for name in (sys.argv[1:] or PIECES):
        PIECES[name]()
