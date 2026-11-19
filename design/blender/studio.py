"""Shared Blender studio for the invitation art (Blender 4.4, Cycles).

Units are metres. Coordinates in the comments of render_pandal.py follow the three.js spec in
design/render3d/scene.js (cm, y up); `P(x, y, z)` converts them to Blender (m, z up).

One soft light from the top left, front and above; a warm, dim ambient; a transparent film with a shadow
catcher on the floor, so every render drops onto the paper of the site with its own soft shadow.
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(11)


def P(x, y, z):
    """three.js spec (cm, y up, z toward camera) -> Blender (m, z up, -y toward camera)."""
    return Vector((x * .01, -z * .01, y * .01))


def hexrgb(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


# ------------------------------------------------------------------ scene
def reset(samples=256):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 8
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    # Standard keeps the palette's exact hues (AgX greys the bright Bodo colours); the light is kept soft
    # enough that nothing clips
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -.45
    sc.unit_settings.system = "METRIC"
    # warm, dim ambient (a soft studio), no visible background
    w = bpy.data.worlds.new("studio")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hexrgb("#FFF1DC")
    bg.inputs["Strength"].default_value = .35
    sc.world = w
    return sc


def key_light(target=(0, 0, .4), dist=3.2, size=2.2, energy=900, az=-135, el=48):
    """The one soft light: top left, a little in front. az is measured from +x toward +y (degrees)."""
    a, e = math.radians(az), math.radians(el)
    pos = Vector(target) + dist * Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
    ld = bpy.data.lights.new("key", "AREA")
    ld.shape = "DISK"
    ld.size = size
    ld.energy = energy
    ld.color = (1.0, .96, .9)
    ob = bpy.data.objects.new("key", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos
    look_at(ob, target)
    # a broad, faint fill from the right so the shadow side never goes dead
    fd = bpy.data.lights.new("fill", "AREA")
    fd.size = 3
    fd.energy = energy * .12
    fd.color = (.95, .97, 1.0)
    fo = bpy.data.objects.new("fill", fd)
    bpy.context.scene.collection.objects.link(fo)
    fo.location = Vector(target) + Vector((2.6, -2.2, .9))
    look_at(fo, target)
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(pos, look, fov_y, res, ortho_width=None):
    """Perspective with a vertical field of view, or orthographic `ortho_width` metres across."""
    cd = bpy.data.cameras.new("cam")
    if ortho_width:
        cd.type = "ORTHO"
        cd.sensor_fit = "HORIZONTAL"
        cd.ortho_scale = ortho_width
    else:
        cd.sensor_fit = "VERTICAL"
        cd.angle_y = math.radians(fov_y)
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos
    look_at(ob, look)
    sc = bpy.context.scene
    sc.camera = ob
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    return ob


def shadow_catcher(size=6.0):
    me = bpy.data.meshes.new("floor")
    s = size / 2
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("floor", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.is_shadow_catcher = True
    return ob


def render(name):
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def mesh_obj(name, verts, faces, uvs=None, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uvs is not None:
        uv = me.uv_layers.new(name="UVMap")
        loop_vi = np.empty(len(me.loops), dtype=np.int64)
        me.loops.foreach_get("vertex_index", loop_vi)
        uv.data.foreach_set("uv", np.asarray(uvs, float)[loop_vi].ravel())
    if smooth:
        me.shade_smooth()
    if mat:
        me.materials.append(mat)
    return link(bpy.data.objects.new(name, me))


def instance(src, loc, rot=(0, 0, 0), scale=1.0, name=None):
    """A linked duplicate (shares the mesh): cheap for hundreds of marigolds."""
    ob = src.copy()
    ob.name = name or src.name
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = (scale,) * 3 if np.isscalar(scale) else scale
    ob.hide_render = False          # the source is usually hidden; its copies are not
    return link(ob)


# ------------------------------------------------------------------ materials
def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    return m, nt, bsdf


def mat_bamboo(tone="#C9A063"):
    """Dry bamboo: warm straw with fine lengthwise streaks, darker node rings, a soft waxy sheen."""
    m, nt, b = _mat("bamboo")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    # node rings every ~9 cm along the pole's own axis (object z)
    ring = N.new("ShaderNodeMath"); ring.operation = "MULTIPLY"; ring.inputs[1].default_value = 1 / .09
    L.new(sep.outputs["Z"], ring.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"
    L.new(ring.outputs[0], fr.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = .0, (1, 1, 1, 1)
    cr.elements[1].position, cr.elements[1].color = .93, (1, 1, 1, 1)
    e = cr.elements.new(.965); e.color = (.42, .3, .18, 1)
    e = cr.elements.new(.99); e.color = (1.05, 1.0, .9, 1)
    L.new(fr.outputs[0], ramp.inputs[0])
    # lengthwise streaks
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (60, 60, 1.5)
    L.new(tc.outputs["Object"], mp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 6
    L.new(mp.outputs[0], nz.inputs[0])
    st = N.new("ShaderNodeValToRGB")
    st.color_ramp.elements[0].color = hexrgb("#A47E45")
    st.color_ramp.elements[1].color = hexrgb(tone)
    L.new(nz.outputs["Fac"], st.inputs[0])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
    L.new(st.outputs["Color"], mix.inputs[6]); L.new(ramp.outputs["Color"], mix.inputs[7])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .48
    b.inputs["Coat Weight"].default_value = .25
    b.inputs["Coat Roughness"].default_value = .35
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .25; bump.inputs["Distance"].default_value = .002
    L.new(nz.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_brass():
    m, nt, b = _mat("brass")
    b.inputs["Base Color"].default_value = hexrgb("#D9A653")
    b.inputs["Metallic"].default_value = 1.0
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = .18; rr.inputs["To Max"].default_value = .32
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m


def mat_succulent():
    """Sijou stems: a waxy mottled green, paler streaks running up the ribs, a soft bloom on the surface."""
    m, nt, b = _mat("sijou")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (40, 40, 4)
    L.new(tc.outputs["Object"], mp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 8
    L.new(mp.outputs[0], nz.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hexrgb("#2E5E1C")
    ramp.color_ramp.elements[1].color = hexrgb("#6E9E3E")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = .35, .7
    L.new(nz.outputs["Fac"], ramp.inputs[0])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .5
    b.inputs["Coat Weight"].default_value = .3
    b.inputs["Coat Roughness"].default_value = .45
    b.inputs["Subsurface Weight"].default_value = .06
    b.inputs["Subsurface Radius"].default_value = (.004, .008, .003)
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .3; bump.inputs["Distance"].default_value = .001
    L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_plain(name, color, rough=.6, sheen=0.0, subsurface=0.0, metallic=0.0):
    m, nt, b = _mat(name)
    b.inputs["Base Color"].default_value = hexrgb(color) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if subsurface:
        b.inputs["Subsurface Weight"].default_value = subsurface
        b.inputs["Subsurface Radius"].default_value = (.01, .006, .003)
    return m


def image_from_array(name, arr):
    """arr: H x W x 4 float sRGB (0..1), row 0 = top. Stored as a packed sRGB image."""
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(arr[::-1]).astype(np.float32).ravel())
    im.pack()
    return im


def dokhona_texture(w=2048, h=384, ground="#EE8A1E", border="#0F7A4A", thread="#F2C318", buti="#0F7A4A", edges=("top", "bottom")):
    """Marigold dokhona: a woven ground with a fine weave, a deep green agor border on both edges
    (gold lines and a row of small step-diamonds), and sparse small butis. Returns (colour, height)."""
    def c(hx):
        return np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    Y, X = np.mgrid[0:h, 0:w]
    col = np.zeros((h, w, 3)) + c(ground)
    hgt = .5 + .25 * np.sin(X * np.pi / 2) * np.sin(Y * np.pi / 2)            # plain weave
    col *= (.94 + .06 * (np.sin(X * np.pi / 2) > 0))[..., None]
    for y0 in [y for e, y in (("top", 14), ("bottom", h - 14 - 66)) if e in edges]:
        band = (Y >= y0) & (Y < y0 + 66)
        col[band] = c(border)
        for yy in (y0 + 6, y0 + 58):
            ln = (Y >= yy) & (Y < yy + 3)
            col[ln] = c(thread); hgt[ln] += .6
        # step diamonds in gold thread
        cx = (X % 34) - 17
        cy = Y - (y0 + 33)
        d = np.abs(cx) + np.abs(cy)
        dm = band & (((d >= 9) & (d <= 12)) | (d <= 3))
        col[dm] = c(thread); hgt[dm] += .8
    # small butis on the ground
    if buti:
        gy = ((Y - 120) % 60) - 30
        gx = ((X + 30 * (((Y - 120) // 60) % 2)) % 60) - 30
        bm = (np.abs(gx) + np.abs(gy) <= 5) & (Y > 100) & (Y < h - 100)
        col[bm] = c(buti); hgt[bm] += .7
    rgba = np.dstack([col, np.ones((h, w))])
    hrgba = np.dstack([np.repeat(np.clip(hgt / 2, 0, 1)[..., None], 3, 2), np.ones((h, w))])
    return rgba, hrgba


def aronai_texture(L_mm, W_mm, ppm=6.0, seed=0, u0=0.0, u1=1.0):
    """One whole handloom aronai, thread by thread, mapped over the cloth: u along its length (0..1, one
    end to the other), v across its width. u0..u1 picks the part of the cloth this texture covers
    (e.g. .5..1 for a hanging end).
    - plain-weave body in deep red: warp and weft threads of slightly different reds, slubs
    - the real aronai plan in gold extra-weft (raised floats): diamond chain at the outer edges, tall
      fern-hatched hajw sawtooth on both edges, a double rule, a column of peacock-eye medallions with
      paired small diamonds between, and plain striped ends for the fringe
    Returns (colour, height, thread-mask) as H x W x 4 float arrays (row 0 = v 1)."""
    r = np.random.default_rng(seed)
    w = int(round((u1 - u0) * L_mm * ppm))
    h = int(round(W_mm * ppm))
    col_ = lambda hx: np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)]) / 255     # noqa: E731
    RED, RED2, YEL, GRN, DARK = col_("#A3121B"), col_("#B81C22"), col_("#E8B62A"), col_("#1D6B3A"), col_("#2A0E0C")
    X = np.arange(w)[None, :] / ppm + u0 * L_mm           # mm along the length (from end A)
    Y = np.arange(h)[:, None] / ppm                       # mm across
    X = np.broadcast_to(X, (h, w)); Y = np.broadcast_to(Y, (h, w))
    # thread spacing, mm: a real one (45 cm wide) has about a thousand warp threads; a small one here is
    # the same cloth in miniature, so its threads shrink with it
    pitch = min(.42, W_mm * .0032)
    wi = np.floor(Y / pitch).astype(int)                  # warp thread index (runs along the length)
    fi = np.floor(X / pitch).astype(int)                  # weft pick index
    over = (wi + fi) % 2 == 0                             # plain weave: warp on top here
    # per-thread shade, plus slubs (thicker, lighter stretches) along some threads
    warp_sh = r.normal(0, .05, wi.max() + 2)[wi]
    weft_sh = r.normal(0, .04, fi.max() + 2)[fi]
    slub = np.clip(np.sin(X * .9 + r.uniform(0, 6, wi.max() + 2)[wi] * 7) - .93, 0, 1) * 1.6
    col = np.where(over[..., None], RED, RED2) * (1 + np.where(over, warp_sh, weft_sh) + slub * .25)[..., None]
    # thread roundness: each crossing a little dome
    fx = (X / pitch) % 1 - .5; fy = (Y / pitch) % 1 - .5
    hgt = .45 + .22 * np.cos(np.pi * np.where(over, fy, fx)) + .1 * slub
    mask = np.zeros((h, w))

    def paint(m, c, lift=.45, floats=True):
        nonlocal col, hgt, mask
        if floats:      # extra-weft floats run across the width: brighter on their crowns, dark between picks
            sh = .86 + .2 * np.cos(np.pi * ((X / (pitch * 1.0)) % 1 - .5))
            cc = c[None, None, :] * sh[..., None]
        else:
            cc = c[None, None, :] * np.ones((h, w, 1))
        col = np.where(m[..., None], cc, col)
        hgt = np.where(m, hgt + lift, hgt)
        mask = np.where(m, 1.0, mask)

    # The real anatomy (references/bodo-research.md, "Anatomy of an aronai"), every motif snapped to the
    # weave's grid so its edges step like woven ones; one contrast thread (gold) on the red ground:
    #   outer edge: a chain of small diamonds | hajw agor: tall sawtooth triangles on both edges pointing
    #   in, filled with fern-like hatching | a thin double rule | centre column: peacock-eye medallions of
    #   dot rings and tiny diamonds round a flower, small paired motifs between | ends: plain ground with
    #   fine stripes, then the fringe (the borders and column stop before the ends)
    c = max(pitch * 2, W_mm * .011)                       # motif cell (a few threads)
    qX = (np.floor(X / c) + .5) * c                       # snapped to the cell grid
    qY = (np.floor(Y / c) + .5) * c
    e = np.minimum(X, L_mm - X)                           # mm from the nearer end
    body = e > W_mm * .62
    # ends: plain heading, then fine stripes across the cloth
    stripe = (e > W_mm * .1) & (e < W_mm * .5) & (((e - W_mm * .1) % (W_mm * .055)) < W_mm * .013)
    paint(stripe, YEL, .3)
    paint((e > W_mm * .56) & (e < W_mm * .58), YEL, .3)
    for edge in (0, 1):
        d = qY if edge == 0 else W_mm - qY                # distance in from this long edge
        dr = Y if edge == 0 else W_mm - Y
        paint(body & (dr < W_mm * .022), DARK, .15, False)            # selvedge
        # the outer chain of small diamonds
        per = W_mm * .05
        cx = (qX % per) - per / 2
        cy = d - W_mm * .048
        dm = np.abs(cx) + np.abs(cy)
        paint(body & (dm <= W_mm * .022) & (dm >= W_mm * .01), YEL, .4)
        paint(body & (dr > W_mm * .078) & (dr < W_mm * .088), YEL, .3)  # rule under the chain
        # hajw agor: tall triangles, base at the rule, apex well into the cloth, hatched like fern fronds
        base, top = W_mm * .095, W_mm * .3
        per = W_mm * .15
        tx = (qX % per) - per / 2
        hgt_ = (d - base) / (top - base)                  # 0 at the base, 1 at the apex
        half = per * .48 * (1 - hgt_)
        inside = body & (hgt_ >= 0) & (hgt_ <= 1) & (np.abs(tx) <= half)
        outline = inside & (np.abs(tx) >= half - c * 1.1)
        spine = inside & (np.abs(tx) < c * .6)
        frond = inside & ((((np.abs(tx) + (d - base) * .7) / (c * 2.2)) % 1) < .42)
        paint(outline | spine | frond, YEL, .45)
        # the thin double rule inside the hajw
        paint(body & (dr > W_mm * .315) & (dr < W_mm * .325), YEL, .3)
        paint(body & (dr > W_mm * .34) & (dr < W_mm * .35), YEL, .3)
    # centre column: medallions, alternating with small paired motifs
    P = W_mm * .5
    k = np.floor((X - W_mm * .62) / P)
    mx = ((X - W_mm * .62) % P) - P / 2
    mqx = ((qX - W_mm * .62) % P) - P / 2
    my = qY - W_mm / 2
    col_ok = body & (e > W_mm * .9)
    Rm = W_mm * .135
    rr = np.sqrt(mqx ** 2 + my ** 2)
    ang = np.arctan2(my, mqx)
    med = col_ok & (k % 2 == 0)
    # outer ring of dots, a solid ring, a ring of tiny diamonds, the flower at the centre
    dots = med & (np.abs(rr - Rm) < c * .8) & (((ang / (2 * np.pi) * 22) % 1) < .45)
    ring = med & (np.abs(rr - Rm * .78) < c * .55)
    tiny = med & (np.abs(rr - Rm * .55) < c * .9) & (((ang / (2 * np.pi) * 12) % 1) < .3)
    petal = med & (rr < Rm * .36) & (np.abs(np.cos(4 * ang)) * Rm * .36 > rr * .9)
    eye = med & (rr < c * 1.1)
    paint(dots | ring | tiny | petal | eye, YEL, .5)
    # between medallions: a pair of small stepped diamonds side by side (birds' place in the real ones)
    pair = col_ok & (k % 2 == 1)
    for sgn in (-1, 1):
        dd = np.abs(mqx) + np.abs(my - sgn * W_mm * .07)
        paint(pair & (dd <= W_mm * .05) & (dd >= W_mm * .028), YEL, .45)
        paint(pair & (dd <= c * .8), YEL, .4)
    del mx
    col = np.clip(col, 0, 1)
    to4 = lambda a: np.dstack([a, np.ones((h, w))])       # noqa: E731
    g = np.clip(hgt / 1.4, 0, 1)
    return to4(col[::-1]), to4(np.repeat(g[::-1, :, None], 3, 2)), to4(np.repeat(mask[::-1, :, None], 3, 2))


def mat_aronai(name, L_mm, W_mm, **kw):
    """Handloom aronai: cotton body (matte, soft sheen at grazing light, a little light through it), the
    yellow and green extra-weft threads silkier (smoother, brighter sheen), weave bump at thread scale."""
    c, hg, mk = aronai_texture(L_mm, W_mm, **kw)
    ims = {}
    for k, arr in (("col", c), ("hgt", hg), ("msk", mk)):
        im = image_from_array(f"{name}-{k}", arr)
        if k != "col":
            im.colorspace_settings.name = "Non-Color"
        ims[k] = im
    m, nt, b = _mat(name)
    N, L = nt.nodes, nt.links
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    t = {}
    for k, im in ims.items():
        n = N.new("ShaderNodeTexImage"); n.image = im; n.interpolation = "Cubic"; n.extension = "EXTEND"
        L.new(uv.outputs[0], n.inputs[0]); t[k] = n
    L.new(t["col"].outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = .7; rr.inputs["To Max"].default_value = .42
    L.new(t["msk"].outputs["Color"], rr.inputs["Value"]); L.new(rr.outputs["Result"], b.inputs["Roughness"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .55; bump.inputs["Distance"].default_value = .0004
    L.new(t["hgt"].outputs["Color"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = .5
    b.inputs["Sheen Roughness"].default_value = .45
    b.inputs["Sheen Tint"].default_value = hexrgb("#FF9C84")
    b.inputs["Subsurface Weight"].default_value = .1
    b.inputs["Subsurface Radius"].default_value = (.003, .001, .0008)
    return m


def mat_cloth(name="dokhona", **kw):
    """Silk-cotton dokhona: the woven texture, a weave bump, sheen and a little light through the cloth."""
    rgba, hrgba = dokhona_texture(**kw)
    im = image_from_array(f"{name}-col", rgba)
    hm = image_from_array(f"{name}-hgt", hrgba)
    hm.colorspace_settings.name = "Non-Color"
    m, nt, b = _mat(name)
    N, L = nt.nodes, nt.links
    t = N.new("ShaderNodeTexImage"); t.image = im; t.interpolation = "Cubic"
    th = N.new("ShaderNodeTexImage"); th.image = hm
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    L.new(uv.outputs[0], t.inputs[0]); L.new(uv.outputs[0], th.inputs[0])
    L.new(t.outputs["Color"], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .35; bump.inputs["Distance"].default_value = .0006
    L.new(th.outputs["Color"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = .62
    b.inputs["Sheen Weight"].default_value = .6
    b.inputs["Sheen Roughness"].default_value = .35
    b.inputs["Sheen Tint"].default_value = hexrgb("#FFE2B0")
    b.inputs["Subsurface Weight"].default_value = .08
    b.inputs["Subsurface Radius"].default_value = (.004, .002, .001)
    return m


def mat_marigold():
    """Petals: colour from the per-vertex 'shade' (darker deep in the head), a per-flower hue shift from
    orange to yellow, sheen and light passing through."""
    m, nt, b = _mat("marigold")
    N, L = nt.nodes, nt.links
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "shade"
    oi = N.new("ShaderNodeObjectInfo")
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"
    base.inputs[6].default_value = hexrgb("#F07A12")
    base.inputs[7].default_value = hexrgb("#FFC21A")
    L.new(oi.outputs["Random"], base.inputs["Factor"])
    half = N.new("ShaderNodeMath"); half.operation = "MULTIPLY"; half.inputs[1].default_value = .45
    L.new(at.outputs["Fac"], half.inputs[0])
    sh = N.new("ShaderNodeMix"); sh.data_type = "RGBA"; sh.blend_type = "MULTIPLY"
    L.new(half.outputs[0], sh.inputs["Factor"])
    L.new(base.outputs[2], sh.inputs[6])
    sh.inputs[7].default_value = hexrgb("#9A3A08")
    L.new(sh.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .55
    b.inputs["Sheen Weight"].default_value = .7
    b.inputs["Sheen Tint"].default_value = hexrgb("#FFD27A")
    b.inputs["Subsurface Weight"].default_value = .25
    b.inputs["Subsurface Radius"].default_value = (.006, .003, .001)
    return m


def mat_flame():
    """A lamp flame: hot white-gold at the core, orange at the rim, its edges fading into the air."""
    m, nt, b = _mat("flame")
    N, L = nt.nodes, nt.links
    out = N["Material Output"]
    N.remove(b)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = .35
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (1.0, .78, .36, 1)
    ramp.color_ramp.elements[1].color = (1.0, .36, .04, 1)
    L.new(lw.outputs["Facing"], ramp.inputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.7
    L.new(ramp.outputs["Color"], em.inputs["Color"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    inv = N.new("ShaderNodeMath"); inv.operation = "POWER"; inv.inputs[1].default_value = 1.6
    L.new(lw.outputs["Facing"], inv.inputs[0])
    L.new(inv.outputs[0], mix.inputs["Fac"])
    L.new(em.outputs[0], mix.inputs[1]); L.new(tr.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return m


def banana_leaf_texture(w=1024, h=256, seed=0):
    """Banana leaf, u along the leaf, v across: a bright young green fading darker at the margins, a pale
    midrib, fine parallel lateral veins, and tears along the veins (alpha 0) from the margin inward."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:h, 0:w]
    v = (Y / (h - 1)) * 2 - 1
    u = X / (w - 1)
    base = np.array([.25, .47, .13]) * (1 - .45 * np.abs(v))[..., None] + np.array([.1, .24, .06]) * (.45 * np.abs(v))[..., None]
    veins = .13 * np.cos((X - np.abs(v) * 90) * 2 * np.pi / 5) + .05 * np.cos((X - np.abs(v) * 90) * 2 * np.pi / 23)
    col = base * (1 + veins)[..., None]
    mid = np.exp(-(v / .03) ** 2)
    col = col * (1 - mid[..., None]) + np.array([.68, .76, .42]) * mid[..., None]
    alpha = np.ones((h, w))
    for _ in range(int(rng.integers(14, 22))):
        x0 = rng.uniform(.1, .95) * w
        side = 1 if rng.random() < .5 else -1
        depth = rng.uniform(.3, .95)
        # tears follow the veins: from the margin toward the midrib, slanting back toward the stem
        along = (X - x0) + (np.abs(v) - 1) * 90 * -1
        cut = (np.abs(along) < rng.uniform(1.2, 2.6)) & (np.sign(v) == side) & (np.abs(v) > 1 - depth)
        alpha[cut] = 0
    edge_brown = np.clip((np.abs(v) - .9) / .1, 0, 1) * .5
    col = col * (1 - edge_brown[..., None]) + np.array([.45, .36, .15]) * edge_brown[..., None]
    return np.dstack([np.clip(col, 0, 1), alpha])


