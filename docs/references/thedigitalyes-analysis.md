# How The Digital Yes gets class and depth (analysis, 2026-11-18)

Studied: their Instagram grid, the "Romantic" demo (romantictemplate.thedigitalyes.com) and the
"Majestic" demo (majestic-template.thedigitalyes.com), at phone size (375×812).

## 1. The opening is one film, not a pile of layers
- Romantic: the whole open (doors swing, room behind, music box, frame fills with flowers) is a
  **single 9 s MP4, 720×1278**, played on tap. Only the names and date are HTML, faded in on top.
- Majestic: the same idea. A pearl wax seal on an envelope flap, the flap lifts, then cut to a scene
  of beaded curtains, a chandelier and an embroidered table.
- Everything in the film shares **one material and one light**: carved ivory plaster, or embroidered
  thread. Because it is all one render, the shadows, light direction and depth of field always agree.
  This is the main reason it looks expensive, and why our layered CSS doors and curtains look "assembled".

## 2. One ground, one material, tone-on-tone
- The background is **one warm paper colour for the whole page** (`#FAF9F7` / `#F7F0EA`). It never
  switches to a saturated colour block.
- The art is **tone-on-tone relief**: ivory on ivory, embossed or debossed, with colour only in small
  touches (blush carnations, sage leaves). Depth comes from the light catching raised edges, not from
  dark drop shadows.
- Colour is an **accent, about 5% of the screen**: a burgundy name, a sage "When", a pink bow.

## 3. Typography: few voices, light weights, lots of air
| Role | Their setting |
|---|---|
| Section titles | Didone-style serif, **regular weight (400)**, 36–48 px, all caps, +0.04em, dark warm grey `#39322D` |
| Kicker or label | Didone caps, 11–13 px, **letter-spacing 0.3–0.35em**, accent colour |
| Body | Cormorant Garamond 14–17 px, regular weight, centred, short lines |
| Numbers (countdown, dates) | The same display serif, light and large, separated by thin vertical hairlines |
- No bold anywhere. Hierarchy comes from **size and spacing**, not weight.

## 4. Layout rhythm
- One centred column with 24 px side padding. Sections are **56–96 px apart vertically** and often
  taller than the screen.
- Each section has the same order: **an object illustration → a big title → a small spaced label →
  content**. The object (champagne coupes, a chandelier, a music box, a balustrade) acts as the
  section's icon and carries the depth.
- There are **no visible section borders or bands**. Sections are separated by space and by the art,
  with at most a soft ribbon or garland image now and then.

## 5. Components
- **Cards** are die-cut shapes (scalloped or notched corners, arched tops) in the same paper colour.
  They are raised with an inner highlight line and a very soft, wide shadow, and sometimes have a
  ribbon threaded through slots ("Countdown" card).
- **Buttons** are rarely filled. They are caps text with a hairline underline ("OPEN IN MAPS",
  "SEND RSVP"), or a single outlined tile.
- **Form fields**: a label above, a 1 px hairline box in a tint of the accent, and a large serif
  placeholder. Choices are two **tiles side by side** (a radio dot over a short label), and the chosen
  tile tints softly.
- **Small delights**: scratch-to-reveal photo, "tap to read" embossed oval for gifts, and a floating
  round sound button in the corner.

## 6. Motion
- Slow fades and small rises on scroll (reveal), a gentle float on the ornaments, sparkle dust.
  Nothing slides in from the side or bounces.

## What this means for our Bodo invite
1. **Pick one ground**: raw-silk ivory for the whole page. Bodo colours become threads and accents
   (scarlet names, an emerald label, a gold hairline), not full-section backgrounds.
2. **Drop the woven band between every section** and the emerald edge strips. Keep at most one band,
   used like a ribbon (for example under the hero).
3. **Lighter, larger type**: Cormorant at weight 400–500 for titles (uppercase, tracked), Cinzel
   labels at weight 400 with more tracking, no bold body text.
4. **Die-cut paper cards** with emboss in place of rounded, heavily shadowed boxes. **Text-link
   buttons** in place of filled pills.
5. **Opening**: the real step change is rendering doors → curtains → pandal as **one Blender film**
   (720×1280 MP4/WebM, about 9–12 s) in one material family (woven silk and brass, one soft key light),
   with the HTML names on top. This replaces the CSS door rig and the 36-frame canvas.
