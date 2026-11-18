# What "depth" means in the reference (depth-reference.mp4, 23.8 s)

The user's definition of depth, from this video: every element looks like a **real, physical object lit by one soft light**: sculpted, embossed and layered. It is not mostly about camera motion or parallax (the page scrolls normally).

## Timeline
| Time | What happens |
|---|---|
| 0–2 s | Olive-gold doors with **embossed leaf relief** (raised, lit from the top left). A thick, die-cut **"Tap to open" plaque** with layered edges casts a real shadow. |
| 2–3.3 s | A **pearl-beaded seam** appears down the middle; the doors swing out and show **thickness**. **The plaque splits in two**: each half goes with its own door. |
| 3.3–5.5 s | Peach curtains, rendered like **sculpted fabric**: deep smooth folds with **dark valleys (ambient occlusion)** and soft highlights on the ridges, pearl trim on the edges. They open like a **zip**: a diamond-shaped gap opens in the middle, then the cloth pulls back to pearl tie-backs. |
| 6–6.5 s | The pearl-trimmed valance drops in. |
| 7–9 s | Names in dark brown script/serif, **printed into a linen texture**. The garden stage (fountain, cypress, urns, roses) has the same "clay render" look: soft shadows, everything grounded. |
| 10–23 s | Pages on **linen paper** with **3D floral vines on both edges**; content fades in; **debossed** countdown boxes and form fields (pressed into the paper); **embossed** olive pill buttons; a **gold-glitter scratch-to-reveal heart**; confetti; soft-edged photos. |

## The five things that create the depth
1. **Rendered, sculpted artwork instead of flat drawing.** Flowers, trees, fountain and curtains look like clay/3D renders: soft gradients, ambient occlusion in creases, shadows that ground them. *Ours is mostly flat vector with a drop shadow, so it reads as stickers on paper.*
2. **One consistent light (top left).** Raised things are lit on top with a shadow below; recessed things (countdown boxes, inputs) are dark on top and light below. Everything agrees.
3. **Real material texture:** linen paper, embossed foil doors, glossy pearls, gold glitter.
4. **Tonal, low-saturation palette.** Peach/sand/olive in many shades, so shading carries the form. Our bright orange/green/red flat fills flatten things.
5. **Embossed and debossed details:** letterpress text, inset fields, raised buttons, thick doors and plaque.

## What it means for our invitation
- **Biggest gap: the illustrations** (altar, roses, wisteria, garlands, arch, pavilion, frames) are flat vectors.
  - Option A: generate matching **3D/clay-render artwork** (the style of the user's own mockups for the doors, badge, couple and curtains) and place it as images.
  - Option B: give the existing vectors a **sculpted look in code**: an SVG lighting filter (blur the shape's alpha into a height map, light it with a top-left `feDiffuseLighting` + a little `feSpecularLighting`) so every petal, leaf and bead looks puffed and lit. Fast, consistent, keeps the art editable.
- **3D curtains:** add ambient occlusion (darken the fold valleys, brighten the ridges), a pearl trim on the inner edge, and a zip-style opening (a gap opening in the middle first).
- **Front page:** split the badge in two with the doors; embossed relief on the door cloth is already in the user's artwork.
- **UI:** deboss the countdown dials and inputs, emboss buttons, a letterpress feel on all text, linen texture, all lit from the top left.
- **Palette:** pull the altar's saturated orange/green toward the tonal palette if they should feel as soft as the reference.
