"""Bodo wedding invite: short FigCraft pass (design system + 4 key static mobile screens).

Follows .claude/skills/figcraft-designer. Typography roles and depth come from references/reference-spec.md,
which the user approved: Pinyon Script (names, section headings), Cormorant Garamond (body), Cinzel (spaced caps).
Art comes from art_bodo.py (design/art/). Run with any python3:  python3 build_bodo.py
"""
import colorsys
import os
import re
import sys

sys.path.insert(0, "/home/bivek/Documents/web_d/projects/dameo/design/build")
from fc import FigCraft  # noqa: E402

ROOT = "/home/bivek/Documents/web_d"
PRJ = f"{ROOT}/projects/wedding-invite"
FILE = f"{PRJ}/design/wedding-invite.figcraft"
ART = f"{PRJ}/design/art"
REVIEW = f"{PRJ}/exports/review"
SKILL = f"{ROOT}/.claude/skills/figcraft-designer/SKILL.md"
os.makedirs(REVIEW, exist_ok=True)

f = FigCraft()
LOG = []

# ============================================================== tokens
SPACING = [("0", 0), ("25", 2), ("50", 4), ("75", 8), ("100", 12), ("200", 16), ("300", 24), ("400", 32),
           ("500", 40), ("600", 48), ("700", 64), ("800", 80), ("900", 96)]
SP = {v: f"spacing/{k}" for k, v in SPACING}
RADIUS = [("0", 0), ("2", 2), ("4", 4), ("6", 6), ("8", 8), ("12", 12), ("16", 16), ("24", 24), ("full", 9999)]
RA = {v: f"radius/{k}" for k, v in RADIUS}

SHADES = {
    "Primary": "00 50 100 150 200 300 350 400 450 500 600 700 800 850 900 950 1000",
    "Secondary": "00 50 100 150 200 300 400 500 600 700 800 850 900 950 1000",
    "Accent": "00 50 100 150 200 300 400 500 600 700 800 850 900 950 1000",
    "Grayscale": "00 50 100 150 200 250 300 400 450 500 600 700 750 800 850 870 900 950 1000",
    "Red": "00 50 100 150 200 300 400 500 600 700 800 850 900 950 1000",
    "Green": "00 50 100 150 200 300 400 500 600 700 800 850 900 950 1000",
    "Yellow": "00 50 100 150 200 300 400 500 600 700 800 850 900 950 1000",
}
BASE = {"Primary": "#2F5B3A",     # Bodo green (buttons)
        "Secondary": "#D69E1E",   # dokhona mustard
        "Accent": "#7B2232",      # maroon
        "Red": "#B3362B", "Green": "#3C8A4E", "Yellow": "#D9A21B"}
LIGHT = {"00": .97, "50": .94, "100": .89, "150": .84, "200": .78, "250": .73, "300": .68, "350": .63,
         "400": .58, "450": .53, "600": .40, "700": .32, "750": .27, "800": .22, "850": .17, "870": .14,
         "900": .11, "950": .07, "1000": .035}
# warm linen neutrals on the light end, the allowed dark backgrounds on the dark end
GRAY = {"00": "#FBF5EA", "50": "#F6EAD2", "100": "#EEDFC2", "150": "#E6D3B2", "200": "#D9C4A0",
        "250": "#CBB591", "300": "#BCA582", "400": "#A08A69", "450": "#8E7859", "500": "#6E5A47",
        "600": "#5E4C3C", "700": "#4A3B2F", "750": "#313131", "800": "#272727", "850": "#1F1F1F",
        "870": "#181818", "900": "#131209", "950": "#0B0A06", "1000": "#000000"}


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def rgbhex(c):
    return "#" + "".join("%02X" % round(max(0, min(1, v)) * 255) for v in c)


def shade(base, key):
    if key == "500":
        return base.upper()
    h, l, s = colorsys.rgb_to_hls(*hexrgb(base))
    tl = LIGHT[key]
    return rgbhex(colorsys.hls_to_rgb(h, tl, s * (0.75 if tl > 0.9 or tl < 0.1 else 0.92)))


CORE = {}
for pal, keys in SHADES.items():
    for k in keys.split():
        CORE[f"{pal}/{k}"] = GRAY[k] if pal == "Grayscale" else shade(BASE[pal], k)
ALPHA = {"700-16": .16, "700-24": .24, "700-40": .40, "700-64": .64, "700-80": .80}
for k, a in ALPHA.items():
    CORE[f"Grayscale-Alpha/{k}"] = GRAY["700"] + "%02X" % round(a * 255)

SYSTEM = []
sec = open(SKILL).read().split("#### Layer 2")[1]
for m in re.finditer(r"^\| ((?:Border|Surface|Action|Text|Icon|Overlay)/[^|]+?) \| ([A-Za-z-]+/[\w-]+) \|", sec, re.M):
    SYSTEM.append([m.group(1).strip(), m.group(2).strip()])
