"""The scroll sections' objects, rendered in Blender (Cycles, GPU): product shots on the paper.

Run:  blender.cmd -b -P render_objects.py -- knot fold-aronai fold-dokhona fold-gamsa instruments meal plate
Writes out/<name>.png; publish.py turns them into the site's WebP files (same names).
Geometry is written in the three.js spec's coordinates (cm, y up, z toward the camera) and converted with P().
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                      # noqa: E402
from mathutils import Euler, Matrix, Vector   # noqa: E402

import studio as S                      # noqa: E402
from studio import P                    # noqa: E402

rng = np.random.default_rng(21)


def shot(name, look, pos, res, fov=30, energy=190, dist=2.4):
    S.key_light(target=P(*look), dist=dist, size=dist * .7, energy=energy * (dist / 2.4) ** 2, az=-122, el=45)
    S.camera(P(*pos), P(*look), fov, res)
    S.render(name)


def marigolds(items, seed=3):
    mesh = S.marigold_mesh(seed=seed)
    src = S.link(S.bpy.data.objects.new("mg-src", mesh))
    src.data.materials.append(S.mat_marigold())
    src.hide_render = True
    for pos, r in items:
        S.instance(src, P(*pos), rot=Euler((rng.uniform(-.4, .4), rng.uniform(-.4, .4), rng.uniform(0, 6.3))), scale=r * .01)


# ------------------------------------------------------------------ folded cloth
def fold_stack(w, d, t, layers, mat, origin=(0, 0, 0), yaw=0.0, uv="wrap", tex_w=None, fringe_mat=None, name="fold"):
    """Folded cloth seen from the front: each layer one continuous sheet - its top, the rounded front fold
    and a little of its underside - softly puffed, the layers stacked and slightly inset.
    uv='wrap': the texture runs along the width and across the depth (aronai band on top);
    uv='border': the cloth's woven border sits on the front fold (dokhona, gamsa)."""
    ox, oy, oz = origin
    base = P(ox, oy, oz)
    for k in range(layers):
        y0 = k * t + (k * .25)
        inset = (layers - 1 - k) * 1.6
        W = w - inset
        # each layer lies a little off true: shifted and turned by hand
        rot = Matrix.Rotation(yaw + rng.uniform(-.025, .025), 3, "Z")
        shift = rng.uniform(-1.2, 1.2)
        # profile (depth z, height y, arc length s): back of top -> front fold -> under
        prof = []
        nz = 30
        for i in range(nz):
            z = -d / 2 + d * i / (nz - 1)
            prof.append((z, y0 + t))
        for i in range(1, 14):
            a = math.pi / 2 - math.pi * i / 13
            prof.append((d / 2 + math.cos(a) * t / 2, y0 + t / 2 + math.sin(a) * t / 2))
        for i in range(1, 8):
            prof.append((d / 2 - d * .35 * i / 7, y0 + .05))
        s = [0.0]
        for i in range(1, len(prof)):
            s.append(s[-1] + math.dist(prof[i], prof[i - 1]))
        s_fold = s[nz - 1] + math.pi * t / 4
        nx = 50
        verts, faces, uvs = [], [], []
        yc, zc = y0 + t / 2, 0.0                       # the layer's centre line
        for i in range(nx):
            ux = i / (nx - 1)
            x = (ux - .5) * W + shift
            puff = math.sin(math.pi * ux) ** .5
            # the ends roll under like a pillow: within the last few cm the sheet curls toward the centre line
            end = max(0.0, (abs(ux - .5) - .44) / .06)
            end = end * end * (3 - 2 * end)
            for j, (z, y) in enumerate(prof):
                top = j < nz
                dz = math.sin(math.pi * j / (nz - 1)) if top else 0
                yy = y + (t * .32 * puff * dz ** .5 if top else 0) - (t * .22 * (1 - puff) ** 2 if top else 0)
                yy += rng.normal(0, .025)
                zz = z + (t * .18 * puff if j >= nz else 0) * (1 if j < nz + 13 else .3)
                yy = yy + (yc - yy) * .55 * end
                zz = zz + (zc - zz) * .1 * end
                xx = x - math.copysign(t * .35 * end, ux - .5)
                verts.append(base + rot @ (P(xx, yy, zz) - P(0, 0, 0)))
                if uv == "wrap":
                    uvs.append((ux * W / (tex_w or W * 2.9), s[j] / d))
                else:
                    uvs.append((ux * W / (tex_w or 40), .045 + abs(s[j] - s_fold) / (2.4 * d)))
        np_ = len(prof)
        for i in range(nx - 1):
            for j in range(np_ - 1):
                a = i * np_ + j
                faces.append((a, a + np_, a + np_ + 1, a + 1))
        ob = S.mesh_obj(f"{name}{k}", verts, faces, uvs=uvs, mat=mat)
        so = ob.modifiers.new("thick", "SOLIDIFY"); so.thickness = .0012
        su = ob.modifiers.new("smooth", "SUBSURF"); su.levels = su.render_levels = 1
    if fringe_mat:
        # short gold tassels along the front fold of the top layer: little bunches of twisted threads
        ytop = (layers - 1) * (t + .25) + t / 2
        rot = Matrix.Rotation(yaw, 3, "Z")
        for k, xk in enumerate(np.linspace(-w / 2 + 5, w / 2 - 5, max(4, int(w / 7)))):
            p = base + rot @ (P(xk, ytop - t * .3, d / 2 + t / 2 + .6) - P(0, 0, 0))
            S.beads_ball = None
            S.fringe(f"{name}-tas{k}", p - Vector((.004, 0, 0)), p + Vector((.004, 0, 0)), (t * .9 + 2.5) * .01, fringe_mat,
                     n=5, r=.0011, droop=(rng.uniform(-.1, .1), -.35, -1), jitter=.15, rng=rng)
            knot_ = S.lathe("tassel-knot", [(0, -.003), (.0028, -.002), (.003, .001), (0, .003)], fringe_mat, seg=12)
            knot_.location = p


