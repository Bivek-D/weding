"""The Bathou pandal stage, rendered in Blender (Cycles, GPU).

Run:  blender.cmd -b -P render_pandal.py -- altar      (parts: altar lamp banana bush; none = all)
Writes out/<part>.png (2x the CSS size, transparent, with soft floor shadows); publish.py turns them into
the site's WebP files with the same names and sizes as before.

Sizes and framing follow the three.js spec in design/render3d/scene.js (cm, y up), converted with P().
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                      # noqa: E402
from mathutils import Euler, Vector     # noqa: E402

import studio as S                      # noqa: E402
from studio import P                    # noqa: E402

rng = np.random.default_rng(5)


def catmull(pts, n=60):
    """A smooth curve through the points (Catmull-Rom), n samples."""
    p = np.array(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    segs = len(p) - 3
    for s in range(segs):
        p0, p1, p2, p3 = p[s:s + 4]
        for t in np.linspace(0, 1, max(2, n // segs), endpoint=(s == segs - 1)):
            t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def marigold_set(mesh, mat, items):
    """items: [(three-spec pos (cm), radius cm)]"""
    src = S.link(S.bpy.data.objects.new("marigold-src", mesh))
    src.data.materials.append(mat)
    src.hide_render = True
    for pos, r in items:
        S.instance(src, P(*pos), rot=Euler((rng.uniform(-.5, .5), rng.uniform(-.5, .5), rng.uniform(0, 6.28))), scale=r * .01)


# ------------------------------------------------------------------ parts of the altar
def sijou(mat_stem, mat_leaf, y0=2):
    """Euphorbia neriifolia: a ribbed five-angled main stem and candelabra branches, each crowned with a
    rosette of spoon-shaped leaves."""
    leaf = S.leaf_mesh(L=1, W=.42, cup=.22, shape="obovate", tip_bend=.05)
    leaf_src = S.link(S.bpy.data.objects.new("sijou-leaf", leaf))
    leaf_src.data.materials.append(mat_leaf)
    leaf_src.hide_render = True
    rib = lambda th: 1 + .16 * math.cos(5 * th)      # noqa: E731

    def stem(pts_cm, r0, r1, name):
        pts = catmull([(x, y + y0, z) for x, y, z in pts_cm], 50)
        bl = [P(*p) for p in pts]
        n = len(bl)
        radii = [(r0 + (r1 - r0) * i / (n - 1)) * .01 for i in range(n)]
        S.tube(name, bl, radii, mat_stem, sides=30, profile=rib)
        tip = bl[-1]
        k = 7 + int(rng.integers(0, 3))
        for j in range(k):
            a = j / k * 2 * math.pi + rng.uniform(-.2, .2)
            tilt = math.radians(rng.uniform(35, 60))
            L = rng.uniform(.045, .06)
            # the leaf's +x points up and out
            rot = Euler((0, -math.pi / 2 + tilt, a), "XYZ")
            S.instance(leaf_src, tip + Vector((0, 0, r1 * .004)), rot=rot, scale=(L, L, L))
    stem([(0, 0, 0), (.5, 25, 0), (0, 50, 0), (.4, 68, 0)], 3.2, 1.6, "sijou-main")
    branches = [(-1, 18, -.6), (1, 20, .4), (-.8, 27, .8), (.9, 29, -.7), (-.5, 35, .3), (.6, 37, .5), (-1.1, 23, .2), (1.1, 25, -.2)]
    for i, (dx, yb, dz) in enumerate(branches):
        out = 7 + rng.uniform(0, 6)
        top = 50 + rng.uniform(0, 14) - (4 if yb > 30 else 0)
        stem([(0, yb, 0), (dx * out * .6, yb + 4, dz * out * .6), (dx * out, yb + 12, dz * out), (dx * out * 1.05, top, dz * out * 1.05)],
             2.0, 1.15, f"sijou-b{i}")


def fence(mat_pole, mat_band, R=24):
    """The round bamboo fence: 18 pairs of poles tied with five bands (birth, pain, death, marriage, peace)."""
    for i in range(18):
        for off in (-.055, .055):
            a = i / 18 * 2 * math.pi + off
            x, z = R * math.sin(a), R * math.cos(a)
            h = 34 + rng.uniform(-1, 1)
            S.bamboo_pole(f"pole{i}", P(x, 0, z), P(x, h, z), .0085, mat_pole)
    for k in range(5):
        y = 5 + k * 6.3
        pts = [P((R + .6) * math.sin(a), y, (R + .6) * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 181)]
        S.tube(f"band{k}", pts, [.0042] * len(pts), mat_band, sides=10, profile=lambda th: 1 + .5 * abs(math.sin(th)), cap=False)


def hem_fringe(ob, nx, ny, mat, length=.022, groups=9):
    """A handloom warp fringe along the bottom row of a drop_cloth: twisted groups of threads, each knotted
    just under the hem."""
    vs = [ob.matrix_world @ ob.data.vertices[(ny - 1) * nx + i].co for i in range(nx)]
    for g in range(groups):
        f = (g + .5) / groups * (nx - 1)
        i0 = int(f)
        base = vs[i0].lerp(vs[min(i0 + 1, nx - 1)], f - i0)
        kn = S.lathe(f"{ob.name}-k{g}", [(0, -.0016), (.0017, -.0008), (.0018, .0006), (0, .0016)], mat, seg=10)
        kn.location = base + Vector((0, 0, -.003))
        Lg = length * (1 + rng.uniform(-.12, .12))
        sway = Vector((rng.uniform(-1, 1) * Lg * .1, rng.uniform(-1, 1) * Lg * .06, 0))
        for th in range(3):
            o = Vector(((th - 1) * .0007, 0, 0))
            pts = [base + o * (1 - u * .6) + Vector((0, 0, -Lg * u)) + sway * u * u for u in np.linspace(0, 1, 8)]
            S.tube(f"{ob.name}-f{g}-{th}", pts, [.0006] * 8, mat, sides=6)


def drop_cloth(name, top_cm, length_cm, width_cm, mat, side, uv_full=False):
    """A cloth end falling straight down from the bar, in soft vertical folds that open toward the hem.
    uv_full: u runs 0 (top) .. 1 (hem) for a whole-cloth texture (mat_aronai) instead of repeating."""
    nx, ny = 26, 60
    verts, faces, uvs = [], [], []
    for j in range(ny):
        t = j / (ny - 1)
        for i in range(nx):
            s = i / (nx - 1)
            x = (s - .5) * width_cm * (1 + .18 * t)
            fold = (1.1 + 1.6 * t) * math.sin(s * math.pi * 5 + .6) * (.4 + .6 * t)
            verts.append(P(top_cm[0] + x * .95, top_cm[1] - t * length_cm, top_cm[2] + fold + 1.5 * t))
            uvs.append((t if uv_full else t * length_cm / 40, s))
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    ob = S.mesh_obj(name, verts, faces, uvs=uvs, mat=mat)
    so = ob.modifiers.new("thick", "SOLIDIFY"); so.thickness = .0015
    su = ob.modifiers.new("smooth", "SUBSURF"); su.levels = su.render_levels = 1
    return ob


def woven_mat(mat):
    """The woven mat on the floor, lying slightly uneven."""
    nx, ny = 90, 52
    W, D = 110, 62
    verts, faces, uvs = [], [], []
    for j in range(ny):
        for i in range(nx):
            u, v = i / (nx - 1), j / (ny - 1)
            x, z = (u - .5) * W, (v - .5) * D + 14
            y = .25 + .18 * math.sin(u * 9 + v * 4) * math.sin(v * 7) + .3 * (u < .02 or u > .98)
            verts.append(P(x, y, z))
            uvs.append((u * 2.2, v))
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    ob = S.mesh_obj("mat", verts, faces, uvs=uvs, mat=mat)
    so = ob.modifiers.new("thick", "SOLIDIFY"); so.thickness = .003
    return ob


def altar():
    S.reset(samples=320)
    m_bamboo = S.mat_bamboo()
    m_band = S.mat_bamboo("#B98A4E")
    m_brass = S.mat_brass()
    m_cloth = S.mat_cloth("dokhona")
    m_matcloth = S.mat_cloth("mat", ground="#E8781A", border="#1D6B3A")
    m_stem = S.mat_succulent()
    m_leaf = S.mat_plain("sijou-leaf", "#4F8A2A", rough=.45, subsurface=.15)
    m_soil = S.mat_plain("soil", "#4A3322", rough=1)
    m_mari = S.mat_marigold()
    mari = S.marigold_mesh()

    S.shadow_catcher()
    woven_mat(m_matcloth)
    S.lathe("soil", [(0, .003), (.23, .003), (.235, .025), (.22, .03), (0, .032)], m_soil)
    fence(m_bamboo, m_band)
    sijou(m_stem, m_leaf)

    # the bamboo frame behind
    for x in (-44, 44):
        S.bamboo_pole(f"post{x}", P(x, 0, -14), P(x, 97, -14), .013, m_bamboo)
    S.bamboo_pole("bar", P(-49, 94, -14), P(49, 94, -14), .012, m_bamboo)
    bar_col = S.bamboo_pole("bar-col", P(-49, 94, -14), P(49, 94, -14), .013, m_bamboo)
    bar_col.hide_render = True

    # aronai festooned between the posts and the centre (each a whole cloth, u 0..1 along it); an aronai
    # end falling at each post, its end panel and warp fringe at the bottom
    cloths = []
    for k, (a, b) in enumerate(((-45, 0), (0, 45))):
        m_ar = S.mat_aronai(f"aronai-swag{k}", 620, 130, ppm=5, seed=10 + k)
        ob, f = S.cloth_strip(f"swag{a}", P(a, 92.6, -12.4), P(b, 92.6, -12.4), length=.62, width=.13, mat=m_ar,
                              nx=120, ny=22, gather=.22, frames=90, uv_repeat=.4 / .62, bend=.4)
        cloths.append((ob, f))
    fringe_m = S.mat_plain("aronai-fringe", "#A3121B", rough=.7, sheen=.5)
    for k, x in enumerate((-44, 44)):
        # the texture covers the hanging half of a 72 cm cloth: plain body at the bar, the end panel below
        m_end = S.mat_aronai(f"aronai-end{k}", 720, 110, ppm=5, seed=20 + k, u0=.5, u1=1.0)
        ob = drop_cloth(f"drop{x}", (x + (1.8 if x > 0 else -1.8), 93, -12), 36, 11, m_end, x, uv_full=True)
        hem_fringe(ob, 26, 60, fringe_m)

    # a dokhona tied round the front of the fence, resting on it
    R = 24
    col = S.lathe("fence-col", [(0, .0), (.25, 0), (.25, .345), (0, .345)], None)
    col.hide_render = True
    a0, a1 = -1.15, 1.15
    A, B = P(R * 1.05 * math.sin(a0), 27.5, R * 1.05 * math.cos(a0)), P(R * 1.05 * math.sin(a1), 27.5, R * 1.05 * math.cos(a1))
    m_front = S.mat_aronai("aronai-fence", 620, 100, ppm=6, seed=31)
    ob, f = S.cloth_strip("front", A, B, length=.62, width=.1, mat=m_front, nx=130, ny=18, gather=.3, frames=90,
                          colliders=[col], bend=.4, uv_repeat=.4 / .62)
    # start it on the arc round the fence instead of the straight chord through it
    vs = ob.data.vertices
    nx, ny = 130, 18
    for i in range(nx):
        t = i / (nx - 1)
        a = a0 + (a1 - a0) * t
        g = .3 + .7 * min(1.0, min(t, 1 - t) / .12)
        for j in range(ny):
            s = j / (ny - 1)
            vs[i * ny + j].co = P(R * 1.06 * math.sin(a), 27.5 - s * 10 * g, R * 1.06 * math.cos(a))
    arc = R * 1.06 * .01 * (a1 - a0)
    ob.modifiers["cloth"].settings.shrink_min = -(.62 / arc - 1)
    cloths.append((ob, f))
    S.simulate_and_freeze(cloths)

    # marigolds: a garland along the swags, a cluster on the front cloth, and the bowls' offerings
    items = []
    for i in range(25):
        t = i / 24
        items.append(((-43 + 86 * t, 89.5 - 9.5 * math.sin(math.pi * t) * (1 - .15 * math.cos(2 * math.pi * t)), -9.4), 2.4))
    for i in range(9):
        a = rng.uniform(-.75, .75)
        items.append(((R * 1.1 * math.sin(a), 29 + rng.uniform(0, 2), R * 1.1 * math.cos(a)), 2.5))
    for x in (-34, 34):
        S.lathe(f"bowl{x}", [(0, .002), (.05, .004), (.085, .02), (.095, .045), (.098, .05), (.092, .05), (.083, .023), (.05, .008), (0, .007)], m_brass).location = P(x, 0, 26)
        for k in range(6):
            items.append(((x + rng.uniform(-4.5, 4.5), 6 + rng.uniform(0, 2.5), 26 + rng.uniform(-4, 4)), 2.7))
    marigold_set(mari, m_mari, items)

    # the aronai round the fence is knotted at the front; its two ends hang down and wave (rendered
    # separately below as a loop). Here they are only shadow casters, posed at the loop's first frame.
    knot_m = S.mat_plain("aronai-knot", "#8C1018", rough=.75, sheen=.25)
    # the knot: a flattened, twisted wrap of the cloth (a few overlapping turns), not a ball
    for i, (dx, dz, rot, sc) in enumerate(((-.6, 0, .5, 1.0), (.7, .2, -.4, .95), (0, .5, 0, .8))):
        kn = S.lathe(f"fence-knot{i}", [(0, -.016), (.012, -.013), (.016, -.003), (.015, .008), (.009, .014), (0, .015)], knot_m, seg=24)
        kn.location = P(dx, 22.5, R * 1.06 + 1.4 + dz)
        kn.rotation_euler = (math.pi / 2, rot, 0)
        kn.scale = (1.25 * sc, .9 * sc, .55)
    for i in range(3):          # the wrap's folds
        S.tube(f"knot-fold{i}", [P(-1.6, 22.5 + (i - 1) * .9, R * 1.06 + 2.1), P(0, 22.7 + (i - 1) * .7, R * 1.06 + 2.5),
                                 P(1.6, 22.5 + (i - 1) * .9, R * 1.06 + 2.1)], [.0028] * 3, knot_m, sides=10)
    tail_mats = [S.mat_aronai(f"aronai-tail{k}", 400, 45, ppm=12, seed=40 + k, u0=.6, u1=1.0) for k in range(2)]
    shadow_only = fence_tails(0.0, tail_mats, knot_m, R)
    for o in shadow_only:
        o.visible_camera = False

    S.key_light(target=P(0, 40, 0), dist=3.0, size=2.0, energy=380, az=-122, el=38)
    S.camera(P(0, 92, 296), P(0, 42, 0), 30, (600, 860))
    S.render("altar")

    # the waving ends: the same camera and light, everything else still there (lighting and shadows on
    # the cloth) but hidden from the camera, the floor catcher off; one frame per step of the loop
    for o in shadow_only:
        S.bpy.data.objects.remove(o, do_unlink=True)
    for o in S.bpy.data.objects:
        if o.type == "MESH":
            o.visible_camera = False
            o.is_shadow_catcher = False
    S.bpy.context.scene.cycles.samples = 128
    for fr in range(TAIL_FRAMES):
        obs = fence_tails(fr / TAIL_FRAMES, tail_mats, knot_m, R)
        S.render(f"altar-tail-{fr:02d}")
        for o in obs:
            S.bpy.data.objects.remove(o, do_unlink=True)


TAIL_FRAMES = 32


def fence_tails(phase, mats, cord, R):
    """The two ends of the fence aronai hanging from the knot, at one moment of a seamless loop: a breeze
    sends a wave down each from the knot to the fringe (the second a little behind the first), so they
    sway out, flutter toward and away from us, and turn as the wave passes. Returns the new objects."""
    import render_aronai as RA
    before = set(S.bpy.data.objects)
    tw = 2 * math.pi
    W = .045
    for k, side in enumerate((-1, 1)):
        ph = tw * phase + k * 1.1
        Lt = 16.0 if k == 0 else 14.5
        pts = []
        for u in np.linspace(0, 1, 70):
            sway = 2.4 * u ** 1.6 * math.sin(ph - 5.2 * u)            # side to side, growing to the end
            flut = 1.3 * u ** 1.4 * math.sin(ph * 1 + 1.3 - 4.4 * u)   # toward and away from us
            x = side * (1.2 + 3.2 * u) + sway
            y = 21.0 - Lt * u + .5 * u * u * abs(math.sin(ph - 5.2 * u))
            z = R * 1.06 + 2.4 + 1.2 * u + flut
            pts.append(P(x, y, z))
        ob, ends = RA.scarf(f"tail{k}", pts, W, base_normal=(0, -1, 0))
        ob.data.materials.append(mats[k])
        p, t, sd = ends[1]
        RA.warp_fringe(f"tf{k}", p, t, sd, W, .022, rng=np.random.default_rng(70 + k), cord=cord)
    return [o for o in S.bpy.data.objects if o not in before]


# ------------------------------------------------------------------ lamps
LAMP_PROFILE = [(0, 0), (7, 0), (7.5, .8), (3, 2), (2.2, 6), (3, 9), (9, 11.5), (10.5, 14), (10.3, 14.6), (9.6, 14.4),
                (8.5, 12.8), (0, 12.5)]


def saki_lamp(x, z, sc, m_brass, m_flame, m_oil, m_wick):
    """A brass saki lamp: a footed bowl of oil, a cotton wick at the lip and its flame (three spec, cm)."""
    prof = [(r * .01 * sc, y * .01 * sc) for r, y in LAMP_PROFILE]
    ob = S.lathe("lamp", prof, m_brass, seg=72)
    ob.location = P(x, 0, z)
    oil = S.lathe("oil", [(0, 13.3 * .01 * sc), (8.6 * .01 * sc, 13.3 * .01 * sc)], m_oil, seg=48)
    oil.location = P(x, 0, z)
    # wick lying on the lip, its tip lifted, and the flame standing on it
    wpts = [P(x + (5 - 4.5 + k * .9) * sc, (13.4 + k * k * .12) * sc, z) for k in range(7)]
    S.tube("wick", wpts, [.0045 * sc] * 7, m_wick, sides=8)
    fl = S.lathe("flame", [(0, 0), (.015, .008), (.022, .028), (.019, .05), (.009, .072), (0, .09)], m_flame, seg=24)
    fl.location = P(x + 5 * sc, 14.6 * sc, z)
    fl.scale = (sc, sc, sc)
    fl.visible_shadow = False
    # its warm light on the brass and the cloth
    ld = S.bpy.data.lights.new("glow", "POINT")
    ld.energy = 6 * sc * sc
    ld.color = (1, .62, .25)
    ld.shadow_soft_size = .01
    lo = S.link(S.bpy.data.objects.new("glow", ld))
    lo.location = P(x + 5 * sc, 17.5 * sc, z)


def lamp_mats():
    return (S.mat_brass(), S.mat_flame(), S.mat_plain("oil", "#7A4E10", rough=.05),
            S.mat_plain("wick", "#F2E6CC", rough=.9))


def lamp():
    S.reset(samples=256)
    mats = lamp_mats()
    S.shadow_catcher()
    saki_lamp(0, 0, 1, *mats)
    S.key_light(target=P(0, 10, 0), dist=1.2, size=.8, energy=60, az=-122, el=40)
    S.camera(P(0, 30, 80), P(0, 12, 0), 30, (88, 120))
    S.render("lamp")


def lamps3():
    S.reset(samples=256)
    mats = lamp_mats()
    S.shadow_catcher()
    # a strip of dokhona under them
    m_cloth = S.mat_cloth("lamps-cloth", ground="#EE8A1E", border="#0F7A4A")
    verts, faces, uvs = [], [], []
    nx, ny = 60, 16
    for j in range(ny):
        for i in range(nx):
            u, v = i / (nx - 1), j / (ny - 1)
            verts.append(P((u - .5) * 120, .15 + .1 * math.sin(u * 13) * math.sin(v * 5), (v - .5) * 40 + 6))
            uvs.append((u * 2.4, v))
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    ob = S.mesh_obj("cloth", verts, faces, uvs=uvs, mat=m_cloth)
    ob.modifiers.new("t", "SOLIDIFY").thickness = .002
    for x, z, sc in ((-30, 4, .9), (0, -6, 1.1), (30, 4, .9)):
        saki_lamp(x, z, sc, *mats)
    items = [((-50 + i * 20 + rng.uniform(-3, 3), 3.2, 22 + rng.uniform(-3, 3)), 4) for i in range(6)]
    marigold_set(S.marigold_mesh(seed=3), S.mat_marigold(), items)
    S.key_light(target=P(0, 8, 0), dist=2.4, size=1.6, energy=260, az=-122, el=42)
    S.camera(P(0, 60, 150), P(0, 10, 2), 30, (400, 220))
    S.render("lamps3")


# ------------------------------------------------------------------ banana plant and marigold bush
def banana():
    """A young banana plant: a streaked pseudostem and broad paddle leaves arching out, torn along the veins."""
    S.reset(samples=256)
    S.shadow_catcher()
    m_stem = S.mat_succulent()
    m_stem.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = .15
    ramp = [n for n in m_stem.node_tree.nodes if n.type == "VALTORGB"][0].color_ramp
    ramp.elements[0].color = S.hexrgb("#41602A")
    ramp.elements[1].color = S.hexrgb("#7E9548")
    pts = [P(0, y, 0) for y in np.linspace(0, 152, 40)]
    S.tube("pseudostem", pts, [(.11 - .04 * (y / 152)) for y in np.linspace(0, 152, 40)], m_stem, sides=28,
           profile=lambda th: 1 + .03 * math.cos(9 * th))
    specs = [(-1, .15, 30), (1, .1, 32), (-.6, .75, 26), (.65, .7, 26), (-1, -.35, 30), (1, -.4, 30), (.05, 1, 9)]
    for k, (dx, up, wd) in enumerate(specs):
        L = 70 if wd < 10 else 125
        zj = rng.uniform(-.5, .5)
        p0 = P(0, 150, 0)
        p1 = P(dx * L * .45, 150 + L * (.5 + up * .45), zj * 30)
        p2 = P(dx * L * .95, 150 + L * up * .7 - 10, zj * 40 + rng.uniform(-10, 10))
        tex = S.banana_leaf_texture(seed=k)
        if wd < 10:   # the young furled leaf at the top has no tears yet
            tex[..., 3] = 1
        m_leaf = S.mat_leaf_tex(f"banana-leaf{k}", tex)
        S.leaf_along(f"leaf{k}", p0, p1, p2, wd * .01, m_leaf, n=90, m=15, cup=-.045, droop=.07)
        # the leaf stalk joining the stem
        S.tube(f"petiole{k}", [P(0, 140, 0), (P(0, 140, 0) + p0) / 2 + (p1 - p0) * .05, p0 + (p1 - p0) * .08],
               [.012, .01, .008], m_stem, sides=10)
    S.key_light(target=P(0, 150, 0), dist=6.5, size=4, energy=1800, az=-122, el=45)
    S.camera(P(0, 165, 520), P(0, 158, 0), 34, (500, 660))
    S.render("banana-l")


def bush():
    """A marigold bush for the front corners: a mound of leaves with full orange and yellow flowers."""
    S.reset(samples=256)
    S.shadow_catcher()
    m_leaf = S.mat_plain("bush-leaf", "#3E7A2A", rough=.5, subsurface=.12)
    for i in range(130):
        x, z = rng.uniform(-75, 75), rng.uniform(-20, 20)
        a, Lg = rng.uniform(0, 6.28), rng.uniform(14, 24)
        p0 = P(x, 1, z)
        p2 = P(x + math.cos(a) * Lg, 8 + rng.uniform(0, 26), z + math.sin(a) * Lg * .5)
        p1 = (p0 + p2) / 2 + Vector((0, 0, .06))
        face = Vector((rng.uniform(-.5, .5), -1, rng.uniform(-.3, .6)))
        S.leaf_along(f"bl{i}", p0, p1, p2, rng.uniform(3.5, 6) * .01, m_leaf, n=24, m=7, cup=.25, tip_round=False, face=face)
    items = [((rng.uniform(-68, 68), 22 + rng.uniform(0, 28), rng.uniform(-14, 18)), rng.uniform(9, 14)) for _ in range(15)]
    marigold_set(S.marigold_mesh(seed=7), S.mat_marigold(), items)
    S.key_light(target=P(0, 25, 0), dist=3, size=2, energy=420, az=-122, el=45)
    S.camera(P(0, 52, 175), P(0, 26, 0), 34, (340, 260))
    S.render("bush-l")


PARTS = {"altar": altar, "lamp": lamp, "lamps3": lamps3, "banana": banana, "bush": bush}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in (args or PARTS):
        PARTS[name]()