# roles this card needs beyond the base list
SYSTEM += [["Surface/Brand", "Secondary/600"], ["Text/Accent", "Accent/300"], ["Border/Brand", "Secondary/500"]]
DARK = dict(SYSTEM)


def mirror(alias):
    pal, k = alias.split("/")
    if pal == "Grayscale-Alpha":
        return alias
    keys = [int(x) for x in SHADES[pal].split()]
    best = min(keys, key=lambda x: abs(x - (1000 - int(k))))
    return f"{pal}/{'00' if best == 0 else best}"


LIGHT_MAP = {n: mirror(a) for n, a in SYSTEM}
LIGHT_MAP.update({  # the linen day card
    "Surface/Primary": "Grayscale/50", "Surface/Primary-subtle": "Grayscale/00",
    "Surface/Primary-Hover": "Grayscale/100", "Surface/Primary-Selected": "Grayscale/150",
    "Surface/Secondary": "Grayscale/100", "Surface/Secondary-Subtle": "Grayscale/100",
    "Surface/Secondary-Hover": "Grayscale/150", "Surface/Secondary-Selected": "Grayscale/200",
    "Surface/Brand": "Secondary/500", "Surface/Accent": "Accent/500", "Surface/Accent-subtle": "Accent/100",
    "Text/Primary": "Grayscale/700", "Text/Secondary": "Grayscale/600", "Text/Tertiary": "Grayscale/500",
    "Text/Primary-Subtle": "Grayscale/500", "Text/Primary-Disabled": "Grayscale/300",
    "Text/Secondary-Disabled": "Grayscale/400", "Text/Inverted": "Grayscale/00", "Text/Accent": "Accent/500",
    "Text/Error": "Red/600",
    "Action/Primary": "Primary/500", "Action/Primary-Hover": "Primary/800", "Action/Primary-Click": "Primary/850",
    "Action/Primary-Disabled": "Grayscale/150",
    "Action/Error": "Red/500", "Action/Error-Hover": "Red/600", "Action/Error-Disabled": "Grayscale/150",
    "Action/Warning - Disabled": "Grayscale/150",
    "Action/Secondary": "Secondary/400", "Action/Secondary-Hover": "Secondary/300",
    "Action/Secondary-Click": "Secondary/200",
    "Border/Primary": "Grayscale/200", "Border/Primary-light": "Grayscale/150", "Border/Secondary": "Grayscale/250",
    "Border/Action-Primary": "Primary/500", "Border/Action-Secondary": "Secondary/600", "Border/Brand": "Secondary/500",
    "Icon/Default": "Grayscale/700", "Icon/Secondary": "Grayscale/600", "Icon/Subtle": "Grayscale/500",
})


def resolve(token, mode="Light"):
    return CORE[(LIGHT_MAP if mode == "Light" else DARK)[token]]


def scopes_for(name):
    g = name.split("/")[0]
    return {"Text": ["TEXT_FILL"], "Border": ["STROKE_COLOR"], "Icon": ["SHAPE_FILL", "STROKE_COLOR"]}.get(
        g, ["FRAME_FILL", "SHAPE_FILL"])


PS, CG, CZ = "Pinyon Script", "Cormorant Garamond", "Cinzel"
STYLES = [  # name, family, weight, size, line height, letter spacing
    ("Heading/Heading 1", PS, "Regular", 60, 60, 0), ("Heading/Heading 2", PS, "Regular", 48, 48, 0),
    ("Heading/Heading 3", PS, "Regular", 36, 40, 0), ("Heading/Heading 4", CG, "Medium", 30, 36, 0),
    ("Heading/Heading 5", CG, "Medium", 24, 32, 0), ("Heading/Heading 6", CG, "SemiBold", 20, 28, 0),
    ("Title/Title 1", CG, "SemiBold", 20, 28, 0), ("Title/Title 2", CG, "SemiBold", 18, 28, 0),
    ("Title/Title 3", CG, "SemiBold", 16, 24, 0), ("Title/Title 4", CG, "SemiBold", 14, 20, 0),
    ("Title/Title 5", CG, "SemiBold", 12, 16, 0),
    ("Body/Body 1", CG, "SemiBold", 16, 24, 0), ("Body/Body 2", CG, "Medium", 16, 24, 0),
    ("Body/Body 3", CG, "Regular", 16, 24, 0), ("Body/Body 4", CG, "SemiBold", 14, 20, 0),
    ("Body/Body 5", CG, "Medium", 14, 20, 0), ("Body/Body 6", CG, "Regular", 14, 20, 0),
    ("Body/Body 7", CG, "Medium", 18, 28, 0),     # added: running text on the card (Cormorant reads small)
    ("Button/Button-lg", CZ, "Bold", 18, 28, 10), ("Button/Button-md", CZ, "Bold", 16, 24, 10),
    ("Button/Button-sm", CZ, "Bold", 14, 20, 10), ("Button/Button-Xsm", CZ, "Bold", 12, 16, 10),
    ("Caption/Caption 1", CG, "Medium", 14, 20, 0), ("Caption/Caption 2", CG, "Regular", 14, 20, 0),
    ("Caption/Caption 3", CZ, "Bold", 12, 16, 20), ("Caption/Caption 4", CZ, "Regular", 12, 16, 15),
    ("Caption/Caption 5", CG, "Regular", 12, 16, 0),
]
STYLE_ID = {}

