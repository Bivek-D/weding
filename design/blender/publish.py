"""Publish Blender renders (out/*.png) into the site as WebP with the names the CSS expects.
Trims the transparent margin (keeping a few px for soft shadows); makes the mirrored -r versions.
Run with the project venv:  ..\\..\\..\\.cache\\venv\\Scripts\\python publish.py [name ...]"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
ART = os.path.abspath(os.path.join(HERE, "..", "..", "site", "public", "art"))
MIRROR = {"banana-l": "banana-r", "bush-l": "bush-r"}
NOCROP = {"lamp", "swag", "strand"}     # the page places these by their exact frames
RESIZE = {"strand": (40, 300)}          # rendered at 2x for clean edges, published at the page's size


def clean(img):
    """Zero the near-invisible alpha the shadow catcher leaves across the whole floor."""
    a = img.getchannel("A").point(lambda v: 0 if v < 5 else v)
    img.putalpha(a)
    return img


def autocrop(img, pad=10):
    # crop to the object and its stronger shadow; the faintest edge of the shadow can go
    box = img.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


names = sys.argv[1:] or [f[:-4] for f in os.listdir(OUT) if f.endswith(".png")]
for name in names:
    img = clean(Image.open(os.path.join(OUT, f"{name}.png")).convert("RGBA"))
    if name not in NOCROP:
        img = autocrop(img)
    if name in RESIZE:
        img = img.resize(RESIZE[name], Image.LANCZOS)
    dest = ART
    if name.startswith("step-"):
        # the timeline's objects: lifted off the paper by the page (Raised), so they live with the relief art,
        # and shown at about 44px, so 132px (3x) is plenty
        dest = os.path.join(ART, "relief")
        img.thumbnail((132, 132), Image.LANCZOS)
    img.save(os.path.join(dest, f"{name}.webp"), quality=88, method=6)
    print("published", f"{name}.webp", img.size)
    if name in MIRROR:
        img.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(ART, f"{MIRROR[name]}.webp"), quality=88, method=6)
        print("published", f"{MIRROR[name]}.webp (mirrored)")
