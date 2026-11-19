"""The aronai over the cover's name badge, rendered in Blender (Cycles, GPU), shot straight on
(orthographic) so it lines up with the page exactly. The cloth is studio.mat_aronai: a whole handloom
aronai woven thread by thread (deep red body, agor-teeth borders, motifs, end panels), so its end panels
fall where the ends hang. (The opened stage's aronai are part of the shrine: render_pandal.py -- altar.)

Run:  blender.cmd -b -P render_aronai.py -- badge
  aronai-badge  560 x 460 (shown 280 x 230): hung over the badge the way an aronai is draped round an
                honoured guest: across the top behind the badge, bunched over both top corners, hanging
                down its sides in soft folds, a knotted warp fringe at each end. The page puts it just
                behind the badge, so the badge covers the part that runs behind it.
publish.py writes it to public/art/ (kept at 2x; the page sizes it).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                      # noqa: E402
from mathutils import Matrix, Vector    # noqa: E402

import studio as S                      # noqa: E402
import render_pandal as RP              # noqa: E402

rng = np.random.default_rng(14)
TILE = 9.8          # the band's length / width


def scarf(name, pts, W, base_normal=(0, -1, 0), m=26):
    """A soft cloth band along a centre line (no simulation): it bunches and folds where it turns over a
    corner, hangs in soft lengthwise folds where it falls free, and flares a touch at its ends.
    UV u runs 0..1 along the whole cloth (for mat_aronai), v across. Returns the object and, for each end,
    (point, direction off the end, across-direction)."""
    n = len(pts)
    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + (pts[i] - pts[i - 1]).length)
    L = s[-1]
    tang = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    # how sharply the line turns here (per m), smoothed: where the cloth bunches
    turn = [0.0] * n
    for i in range(1, n - 1):
        turn[i] = tang[i - 1].angle(tang[i + 1], 0) / max(1e-6, s[i + 1] - s[i - 1])
    turn = np.convolve(np.array(turn), np.ones(15) / 15, mode="same")
    turn = np.clip(turn / 30.0, 0, 1)
    verts, faces, uvs, ends = [], [], [], []
    for i, p in enumerate(pts):
        t = tang[i]
        n0 = Vector(base_normal); n0 = (n0 - t * n0.dot(t)).normalized()
        hang = min(1.0, max(0.0, (.10 - p.z) / .12))          # 0 along the top, 1 hanging low
        endf = max(0.0, 1 - min(s[i], L - s[i]) / .03)        # near either end
        ang = (.08 + .25 * hang) * math.sin(s[i] / .034 + 1.3)  # a slow turn about its own length
        nrm = Matrix.Rotation(ang, 3, t) @ n0
        side = t.cross(nrm).normalized()
        wid = W * (1 - .3 * turn[i]) * (1 + .1 * endf)         # gathered at the corners, open at the ends
        amp = W * (.03 + .16 * turn[i] + .07 * hang)           # fold depth
        ph = s[i] / .05
        for j in range(m):
            v = j / (m - 1)
            x = (v - .5) * wid
            # lengthwise folds across the width (two and a half), drifting along the cloth, plus the
            # cloth's own slight dome
            d = amp * math.sin(2 * math.pi * (v * 1.5 + .15 * math.sin(ph))) + W * .05 * (1 - (2 * v - 1) ** 2)
            verts.append(p + side * x + nrm * d)
            uvs.append((s[i] / L, v))
        if i in (0, n - 1):
            ends.append((p, -t if i == 0 else t, side))
    for i in range(n - 1):
        for j in range(m - 1):
            a = i * m + j
            faces.append((a, a + m, a + m + 1, a + 1))
    ob = S.mesh_obj(name, verts, faces, uvs=uvs)
    so = ob.modifiers.new("thick", "SOLIDIFY"); so.thickness = .0009; so.offset = 0
    su = ob.modifiers.new("smooth", "SUBSURF"); su.levels = su.render_levels = 1
    return ob, ends


def warp_fringe(name, p, t, side, W, length, red="#A3121B", rng=rng, cord=None):
    """A handloom fringe: the warp threads left long at the end, twisted together in small groups and
    knotted. Pass a freshly seeded rng to get the same fringe every time (animation frames)."""
    cord = cord or S.mat_plain(f"{name}-cord", red, rough=.7, sheen=.5)
    groups = max(5, int(W / .0045))
    for g in range(groups):
        x = (g + .5) / groups - .5
        base = p + side * (x * W * .92)
        Lg = length * (1 + rng.uniform(-.12, .12))
        sway = side * rng.uniform(-1, 1) * Lg * .12
        # the knot just off the cloth, then the twisted group below it
        kn = S.lathe(f"{name}k{g}", [(0, -.0011), (.0011, -.0006), (.0012, .0004), (0, .0011)], cord, seg=10)
        kn.location = base + t * .0022
        for th in range(3):
            o = side * ((th - 1) * .00045)
            pts = [base + o * (1 - u * .6) + t * (Lg * u) + sway * u * u for u in np.linspace(0, 1, 8)]
            S.tube(f"{name}{g}-{th}", pts, [.00042] * 8, cord, sides=6)


def badge():
    S.reset(320)
    # the centre line, in the page's px (x right, y down) for the left half: from the badge's top centre,
    # along its top just above the edge, round the top corner and down its side
    # the two sides hang a little differently: one end longer, each swinging slightly out at the bottom
    left = [(0, -126), (-40, -128), (-73, -126), (-94, -119), (-106, -106), (-111, -86), (-110, -52),
            (-108, -16), (-108, 20), (-111, 56)]
    right = [(0, -126), (40, -127), (73, -125), (95, -117), (107, -103), (110, -82), (108, -48),
             (106, -14), (107, 18), (110, 40)]
    path = list(reversed(left)) + right[1:]
    pts = [Vector(p) for p in RP.catmull([(x * .001, 0, -y * .001) for x, y in path], 220)]
    W = .028
    ob, ends = scarf("aronai", pts, W, base_normal=(0, -1, 0))
    L_mm = sum((pts[i] - pts[i - 1]).length for i in range(1, len(pts))) * 1000
    ob.data.materials.append(S.mat_aronai("aronai-badge", L_mm, W * 1000, ppm=16, seed=3))
    for k, (p, t, side) in enumerate(ends):
        warp_fringe(f"fr{k}", p, t, side, W, .016)
    S.key_light(target=(0, 0, .03), dist=2.0, size=1.6, energy=100, az=-110, el=40)
    S.camera((0, -2, .025), (0, 0, .025), 0, (560, 460), ortho_width=.28)
    S.render("aronai-badge")


def hang():
    """aronai-hang, 240 x 720 (shown about 60 x 180): an aronai hung on the wall beside the shrine, folded
    over a short bamboo rod that hangs by a red cord from a brass nail; it falls in soft folds to its
    striped end and fringe. The page mirrors it for the other side."""
    S.reset(256)
    W = .085
    # the cloth: over the top of the rod from behind, then down the front, drifting a little to one side
    pts = [Vector((0, .006 * math.cos(a), .008 * math.sin(a))) for a in np.linspace(math.pi * .95, math.pi * .45, 8)]
    for u in np.linspace(0, 1, 90)[1:]:
        pts.append(Vector((.006 * math.sin(u * 2.4) * u, -.009 - .004 * u, .006 - .39 * u)))
    ob, ends = scarf("hang", pts, W, base_normal=(0, -1, 0))
    L_mm = sum((pts[i] - pts[i - 1]).length for i in range(1, len(pts))) * 1000
    # the texture covers this visible part of a longer cloth: body at the rod, striped end at the bottom
    ob.data.materials.append(S.mat_aronai("aronai-hang", L_mm * 1.6, W * 1000, ppm=8, seed=5, u0=.375, u1=1.0))
    p, t, sd = ends[1]
    warp_fringe("hf", p, t, sd, W, .03, rng=np.random.default_rng(9))
    # the rod, the cord and the nail
    S.bamboo_pole("rod", (-.062, .0, .0), (.062, .0, .0), .0055, S.mat_bamboo())
    cord = S.mat_plain("cord", "#A3121B", rough=.7, sheen=.4)
    S.tube("cord", [(-.055, -.002, .003), (-.03, -.002, .05), (0, -.002, .085), (.03, -.002, .05), (.055, -.002, .003)],
           [.0013] * 5, cord, sides=8)
    nail = S.lathe("nail", [(0, 0), (.006, 0), (.0065, .002), (.003, .004), (0, .0045)], S.mat_brass(), seg=24)
    nail.location = (0, -.003, .087); nail.rotation_euler = (math.pi / 2, 0, 0)
    S.key_light(target=(0, 0, -.15), dist=2.0, size=1.6, energy=110, az=-110, el=40)
    S.camera((0, -2, -.2), (0, 0, -.2), 0, (240, 720), ortho_width=.2)
    S.render("aronai-hang")


def bow():
    """The aronai bow that ties the closed curtains, in parts on one frame so the page can untie it and let
    it fall: cbow-body (the two loops and the knot), cbow-tail-l and cbow-tail-r (each hanging end with its
    striped end and fringe). 680 x 600, shown at about 150 x 132."""
    W = .036
    tex = dict(ppm=14, seed=12)

    def loop(sgn):
        pts = []
        for a in np.linspace(0, 1, 70):
            th = a * 2 * math.pi
            # a teardrop out to the side: wide at its far end, pinched at the knot
            r = .105 * math.sin(th / 2) ** 1.4
            pts.append(Vector((sgn * r * (1 - .05 * math.cos(th)), -.004 * math.sin(th) ** 2, .018 * math.sin(th) + .01 * math.sin(th / 2) ** 2 - .004)))
        return pts

    def tail(sgn):
        pts = []
        for u in np.linspace(0, 1, 70):
            pts.append(Vector((sgn * (.012 + .055 * u + .012 * math.sin(u * 3.2)), -.006 + .004 * u, -.012 - .17 * u)))
        return pts

    # each part rendered alone (same camera and light), so the page can move them separately
    for part in ("body", "tail-l", "tail-r"):
        S.reset(256)
        if part == "body":
            for k, sgn in enumerate((-1, 1)):
                ob, _ = scarf(f"loop{k}", loop(sgn), W, base_normal=(0, -1, 0))
                ob.data.materials.append(S.mat_aronai(f"bl{k}", 300, W * 1000, u0=.35, u1=.65, **tex))
            # the knot: a short wrap of cloth bulging toward us
            kp = [Vector((0, -.012 * math.sin(math.pi * u), .022 - .046 * u)) for u in np.linspace(0, 1, 30)]
            ob, _ = scarf("knot", kp, W * 1.05, base_normal=(0, -1, 0))
            ob.data.materials.append(S.mat_aronai("bk", 300, W * 1000, u0=.45, u1=.55, **tex))
        else:
            sgn = -1 if part == "tail-l" else 1
            ob, ends = scarf("tail", tail(sgn), W, base_normal=(0, -1, 0))
            ob.data.materials.append(S.mat_aronai(f"bt{sgn}", 600, W * 1000, u0=.7, u1=1.0, **tex))
            p, t, sd = ends[1]
            warp_fringe(f"btf{sgn}", p, t, sd, W, .02, rng=np.random.default_rng(30 + sgn))
        S.key_light(target=(0, 0, -.05), dist=2.0, size=1.6, energy=110, az=-110, el=40)
        S.camera((0, -2, -.07), (0, 0, -.07), 0, (680, 600), ortho_width=.34)
        S.render(f"cbow-{part}")


def cover():
    """The aronai tied round the cover's doors, at the page's scale (1 mm = 1 css px, rendered at 2x):
    cover-band   1040 x 64: the straight band across the doors (the page hangs it as a hinged chain so
                 it can go slack and fall); the middle of a long cloth, body pattern only
    cover-loop-l / cover-loop-r / cover-knot / cover-tail-l / cover-tail-r   640 x 540, one frame: the
                 bow, each part alone so the page can untie it piece by piece. The knot is at 50%, 29.6%."""
    W = .03
    tex = dict(ppm=16, seed=21)
    # the band: a little wavy where it lies over the doors' cloth
    S.reset(192)
    pts = [Vector((x, .0012 * math.sin(x * 60), .0006 * math.sin(x * 23))) for x in np.linspace(-.26, .26, 160)]
    ob, _ = scarf("band", pts, W, base_normal=(0, -1, 0))
    ob.data.materials.append(S.mat_aronai("cb", 2000, W * 1000, u0=.37, u1=.63, **tex))
    S.key_light(target=(0, 0, 0), dist=2.0, size=1.6, energy=100, az=-110, el=40)
    S.camera((0, -2, 0), (0, 0, 0), 0, (1040, 64), ortho_width=.52)
    S.render("cover-band")

    def loop(sgn):
        pts = []
        for a in np.linspace(0, 1, 90):
            th = a * 2 * math.pi
            r = .135 * math.sin(th / 2) ** 1.3          # a full teardrop loop out to the side
            pts.append(Vector((sgn * (.01 + r), -.005 * math.sin(th) ** 2 - .004 * math.sin(th / 2),
                               .03 * math.sin(th) + .016 * math.sin(th / 2) ** 2 - .006)))
        return pts

    def tail(sgn):
        # from under the knot, down and out, a soft S as it hangs, the end turning a little
        return [Vector((sgn * (.006 + .07 * u + .014 * math.sin(u * 3.4)), -.008 + .006 * u, -.014 - .165 * u))
                for u in np.linspace(0, 1, 80)]

    for part in ("loop-l", "loop-r", "knot", "tail-l", "tail-r"):
        S.reset(256)
        if part.startswith("loop"):
            sgn = -1 if part.endswith("l") else 1
            ob, _ = scarf("loop", loop(sgn), W, base_normal=(0, -1, 0))
            ob.data.materials.append(S.mat_aronai(f"cl{sgn}", 2000, W * 1000, u0=.4 + .05 * sgn, u1=.5 + .05 * sgn, **tex))
        elif part == "knot":
            # the knot: the cloth wrapped round itself, bulging toward us, two creases across it
            kp = [Vector((.004 * math.sin(u * 6), -.016 * math.sin(math.pi * u) ** .8, .026 - .052 * u)) for u in np.linspace(0, 1, 40)]
            ob, _ = scarf("knot", kp, W * 1.15, base_normal=(0, -1, 0))
            ob.data.materials.append(S.mat_aronai("ck", 2000, W * 1000, u0=.48, u1=.51, **tex))
            for i, zz in enumerate((.009, -.01)):
                S.tube(f"crease{i}", [(-.017, -.019, zz), (0, -.023, zz + .002), (.017, -.019, zz)], [.0016] * 3,
                       S.mat_plain(f"cr{i}", "#7E0E15", rough=.8), sides=8)
        else:
            sgn = -1 if part.endswith("l") else 1
            ob, ends = scarf("tail", tail(sgn), W, base_normal=(0, -1, 0))
            ob.data.materials.append(S.mat_aronai(f"ct{sgn}", 2000, W * 1000, u0=.9, u1=1.0, **tex))
            p, t, sd = ends[1]
            warp_fringe(f"ctf{sgn}", p, t, sd, W, .02, rng=np.random.default_rng(50 + sgn))
        S.key_light(target=(0, 0, -.05), dist=2.0, size=1.6, energy=110, az=-110, el=40)
        S.camera((0, -2, -.055), (0, 0, -.055), 0, (640, 540), ortho_width=.32)
        S.render(f"cover-{part}")


UNTIE_FRAMES = 48


def untie():
    """cover-untie-00..47, 320 x 620 each (shown at 1x), knot at (160, 80), its shadow on the doors baked in: the cover bow coming undone as one
    continuous motion of cloth. The right tail is drawn down and out, and grows as the right loop's cloth
    runs through the knot into it; then the left loop goes the same way into the left tail; the knot
    opens, and the two freed ends swing loose and fall. publish.py packs the frames into one sprite."""
    W = .03
    tex = dict(ppm=12, seed=21)
    S.reset(256)                 # enough samples that the soft shadow doesn't shimmer frame to frame
    mats = {k: S.mat_aronai(f"u{k}", 2000, W * 1000, u0=a, u1=b, **tex)
            for k, (a, b) in {"loopL": (.35, .45), "loopR": (.55, .65), "knot": (.48, .51), "tail": (.9, 1.0)}.items()}
    crease = S.mat_plain("ucr", "#7E0E15", rough=.8)
    # the doors' cloth just behind the bow, as a shadow catcher: the bow's own shadow is part of every
    # frame (no CSS shadow filter to redraw while it plays)
    wall = S.mesh_obj("doors", [(-.4, .02, .2), (-.4, .02, -.7), (.4, .02, -.7), (.4, .02, .2)], [(0, 1, 2, 3)], smooth=False)   # facing the camera and light
    wall.is_shadow_catcher = True
    S.key_light(target=(0, 0, -.12), dist=2.0, size=1.6, energy=110, az=-110, el=40)
    S.camera((0, -2, -.23), (0, 0, -.23), 0, (320, 620), ortho_width=.32)
    ease = lambda x: x * x * (3 - 2 * x)                     # noqa: E731

    def phase(t, a, b):
        return ease(min(1.0, max(0.0, (t - a) / (b - a))))

    def loop_pts(sgn, f):
        pts = []
        for a in np.linspace(0, 1, 90):
            th = a * 2 * math.pi
            r = .135 * f * math.sin(th / 2) ** 1.3
            pts.append(Vector((sgn * (.01 * f + r), -.005 * math.sin(th) ** 2 - .004 * math.sin(th / 2),
                               (.03 * math.sin(th) + .016 * math.sin(th / 2) ** 2) * (.4 + .6 * f) - .006)))
        return pts

    def curve(p0, c, p1, n=80):
        p0, c, p1 = Vector(p0), Vector(c), Vector(p1)
        return [(1 - u) ** 2 * p0 + 2 * (1 - u) * u * c + u * u * p1 for u in map(float, np.linspace(0, 1, n))]

    for fr in range(UNTIE_FRAMES):
        t = fr / (UNTIE_FRAMES - 1)
        a = phase(t, 0.0, .42)        # right tail pulled, right loop running through
        b = phase(t, .36, .72)        # then the left
        c = phase(t, .7, 1.0)         # the knot opens, the ends fall
        objs = []
        for sgn, f in ((1, 1 - a), (-1, 1 - b)):
            if f > .06:
                ob, _ = scarf("loop", loop_pts(sgn, f), W, base_normal=(0, -1, 0))
                ob.data.materials.append(mats["loopR" if sgn > 0 else "loopL"]); objs.append(ob)
        # the tails: each runs from under the knot to its end; pulled ends move out and down; once the knot
        # opens they come free, swing toward hanging straight, and drop
        for sgn, pull in ((1, a), (-1, b)):
            start = Vector((sgn * (.006 + .03 * c), -.008, -.014))
            rest_end = Vector((sgn * .083, -.002, -.18))
            pulled_end = Vector((sgn * .14, .0, -.33))
            end = rest_end.lerp(pulled_end, pull)
            end = end.lerp(Vector((start.x + sgn * .02, 0, start.z - (end - start).length)), c * .8)   # swings to hang
            ctrl = start.lerp(end, .5) + Vector((sgn * (.03 - .02 * pull), -.004, .02 * (1 - c)))
            drop = Vector((0, 0, -.11 * c * c))      # the page carries the fall on from here
            pts = [p + drop for p in curve(start, ctrl, end)]
            ob, ends = scarf("tail", pts, W, base_normal=(0, -1, 0))
            ob.data.materials.append(mats["tail"]); objs.append(ob)
            p, tt, sd = ends[1]
            before = set(S.bpy.data.objects)
            warp_fringe(f"uf{sgn}", p, tt, sd, W, .02, rng=np.random.default_rng(50 + sgn), cord=crease)
            objs += [o for o in S.bpy.data.objects if o not in before]
        k = 1 - c
        if k > .2:
            kp = [Vector((.004 * math.sin(u * 6), -.016 * math.sin(math.pi * u) ** .8, .026 - .052 * u)) for u in np.linspace(0, 1, 40)]
            ob, _ = scarf("knot", kp, W * 1.15 * (1 + .25 * a * b), base_normal=(0, -1, 0))
            ob.data.materials.append(mats["knot"])
            ob.scale = (1 + .3 * c, 1, k)
            ob.location.z -= .11 * c * c                # it goes down with the ends, not left in the air
            objs.append(ob)
        S.render(f"cover-untie-{fr:02d}")
        if fr == 0:
            # the still bow on the closed cover: this same pose, sharp (2x), so the film takes over seamlessly
            sc = S.bpy.context.scene
            sc.render.resolution_x, sc.render.resolution_y = 640, 1240
            sc.cycles.samples = 256
            S.render("cover-bow")
            sc.render.resolution_x, sc.render.resolution_y = 320, 620
            sc.cycles.samples = 256
        for o in objs:
            S.bpy.data.objects.remove(o, do_unlink=True)


PARTS = {"badge": badge, "hang": hang, "bow": bow, "cover": cover, "untie": untie}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in (args or PARTS):
        PARTS[name]()