# ============================================================== helpers


def mk(type_, parent=None, name=None, text=None, **props):
    p = {"type": type_, "select": False}
    if parent is not None:
        p["parent"] = parent
    if name:
        p["name"] = name
    if text is not None:
        p["text"] = text
    for k in ("x", "y", "width", "height", "path"):
        if k in props:
            p[k] = props.pop(k)
    if props:
        p["props"] = props
    return f.cmd("node.create", **p)["id"]


def setp(ids, **props):
    return f.tool("set_properties", ids=ids if isinstance(ids, list) else [ids], props=props)


def get(i, depth=1):
    return f.tool("get_node", id=i, depth=depth)


def bind(ids, field, var):
    f.cmd("variable.bind", ids=ids if isinstance(ids, list) else [ids], field=field, variable=var)


def tokens(i, gap=None, pad=None, radius=None, fill=None, stroke=None):
    if gap is not None:
        bind(i, "gap", SP[gap])
    if pad is not None:
        for side, v in zip(("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"), pad):
            bind(i, side, SP[v])
    if radius is not None:
        bind(i, "cornerRadius", RA[radius])
    if fill:
        bind(i, "fill", fill)
    if stroke:
        bind(i, "stroke", stroke)


def box(parent, name, layout="vertical", gap=0, pad=0, fill=None, stroke=None, radius=0, sw=1,
        sizing=("hug", "hug"), **props):
    pads = pad if isinstance(pad, list) else [pad] * 4
    pr = dict(layout=layout, gap=gap, padding=pads, clip=False, fill=None, cornerRadius=radius,
              sizingH=sizing[0], sizingV=sizing[1])
    if stroke:
        pr.update(strokes=["#FFFFFF"], strokeWeight=sw, strokeAlign=props.pop("strokeAlign", "inside"))
    pr.update(props)
    if fill:
        pr["fill"] = "#000000"
    i = mk("frame", parent, name, **pr)
    tokens(i, gap=gap, pad=pads, radius=radius if radius in RA else None, fill=fill, stroke=stroke)
    return i


def txt(parent, s, style, color, name=None, width=None, align="center", **props):
    p = dict(textAlign=align, **props)
    if width:
        p.update(width=width, textAutoResize="height")
    i = mk("text", parent, name or s[:40].replace("\n", " "), text=s, **p)
    f.cmd("style.apply", ids=[i], style=STYLE_ID[style])
    bind(i, "fill", color)
    return i


def img(parent, name, file, w, h, x=0, y=0, absolute=True, mode="fill", **props):
    i = mk("rectangle", parent, name, x=x, y=y, width=w, height=h, fills=[], **props)
    f.cmd("image.place", path=f"{ART}/{file}", target=i, mode=mode)
    if absolute:
        setp(i, absolute=True, x=x, y=y)
    return i


def contrast(a, b):
    def lum(h):
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in hexrgb(h)]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def first_set(holder):
    return [c["id"] for c in get(holder)["children"] if c["type"] == "COMPONENT_SET"][0]


# depth: one light from the top left
EMBOSS = [{"type": "dropShadow", "color": "#2A1E1447", "offset": [2, 3], "radius": 6, "spread": 0},
          {"type": "innerShadow", "color": "#FFFFFF47", "offset": [1, 1], "radius": 1, "spread": 0},
          {"type": "innerShadow", "color": "#00000038", "offset": [-1, -2], "radius": 2, "spread": 0}]
PRESSED = [{"type": "innerShadow", "color": "#00000052", "offset": [2, 2], "radius": 4, "spread": 0}]
DEBOSS = [{"type": "innerShadow", "color": "#4A3B2F4D", "offset": [2, 2], "radius": 4, "spread": 0},
          {"type": "innerShadow", "color": "#FFFFFFB3", "offset": [-1, -1], "radius": 1, "spread": 0}]
CAST = [{"type": "dropShadow", "color": "#1F150E59", "offset": [4, 8], "radius": 14, "spread": 0}]

# ============================================================== file + pages
f.cmd("file.new", name="Bodo wedding invite")
pages = f.cmd("page.list")
pages = pages.get("pages", pages) if isinstance(pages, dict) else pages
DS = pages[0]["id"]
f.cmd("page.rename", id=DS, name="Design System")
UI = f.cmd("page.add", name="UI")
UI = UI.get("id", UI) if isinstance(UI, dict) else UI
f.cmd("page.select", id=DS)

