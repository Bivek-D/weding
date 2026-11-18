# Reference spec: what we keep for the fresh start

On 2026-11-17 the user dropped the earlier design and its tech stack. The only things kept are the **references**: the feeling of **depth**, the **typography** and the **component list**. The new build can use any stack.

Sources:
- `depth-reference.mp4` (23.8 s). This is the main reference. Keyframes: `depth-reference-keyframes-1.jpg`, `-2.jpg`. Full notes: `depth-analysis.md`.
- `reference-video.mp4` (26.9 s). Motion and scroll timing. Notes: `motion-analysis.md`, frames in `frames/`.
- The user's own mockups, if wanted again: `doors-mockup.png`, `badge-full.png`, `curtains-assam-mockup.png`, `curtain-folds-reference.jpg`, `hero-bathou-mockup.png`, `background-paper-mockup.png`, `welcome-couple-mockup.png`.
- The old build is in `../archive/2026-11-17-v1/`, for reference only.

---

## 1. Depth: the look

Every element looks like a real, physical object under **one soft light from the top left**. It's crafted paper and clay, not flat vector art.

| Rule | How it looks |
|---|---|
| One light, top left | Raised things: a highlight on the top-left edge, a soft shadow to the bottom right. Recessed things: dark on top, light at the bottom. Everything follows the same light. |
| Sculpted art | Flowers, vines, trees, the fountain and the curtains look like clay or 3D renders. Soft gradients, dark creases (ambient occlusion), and contact shadows that ground every object. |
| Material texture | Linen paper on every page, embossed leaf relief on the doors, glossy pearls, gold glitter. |
| Tonal palette | Low saturation, so the shading carries the form: peach/sand linen, dusty rose, ivory, olive green, dark brown ink. No bright flat fills. |
| Emboss / deboss | Text is printed into the linen (letterpress). Countdown boxes and form fields are pressed in. Buttons, the plaque and the heart card are raised. The doors and the plaque have visible thickness. |
| Layers | The page scrolls normally, with no parallax. Depth comes from lighting and shadows, not camera movement. |

### Palette (sampled by eye from the reference)
| Token | Hex | Use |
|---|---|---|
| linen | `#F2D9C4` | page background (plus a linen texture) |
| linen-deep | `#E6C3A8` | shading, debossed wells |
| curtain-peach | `#EFC9AE` | curtains and valance, folds down to `#C99C80` |
| ivory | `#FBF1E8` | heart card, highlights, pearls |
| rose | `#D9A3A0` | roses, floral accents |
| olive | `#4F5338` | buttons, sound toggle, leaves (dark) |
| olive-door | `#7E7A55` | doors (foil sheen up to `#A9A27A`) |
| gold | `#B89B6A` | glitter heart, trims, door edge |
| ink | `#4A3528` | all text (dark brown, never black) |
| ink-soft | `#7A6252` | secondary text, captions, dividers |

---

## 2. Typography

Three voices, all in dark brown ink, printed into the linen:

| Role | Look in the reference | Suggested free font |
|---|---|---|
| **Names and display script** ("Zayn", "Nora", "&") | Large, flowing calligraphy with long entry and exit strokes | *Great Vibes* or *Pinyon Script* |
| **Section headings** ("Counting Down to Forever", "Program Timeline", "Scratch to Reveal", "Our forever begins", "Pre-Wedding Events") | A softer upright script, readable, one or two lines, centred | *Parisienne*, *Italianno* or *Allura* |
| **Body and details** (welcome paragraph, "Son of Mr. & Mrs. Malik", event names, dates) | A classic serif with high contrast. Italics for the welcome text, roman for names, dates and places | *Cormorant Garamond* or *Playfair Display* |
| **Labels and buttons** ("DAYS", "HOURS", "SAVE THE DATE", "TAP TO OPEN") | Small caps with wide letter spacing (≈ .15em) | *Cormorant SC* / *Cinzel* |

- Everything is centred.
- Sizes on a 393 px phone: names about 56 px, headings 32–36 px, body 16–18 px, labels 10–11 px.
- Dividers: a thin ink line with a small heart (♥) in the middle, used between almost every block.

---

## 3. Components, in page order

1. **Door intro**
   - Two olive doors with embossed leaf relief, meeting at a centre seam.
   - A thick, die-cut ivory **plaque** sits over the seam: "TAP TO OPEN" with a sprig.
   - On tap, a **pearl-beaded seam** appears, the doors swing *outward* (you see their thickness), and the plaque **splits in two**, each half going with its door. About 2–3 s.
2. **Curtains**
   - Full-screen peach curtains with deep sculpted folds and pearl trim on the inner edges.
   - They open like a **zip**: a diamond gap opens in the middle first, then the cloth gathers back to pearl tie-backs.
   - Then the **pearl-trimmed swag valance** drops in from the top.
3. **Hero / names**
   - A small heart, then "We're getting married", then a heart divider.
   - Then the **groom's name in script**, his parents, degree and job. Then "&". Then the **bride's name** with the same detail lines.
   - The **garden stage** sits at the bottom: fountain, cypress trees, urns, roses, all sculpted.
4. **Floral vine edges**: 3D rose-and-leaf vines down both side edges of every page after the hero.
5. **Welcome text**: an italic serif paragraph, centred, with a heart divider above and below.
6. **Scratch to reveal**
   - A heading, then a **gold-glitter heart** the guest scratches with a finger.
   - Underneath is an ivory heart card: "You're Invited! / November 30, 2026 / Monday / 10:30 AM".
   - Revealing it fires **confetti** and the "Our forever begins" heading.
7. **Save the Date button**: an embossed olive pill with a calendar icon and spaced caps. It adds the event to the guest's calendar.
8. **Countdown**
   - Heading "Counting Down to Forever".
   - Four **debossed square wells** (days, hours, minutes, seconds), each with a number in serif and a caps label under it.
   - A soft photo of the couple fades in above the heading.
9. **Program timeline**
   - A clock icon and the heading.
   - A vertical line on the left, with entries: event name in serif, date and time, and a short line.
10. **Dress code**: "Men", "Women" and others, each with a one-line description.
11. **Pre-wedding events**: an icon and the heading, then each event (Mahendi, Haldi…) with its date, time and place.
12. **RSVP form**
    - Fields: "Your Name", "Will you be attending?" (select) and "Your Message" (textarea).
    - All fields are **debossed** into the linen.
    - Full-width olive "Send Message" button.
13. **Sound toggle**: a small olive rounded-square button fixed at the top right, for background music.

### Motion
- Content **fades in** softly as it scrolls into view, with a tiny rise and staggered lines.
- The pages themselves scroll plainly.
- Ambient: curtains sway a little; the plaque can breathe on the intro.