def gold_thread():
    return S.mat_plain("zari", "#D9A84A", rough=.32, metallic=.9)


def fold_aronai():
    S.reset(256); S.shadow_catcher()
    fold_stack(130, 42, 6, 4, S.mat_woven("band-scarlet"), uv="wrap", tex_w=130 * 2.9)
    shot("fold-aronai", (0, 10, 6), (0, 85, 175), (440, 240))


def fold_dokhona():
    S.reset(256); S.shadow_catcher()
    m = S.mat_cloth("dokhona-fold", ground="#F2C318", border="#D7332B", thread="#D9A84A", buti="#D7332B")
    fold_stack(120, 70, 7, 3, m, uv="border", tex_w=170)
    shot("fold-dokhona", (0, 8, 0), (0, 95, 190), (320, 240))


def fold_gamsa():
    S.reset(256); S.shadow_catcher()
    m = S.mat_cloth("gamsa-fold", ground="#0F7A4A", border="#F4F1E8", thread="#0F7A4A", buti=None)
    fold_stack(120, 70, 7, 3, m, uv="border", tex_w=170)
    shot("fold-gamsa", (0, 8, 0), (0, 95, 190), (320, 240))


# ------------------------------------------------------------------ the knot
def knot():
    """Two aronai, emerald and scarlet, lying interlocked: each passes over the other once, under once.
    Two families, one knot. Fringed tails run out to either side."""
    S.reset(320); S.shadow_catcher()
    em, sc = S.mat_woven("band-emerald", "#C0FFE0"), S.mat_woven("band-scarlet")
    W = 15

    def lift(x, zf, over_when_front):
        side = 1 / (1 + math.exp(-(zf if over_when_front else -zf) / 2.5))
        return .45 + 3.0 * math.exp(-(x / 10) ** 2) * side

    def loop(cx, ph, over_when_front):
        pts, nms = [], []
        for t in np.linspace(0, 1, 260):
            a = 2 * math.pi * t + ph
            x, zf = cx + 30 * math.cos(a), 20 * math.sin(a)
            y = lift(x, zf, over_when_front) + .25 * math.sin(a * 7)
            pts.append(P(x, y, zf))
            nms.append((0, 0, 1))
        return pts, nms
    for (cx, ph, front, m, nm) in ((-17, 0, True, em, "em"), (17, math.pi, False, sc, "sc")):
        pts, nms = loop(cx, ph, front)
        S.ribbon(f"loop-{nm}", pts, W * .01, m, normals=nms, puff=.035, tex_len=W * 9.8 * .01)
    # tails: from the outer side of each loop out toward the viewer, ending in gold fringe
    zari = gold_thread()
    for sgn, m, nm in ((-1, em, "em"), (1, sc, "sc")):
        pts = []
        for t in np.linspace(0, 1, 80):
            x = sgn * (44 + 30 * t + 4 * math.sin(t * 3))
            zf = 4 + 30 * t
            pts.append(P(x, .45 + .3 * math.sin(t * 9), zf))
        S.ribbon(f"tail-{nm}", pts, W * .01, m, puff=.03, tex_len=W * 9.8 * .01)
        end = pts[-1]
        dirv = (pts[-1] - pts[-2]).normalized()
        side = dirv.cross(Vector((0, 0, 1))).normalized()
        S.fringe(f"fr-{nm}", end - side * W * .005, end + side * W * .005, .06, zari, n=22, droop=tuple(dirv * 1 + Vector((0, 0, -.05))), rng=rng)
    shot("knot", (0, 0, 10), (0, 170, 215), (440, 260), energy=190)