f.cmd("variable.createCollection", name="spacing")
f.cmd("variable.createCollection", name="radius")
f.cmd("variable.createCollection", name="Core Colors")
f.cmd("variable.createCollection", name="Color System", modes=["Light", "Dark"])
steps = []
for k, v in SPACING:
    steps += [{"command": "variable.create", "params": {"collection": "spacing", "name": f"spacing/{k}", "type": "number", "value": v}},
              {"command": "variable.update", "params": {"variable": f"spacing/{k}", "scopes": ["GAP", "WIDTH_HEIGHT"]}}]
for k, v in RADIUS:
    steps += [{"command": "variable.create", "params": {"collection": "radius", "name": f"radius/{k}", "type": "number", "value": v}},
              {"command": "variable.update", "params": {"variable": f"radius/{k}", "scopes": ["CORNER_RADIUS"]}}]
f.batch(steps, "Spacing + radius")
steps = []
for n, v in CORE.items():
    steps += [{"command": "variable.create", "params": {"collection": "Core Colors", "name": n, "type": "color", "value": v}},
              {"command": "variable.update", "params": {"variable": n, "scopes": []}}]
f.batch(steps, "Core Colors")
steps = []
for n, a in SYSTEM:
    steps += [{"command": "variable.create", "params": {"collection": "Color System", "name": n, "type": "color", "value": "#000000"}},
              {"command": "variable.set", "params": {"variable": n, "mode": "Light", "value": {"alias": LIGHT_MAP[n]}}},
              {"command": "variable.set", "params": {"variable": n, "mode": "Dark", "value": {"alias": a}}},
              {"command": "variable.update", "params": {"variable": n, "scopes": scopes_for(n)}}]
f.batch(steps, "Color System")

for name, fam, wt, size, lh, ls in STYLES:
    STYLE_ID[name.split("/")[1]] = f.cmd("style.create", type="text", name=name, value={
        "fontFamily": fam, "fontStyle": wt, "fontSize": size, "lineHeight": lh,
        "letterSpacing": f"{ls}%" if ls else 0})["id"]

# contrast report, Light (the card) on linen and on the debossed well
BG, WELL = resolve("Surface/Primary"), resolve("Surface/Secondary-Subtle")
for t in ("Text/Primary", "Text/Secondary", "Text/Tertiary", "Text/Accent", "Text/Error"):
    LOG.append(f"{t} on Surface/Primary {contrast(resolve(t), BG):.2f} · on well {contrast(resolve(t), WELL):.2f}")
LOG.append(f"Text/Inverted on Action/Primary {contrast(resolve('Text/Inverted'), resolve('Action/Primary')):.2f}")
for t in ("Action/Primary-Hover", "Action/Primary-Click"):
    LOG.append(f"Text/Inverted on {t} {contrast(resolve('Text/Inverted'), resolve(t)):.2f}")
LOG.append(f"Text/Primary on Action/Secondary-Click {contrast(resolve('Text/Primary'), resolve('Action/Secondary-Click')):.2f}")
LOG.append(f"Text/Inverted on Action/Error {contrast(resolve('Text/Inverted'), resolve('Action/Error')):.2f} · hover {contrast(resolve('Text/Inverted'), resolve('Action/Error-Hover')):.2f}")
LOG.append(f"Text/Primary on Action/Secondary {contrast(resolve('Text/Primary'), resolve('Action/Secondary')):.2f}")
LOG.append(f"Text/Primary on Action/Secondary-Hover {contrast(resolve('Text/Primary'), resolve('Action/Secondary-Hover')):.2f}")
LOG.append(f"focus ring Border/Action-Primary on Surface/Primary {contrast(resolve('Border/Action-Primary'), BG):.2f}")
LOG.append(f"Text/Primary dark mode on Surface/Primary {contrast(resolve('Text/Primary', 'Dark'), resolve('Surface/Primary', 'Dark')):.2f}")

# ============================================================== components
COMP = box(None, "Components", gap=48, pad=[64] * 4, fill="Surface/Primary", x=1700, y=0)
f.cmd("variable.setMode", ids=[COMP], collection="Color System", mode="Light")
txt(COMP, "Components", "Heading 4", "Text/Primary", align="left")

# ---- Button: Type x State, embossed pills
BTN = {  # fills per state (default, hover, pressed, disabled), label, disabled label, border
    "Primary": (["Action/Primary", "Action/Primary-Hover", "Action/Primary-Click", "Action/Primary-Disabled"], "Text/Inverted", "Text/Primary-Disabled", None),
    "Secondary": (["Action/Secondary", "Action/Secondary-Hover", "Action/Secondary-Click", "Surface/Secondary"], "Text/Primary", "Text/Primary-Disabled", None),
    "Tertiary": ([None, "Surface/Primary-Hover", "Surface/Primary-Selected", None], "Text/Primary", "Text/Primary-Disabled", "Border/Secondary"),
    "Error": (["Action/Error", "Action/Error-Hover", "Action/Error-Hover", "Action/Error-Disabled"], "Text/Inverted", "Text/Primary-Disabled", None),
    "Warning": (["Action/Warning", "Action/Warning - Hover", "Action/Warning - Hover", "Action/Warning - Disabled"], "Text/Primary", "Text/Primary-Disabled", None),
}
STATES = ["Default", "Hover", "Pressed", "Focus", "Disabled"]
LABEL = {"Primary": "Save the date", "Secondary": "Get directions", "Tertiary": "Add to calendar",
         "Error": "Cancel my reply", "Warning": "Try again"}