def mat_leaf_tex(name, rgba, sss=.2, rough=.5):
    im = image_from_array(f"{name}-tex", rgba)
    m, nt, b = _mat(name)
    N, L = nt.nodes, nt.links
    t = N.new("ShaderNodeTexImage"); t.image = im; t.interpolation = "Cubic"
    L.new(t.outputs["Color"], b.inputs["Base Color"])
    L.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = (.002, .006, .001)
    b.inputs["Sheen Weight"].default_value = .25
    m.surface_render_method = "DITHERED"
    return m


TEX = os.path.abspath(os.path.join(HERE, "..", "render3d", "tex"))


def mat_woven(band="band-scarlet", sheen="#FFC0A0", bump=.5):
    """An aronai woven band from design/render3d/tex: albedo for colour, height for the weave bump,
    and the thread mask where the gold zari is (metallic .9, roughness .3)."""
    m, nt, b = _mat(f"woven-{band}")
    N, L = nt.nodes, nt.links
    imgs = {}
    for kind in ("albedo", "height", "mask"):
        im = bpy.data.images.load(os.path.join(TEX, f"{band}-{kind}.png"), check_existing=True)
        if kind != "albedo":
            im.colorspace_settings.name = "Non-Color"
        t = N.new("ShaderNodeTexImage"); t.image = im; t.interpolation = "Cubic"
        imgs[kind] = t
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    for t in imgs.values():
        L.new(uv.outputs[0], t.inputs[0])
    L.new(imgs["albedo"].outputs["Color"], b.inputs["Base Color"])
    L.new(imgs["mask"].outputs["Color"], b.inputs["Metallic"])
    rr = N.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = .62; rr.inputs["To Max"].default_value = .3
    L.new(imgs["mask"].outputs["Color"], rr.inputs["Value"]); L.new(rr.outputs["Result"], b.inputs["Roughness"])
    bn = N.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump; bn.inputs["Distance"].default_value = .0006
    L.new(imgs["height"].outputs["Color"], bn.inputs["Height"]); L.new(bn.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = .55
    b.inputs["Sheen Tint"].default_value = hexrgb(sheen)
    b.inputs["Subsurface Weight"].default_value = .05
    return m


def mat_wood(base="#7A4A22", dark="#3E220C"):
    """Turned wood: long grain lines, a warm satin finish."""
    m, nt, b = _mat("wood")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 14)
    L.new(tc.outputs["Object"], mp.inputs[0])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 28
    wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 4
    L.new(mp.outputs[0], wv.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hexrgb(dark); ramp.color_ramp.elements[1].color = hexrgb(base)
    L.new(wv.outputs["Fac"], ramp.inputs[0])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .42
    b.inputs["Coat Weight"].default_value = .35
    b.inputs["Coat Roughness"].default_value = .3
    bn = N.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = .15
    L.new(wv.outputs["Fac"], bn.inputs["Height"]); L.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


def ribbon(name, pts, width, mat, normals=None, tex_len=None, thick=.0018, puff=.0, subdiv=1):
    """A cloth ribbon along points (m). normals: the ribbon's face normal per point (default: up).
    UV: u along the ribbon (in units of tex_len), v across. `puff` domes it softly across its width."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    normals = [Vector(v).normalized() for v in normals] if normals else [Vector((0, 0, 1))] * n
    verts, faces, uvs = [], [], []
    m_ = 7
    s_acc = 0.0
    for i, p in enumerate(pts):
        if i:
            s_acc += (p - pts[i - 1]).length
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        nm = normals[i]
        side = t.cross(nm).normalized()
        for j in range(m_):
            v = j / (m_ - 1) * 2 - 1
            verts.append(p + side * (v * width / 2) + nm * (puff * width * (1 - v * v)))
            uvs.append((s_acc / (tex_len or width * 9.8), (v + 1) / 2))
    for i in range(n - 1):
        for j in range(m_ - 1):
            a = i * m_ + j
            faces.append((a, a + m_, a + m_ + 1, a + 1))
    ob = mesh_obj(name, verts, faces, uvs=uvs, mat=mat)
    so = ob.modifiers.new("thick", "SOLIDIFY"); so.thickness = thick; so.offset = 0
    if subdiv:
        su = ob.modifiers.new("smooth", "SUBSURF"); su.levels = su.render_levels = subdiv
    return ob


def fringe(name, a, b, length, mat, n=40, r=.0012, droop=(0, 0, -1), jitter=.2, rng=None):
    """Threads hanging from the line a -> b (m): each a thin cord that falls and curls a little."""
    rng = rng or np.random.default_rng(1)
    a, b, d = Vector(a), Vector(b), Vector(droop).normalized()
    obs = []
    for k in range(n):
        p0 = a.lerp(b, (k + .5) / n)
        L = length * (1 + rng.uniform(-jitter, jitter))
        sway = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * L * .12
        pts = [p0 + d * (L * t) + sway * t * t for t in np.linspace(0, 1, 8)]
        obs.append(tube(f"{name}{k}", pts, [r] * 8, mat, sides=6))
    return obs


# ------------------------------------------------------------------ geometry
def leaf_along(name, p0, p1, p2, width, mat, n=60, m=11, cup=.25, droop=.0, tip_round=True, face=(0, -1, 0)):
    """A leaf following a quadratic curve p0 -> p2 (Blender coords, m). Width profile is an oblong paddle
    (banana) or a lance; `cup` folds it along the midrib (negative = arched, the halves drooping), and
    `droop` lets the outer margins hang down a little more toward the tip."""
    P0, P1, P2 = (Vector(p) for p in (p0, p1, p2))

    def at(t):
        return P0 * (1 - t) ** 2 + P1 * (2 * (1 - t) * t) + P2 * (t * t)
    verts, faces, uvs = [], [], []
    for i in range(n):
        t = i / (n - 1)
        c = at(t)
        tan = (at(min(1, t + .01)) - at(max(0, t - .01))).normalized()
        side = tan.cross(Vector(face))          # the blade opens toward `face` (the camera by default)
        if side.length < .1:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(tan).normalized()
        if tip_round:
            wd = width * min(1.0, (t / .08) ** .6) * math.sqrt(max(0.0, 1 - max(0.0, (t - .82) / .18) ** 2))
        else:
            wd = width * math.sin(math.pi * t) ** .8
        for j in range(m):
            sv = j / (m - 1) * 2 - 1
            p = c + side * (sv * wd / 2) + up * (-cup * wd * sv * sv - droop * wd * abs(sv) * t)
            verts.append(p)
            uvs.append((t, (sv + 1) / 2))
    for i in range(n - 1):
        for j in range(m - 1):
            a = i * m + j
            faces.append((a, a + m, a + m + 1, a + 1))
    return mesh_obj(name, verts, faces, uvs=uvs, mat=mat)


# ------------------------------------------------------------------ geometry (shapes)
def lathe(name, profile, mat, seg=64):
    """Revolve [(r, z), ...] (metres) round z."""
    verts, faces = [], []
    n = len(profile)
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for r, z in profile:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(seg):
        j = (i + 1) % seg
        for k in range(n - 1):
            faces.append((i * n + k, j * n + k, j * n + k + 1, i * n + k + 1))
    ob = mesh_obj(name, verts, faces, mat=mat)
    return ob


def tube(name, pts, radii, mat, sides=16, profile=None, cap=True):
    """A tube along a polyline of points with per-point radii. profile(theta) scales the radius
    round the circumference (e.g. ribs)."""
    pts = [Vector(p) for p in pts]
    verts, faces = [], []
    n = len(pts)
    prev_side = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = (t.cross(Vector((0, 0, 1))) if abs(t.z) < .95 else t.cross(Vector((1, 0, 0)))).normalized()
        if prev_side is not None and side.dot(prev_side) < 0:
            side = -side
        prev_side = side
        up = side.cross(t).normalized()
        for k in range(sides):
            th = 2 * math.pi * k / sides
            r = float(radii[i] * (profile(th) if profile else 1))
            verts.append(p + r * (math.cos(th) * side + math.sin(th) * up))
    for i in range(n - 1):
        for k in range(sides):
            a, b_ = i * sides + k, i * sides + (k + 1) % sides
            faces.append((a, b_, b_ + sides, a + sides))
    if cap:
        verts.append(pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * .5)
        c = len(verts) - 1
        for k in range(sides):
            faces.append(((n - 1) * sides + k, (n - 1) * sides + (k + 1) % sides, c))
    return mesh_obj(name, verts, faces, mat=mat)


def bamboo_pole(name, a, b, r, mat):
    """A straight bamboo culm from a to b (m), with slightly swollen nodes."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    n = max(8, int(L / .01))
    pts, radii = [], []
    for i in range(n + 1):
        t = i / n
        z = t * L
        node = math.exp(-(((z % .09) - .085) / .004) ** 2)
        pts.append((0, 0, z))
        radii.append(r * (1 + .06 * node))
    ob = tube(name, pts, radii, mat, sides=20)
    ob.location = a
    ob.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return ob


def marigold_mesh(petals=190, seed=0):
    """One marigold head, radius 1: ruffled, cupped petals on a dome, outer ones splayed. Vertex attribute
    'shade' is 1 deep in the head and 0 on the outer tips."""
    rng = np.random.default_rng(seed)
    bm = bmesh.new()
    shade_vals = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(petals):
        f = (i + .5) / petals
        phi = math.acos(1 - f * 1.55)                 # from the crown down past the equator
        th = i * golden
        d = Vector((math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi)))
        base = d * (.55 + .15 * rng.random())
        size = .42 + .22 * f + .08 * rng.random()
        # petal frame: out along d, curling back
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d).normalized()
        rot = Matrix.Rotation(rng.uniform(-1, 1) * .8, 3, d)
        side, up = rot @ side, rot @ up
        grid = []
        for a in range(4):            # along the petal
            row = []
            for b in range(5):        # across, ruffled edge
                u, v = a / 3, b / 4 - .5
                ruff = .08 * math.sin(b * 2.6 + i) * u
                p = base + d * (u * size * .55) + up * (u * u * size * .25 + v * v * .15 * size + ruff) + side * (v * size * (.55 + .2 * u))
                row.append(bm.verts.new(p))
                shade_vals.append(max(0.0, 1 - f * 1.3) * .6 + (1 - u) * .35)
            grid.append(row)
        for a in range(3):
            for b in range(4):
                bm.faces.new((grid[a][b], grid[a][b + 1], grid[a + 1][b + 1], grid[a + 1][b]))
    me = bpy.data.meshes.new("marigold")
    bm.to_mesh(me)
    bm.free()
    attr = me.attributes.new("shade", "FLOAT", "POINT")
    attr.data.foreach_set("value", np.array(shade_vals, np.float32))
    me.shade_smooth()
    return me