# ------------------------------------------------------------------ instruments
def instruments():
    """Kham (barrel drum with zigzag leather lacing), siphung (long bamboo flute with a scarlet tassel)
    and jotha (a pair of brass cymbals tied with a red cord)."""
    S.reset(256); S.shadow_catcher()
    drum = kham_drum()
    drum.rotation_euler = Euler((0, math.pi / 2, .35))
    drum.location = P(-6, 13.6, 0)
    instruments_rest()


def kham_drum():
    """The kham, built along its own z axis (all parts parented to the returned shell)."""
    wood = S.mat_wood()
    skin = S.mat_plain("skin", "#E6D3AC", rough=.75, sheen=.3, subsurface=.08)
    hoop_m = S.mat_plain("hoop", "#3A2412", rough=.55)
    lace_m = S.mat_plain("lace", "#9C7448", rough=.65)
    # the drum, built along its own z axis, then laid on its side
    prof = [(.105 + .026 * math.sin(math.pi * i / 24), -.26 + .52 * i / 24) for i in range(25)]
    drum = S.lathe("kham", [(0, -.262)] + prof + [(0, .262)], wood, seg=72)
    parts = [drum]
    for z in (-.265, .265):
        h = S.lathe("head", [(0, z), (.111, z)], skin, seg=72); parts.append(h)
        ring = S.tube("hoop", [(math.cos(a) * .113, math.sin(a) * .113, z) for a in np.linspace(0, 2 * math.pi, 97)],
                      [.011] * 97, hoop_m, sides=12, cap=False); parts.append(ring)
    lace = []
    for i in range(25):
        a = i / 24 * 2 * math.pi
        z = .255 if i % 2 == 0 else -.255
        if i:
            a0, z0 = (i - 1) / 24 * 2 * math.pi, (.255 if (i - 1) % 2 == 0 else -.255)
            for u in np.linspace(0, 1, 14)[1:]:
                aa, zz = a0 + (a - a0) * u, z0 + (z - z0) * u
                r = .105 + .026 * math.sin(math.pi * (zz + .26) / .52) + .005
                lace.append((math.cos(aa) * r, math.sin(aa) * r, zz))
        else:
            lace.append((math.cos(a) * .118, math.sin(a) * .118, z))
    parts.append(S.tube("lace", lace, [.0042] * len(lace), lace_m, sides=6, cap=False))
    for p in parts:
        p.parent = drum if p is not drum else None
    return drum