board = box(COMP, "Board / Buttons", gap=16)
txt(board, "Button · Type × State · Button-md", "Title 3", "Text/Secondary", align="left")
holder = mk("frame", board, "Button holder", width=1200, height=320, fill=None, clip=False)
variants = []
for r_, (typ, (fills, lab, lab_dis, border)) in enumerate(BTN.items()):
    for c_, st in enumerate(STATES):
        fi = {"Default": fills[0], "Hover": fills[1], "Pressed": fills[2], "Focus": fills[0], "Disabled": fills[3]}[st]
        b = box(holder, f"Type={typ}, State={st}", "horizontal", pad=[12, 24, 12, 24], fill=fi, stroke=border,
                radius=9999, crossAlign="center", mainAlign="center", x=c_ * 240, y=r_ * 64)
        txt(b, LABEL[typ], "Button-md", lab_dis if st == "Disabled" else lab, name="Label")
        fx = {"Pressed": PRESSED, "Disabled": []}.get(st, EMBOSS if fi else [])
        setp(b, effects=fx)
        if st == "Focus":
            setp(b, strokes=["#FFFFFF"], strokeWeight=2, strokeAlign="outside")
            bind(b, "stroke", "Border/Action-Primary")
        f.cmd("component.create", ids=[b])
        f.cmd("component.addProperty", id=b, name="Label", type="text", layer=get(b)["children"][0]["id"])
        variants.append(b)
f.cmd("component.combineVariants", ids=variants)
BUTTON_SET = first_set(holder)
setp(BUTTON_SET, name="Button", x=0, y=0)
BTN_ID = {c["name"]: c["id"] for c in get(BUTTON_SET)["children"]}

# ---- Input: State (debossed into the linen)
board = box(COMP, "Board / Inputs", gap=16)
txt(board, "Input · State (debossed)", "Title 3", "Text/Secondary", align="left")
in_holder = box(board, "Input holder", "horizontal", gap=24, crossAlign="min")
inputs = []
IN = {"Default": ("Your name", "Text/Tertiary", None), "Hover": ("Your name", "Text/Tertiary", "Border/Secondary"),
      "Focus": ("Your name", "Text/Tertiary", "Border/Action-Primary"), "Filled": ("Maina Brahma", "Text/Primary", None),
      "Error": ("Your name", "Text/Tertiary", "Border/Error"), "Disabled": ("Your name", "Text/Primary-Disabled", None)}
for st, (val, vc, ring) in IN.items():
    w = box(in_holder, f"State={st}", gap=4, sizing=("fixed", "hug"), width=300)
    txt(w, "Name", "Title 4", "Text/Secondary" if st != "Disabled" else "Text/Primary-Disabled", name="Label", align="left")
    fld = box(w, "Field", "horizontal", pad=[12, 16, 12, 16], radius=8, crossAlign="center",
              fill="Surface/Primary-subtle" if st == "Disabled" else "Surface/Secondary-Subtle", sizing=("fill", "hug"))
    setp(fld, effects=DEBOSS if st != "Disabled" else [])
    txt(fld, val, "Body 3", vc, name="Value", align="left")
    if ring:
        setp(fld, strokes=["#FFFFFF"], strokeWeight=2 if st == "Focus" else 1,
             strokeAlign="outside" if st == "Focus" else "inside")
        bind(fld, "stroke", ring)
    if st == "Error":
        txt(w, "Please add your name so we can find your seat", "Caption 2", "Text/Error", name="Helper", align="left")
    f.cmd("component.create", ids=[w])
    kids = {c["name"]: c["id"] for c in get(w, 2)["children"]}
    f.cmd("component.addProperty", id=w, name="Label", type="text", layer=kids["Label"])
    f.cmd("component.addProperty", id=w, name="Value", type="text",
          layer=[c["id"] for c in get(kids["Field"])["children"]][0])
    inputs.append(w)
f.cmd("component.combineVariants", ids=inputs)
INPUT_SET = first_set(in_holder)
setp(INPUT_SET, name="Input")
INPUT_ID = {c["name"]: c["id"] for c in get(INPUT_SET)["children"]}

# ---- Countdown / Well (debossed number box)
board = box(COMP, "Board / Countdown", gap=16)
txt(board, "Countdown / Well · Agor divider · Aronai band", "Title 3", "Text/Secondary", align="left")
row = box(board, "Row", "horizontal", gap=24, crossAlign="center")
well = box(row, "Countdown / Well", gap=0, pad=[12, 8, 8, 8], radius=12, fill="Surface/Secondary-Subtle",
           crossAlign="center", sizing=("fixed", "hug"), width=74)
