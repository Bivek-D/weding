"""Publish three.js renders (out/*.png) into the site as WebP, with the names the CSS expects.
Mirrored right-hand bow pieces are made here, and the bow tails get their V-cut ends.
Run with the scratch venv:  python publish.py"""
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
ART = os.path.abspath(os.path.join(HERE, "..", "..", "site", "public", "art"))


def save(img, name, q=90):
    img.save(os.path.join(ART, name), quality=q, method=5)
    print("published", name, img.size)


def vcut(img, tip, direction, depth=18, half=30):
    """Cut a V notch into a ribbon end: tip (x, y) on the end, direction = unit vector along the ribbon."""
    d = np.array(direction, float)
    d /= np.linalg.norm(d)
    n = np.array([-d[1], d[0]])
    t = np.array(tip, float)
    poly = [tuple(t - d * depth), tuple(t + n * half + d * 8), tuple(t - n * half + d * 8)]
    a = img.getchannel("A")
    ImageDraw.Draw(a).polygon(poly, fill=0)
    img.putalpha(a)
    return img


def autocrop(img, pad=6):
    """Trim the transparent margin round a render (keeps a few px so soft shadows aren't clipped)."""
    box = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


for name in os.listdir(OUT):
    if not name.endswith(".png"):
        continue
    job = name[:-4]
    img = Image.open(os.path.join(OUT, name)).convert("RGBA")
    if job in ("altar", "banana-l", "bush-l", "fold-aronai", "fold-dokhona", "fold-gamsa", "instruments", "meal", "lamps3", "knot", "plate"):
        img = autocrop(img)
    if job == "door-base":
        save(img.convert("RGB"), "door-base.webp")
    elif job == "bow-tail":
        img = vcut(img, (70, 300), (70 - 150, 300 - 140))
        save(img, "bow-tail.webp")
        save(img.transpose(Image.FLIP_LEFT_RIGHT), "bow-tail-r.webp")
    elif job in ("banana-l", "bush-l"):
        base = job[:-2]
        save(img, f"{base}-l.webp")
        save(img.transpose(Image.FLIP_LEFT_RIGHT), f"{base}-r.webp")
    elif job.startswith("edge-"):
        save(img.convert("RGB"), f"{job}.webp")
    elif job.startswith("band-"):
        save(img.convert("RGB"), f"{job}.webp")
    elif job == "bow-loop":
        save(img, "bow-loop.webp")
        save(img.transpose(Image.FLIP_LEFT_RIGHT), "bow-loop-r.webp")
    else:
        save(img, f"{job}.webp")