def instruments_rest():
    # siphung resting across the drum, its far end on the floor
    bam = S.mat_bamboo("#D2AE70")
    A, B = P(-40, 40.5, 1), P(70, 1.9, 10)
    S.bamboo_pole("siphung", A, B, .019, bam)
    hole_m = S.mat_plain("hole", "#2A1A0C", rough=.9)
    d = (B - A).normalized()
    for k in range(6):
        c = A + d * ((.42 + k * .055) * (B - A).length) + Vector((0, 0, .0185))
        h = S.lathe("hole", [(0, 0), (.0042, 0), (.0042, .002)], hole_m, seg=16)
        h.location = c
        h.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.cross(Vector((0, 0, 1))).cross(d)).to_euler()
    red = S.mat_plain("cord", "#C0281E", rough=.6, sheen=.3)
    tas_top = B - d * .1 + Vector((0, 0, -.01))
    S.tube("tie", [tas_top + Vector((0, 0, .02)), tas_top + Vector((0, -.01, -.005)), tas_top + Vector((0, -.03, -.012))],
           [.0035] * 3, red, sides=8)
    S.fringe("tassel", tas_top + Vector((-.006, -.03, -.012)), tas_top + Vector((.006, -.03, -.012)), .05, red, n=14, r=.0013,
             droop=(.1, -1, -.15), rng=rng)
    # jotha: two cymbals and the cord between them
    brass = S.mat_brass()
    cym = [(r * .01, y * .01) for r, y in ((0, 2.4), (2.5, 2.2), (3.2, 1), (9, .4), (9.4, 0), (9.2, -.15), (3, .75), (2.3, 1.9), (0, 2.1))]
    for (x, z, rt) in ((44, 26, .2), (57, 17, -.4)):
        c = S.lathe("cymbal", cym, brass, seg=72)
        c.location = P(x, .2, z)
        c.rotation_euler = (rt * .25, -rt * .2, rt)
    S.tube("cymbal-cord", [P(44, 2.6, 26), P(48, 1.0, 24), P(52, .5, 21), P(57, 2.6, 17)], [.0025] * 4, red, sides=8)
    shot("instruments", (12, 16, 8), (0, 72, 158), (520, 280))


