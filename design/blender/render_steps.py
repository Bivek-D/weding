"""The day's timeline: one small object for each moment, sitting on the gold thread (Cycles, GPU).
No floor shadow: the page lifts them off the paper itself (Raised), like the other beads.

Run:  blender.cmd -b -P render_steps.py -- arrive haba meal reception dinner
  step-arrive     guests arrive: a cup of tea on a folded aronai
  step-haba       Hathasuni Haba: the sijou in its round bamboo fence (the Bathou)
  step-meal       first meal: rice and a green chilli on a piece of banana leaf
  step-reception  reception: the kham drum
  step-dinner     dinner: a brass thali with rice and three bowls
publish.py puts them in public/art/relief/ as step-*.webp.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                      # noqa: E402
from mathutils import Euler             # noqa: E402

import studio as S                      # noqa: E402
from studio import P                    # noqa: E402
import render_objects as RO             # noqa: E402
import render_pandal as RP              # noqa: E402

rng = np.random.default_rng(8)
RES = (200, 200)


def shot(name, look, pos, fov=28, energy=190, dist=2.4):
    S.key_light(target=P(*look), dist=dist, size=dist * .7, energy=energy * (dist / 2.4) ** 2, az=-122, el=45)
    S.camera(P(*pos), P(*look), fov, RES)
    S.render(name)


def cm(profile, k=1.0):
    return [(r * .01 * k, y * .01 * k) for r, y in profile]


def arrive():
    S.reset(256)
    RO.fold_stack(40, 26, 3.2, 2, S.mat_woven("band-scarlet"), origin=(0, 0, 0), yaw=-.3, uv="wrap", tex_w=40 * 2.9, name="ar")
    china = S.mat_plain("china", "#F6F0E4", rough=.22, subsurface=.04)
    gold = S.mat_plain("rim", "#D9A84A", rough=.3, metallic=.9)
    y0, K = 7.0, 1.45
    sau = S.lathe("saucer", cm([(0, 0), (5, 0), (7.6, .9), (8.2, 1.4), (7.8, 1.5), (5, .7), (0, .6)], K), china, seg=64)
    sau.location = P(1, y0, 2)
    cup = S.lathe("cup", cm([(0, .6), (2.8, .6), (3.4, 1.3), (4.4, 4.2), (4.8, 6.6), (4.5, 6.7), (4.1, 4.4), (3.0, 1.6), (0, 1.5)], K), china, seg=64)
    cup.location = P(1, y0, 2)
    tea = S.lathe("tea", cm([(0, 5.6), (4.25, 5.6)], K), S.mat_plain("tea", "#8A4A16", rough=.08), seg=48)
    tea.location = P(1, y0, 2)
    S.tube("cup-rim", [P(1 + 4.65 * K * math.cos(a), y0 + 6.65 * K, 2 + 4.65 * K * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 65)],
           [.0011 * K] * 65, gold, sides=8, cap=False)
    # the handle, on the right
    S.tube("handle", [P(1 + x * K, y0 + y * K, 2) for x, y in ((4.4, 5.4), (6.6, 5.2), (7.2, 3.6), (6.0, 2.4), (4.0, 2.4))],
           [.0055 * K] * 5, china, sides=12)
    shot("step-arrive", (0, 8, 0), (0, 62, 96))


def haba():
    S.reset(256)
    m_stem = S.mat_succulent()
    m_leaf = S.mat_plain("sijou-leaf", "#4F8A2A", rough=.45, subsurface=.15)
    S.lathe("soil", [(0, .003), (.23, .003), (.235, .025), (.22, .03), (0, .032)], S.mat_plain("soil", "#4A3322", rough=1))
    RP.fence(S.mat_bamboo(), S.mat_bamboo("#B98A4E"))
    RP.sijou(m_stem, m_leaf)
    shot("step-haba", (0, 36, 0), (0, 80, 210), fov=26, dist=3.0)


def meal():
    S.reset(256)
    tex = S.banana_leaf_texture(seed=12)
    tex[..., 3] = 1
    leaf_m = S.mat_leaf_tex("leaf", tex, sss=.1, rough=.32)
    leaf_m.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = .4
    S.leaf_along("leaf", P(-21, .4, 3), P(0, 1.2, -2), P(21, .4, 1), .24, leaf_m, n=50, m=13, cup=-.02, face=(0, 0, 1))
    rice = S.lathe("rice", [(r * .01, (6 * math.sqrt(max(0, 1 - (r / 11) ** 2)) + .6) * .01) for r in np.linspace(0, 11, 20)] + [(.11, .006)],
                   RO.mat_rice(), seg=56)
    rice.location = P(-3, .8, 1)
    rice.scale = (1.15, 1, 1)
    S.tube("chilli", [P(9 + 1.4 * k, 1.4 + .2 * math.sin(k), 8 - .5 * k + .05 * k * k) for k in range(9)],
           [.006 - .0004 * k for k in range(9)], S.mat_plain("chilli", "#3E8E2A", rough=.25), sides=12)
    shot("step-meal", (0, 3, 0), (0, 66, 84))


def reception():
    S.reset(256)
    drum = RO.kham_drum()
    drum.rotation_euler = Euler((0, math.pi / 2, .55))
    drum.location = P(0, 13.6, 0)
    shot("step-reception", (0, 12, 0), (0, 60, 125), fov=30)


def dinner():
    S.reset(256)
    brass = S.mat_brass()
    S.lathe("thali", cm([(0, 0), (16, 0), (19, 1), (21, 2.4), (21.6, 3.0), (20.8, 3.0), (18.5, 1.6), (0, 1.2)]), brass, seg=96)
    rice = S.lathe("rice", [(r * .01, (4.2 * math.sqrt(max(0, 1 - (r / 7.5) ** 2)) + 1.2) * .01) for r in np.linspace(0, 7.5, 16)] + [(.075, .012)],
                   RO.mat_rice(), seg=48)
    rice.location = P(-5, 0, 5)
    katori = cm([(0, 0), (2.6, 0), (4.4, 2.4), (4.8, 3.4), (4.4, 3.4), (3.8, 2.4), (0, .6)])
    for (x, z, col) in ((7, 6, "#E2A21E"), (8, -6, "#4E7A22"), (-6, -9, "#A8401C")):
        b = S.lathe("katori", katori, brass, seg=48)
        b.location = P(x, 1.2, z)
        f = S.lathe("dish", cm([(0, 2.9), (4.1, 2.9)]), S.mat_plain("dish", col, rough=.3, subsurface=.15), seg=32)
        f.location = P(x, 1.2, z)
    shot("step-dinner", (0, 2, 0), (0, 80, 80))


PARTS = {"arrive": arrive, "haba": haba, "meal": meal, "reception": reception, "dinner": dinner}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in (args or PARTS):
        PARTS[name]()