def leaf_mesh(L=1.0, W=.32, cup=.18, n=14, m=6, shape="lance", tip_bend=.15):
    """A leaf of length L along +x, base at the origin, cupped across and drooping at the tip."""
    verts, faces, uvs = [], [], []
    for i in range(n):
        t = i / (n - 1)
        if shape == "obovate":
            wd = W * math.sin(math.pi * min(1, t)) ** .5 * (.4 + .9 * t) * (1 - t ** 6)
        else:
            wd = W * math.sin(math.pi * t) ** .8
        for j in range(m):
            v = j / (m - 1) * 2 - 1
            verts.append((t * L, v * wd / 2, cup * wd * v * v - tip_bend * L * t * t))
            uvs.append((t, (v + 1) / 2))
    for i in range(n - 1):
        for j in range(m - 1):
            a = i * m + j
            faces.append((a, a + m, a + m + 1, a + 1))
    me = bpy.data.meshes.new("leaf")
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    uv.data.foreach_set("uv", np.array(uvs, float)[lv].ravel())
    me.shade_smooth()
    return me


# ------------------------------------------------------------------ cloth
def cloth_strip(name, A, B, length, width, mat, nx=140, ny=26, gather=.28, sag_dir=(0, 0, -1), frames=90,
                shrink=0.0, uv_repeat=1.0, colliders=(), across=None, bend=.6, pin_top=False, side_gather=1.0,
                u_gather=False):
    """A strip of cloth pinned at both ends at A and B (Blender coords, m), gathered at its ends so it
    falls into festoon folds between them, simulated, then frozen. `length` is the flat cloth length,
    longer than |AB|, so it sags. `across` is the direction of the cloth's width at the pins
    (default: straight down, a hanging swag)."""
    A, B = Vector(A), Vector(B)
    span = (B - A).length
    ax = (B - A).normalized()
    wdir = Vector(across).normalized() if across else Vector(sag_dir).normalized()
    wdir = (wdir - ax * wdir.dot(ax)).normalized()
    verts_rest, verts_start, faces, uvs, pins = [], [], [], [], []
    for i in range(nx):
        t = i / (nx - 1)
        for j in range(ny):
            s = j / (ny - 1)
            # rest: the flat cloth, length x width
            verts_rest.append(A + ax * (t * length) + wdir * (s * width))
            # start: compressed into the span, the ends gathered up tight toward the top edge (the pins)
            if u_gather:     # a swag: the drop shortens smoothly toward both ends, so the hem hangs in a U
                g = gather + (1 - gather) * math.sin(math.pi * t) ** .9
            else:
                g = gather + (1 - gather) * min(1.0, min(t, 1 - t) / .12)
            verts_start.append(A + ax * (t * span) + wdir * (s * width * g))
            uvs.append((t * uv_repeat * length / .4, s))
            # pins: the gathered ends (down to side_gather of the drop), and the whole top edge for a valance
            if (i in (0, nx - 1) and s <= side_gather) or (pin_top and j == 0):
                pins.append(len(verts_rest) - 1)
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            faces.append((a, a + ny, a + ny + 1, a + 1))
    # the mesh starts compressed into the span with gathered ends; a negative shrink grows its rest
    # lengths back to the full cloth length, so it sags and falls into folds between the pins
    ob = mesh_obj(name, verts_start, faces, uvs=uvs, mat=mat)
    if shrink == 0.0:
        shrink = -(length / span - 1)
    vg = ob.vertex_groups.new(name="pin")
    vg.add(pins, 1.0, "REPLACE")
    mod = ob.modifiers.new("cloth", "CLOTH")
    cs = mod.settings
    cs.quality = 10
    cs.mass = .12
    cs.air_damping = 2.0
    cs.tension_stiffness = cs.compression_stiffness = 20
    cs.shear_stiffness = 6
    cs.bending_stiffness = bend
    cs.vertex_group_mass = "pin"
    cs.pin_stiffness = 1.0
    cs.shrink_min = max(shrink, -.95)
    mod.collision_settings.distance_min = .003
    mod.collision_settings.use_self_collision = False
    mod.point_cache.frame_start = 1
    mod.point_cache.frame_end = frames
    for c in colliders:
        if not any(m.type == "COLLISION" for m in c.modifiers):
            cm = c.modifiers.new("collision", "COLLISION")
            c.collision.thickness_outer = .004
    return ob, frames


def simulate_and_freeze(objs_frames):
    """Run every cloth to its last frame, then replace each object's mesh with the result and add a
    little thickness and smoothing."""
    sc = bpy.context.scene
    last = max(f for _, f in objs_frames)
    sc.frame_start, sc.frame_end = 1, last
    for f in range(1, last + 1):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    for ob, _ in objs_frames:
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        ob.modifiers.clear()
        ob.shape_key_clear()
        old = ob.data
        ob.data = me
        bpy.data.meshes.remove(old)
        me.shade_smooth()
        so = ob.modifiers.new("thick", "SOLIDIFY")
        so.thickness = .0015
        su = ob.modifiers.new("smooth", "SUBSURF")
        su.levels = su.render_levels = 1
    sc.frame_set(last)
