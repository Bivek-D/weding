"""Material maps for the three.js renders (render3d/): the woven patterns as raw albedo, height and
thread mask, with no lighting baked in. The renderer adds real light, sheen and metallic zari thread.

Writes PNGs into design/render3d/tex/. Run with the scratch venv:  python maps.py
"""
import os

import numpy as np
from PIL import Image

from art_bodo2 import (CH, CW, PAL, band_grid, buti, diamond_chain, hills, medallion, paste, render_grid, rgb)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.abspath(os.path.join(HERE, "..", "render3d", "tex"))
os.makedirs(TEX, exist_ok=True)


def save_maps(name, col, hgt, thread_hex):
    col = np.clip(col, 0, 1)
    Image.fromarray((col * 255).astype(np.uint8), "RGB").save(os.path.join(TEX, f"{name}-albedo.png"))
    h = (hgt - hgt.min()) / max(hgt.max() - hgt.min(), 1e-6)
    Image.fromarray((h * 255).astype(np.uint8), "L").save(os.path.join(TEX, f"{name}-height.png"))
    mask = np.all(np.abs(col - rgb(thread_hex)) < .02, axis=-1)
    Image.fromarray((mask * 255).astype(np.uint8), "L").save(os.path.join(TEX, f"{name}-mask.png"))
    print("maps", name, col.shape[1], "x", col.shape[0])


def door(w=393, h=1704):
    gw, gh = w // CW + 1, h // CH + 1
    g = np.zeros((gh, gw), bool)
    for j, yy in enumerate(range(4, gh, 40)):
        off = 0 if j % 2 else 19
        for xx in range(16 + off, gw - 26, 38):
            paste(g, medallion(12), yy, xx - 12)
        for xx in range(35 + off - 38, gw - 26, 38):
            paste(g, buti(4), yy + 7, xx - 5)
        paste(g, diamond_chain(gw), yy + 28, 0)
    hb = hills(gh, 9, 10, True).T
    g[:, :hb.shape[1]] |= hb[:gh]
    g[:, hb.shape[1]] = True
    col, hgt = render_grid(g, PAL["emerald"], PAL["gold"], pad_rows=0)
    save_maps("door", col[:h, :w], hgt[:h, :w], PAL["gold"])


def band(name, length, ground, thread, kind="full", vertical=False):
    g = band_grid(length // CW + 1, kind)
    col, hgt = render_grid(g, PAL[ground], PAL[thread])
    col, hgt = col[:, :length], hgt[:, :length]
    if vertical:
        col, hgt = np.transpose(col, (1, 0, 2)), hgt.T
    save_maps(name, col, hgt, PAL[thread])


if __name__ == "__main__":
    door()
    band("column", 1704, "scarlet", "gold", vertical=True)
    band("hem", 393, "scarlet", "gold")
    band("ribbon", 1200, "yellow", "scarlet")
    band("mat", 600, "marigold", "emerald")
    band("edge-emerald", 1200, "emerald", "ivory", kind="slim", vertical=True)
    band("edge-scarlet", 1200, "scarlet", "gold", kind="slim", vertical=True)
    for tone, thread in (("scarlet", "gold"), ("emerald", "ivory"), ("navy", "gold"), ("yellow", "scarlet"), ("magenta", "ivory")):
        band(f"band-{tone}", 1200, tone, thread)
