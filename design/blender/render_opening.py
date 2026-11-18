"""Opening-stage pieces, rendered in Blender (Cycles, GPU), shot straight on (orthographic) so they line up
with the header bar exactly.

Run:  blender.cmd -b -P render_opening.py -- swag strand
  swag    420 x 230: one scarlet jwmgra valance swag, gathered at both top corners, a gold agor border
          along its hem and a gold fringe hanging from it (four of them overlap across the top of the stage)
  strand  rendered 80 x 600, published at 40 x 300: a hanging marigold garland strand with leaves and a
          scarlet-and-gold thread tassel
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                      # noqa: E402
from mathutils import Euler, Vector     # noqa: E402

import studio as S                      # noqa: E402

rng = np.random.default_rng(31)


def swag():
    S.reset(320)
    # the cloth: scarlet ground, the agor border only on the edge that becomes the hem
    m = S.mat_cloth("jwmgra", ground="#C42A22", border="#8E1E18", thread="#E0B24E", buti=None, edges=("top",))
    m.node_tree.nodes["Principled BSDF"].inputs["Sheen Tint"].default_value = S.hexrgb("#FFC0A0")
    span, width = .40, .172
    A, B = Vector((-span / 2, 0, 0)), Vector((span / 2, 0, 0))
    ob, f = S.cloth_strip("swag", A, B, length=.5, width=width, mat=m, nx=130, ny=40, gather=.08, frames=120,
                          uv_repeat=.7, bend=.5, pin_top=True, u_gather=True)
    S.simulate_and_freeze([(ob, f)])
    # gold fringe along the hem, where the cloth actually ended up
    dg = S.bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    nx, ny = 130, 40
    # the hem row is the last one across (s = 1) in the simulated base mesh, before subdivision
    base = ob.data
    hem = [ob.matrix_world @ base.vertices[i * ny + ny - 1].co for i in range(nx)]
    ev.to_mesh_clear()
    zari = S.mat_plain("zari", "#D9A84A", rough=.35, metallic=.85)
    for k, p in enumerate(hem[3:-3:2]):
        L = .028 + rng.uniform(-.003, .003)
        pts = [p + Vector((rng.uniform(-.001, .001) * t, 0, -L * t)) for t in np.linspace(0, 1, 6)]
        S.tube(f"fr{k}", pts, [.0009] * 6, zari, sides=6)
    # straight on, the gathered top corners at the top edge of the frame
    S.key_light(target=(0, 0, -.1), dist=2.0, size=1.6, energy=120, az=-110, el=40)
    w = .44
    h = w * 230 / 420
    S.camera((0, -2, -h / 2 + .006), (0, 0, -h / 2 + .006), 0, (420, 230), ortho_width=w)
    S.render("swag")


def strand():
    S.reset(320)
    mari = S.marigold_mesh(seed=11)
    src = S.link(S.bpy.data.objects.new("mg", mari))
    src.data.materials.append(S.mat_marigold())
    src.hide_render = True
    leaf_m = S.mat_plain("leaf", "#3C7A2A", rough=.45, subsurface=.12)
    zari = S.mat_plain("zari", "#D9A84A", rough=.35, metallic=.85)
    red = S.mat_plain("red", "#C0281E", rough=.55, sheen=.3)
    # the thread, then the flowers threaded on it from the top down, a pair of leaves every few
    z, r, k = -.012, .0165, 0
    while z > -.50:
        x = .0012 * math.sin(k * 1.7)
        S.instance(src, (x, 0, z), rot=Euler((math.pi / 2 + rng.uniform(-.3, .3), rng.uniform(-.3, .3), rng.uniform(0, 6.3))), scale=r)
        if k % 4 == 2:
            for sgn in (-1, 1):
                S.leaf_along(f"lf{k}{sgn}", (x, -.002, z - r * .7), (x + sgn * .012, -.006, z - r * .9), (x + sgn * .02, -.004, z - r * 1.6),
                             .009, leaf_m, n=16, m=7, cup=.2, tip_round=False)
        z -= r * 1.62
        r = max(.0115, r * .975)
        k += 1
    S.tube("thread", [(0, .002, -.002), (0, .002, z - .01)], [.0008, .0008], zari, sides=6)
    # the tassel: a scarlet bead, a gold collar and scarlet-and-gold threads
    S.beads = None
    bead = S.lathe("bead", [(0, -.008), (.006, -.006), (.0075, 0), (.006, .006), (0, .008)], red, seg=24)
    bead.location = (0, 0, z - .012)
    col = S.lathe("collar", [(0, -.002), (.0045, -.002), (.0048, .002), (0, .002)], zari, seg=20)
    col.location = (0, 0, z - .023)
    for i, mt in enumerate((red, zari, red, red, zari, red, red)):
        a = (i - 3) * .0012
        S.tube(f"t{i}", [(a, 0, z - .024), (a * 1.8, 0, z - .045), (a * 2.2, rng.uniform(-.001, .001), z - .066)], [.0011] * 3, mt, sides=6)
    S.key_light(target=(0, 0, -.25), dist=2.2, size=1.4, energy=200, az=-110, el=40)
    w = .08
    h = w * 600 / 80
    S.camera((0, -2, -h / 2 + .004), (0, 0, -h / 2 + .004), 0, (80, 600), ortho_width=w)
    S.render("strand")


PARTS = {"swag": swag, "strand": strand}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in (args or PARTS):
        PARTS[name]()