setp(well, effects=DEBOSS)
txt(well, "208", "Heading 5", "Text/Primary", name="Number")
txt(well, "Days", "Caption 4", "Text/Secondary", name="Unit")
f.cmd("component.create", ids=[well])
wk = {c["name"]: c["id"] for c in get(well)["children"]}
f.cmd("component.addProperty", id=well, name="Number", type="text", layer=wk["Number"])
f.cmd("component.addProperty", id=well, name="Unit", type="text", layer=wk["Unit"])
WELL_C = well

# ---- Divider / Agor: line, stepped diamond, line
div = box(row, "Divider / Agor", "horizontal", gap=8, crossAlign="center", sizing=("fixed", "hug"), width=220)
for side in ("Left", "Right"):
    ln = mk("rectangle", div, f"Line {side}", width=80, height=1, fill="#000000", sizingH="fill")
    bind(ln, "fill", "Border/Brand")
    if side == "Left":
        DIAMOND = ("M7 0h2v2h2v2h2v2h2v4h-2v2h-2v2h-2v2H7v-2H5v-2H3v-2H1V6h2V4h2V2h2z"
                   "M7 5v1H6v1H5v2h1v1h1v1h2v-1h1V9h1V7h-1V6H9V5z")
        dm = mk("vector", div, "Agor diamond", path=DIAMOND, fill="#000000")
        bind(dm, "fill", "Surface/Accent")
f.cmd("component.create", ids=[div])
DIV_C = div

# ---- Band / Aronai (woven strip used between sections)
band = mk("frame", row, "Band / Aronai", width=393, height=22, fill=None, clip=True)
img(band, "Weave", "band-h.png", 393, 22, absolute=False)
f.cmd("component.create", ids=[band])
BAND_C = band

# ============================================================== Foundations
FND = box(None, "Foundations", gap=64, pad=[64] * 4, fill="Surface/Primary", x=0, y=0)
f.cmd("variable.setMode", ids=[FND], collection="Color System", mode="Light")
txt(FND, "Foundations · Bodo wedding invite", "Heading 4", "Text/Primary", align="left")
s_ = box(FND, "Core Colors", gap=24)
txt(s_, "Core Colors", "Heading 6", "Text/Primary", align="left")
for pal in list(SHADES) + ["Grayscale-Alpha"]:
    r = box(s_, f"Palette / {pal}", gap=8)
    txt(r, pal, "Title 4", "Text/Secondary", align="left")
    sw = box(r, "Swatches", "horizontal", gap=4)
    for k in (SHADES[pal].split() if pal in SHADES else list(ALPHA)):
        c = box(sw, f"{pal}/{k}", gap=4)
        q = mk("rectangle", c, "Swatch", width=56, height=40, fill="#000000")
        bind(q, "fill", f"{pal}/{k}")
        txt(c, k, "Caption 5", "Text/Secondary", name="Shade", align="left")
        txt(c, CORE[f"{pal}/{k}"][:7], "Caption 5", "Text/Tertiary", name="Hex", align="left")
s_ = box(FND, "Color System", gap=24)
txt(s_, "Color System · Light (the card) and Dark", "Heading 6", "Text/Primary", align="left")
cols = box(s_, "Modes", "horizontal", gap=32, crossAlign="min")
groups = {}
for n, _ in SYSTEM:
    groups.setdefault(n.split("/")[0], []).append(n)
for mode in ("Light", "Dark"):
    col = box(cols, f"Mode / {mode}", gap=16, pad=[24] * 4, fill="Surface/Primary", stroke="Border/Primary", radius=16)
    f.cmd("variable.setMode", ids=[col], collection="Color System", mode=mode)
    txt(col, mode, "Title 2", "Text/Primary", align="left")
    grid = box(col, "Groups", "horizontal", gap=24, crossAlign="min")
    for g, names in groups.items():
        gc = box(grid, f"Group / {g}", gap=8)
        txt(gc, g, "Title 4", "Text/Secondary", align="left")
        for n in names:
            r = box(gc, n, "horizontal", gap=8, crossAlign="center")
            q = mk("rectangle", r, "Swatch", width=24, height=24, fill="#000000", strokes=["#FFFFFF"], strokeWeight=1)
            bind(q, "fill", n)
            bind(q, "stroke", "Border/Primary")
            lab = box(r, "Label", gap=0)
            txt(lab, n.split("/", 1)[1], "Caption 5", "Text/Primary", name="Token", align="left")
            txt(lab, "→ " + (LIGHT_MAP[n] if mode == "Light" else DARK[n]), "Caption 5", "Text/Tertiary", name="Alias", align="left")
