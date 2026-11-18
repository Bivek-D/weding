# Hand-off: Bodo wedding invitation (moving to the Blender machine)

This file is for continuing the project on another computer, by you or by a Claude session there.
Read this first, then `brief.md`, `references/reference-spec.md` and `references/bodo-research.md`.

## What it is

A mobile wedding-invitation website for a Bodo (Assam) wedding. The couple are placeholders: Riju Basumatary and Anjali Narzary, Kokrajhar, Sunday 13 June 2027. All content is in `site/src/content/couple.json`.

**What happens on screen:**
1. The cover shows woven doors with a bamboo badge sitting on a yellow aronai bow.
2. On tap, the bow unties, the seam unstitches, the badge parts (Riju on the left door, Anjali on the right) and the doors swing open.
3. Curtains open like a zip, showing the Bathou pandal with lamps, banana plants and marigolds.
4. The scroll sections follow: welcome, countdown, ceremonies, dress code, story, timeline, travel, gifts and RSVP.

## How the user likes to work (keep these)
- **Elegant and classy over busy.**
- **Depth everywhere:** one soft light from the top left, real shadows, things raised off the cloth.
- **Type:** no script or italic fonts. Names and headings use upright Cormorant Garamond; labels use Cinzel in spaced caps.
- **Language:** English only, with Bodo words used only as accents ("Haba", "Khulumbai", garment names).
- **Colours:** bright Bodo colours (`references/bodo-palette.png`): gwmw yellow `#F2C318`, marigold `#EE8A1E`, scarlet `#D7332B`, emerald `#0F7A4A`, gold thread `#D9A84A`, ivory `#FBF6EC`, navy `#1E2457`.
- **Motion:** the user liked the slow, smooth opening (about 15 s), the wandering butterflies and the tilt-to-parallax depth.
- **Testing:** the user tests on a phone (Brave, Android) over the local network. `./serve.sh` builds and serves the site on port 8080 and prints the address.
- **Feedback that led here:** the three.js renders of the knot and the pandal drapes looked stiff and plastic, "not polished, not classy". The agreed next step is **Blender renders** for realistic, polished art (see the plan below).

## Folder map
| Path | What |
|---|---|
| `site/` | Next.js 15 app (React 19, GSAP + ScrollTrigger, Lenis, Motion). `src/components/Opening.tsx` (the opening), `Sections.tsx` (scroll sections), `src/app/api/rsvp/route.ts` (RSVP, with Supabase and Resend when keys are set; see `.env.example`). |
| `site/public/art/` | Every image the site uses. **Blender renders replace files here, keeping the same names and sizes.** |
| `site/public/art/curtain/00–35.webp` | Curtain opening sequence: 36 frames, 640×1388, transparent, with soft cast shadows baked in. |
| `design/render3d/` | The current three.js renderer: `scene.js` builds the objects, `node render.mjs [job]` renders them to `out/`, `python publish.py` copies them into `site/public/art`. Use it as the spec for shapes, sizes and camera framing. |
| `design/render3d/tex/` | Woven pattern maps (albedo, height, thread mask) for doors, column, hem, ribbon, bands, mat and edges. Use these as Blender textures: the thread mask sets where the metallic gold zari is. |
| `design/build/` | Python art scripts: `art_bodo2.py` (patterns and the curtain frames), `art_scene.py`, `maps.py`. They need the venv: `pip install numpy pillow scipy`. |
| `references/` | Videos, mockups, research notes and the palette. |
| `brief.md` | Decisions log. |

The old static build (`archive/`) is not included; it isn't needed.

## Setup on the new machine
```bash
cd site && npm install && npm run dev          # http://localhost:3000
cd .. && ./serve.sh                             # build and serve on the LAN (port 8080)
```
- **three.js renderer (optional):** run `cd design/render3d && npm i playwright-core && npx playwright install chromium && node render.mjs altar`.
- **Fonts:** bundled in `site/src/fonts/` (SIL Open Font License).

## The Blender plan (next step)
Render each piece with Cycles at 2× the CSS size, with a transparent film (Film → Transparent) and a shadow catcher under objects that stand on the floor. Light everything with a large soft area light from the top left, front and above, plus a warm neutral HDRI at low strength.

**Fabric materials:**
- Principled BSDF with Sheen.
- Use the `tex/*-albedo.png` maps for colour and `*-height.png` for bump.
- Use `*-mask.png` to mix in metallic gold thread (metallic 0.9, roughness 0.3).
- Drapes, curtains and the knot need real **cloth simulation** with pinned edges and subdivision, so they fold naturally.

Keep the names and pixel sizes so the site picks them up without code changes:

| File (`site/public/art/`) | Size px | What to model |
|---|---|---|
| `altar.webp` | about 600×612 (cropped to content) | Bathou pandal: bamboo frame (two posts and a crossbar) with draped marigold dokhona swags and green woven borders, a marigold garland, and the sijou (Euphorbia neriifolia: candelabra stems with leaf tufts) inside a round bamboo fence of **18 pairs of poles tied with 5 bands**. Also a woven mat and two brass bowls of marigolds. **No lamps** (the site lights them separately). |
| `lamp.webp` | 88×120 | Brass saki lamp with a flame |
| `lamps3.webp` | about 334×118 | Three lit brass lamps on cloth with marigolds |
| `banana-l.webp` / `-r` | about 497×488 | Banana plant: torn paddle leaves, streaked pseudostem (mirror for `-r`) |
| `bush-l.webp` / `-r` | about 340×171 | Marigold bush (foreground, front corners) |
| `strand.webp` | 40×300 | Hanging marigold garland strand with a scarlet and gold thread tassel |
| `curtain/00–35.webp` | 640×1388 each | Yellow dokhona curtains (scarlet woven column on the inner edge, scarlet hem panel) opening like a zip (the middle opens first), gathered to emerald aronai tie-backs at 60% of the height. Include the soft cast shadow. |
| `swag.webp` | 420×230 | One scarlet jwmgra valance swag with a gold border and fringe |
| `knot.webp` | about 328×152 | Two aronai, emerald and scarlet, tied in one knot ("two families, one knot") |
| `fold-aronai.webp`, `fold-dokhona.webp`, `fold-gamsa.webp` | about 377×110 / 320×124 | Neatly folded textiles, front-three-quarter product shot |
| `instruments.webp` | about 382×158 | Kham (barrel drum, zigzag leather lacing), siphung (long bamboo flute) and jotha cymbals |
| `meal.webp` | about 340×124 | Rice and ondlakhari on a banana leaf, with a wooden hatha bowl |
| `plate.webp` | about 253×148 | Brass plate with a folded aronai and a ring of marigolds |
| `door-base.webp`, `door-column.webp`, `door-hem.webp`, `plaque.webp`, `ribbon.webp`, `bow-*.webp`, `wing.webp` | as now | The cover. The user was happy with these; re-render only if they visibly improve. |

**After rendering:**
1. Convert to WebP (quality 88–90), keeping transparency.
2. Run the site and check it at phone size (412×780).
3. Run `./serve.sh` for the user to check on their phone.

## Open items
- Real couple names, date and venues still to come (they all go in `couple.json`).
- Confirm "Khulumbai" and the agor motif names with someone from the Bodo community before the card is shared.
- Supabase and Resend keys for real RSVP storage and email.
- Possibly a gold-foil line-art style for the section-page objects (discussed as a classy alternative).
