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
NOCROP = {"cover-bow", "lamp", "swag", "strand", "aronai-badge", "aronai-hang", "cbow-body", "cbow-tail-l", "cbow-tail-r"}     # the page places these by their exact frames
# rendered at 2x for clean edges, published at the page's size (the aronai stay at 2x: the page sizes them)
RESIZE = {"strand": (40, 300)}


def clean(img):
    """Zero the near-invisible alpha the shadow catcher leaves across the whole floor."""
    a = img.getchannel("A").point(lambda v: 0 if v < 5 else v)
    img.putalpha(a)
    return img


# floor shadows that run past the sides of the frame: fade them out over this many px from each side
# (otherwise the image edge cuts them off in a hard vertical line), and soften them a little
SHADOW_FADE = {"altar": (140, .7)}
# floor shadows that should only pool round where the object stands (the catcher also darkens the whole
# floor in a rectangle that ends in hard lines): keep them inside an ellipse round the contact point
# (cx, cy, rx, ry as fractions of the image, strength)
SHADOW_POOL = {"banana-l": (.5, 1.0, .3, .2, .8), "bush-l": (.5, 1.0, .45, .3, .8)}


def _shadow_px(img):
    import numpy as np
    a = np.asarray(img).astype(np.float32)
    return a, (a[..., :3].max(axis=2) < 45) & (a[..., 3] < 250)


def pool_shadow(img, cx, cy, rx, ry, k):
    import numpy as np
    a, shadow = _shadow_px(img)
    h, w = a.shape[:2]
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((X - cx * w) / (rx * w)) ** 2 + ((Y - cy * h) / (ry * h)) ** 2)
    f = np.clip(1 - d, 0, 1)
    f = f * f * (3 - 2 * f)
    a[..., 3] = np.where(shadow, a[..., 3] * k * f, a[..., 3])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def fade_shadow(img, ramp, k):
    """Only the shadow-catcher pixels (black, partly transparent) fade; the objects are untouched."""
    import numpy as np
    a, shadow = _shadow_px(img)
    al = a[..., 3]
    x = np.arange(img.width, dtype=np.float32)
    side = np.clip(np.minimum(x, img.width - 1 - x) / ramp, 0, 1)
    side = side * side * (3 - 2 * side)                   # smooth
    al = np.where(shadow, al * k * side[None, :], al)
    a[..., 3] = al
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def autocrop(img, pad=10):
    # crop to the object and its stronger shadow; the faintest edge of the shadow can go
    box = img.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def crop_box(img, pad=10):
    box = img.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    l, t, r, b = box
    return max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)


def altar_tail():
    """The fence aronai's waving ends: out/altar-tail-00..31.png (full altar frames, only the ends visible)
    cropped to the area they ever cover and laid side by side in one strip. Prints where the strip sits
    on the published altar image, in % (for opening.module.css .fenceTail)."""
    frames = sorted(f for f in os.listdir(OUT) if f.startswith("altar-tail-"))
    imgs = [clean(Image.open(os.path.join(OUT, f)).convert("RGBA")) for f in frames]
    bb = None
    for im in imgs:
        b = im.getchannel("A").getbbox()
        bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    l, t, r, b = bb[0] - 2, bb[1] - 2, bb[2] + 2, bb[3] + 2
    w, h = r - l, b - t
    sheet = Image.new("RGBA", (w * len(imgs), h))
    for i, im in enumerate(imgs):
        sheet.paste(im.crop((l, t, r, b)), (i * w, 0))
    sheet.save(os.path.join(ART, "altar-tail.webp"), quality=90, method=6)
    al, at, ar, ab = crop_box(clean(Image.open(os.path.join(OUT, "altar.png")).convert("RGBA")))
    aw, ah = ar - al, ab - at
    print(f"published altar-tail.webp {sheet.size}, {len(imgs)} frames of {w}x{h}")
    print(f"  .fenceTail {{ left: {(l - al) / aw * 100:.3f}%; top: {(t - at) / ah * 100:.3f}%; "
          f"width: {w / aw * 100:.3f}%; height: {h / ah * 100:.3f}%; }}")


def cover_untie(cols=6):
    """out/cover-untie-00..29.png (320 x 500 each) into one grid sprite, cols across, for the page to step
    through (opening.module.css .untie)."""
    frames = sorted(f for f in os.listdir(OUT) if f.startswith("cover-untie-"))
    imgs = [clean(Image.open(os.path.join(OUT, f)).convert("RGBA")) for f in frames]
    w, h = imgs[0].size
    rows = -(-len(imgs) // cols)
    sheet = Image.new("RGBA", (w * cols, h * rows))
    for i, im in enumerate(imgs):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(os.path.join(ART, "cover-untie.webp"), quality=86, method=6)
    print(f"published cover-untie.webp {sheet.size}: {len(imgs)} frames of {w}x{h}, {cols} x {rows}")


names = sys.argv[1:] or [f[:-4] for f in os.listdir(OUT) if f.endswith(".png") and not f.startswith(("altar-tail-", "cover-untie-"))]
for name in names:
    if name == "altar-tail":
        altar_tail()
        continue
    if name == "cover-untie":
        cover_untie()
        continue
    img = clean(Image.open(os.path.join(OUT, f"{name}.png")).convert("RGBA"))
    if name not in NOCROP and not name.startswith("cover-"):     # the cover aronai parts share one frame
        img = autocrop(img)
    if name in SHADOW_FADE:
        img = fade_shadow(img, *SHADOW_FADE[name])
    if name in SHADOW_POOL:
        img = pool_shadow(img, *SHADOW_POOL[name])
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