s_ = box(FND, "Spacing", gap=12)
txt(s_, "spacing", "Heading 6", "Text/Primary", align="left")
for k, v in SPACING:
    r = box(s_, f"spacing/{k}", "horizontal", gap=16, crossAlign="center")
    txt(r, f"spacing/{k} · {v}", "Caption 5", "Text/Secondary", width=140, align="left")
    bar = mk("rectangle", r, "Bar", width=max(v, 1), height=16, fill="#000000")
    bind(bar, "fill", "Surface/Brand")
    bind(bar, "width", f"spacing/{k}")
s_ = box(FND, "Radius", gap=12)
txt(s_, "radius", "Heading 6", "Text/Primary", align="left")
rr = box(s_, "Samples", "horizontal", gap=24)
for k, v in RADIUS:
    c = box(rr, f"radius/{k}", gap=8)
    q = mk("rectangle", c, "Sample", width=64, height=64, fill="#000000", strokes=["#FFFFFF"], strokeWeight=1)
    bind(q, "fill", "Surface/Secondary")
    bind(q, "stroke", "Border/Brand")
    bind(q, "cornerRadius", f"radius/{k}")
    txt(c, f"radius/{k}", "Caption 5", "Text/Secondary", align="left")
s_ = box(FND, "Text styles", gap=16)
txt(s_, "Text styles", "Heading 6", "Text/Primary", align="left")
for name, fam, wt, size, lh, ls in STYLES:
    r = box(s_, name, "horizontal", gap=24, crossAlign="center")
    txt(r, f"{name.replace('/', ' / ')}\n{fam} {wt} {size}/{lh}" + (f" · {ls}%" if ls else ""), "Caption 5",
        "Text/Tertiary", width=220, align="left")
    txt(r, "Riju and Anjali" if size >= 30 else "Together before the Bathou", name.split("/")[1], "Text/Primary",
        name="Sample", align="left")
f.cmd("file.save", path=FILE)

# ============================================================== screens
f.cmd("page.select", id=UI)
SW, SH = 393, 852


def screen(name, x, h=SH, layout=True):
    s = mk("frame", None, name, x=x, y=0, width=SW, height=h, fill="#000000", clip=True)
    bind(s, "fill", "Surface/Primary")
    f.cmd("variable.setMode", ids=[s], collection="Color System", mode="Light")
    if layout:
        setp(s, layout="vertical", crossAlign="center", sizingV="hug")
    return s


def inst(comp, parent, name, **props):
    i = f.cmd("instance.create", component=comp, parent=parent)["id"]
    setp(i, name=name)
    if props:
        f.cmd("instance.setProperties", ids=[i], properties=props)
    return i


# ---- A: Opening / closed woven doors
A = screen("Opening / Closed doors", 0, layout=False)
img(A, "Door / Left", "door-left.png", 197, SH, 0, 0, absolute=False)
img(A, "Door / Right", "door-right.png", 196, SH, 197, 0, absolute=False)
pl = mk("frame", A, "Plaque", x=SW / 2 - 75, y=SH / 2 - 85, width=150, height=170, fill=None, clip=False)
img(pl, "Plaque / Art", "plaque.png", 150, 170, 0, 0, absolute=False)
setp(pl, effects=CAST)
pt = box(pl, "Plaque / Text", gap=4, crossAlign="center", sizing=("fixed", "hug"), width=150)
setp(pt, absolute=True, x=0, y=70)
txt(pt, "R & A", "Heading 3", "Text/Accent", name="Monogram")
txt(pt, "Tap to open", "Caption 3", "Text/Primary", name="Hint")

# ---- B: Hero / names under the Bathou altar
B = screen("Hero / Names", 473, layout=False)
img(B, "Curtains", "curtains.png", SW, SH, 0, 0, absolute=False)
alt_w = 236
alt_h = round(alt_w * 854 / 596)
img(B, "Altar / Bathou", "altar.png", alt_w, alt_h, (SW - alt_w) / 2, SH - alt_h - 14, absolute=False)
for k in range(5):
    lx = SW / 2 - 2 * 40 + k * 40 - 11
    lp = img(B, f"Lamp {k + 1}", "lamp.png", 30, 41, lx - 4, SH - 50, absolute=False)
img(B, "Valance", "valance.png", SW, 170, 0, 0, absolute=False)
for k, (bx, by, rot) in enumerate([(88, 132, -12), (196, 150, 8), (300, 126, -6)]):
    bf = img(B, f"Butterfly {k + 1}", "butterfly.png", 36, 27, bx - 6, by - 4, absolute=False)
    setp(bf, rotation=rot)
names = box(B, "Names", gap=8, crossAlign="center", sizing=("fixed", "hug"), width=240)
setp(names, x=(SW - 240) / 2, y=180)
txt(names, "We are getting married", "Body 7", "Text/Secondary", name="Lead")
inst(DIV_C, names, "Divider")
txt(names, "Riju", "Heading 1", "Text/Accent", name="Groom")
txt(names, "Son of Mr and Mrs Basumatary", "Caption 2", "Text/Secondary", name="Groom / Parents")
txt(names, "&", "Heading 3", "Text/Primary", name="Amp")
txt(names, "Anjali", "Heading 1", "Text/Accent", name="Bride")
txt(names, "Daughter of Mr and Mrs Narzary", "Caption 2", "Text/Secondary", name="Bride / Parents")
txt(names, "Sunday · 13 June 2027", "Caption 3", "Text/Primary", name="Date")

