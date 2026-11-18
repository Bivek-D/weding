"""Bodo-themed art for the static FigCraft pass: woven, lit from the top left (references/reference-spec.md).

Everything is rendered at 2x for a 393 x 852 phone and written to design/art/:
  linen.png          warm ivory linen tile (page background)
  band-h.png         aronai strip, horizontal (section divider, valance header)
  band-v.png         aronai strip, vertical (curtain border, page side edges)
  door-left.png / door-right.png   woven green doors with embossed agor lattice and mustard borders
  plaque.png         bamboo-framed ivory plaque (text is added in FigCraft)
  curtains.png       mustard dokhona curtains tied back with aronai knots (transparent middle)
  valance.png        aronai header + four swags flush with the top
  altar.png          Bathou altar cut from references/hero-bathou-mockup.png
  lamp.png           brass saki lamp with a lit flame
  butterfly.png      small woven-wing butterfly (Bagurumba)

Run with the scratch venv (numpy, pillow, scipy):  python art_bodo.py
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(PRJ, "design", "art")
os.makedirs(OUT, exist_ok=True)

S = 2                       # render scale
W, H = 393 * S, 852 * S     # one phone screen

C = {  # Bodo bold palette (brief.md); linear-ish sRGB 0..1
    "mustard": "#D69E1E", "mustard_d": "#A8740F", "green": "#2F5B3A", "green_d": "#1F3F28",
    "green_l": "#4E7A55", "maroon": "#7B2232", "ivory": "#F7ECD6", "black": "#231A14",
    "bamboo": "#C9A063", "brass": "#B98A3A",
}


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def save(name, img, alpha=None):
    img = np.clip(img, 0, 1)
    if alpha is not None:
        img = np.dstack([img, np.clip(alpha, 0, 1)])
        Image.fromarray((img * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, name))
    else:
        Image.fromarray((img * 255).astype(np.uint8), "RGB").save(os.path.join(OUT, name))
    print("wrote", name, img.shape[1], "x", img.shape[0])


def light(height, k=1.0, spec=.25, amb=.55):
    """Shade a height map with one light from the top left. Returns a multiplier and a highlight."""
    gy, gx = np.gradient(height)
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(height)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    L = np.array([-1.0, -1.0, 1.5])
    L /= np.linalg.norm(L)
    d = (nx * L[0] + ny * L[1] + nz * L[2]) / n
    flat = L[2]
    mul = amb + (1 - amb) * d / flat
    hl = np.clip(d - flat, 0, None) ** 1.5 * spec * 6
    return mul, hl


def weave(h, w, p=3):
    """Basket-weave thread bumps (0..1)."""
    y, x = np.mgrid[0:h, 0:w]
    chk = ((x // p + y // p) % 2).astype(float)
    return chk * np.abs(np.sin(np.pi * (x + .5) / p)) + (1 - chk) * np.abs(np.sin(np.pi * (y + .5) / p))


# ------------------------------------------------------------------ aronai band
def band(length, width, cell=6):
    """A horizontal aronai strip `length` x `width` px: mustard ground, maroon edge stripes, green teeth,
    stepped hollow diamonds (pigeon-eye agor) in the middle. Returns (rgb, height)."""
    gy, gx = np.mgrid[0:width, 0:length] // cell
    rows = width // cell
    idx = np.zeros((width, length), int)          # 0 ground, 1 maroon, 2 green, 3 ivory
    edge = (gy == 0) | (gy == rows - 1)
    idx[edge] = 1
    # green teeth pointing inward from each edge stripe
    t = 3
    ph = gx % (2 * t)
    tooth = np.abs(ph - t)
    idx[(gy >= 1) & (gy <= t - 1) & (gy - 1 < t - 1 - tooth + 1) & ~edge] = 2
    idx[(gy <= rows - 2) & (gy >= rows - t) & (rows - 2 - gy < t - 1 - tooth + 1) & ~edge] = 2
    # centre diamonds
    mid = (rows - 1) / 2
    period = max(rows, 10)
    cx = (gx % period) - period // 2
    dist = np.abs(cx) + np.abs(gy - mid)
    r = max(2, int(mid) - t)
    idx[(dist <= r) & (dist >= r - .5)] = 1
    idx[(dist == r - 1.5) | (dist == r - 1)] = 3
    idx[dist <= .5] = 1
    # small ivory crosses between diamonds
    cross = (np.abs(np.abs(cx) - period // 2) + np.abs(gy - mid) <= .5)
    idx[cross & (idx == 0)] = 3
    col = np.zeros((width, length, 3))
    for i, name in enumerate(["mustard", "maroon", "green", "ivory"]):
        col[idx == i] = rgb(C[name])
    hgt = weave(width, length, 3) * .5 + (idx > 0) * .7
    hgt = nd.gaussian_filter(hgt, .8)
    return col, hgt


def lit(col, hgt, k=1.4, spec=.25):
    mul, hl = light(hgt, k, spec)
    return col * mul[..., None] + hl[..., None]


# ------------------------------------------------------------------ linen
def linen(size=512):
    rng = np.random.default_rng(3)
    y, x = np.mgrid[0:size, 0:size]
    fx = nd.gaussian_filter(rng.normal(size=(size, size)), (0, 6), mode="wrap")
    fy = nd.gaussian_filter(rng.normal(size=(size, size)), (6, 0), mode="wrap")
    h = fx * .9 + fy * .9 + weave(size, size, 2) * .08
    mul, _ = light(h, 1.2, 0, amb=.8)
    blot = nd.gaussian_filter(rng.normal(size=(size, size)), 40, mode="wrap")
    blot = blot / np.abs(blot).max() * .025
    col = rgb("#F6EAD2")[None, None] * (mul + blot)[..., None]
    return col


# ------------------------------------------------------------------ doors
def doors():
    col = np.zeros((H, W, 3)) + rgb(C["green"])
    hgt = weave(H, W, 3) * .35
    # tone-on-tone embossed agor lattice: stepped diamonds on a diagonal grid
    cell = 8
    gy, gx = np.mgrid[0:H, 0:W] // cell
    P = 14
    u, v = (gx % P) - P // 2, (gy % (P * 2)) - P
    d = np.abs(u) * 2 + np.abs(v)
    ring = (np.abs(d - 10) <= 1)
    eye = d <= 2
    vine = (np.abs(u) == 0) & (np.abs(v) > 12)
    relief = ring | eye | vine
    hgt += relief * 1.2
    col[relief] = rgb(C["green_l"])
    # mustard woven borders: outer edges and both sides of the seam
    bw = 30 * S // 2
    bcol, bh = band(H, bw)
    bcol, bh = np.transpose(bcol, (1, 0, 2)), bh.T
    for x0 in (0, W // 2 - bw, W // 2, W - bw):
        col[:, x0:x0 + bw] = bcol
        hgt[:, x0:x0 + bw] = bh * 1.3 + .5
    # horizontal bands near top and bottom
    hb, hh = band(W, bw)
    for y0 in (int(H * .06), int(H * .94) - bw):
        col[y0:y0 + bw] = hb
        hgt[y0:y0 + bw] = hh * 1.3 + .5
    hgt = nd.gaussian_filter(hgt, 1.1)
    out = lit(col, hgt, 2.2, .35)
    # soft vignette: darker toward the hinges, light pooling top left
    yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    out *= (1 - .25 * ((xx - .5) * 2) ** 4)[..., None] * (1.06 - .12 * yy)[..., None]
    save("door-left.png", out[:, :W // 2])
    save("door-right.png", out[:, W // 2:])


# ------------------------------------------------------------------ plaque
def plaque(w=150 * S, h=170 * S):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = w / 2, h / 2
    # cushion shape: superellipse with notched corners
    nx, ny = np.abs(x - cx) / (w / 2 - 4), np.abs(y - cy) / (h / 2 - 4)
    se = nx ** 4 + ny ** 4
    notch = ((nx - 1) ** 2 + (ny - 1) ** 2) < .09
    inside = (se < 1) & ~notch
    dist = nd.distance_transform_edt(inside)
    rim = (dist < 16) & inside
    col = np.zeros((h, w, 3)) + rgb(C["ivory"])
    # bamboo rim: tan with node rings along the perimeter
    ang = np.arctan2(y - cy, x - cx)
    nodes = (np.abs(((ang / (2 * np.pi)) * 28) % 1 - .5) < .05)
    col[rim] = rgb(C["bamboo"])
    col[rim & nodes] = rgb("#9C7640")
    hgt = np.clip(dist, 0, 10) / 10 * 1.0
    hgt += rim * np.sin(np.clip(dist, 0, 16) / 16 * np.pi) * 2.2
    hgt -= (rim & nodes) * .6
    # inner fine line and agor emblem (stepped diamond) at the top
    inner = (dist > 22) & (dist < 24)
    col[inner] = rgb(C["mustard_d"])
    g = 5
    ex, ey = (x - cx) // g, (y - (cy - h * .2)) // g
    dd = np.abs(ex) + np.abs(ey)
    emb = ((dd == 4) | (dd <= 1)) & inside
    col[emb & (dd == 4)] = rgb(C["maroon"])
    col[emb & (dd <= 1)] = rgb(C["green"])
    hgt += emb * .8 - inner * .4
    hgt = nd.gaussian_filter(hgt, 1.2)
    out = lit(col, hgt, 3.0, .4)
    alpha = nd.gaussian_filter(inside.astype(float), .8)
    save("plaque.png", out, alpha)


# ------------------------------------------------------------------ curtains (open, tied back)
def curtains():
    yt = int(H * .60)
    e0, et, eb = .30 * W, .095 * W, .19 * W
    y = np.arange(H)
    up = np.clip(y / yt, 0, 1)
    dn = np.clip((y - yt) / (H - yt), 0, 1)
    e = np.where(y < yt, et + (e0 - et) * np.cos(np.pi / 2 * up) ** 1.3, et + (eb - et) * dn ** .75)
    X = np.arange(W)[None, :].repeat(H, 0)
    E = e[:, None]
    inside = X < E
    u = np.clip(X / E, 0, 1)
    folds = 8
    squeeze = 1 + 2.2 * np.exp(-((y - yt) / (H * .12)) ** 2)[:, None]
    hgt = np.cos(2 * np.pi * folds * u ** .9) * 4 * (1 / squeeze + .3) * (W / 400)
    hgt += np.sin(2 * np.pi * 3 * u + y[:, None] / 300) * 1.5
    hgt = nd.gaussian_filter(hgt, 3)
    col = np.zeros((H, W, 3)) + rgb(C["mustard"])
    # inner-edge aronai border, following the edge
    bw = 40
    bcol, bh = band(H, bw, cell=4)
    bcol, bh = np.transpose(bcol, (1, 0, 2))[:, ::-1], bh.T[:, ::-1]
    dx = (E - X).astype(int)
    on = inside & (dx < bw)
    rows = np.nonzero(on)
    col[rows] = bcol[rows[0], np.clip(bw - 1 - dx[rows], 0, bw - 1)]
    hgt[rows] += bh[rows[0], np.clip(bw - 1 - dx[rows], 0, bw - 1)] * 2
    # ambient occlusion in the fold valleys and under the valance
    ao = 1 - .18 * (.5 - .5 * np.cos(2 * np.pi * folds * u ** .9))
    ao *= (1 - .25 * np.exp(-y / (H * .08)))[:, None]
    mul, hl = light(hgt, .6, .1, amb=.66)
    out = col * (mul * ao)[..., None] + hl[..., None]
    # aronai tie-back knot: a strip across the drape at yt
    th = 36
    kb, kh = band(W, th, cell=4)
    sag = (np.sin(np.pi * np.clip(X[0] / et, 0, 1)) * 10).astype(int)
    for xx in range(int(et) + 8):
        y0 = yt - th // 2 + sag[min(xx, W - 1)]
        seg = kb[:, xx]
        sh = np.linspace(1.15, .8, th)[:, None]
        out[y0:y0 + th, xx] = seg * sh
        inside[y0:y0 + th, xx] = True
    # hanging tails of the knot
    tw = 24
    tb, _ = band(int(H * .12), tw, cell=3)
    tb = np.transpose(tb, (1, 0, 2))
    for k, off in enumerate((-6, 10)):
        x0 = int(et) - 4 + off
        y0 = yt + th // 2 - 4
        hh = tb.shape[0] - k * 30
        out[y0:y0 + hh, x0:x0 + tw] = tb[:hh] * np.linspace(1.05, .85, tw)[None, :, None]
        inside[y0:y0 + hh, x0:x0 + tw] = True
    alpha = nd.gaussian_filter(inside.astype(float), .7)
    full = out.copy()
    full[:, W // 2:] = out[:, :W - W // 2][:, ::-1]
    fa = alpha.copy()
    fa[:, W // 2:] = alpha[:, :W - W // 2][:, ::-1]
    # mirrored right curtain: re-shade so it is still lit from the left (darken the flipped highlights)
    full[:, W // 2:] *= .93
    save("curtains.png", full, fa)


# ------------------------------------------------------------------ valance
def valance(hh=190 * S // 2 * 2):
    hh = int(H * .2)
    head = 26 * S
    col = np.zeros((hh, W, 3)) + rgb(C["mustard"])
    alpha = np.zeros((hh, W))
    hgt = np.zeros((hh, W))
    n = 4
    sw = W / n
    y, x = np.mgrid[0:hh, 0:W].astype(float)
    t = (x % sw) / sw
    depth = (hh - head - 30) * np.sin(np.pi * t) + 18
    s = (y - head) / depth
    cloth = (s >= -0.2) & (s <= 1)
    alpha[cloth] = 1
    hgt += np.cos(2 * np.pi * 4.2 * np.clip(s, 0, 1)) * 2.5 * np.sin(np.pi * t)
    ao = 1 - .2 * (.5 - .5 * np.cos(2 * np.pi * 4.2 * np.clip(s, 0, 1)))
    # maroon border along the lower edge, green teeth hanging below
    lower = (s > .86) & cloth
    col[lower] = rgb(C["maroon"])
    hgt += lower * 3
    teeth = (s > 1) & (s < 1 + .14) & ((np.abs(((x % 14) - 7)) / 7) < 1 - (s - 1) / .14)
    col[teeth] = rgb(C["green"])
    alpha[teeth] = 1
    # header: horizontal aronai band flush with the top
    hb, hbh = band(W, head)
    col[:head] = hb
    hgt[:head] = hbh * 4
    alpha[:head] = 1
    ao[:head] = 1
    hgt = nd.gaussian_filter(hgt, 2)
    mul, hl = light(hgt, .7, .1, amb=.66)
    out = col * (mul * ao)[..., None] + hl[..., None]
    save("valance.png", out, nd.gaussian_filter(alpha, .6))


# ------------------------------------------------------------------ strips
def strips():
    bc, bh = band(W, 22 * S)
    save("band-h.png", lit(bc, bh, 2.2, .3))
    vc, vh = band(H, 14 * S)
    save("band-v.png", lit(np.transpose(vc, (1, 0, 2)), vh.T, 2.2, .3))


# ------------------------------------------------------------------ altar cutout
def altar():
    im = np.asarray(Image.open(os.path.join(PRJ, "references", "hero-bathou-mockup.png")).convert("RGB")).astype(float)
    sx = im.shape[1] / 852
    box = [int(v * sx) for v in (130, 836, 726, 1690)]
    a = im[box[1]:box[3], box[0]:box[2]] / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    pink = ((b - g > .025) & (r > g) & (r > .7)) | ((b - g > .008) & (r - g > .03) & (r > .82))
    bg = nd.binary_opening(pink, iterations=1)
    lab, n = nd.label(bg)
    sizes = nd.sum(bg, lab, range(1, n + 1))
    big = [i + 1 for i, sz in enumerate(sizes) if sz > 40]
    mask = ~np.isin(lab, big)
    mask = nd.binary_closing(mask, iterations=2)
    mask = nd.binary_fill_holes(mask) & mask | nd.binary_erosion(mask, iterations=1)
    alpha = nd.gaussian_filter(mask.astype(float), .9)
    # warm the stray pink fringe
    fringe = (alpha < .99) & (alpha > 0)
    a[fringe] = a[fringe] * [1, .97, .9]
    save("altar.png", a, alpha)


# ------------------------------------------------------------------ lamp + butterfly
def lamp(w=44 * S, h=60 * S):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    cx = w / 2
    bowl = (((x - cx) / (w * .42)) ** 2 + ((y - h * .78) / (h * .16)) ** 2 < 1) & (y > h * .74)
    rimm = (((x - cx) / (w * .44)) ** 2 + ((y - h * .75) / (h * .05)) ** 2) < 1
    body = bowl | rimm
    hgt = nd.distance_transform_edt(body)
    hgt = np.sqrt(np.clip(hgt, 0, 12) / 12)
    col = np.zeros((h, w, 3)) + rgb(C["brass"])
    mul, hl = light(hgt * 8, 1.0, .6, amb=.45)
    out = col * mul[..., None] + hl[..., None]
    # flame teardrop + glow
    fy = (y - h * .52) / (h * .2)
    fw = np.clip(1 - fy, 0, 1) ** .6 * np.clip(fy + 1, 0, 1) ** .4 * w * .13
    flame = (np.abs(x - cx) < fw) & (fy > -1) & (fy < 1)
    core = (np.abs(x - cx) < fw * .45) & (fy > 0) & (fy < .9)
    glow = np.exp(-(((x - cx) / (w * .35)) ** 2 + ((y - h * .5) / (h * .3)) ** 2))
    out = np.where(flame[..., None], rgb("#F5B33C"), out)
    out = np.where(core[..., None], rgb("#FFF0C2"), out)
    alpha = np.maximum(body.astype(float), flame * 1.0)
    glow_rgb = rgb("#FFD27A")
    ga = glow * .55
    out = np.where((alpha > 0)[..., None], out, glow_rgb)
    alpha = np.maximum(alpha, ga)
    save("lamp.png", out, nd.gaussian_filter(alpha, .6))


def butterfly(w=40 * S, h=30 * S):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = w / 2, h / 2
    dx = np.abs(x - cx)
    up = ((dx - w * .2) / (w * .22)) ** 2 + ((y - cy * .75) / (h * .33)) ** 2 < 1
    lo = ((dx - w * .15) / (w * .15)) ** 2 + ((y - cy * 1.35) / (h * .22)) ** 2 < 1
    wings = (up | lo) & (dx > 1.5)
    bodym = (dx < 2.2) & (y > h * .25) & (y < h * .85)
    col = np.zeros((h, w, 3)) + rgb(C["maroon"])
    edge = wings & ~nd.binary_erosion(wings, iterations=3)
    col[edge] = rgb(C["mustard"])
    dots = ((((dx - w * .22) / 3.5) ** 2 + ((y - cy * .7) / 3.5) ** 2) < 1)
    col[dots & wings] = rgb(C["ivory"])
    col[bodym] = rgb(C["black"])
    hgt = nd.gaussian_filter(nd.distance_transform_edt(wings | bodym).clip(0, 6), 1)
    out = lit(col, hgt, 1.0, .3)
    save("butterfly.png", out, nd.gaussian_filter((wings | bodym).astype(float), .6))


if __name__ == "__main__":
    save("linen.png", linen())
    strips()
    doors()
    plaque()
    curtains()
    valance()
    altar()
    lamp()
    butterfly()