# ------------------------------------------------------------------ the first meal
def mat_rice():
    m, nt, b = S._mat("rice")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    # heaped grains: plump cells, plus a lumpy noise so the mound isn't a smooth dome
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 95; vo.feature = "DISTANCE_TO_EDGE"
    L.new(tc.outputs["Object"], vo.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs[0])
    sq = N.new("ShaderNodeMath"); sq.operation = "SQRT"
    L.new(vo.outputs["Distance"], sq.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = .6
    L.new(nz.outputs["Fac"], add.inputs[0]); L.new(sq.outputs[0], add.inputs[2])
    bn = N.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = .8; bn.inputs["Distance"].default_value = .004
    L.new(add.outputs[0], bn.inputs["Height"]); L.new(bn.outputs["Normal"], b.inputs["Normal"])
    # a touch of shade deep between grains
    ao = N.new("ShaderNodeMix"); ao.data_type = "RGBA"; ao.blend_type = "MULTIPLY"
    ao.inputs[7].default_value = S.hexrgb("#B8AC90")
    inv = N.new("ShaderNodeMath"); inv.operation = "LESS_THAN"; inv.inputs[1].default_value = .06
    L.new(vo.outputs["Distance"], inv.inputs[0]); L.new(inv.outputs[0], ao.inputs["Factor"])
    ao.inputs[6].default_value = S.hexrgb("#E4DAC2")
    L.new(ao.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .6
    b.inputs["Subsurface Weight"].default_value = .35
    b.inputs["Subsurface Radius"].default_value = (.004, .004, .003)
    b.inputs["Sheen Weight"].default_value = .3
    return m


def meal():
    """Rice and ondlakhari on a banana leaf, with the wooden hatha bowl: the first meal the bride serves."""
    S.reset(256); S.shadow_catcher()
    tex = S.banana_leaf_texture(seed=40)
    tex[..., 3] = 1
    leaf_m = S.mat_leaf_tex("meal-leaf", tex, sss=.1, rough=.32)
    leaf_m.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = .4
    S.leaf_along("plate-leaf", P(-72, .4, 4), P(0, 2.2, -4), P(74, .6, 2), .6, leaf_m, n=80, m=17, cup=-.02, face=(0, 0, 1))
    rice = S.lathe("rice", [(r * .01 * 1.0, (7.6 * math.sqrt(max(0, 1 - (r / 22) ** 2)) + .6) * .01) for r in np.linspace(0, 22, 24)] + [(.22, .006)], mat_rice(), seg=64)
    rice.location = P(-8, 1.0, 2)
    rice.scale = (1.15, 1, 1)
    # ondlakhari in a small leaf cup
    cup = S.lathe("leaf-cup", [(0, 0), (.08, .002), (.11, .03), (.115, .036), (.108, .036), (.075, .006), (0, .004)], leaf_m, seg=48)
    cup.location = P(26, .6, 6)
    curry = S.lathe("ondlakhari", [(r * .01, (2.4 * math.sqrt(max(0, 1 - (r / 10.2) ** 2)) + 1.0) * .01) for r in np.linspace(0, 10.2, 16)], S.mat_plain("curry", "#C98A3C", rough=.25, subsurface=.2), seg=48)
    curry.location = P(26, .6, 6)
    # a green chilli and a wedge of lemon by the rice
    S.tube("chilli", [P(4 + 1.6 * k, 1.4 + .2 * math.sin(k), 17 + .4 * k * k * .1) for k in range(9)],
           [.006 - .0005 * k for k in range(9)], S.mat_plain("chilli", "#3E8E2A", rough=.25), sides=12)
    lem = S.lathe("lemon", [(0, 0), (.025, .004), (.03, .015), (.022, .028), (0, .03)], S.mat_plain("lemon", "#E8D44A", rough=.4, subsurface=.2), seg=24)
    lem.location = P(-30, .8, 16); lem.scale = (1, .5, 1); lem.rotation_euler = (0, 1.4, .4)
    bowl = S.lathe("hatha", [(r * .01, y * .01) for r, y in ((0, 0), (9, 0), (13, 4), (15.5, 9), (16, 10), (15, 10), (12.5, 5), (0, 4))], S.mat_wood("#6A3E1C", "#2E1808"), seg=72)
    bowl.location = P(-52, 0, -22)
    shot("meal", (-6, 4, 0), (0, 110, 175), (520, 260), energy=150)


# ------------------------------------------------------------------ brass plate
def plate():
    """A brass plate with a folded aronai and a ring of marigolds: the honour given to every guest."""
    S.reset(256); S.shadow_catcher()
    tray = S.lathe("tray", [(r * .01, y * .01) for r, y in ((0, 0), (30, 0), (36, 1.5), (44, 3.2), (45, 4.2), (43.5, 4.2), (35, 2.6), (0, 2))], S.mat_brass(), seg=96)
    fold_stack(56, 30, 4.5, 3, S.mat_woven("band-scarlet"), origin=(-4, 2.2, -4), yaw=-.25, uv="wrap", tex_w=56 * 2.9, name="pf")
    items = []
    for i in range(9):
        a = -.6 + i * .32
        items.append(((math.cos(a) * 34, 6, math.sin(a) * 34 * .55 + 8), 5))
    marigolds(items)
    shot("plate", (0, 6, 4), (0, 95, 150), (440, 240))


PARTS = {"knot": knot, "fold-aronai": fold_aronai, "fold-dokhona": fold_dokhona, "fold-gamsa": fold_gamsa,
         "instruments": instruments, "meal": meal, "plate": plate}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in (args or PARTS):
        PARTS[name]()