# ---- C: Welcome + countdown
Cs = screen("Section / Welcome and countdown", 946)
tokens(Cs, gap=24, pad=[0, 0, 48, 0])
img(Cs, "Edge / Left", "band-v.png", 14, 1200, 0, 0)
img(Cs, "Edge / Right", "band-v.png", 14, 1200, SW - 14, 0)
inst(BAND_C, Cs, "Band / Top")
wel = box(Cs, "Welcome", gap=16, pad=[24, 40, 0, 40], crossAlign="center", sizing=("fill", "hug"))
inst(DIV_C, wel, "Divider")
txt(wel, "Welcome", "Heading 3", "Text/Accent", name="Heading")
txt(wel, "With the blessings of our elders and before the sacred Bathou, we invite you to share the day our "
         "two families become one. Come in your finest dokhona and aronai, and celebrate with us.",
    "Body 7", "Text/Primary", name="Paragraph", width=300)
inst(BAND_C, Cs, "Band / Middle")
cd = box(Cs, "Countdown", gap=24, pad=[16, 32, 0, 32], crossAlign="center", sizing=("fill", "hug"))
txt(cd, "Counting down\nto our day", "Heading 3", "Text/Accent", name="Heading")
wells = box(cd, "Wells", "horizontal", gap=4)
for num, unit in (("208", "Days"), ("14", "Hours"), ("37", "Minutes"), ("09", "Seconds")):
    inst(WELL_C, wells, f"Well / {unit}", Number=num, Unit=unit)
txt(cd, "Kokrajhar, Bodoland · Sunday 13 June 2027", "Body 6", "Text/Secondary", name="When")
b = f.cmd("instance.create", component=BTN_ID["Type=Primary, State=Default"], parent=cd)["id"]
setp(b, name="Save the date")
inst(DIV_C, Cs, "Divider / End")

# ---- D: RSVP
D = screen("Section / RSVP", 1419)
tokens(D, gap=24, pad=[0, 0, 0, 0])
img(D, "Edge / Left", "band-v.png", 14, 1200, 0, 0)
img(D, "Edge / Right", "band-v.png", 14, 1200, SW - 14, 0)
inst(BAND_C, D, "Band / Top")
rs = box(D, "RSVP", gap=16, pad=[24, 40, 0, 40], crossAlign="center", sizing=("fill", "hug"))
inst(DIV_C, rs, "Divider")
txt(rs, "Will you join us", "Heading 3", "Text/Accent", name="Heading")
txt(rs, "Kindly reply by 1 May 2027 so we can prepare your seat and your aronai.", "Body 7", "Text/Primary",
    name="Lead", width=300)
form = box(D, "Form", gap=16, pad=[8, 40, 0, 40], sizing=("fill", "hug"))
for st, lab, val in (("Filled", "Your name", "Maina Brahma"), ("Default", "Will you be attending?", "Choose one"),
                     ("Default", "Guests with you", "Just me"), ("Default", "A blessing for the couple", "Write your wishes")):
    i = f.cmd("instance.create", component=INPUT_ID[f"State={st}"], parent=form)["id"]
    setp(i, name=f"Field / {lab}", sizingH="fill")
    f.cmd("instance.setProperties", ids=[i], properties={"Label": lab, "Value": val})
b = f.cmd("instance.create", component=BTN_ID["Type=Primary, State=Default"], parent=form)["id"]
setp(b, name="Send", sizingH="fill")
f.cmd("instance.setProperties", ids=[b], properties={"Label": "Send my reply"})
foot = box(D, "Footer", gap=8, pad=[24, 40, 24, 40], crossAlign="center", sizing=("fill", "hug"))
inst(BAND_C, D, "Band / Bottom")
txt(foot, "With love", "Body 7", "Text/Secondary", name="Lead")
txt(foot, "Riju & Anjali", "Heading 2", "Text/Accent", name="Signature")
img(foot, "Lamp", "lamp.png", 30, 41, absolute=False)

f.cmd("file.save", path=FILE)

# ============================================================== review exports
for nid, fn in ((A, "r1-opening.png"), (B, "r1-hero.png"), (Cs, "r1-welcome-countdown.png"), (D, "r1-rsvp.png")):
    f.cmd("file.export", ids=[nid], format="png", scale=2, path=f"{REVIEW}/{fn}")
f.cmd("page.select", id=DS)
for nid, fn in ((FND, "r1-foundations.png"), (COMP, "r1-components.png")):
    f.cmd("file.export", ids=[nid], format="png", scale=1, path=f"{REVIEW}/{fn}")
f.cmd("file.save", path=FILE)
print("\n".join(LOG))
f.close()
