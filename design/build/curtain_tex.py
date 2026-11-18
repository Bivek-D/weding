"""Exports the flat curtain cloth for the live (WebGL) curtain in site/src/lib/curtainGL.ts.

The shader rebuilds the same gather, folds, hem roll, tie-back and top-left light as
art_bodo2.curtain_frames(), but in real time, so the opening is smooth at any frame rate.

Writes (lossless WebP into site/public/art/curtain-gl/):
  cloth.webp  480 x 1388  RGB = woven colour, A = thread height / 2
  tie.webp    192 x  h    RGB = emerald aronai tie-back colour, A = 1

Run with the project venv:  ..\\..\\..\\.cache\\venv\\Scripts\\python curtain_tex.py
"""
import os

import numpy as np
from PIL import Image

import art_bodo2 as A

W, H = 640, 1388
HALF = W // 2
WC = int(HALF * 1.5)
OUT = os.path.join(A.OUT, "curtain-gl")
os.makedirs(OUT, exist_ok=True)


def rgba(col, a):
    arr = np.dstack([np.clip(col, 0, 1), np.clip(a, 0, 1)])
    return Image.fromarray((arr * 255 + .5).astype(np.uint8), "RGBA")


tex, thgt = A.curtain_texture(H, WC)
print("cloth height range", float(thgt.min()), float(thgt.max()))
rgba(tex, thgt / 2).save(os.path.join(OUT, "cloth.webp"), lossless=True, method=6)

tie_c, _ = A.aronai_band(int(W * .3), A.PAL["emerald"], A.PAL["ivory"], "slim")
rgba(tie_c, np.ones(tie_c.shape[:2])).save(os.path.join(OUT, "tie.webp"), lossless=True, method=6)
print("tie", tie_c.shape)
