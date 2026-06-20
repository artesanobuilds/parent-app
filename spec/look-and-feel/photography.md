# Photography — Hearth

Photography is the dominant visual layer. Type and chrome step out of the way. If a screen has a photo on it, the photo carries the screen.

**Production source for v1: Midjourney.** Confirmed Miguel 2026-05-31 — MJ can hit our exact palette and contrast targets when prompted with locked hex values + `--style raw`. We treat MJ as the canonical photography pipeline. No hired photographer for v1. The full prompt library lives in `midjourney-prompts.md`; this file is the direction those prompts must satisfy.

Reference touchstones, in order:

1. **Wonder Valley** (welcometowondervalley.com) — warm-earth instance. Cream paper, olive bottles, terracotta pots, golden hour through a kitchen window. Subject lives in the world; the camera is a guest.
2. **Rose LA** (roselosangeles.com) — gallery instance. Product-on-saturated-color tiles, dramatic single-source side light, near-square crops, deep negative space inside the photo.

We generate in the Wonder Valley register for editorial / lifestyle frames and in the Rose LA register for category tiles. Same palette, same lighting language, two compositions.

## Pipeline

End-to-end, every shipped image moves through this path:

| Step | Tool | Output | Gate |
|---|---|---|---|
| 1. Brief | `midjourney-prompts.md` (this repo) | Named prompt with palette lock, aspect, `--no` list | Prompt cites hex values from `DESIGN.tokens.md` |
| 2. Generate | Midjourney `/imagine` | 4-up grid | At least one variant passes both gates below |
| 3. Palette QA | `tools/lint-design-tokens.py --image` (planned) — samples dominant color, compares to expected `photo/*` hex within ΔE 6 | Pass / fail | Fail = regenerate with stronger palette lock |
| 4. Uncanny QA | Human review | Pass / fail | Fail = regenerate; see "Uncanny test" below |
| 5. Upscale | MJ Upscale (Subtle) | 2048px long edge minimum | No new artifacts introduced |
| 6. Integration | iOS: `Assets.xcassets/Photography/<slug>.imageset/` (1x, 2x, 3x). CMS: `mvp-backend/cms/public/photo/<slug>.jpg` (sRGB, 80% quality, mozjpeg). | Final asset | Filename matches prompt name in library |

The slug is the prompt name (e.g. `tile-saffron-play-and-toys`). iOS asset names are PascalCase from that slug. CMS keeps kebab-case.

## Subjects — R is for Real (revised)

The HEARTH "R — Real" principle now reads: **photorealistic, never uncanny, never the AI-glossy look.** The casting reads as actual families, not stock-photo families, not the AI's idea of a family.

| Use | Composition | Lighting | Crop | Notes |
|---|---|---|---|---|
| Article / home hero | Editorial lifestyle. Parent + kid mid-activity, candid, in a real-feeling room. | Late-afternoon north-window; warm side light. | 4:5 portrait, subject 35–55% of frame. | Negative space in upper third for headline overlay. |
| Category tile | Single subject centered on saturated paper background (a `photo/*` token color). | One key light upper-left, dramatic single shadow. | 1:1 square. Subject centered. | One object only. The color is the loudest thing. |
| Kid-agent portrait | Single warm portrait of a child or parent-with-child. Sober register — no color tile. | Soft ambient lamp glow or window glow. | 4:5 portrait, tight on shoulders/face. | No props. Quiet. On `bg/sober`. |
| Community-post inline | Phone-camera realism. A real kitchen, a real mess, a real moment. | Available light only. | 4:5 or 1:1, intentionally imperfect. | Compresses to thumbnail — read at 200pt wide. |
| Outdoor / nature | Family in landscape. Trees and sky earn space. | Golden hour or overcast diffuse. | 3:2 landscape, subject 20–30% of frame. | Wide on purpose; the place is the subject. |
| Crisis surface | **No photography.** Type only. | — | — | A photograph on a crisis surface is a violation. Type IS the design. |

Casting direction baked into every people-shot prompt:

- Varied bodies, ages, skin tones, abilities, family structures. Specify ethnicity / age / body type explicitly per prompt — MJ defaults too narrow otherwise.
- People in real rooms — actual kitchens, sidewalks, hardwood living rooms — not studios, never seamless paper.
- Faces allowed to be tired, mid-blink, mid-laugh. Specify "candid expression, not posed, slight imperfection" in every prompt.
- No model-agency cheekbones. No symmetry-perfect faces. No glowing-skin retouch.

## Lighting

- Side-lit, warm, slightly golden. Kodak Portra 400 reference in every prompt.
- One light source per frame, ambient or natural. Studio strobes give themselves away as AI.
- Shadows are kept — not filled in. The shadow is part of the composition.
- White balance leans warm (3800–4500K). Never blue-cast.
- Slightly desaturated overall. MJ defaults oversaturated; the `--style raw` flag is mandatory.

## Composition

- Subject 35–55% of frame for lifestyle; centered for product tiles.
- Generous negative space — magazine crop. Eye needs somewhere to rest.
- Rule-of-thirds for lifestyle; dead-center for tiles.
- One subject. If two, they touch or share an axis.
- Hands doing real things — turning a page, slicing a peach, tying a shoe. Never posed.

## Palette adherence — the lock

MJ defaults oversaturated and tends toward generic cinematic teal-orange. We override with two simultaneous techniques in every prompt. Both are mandatory.

**(a) Cite hex values inline.** Every prompt names the target background or dominant color by hex from `DESIGN.tokens.md`. Example phrasing:

> "...background a flat saffron paper color #E8A33C, no other dominant colors in the frame, no teal, no orange-blue cinematic grade..."

**(b) Use `--style raw` and the latest version.** `--style raw --v 6` (or `--v 7` if available at generation time) suppresses MJ's default Instagram-grade styling. Without `--style raw`, MJ adds saturation, contrast, and a film LUT that breaks the palette lock.

Locked hex values for prompts (mirror of `DESIGN.tokens.md`):

```
photo/saffron   #E8A33C   tile bg — energy / play
photo/rose      #B86A60   tile bg — care / tenderness (terracotta family)
photo/royal     #2E3A5F   tile bg — focus / learning (desaturated ink-indigo)
photo/forest    #2D3F2C   tile bg — nature / outdoors
bg/canvas       #F3F0EB   cream canvas (lifestyle hero bg, kid-agent bg)
bg/sober        #FAF7F2   sober surface (kid-agent, near-crisis)
ink/primary     #1A1A1A   on-cream type
```

`photo/clay` and `photo/sand` are retired from v1. If a category genuinely needs a sixth color, open a discussion to add it back; do not invent.

## Category-tile templates

One template per `photo/*` color. The variable is the subject placed centered on the saturated background. Full `/imagine` commands in `midjourney-prompts.md`.

| Token | Hex | Mood | Use for taxonomy parent | Example subject |
|---|---|---|---|---|
| `photo/saffron` | `#E8A33C` | energy, play, joy | raising-kids; school-activities; home-style-products | a stack of three picture books; a wooden train car |
| `photo/rose` | `#B86A60` | care, tenderness, emotional | family-life; inner-life; food-nutrition (warm dishes) | a stoneware bowl; a folded linen napkin and a candle |
| `photo/royal` | `#2E3A5F` | focus, learning, depth | school-activities (academic); pregnancy-babies (sleep) | a hardcover composition notebook; a swaddle folded |
| `photo/forest` | `#2D3F2C` | nature, outdoors, grounded | out-in-world; food-nutrition (gardens) | a sprig of rosemary; a wooden Brio train |

Tile composition rules:

- One subject per tile. No clusters.
- Subject in service of the color, not the other way around.
- Drop shadow stays — it's the depth.
- Subject sits dead-center, occupying 30–45% of the square.
- No type baked into the photo. Headlines overlay at the surface layer.
- Reshoot (regenerate) per category; do not reuse the same subject across tokens.

## Forbidden cliches

If a brief asks for any of these, push back. If MJ surfaces any of these, reject the generation. Add to every prompt's `--no` list.

- newborn feet cradled in parent hands
- silhouette family against a sunset
- "tired mom" gripping a coffee mug in a beige kitchen
- "dad juggling laptop and baby"
- a child reaching toward the camera with finger paint on hands
- a family in matching white t-shirts on a beach
- a pregnant belly with hands forming a heart
- a single tear on a child's cheek
- a parent's hand holding a child's hand, shot from above
- balloons released into a blue sky
- hands praying over a baby
- stock-photo white-toothed grins; perfect teeth
- perfectly-matched-outfits family portraits
- stock-photo "diverse group of friends laughing at brunch"
- studio backdrops, seamless paper of any color we don't ship as a token
- lens flare added in post, fake bokeh, plug-in film grain
- visible iconography, logos, competitor products
- chalkboard text, mason jars, fairy lights
- any baby in a pumpkin, basket, watering can, or sleeping in dad's beard
- the AI-glossy look: plastic skin, glowing highlights, symmetric retouched faces, hyper-saturated golden hour

## Crisis surface — rule

**No photography on any crisis-lock or near-crisis surface.** Type-only — type IS the design. `bg/sober` canvas, `ink/primary` text, no decorative elements. A photograph in a crisis context is a tonal violation regardless of how well it's shot. See `voice.md` for the matching copy register and `DESIGN.md` for the surface rule.

## QA — two gates per generation

Every MJ output must pass both before it ships.

**Gate 1 — Palette compliance.** Sample dominant color from the image; compare to expected `photo/*` hex within ΔE 6 (CIE 2000). Run via `tools/lint-design-tokens.py --image <path>` (planned utility — until it lands, eyeball against the hex tile in `DESIGN.tokens.md` next to the image at 100%). If dominant color drifts toward orange-cinematic, teal-shadow, or any color outside the palette, regenerate with `--style raw` re-emphasized and the hex re-cited.

**Gate 2 — Uncanny test.** Ask: does this look like a real family in a real room, or does it look like the AI's idea of a family? Tells of an uncanny fail:

- Plastic-perfect skin with no pores or asymmetry
- Eyes that don't quite focus on the same point
- Hands with the wrong finger count, wrong joint geometry, or melted-together fingers
- Symmetry-perfect faces (real faces are slightly asymmetric)
- Hair-edge glow halo
- Background objects that don't make geometric sense
- Anyone wearing the kind of clothes nobody actually wears
- The whole-image "MJ sheen" — over-rendered, over-lit, over-everything

Two failures on a generation → regenerate. Three regenerations on one prompt → revise the prompt itself, do not keep rolling.

## Tokens used

```
photo/saffron
photo/rose
photo/royal
photo/forest
ink/onPhoto-dark
ink/onPhoto-light
ink/primary
bg/canvas
bg/sober
bg/elevated
border/hairline
shape/lg
shape/xl
elevation/0   (tiles use no shadow at surface level; in-photo shadow only)
elevation/1   (lifestyle hero on cream)
```

## Rules

- Midjourney is the production photography source for v1.
- Every prompt locks palette by hex and uses `--style raw --v 6` (or `--v 7`).
- One subject per frame; one light source per frame.
- Side-lit and warm; cool overhead light is a fail.
- Real-feeling rooms only; no studio seamless paper; no AI-glossy sheen.
- Tiles are product-on-saturated-color; lifestyle is people-in-their-rooms.
- Regenerate per category; do not recolor the same image across tokens.
- Crisis surfaces get no photography — type only.
- Never bake type, logos, or UI into the photo.
- Every generation passes both palette QA and the uncanny test before it ships.

## Mode B — Human photographers (post-launch, when we hire)

This section is the brief for the day we shift from generated to shot photography. The Universal Rules above (subjects, lighting, composition, palette, forbidden cliches, crisis-surface rule) apply identically — only the pipeline changes. Until that day, this section is reference, not active spec.

### Casting

- 6-8 families per shoot day, varied across ages 0-18, body types, skin tones, household structures (single-parent, two-parent, intergenerational, blended). Cast across the 11 taxonomy parents so every section of the library has representation.
- **Not** model agencies. Independent casting via parenting communities, neighborhood mutual-aid networks, friend-of-friend referrals. Parents read as themselves, not as "the parent role."
- One audition signal that matters: can they ignore the camera. Stiffness reads as stock photography.

### Locations

- Real family homes — never studios, never seamless paper, never rented "lifestyle spaces". The point of the entire palette is that it lives in homes a parent recognizes.
- North-facing window, side-light. Late-afternoon ideal. Avoid south-facing direct sun (kills the warm-but-soft look the spec calls for).
- Two locations per shoot day maximum. Travel time is the budget killer.
- Walk the location 24 hours before the shoot; identify the window, the surfaces, the backdrops you'll use. Improvising on-site burns half the day.

### Shot list (per shoot day)

- 1 hero composition (the "Wonder Valley vanity" equivalent — wide, magazine-spread, family-in-their-room).
- 3 tile-color variations of the same family vignette — shoot the same subject against saffron paper, rose paper, and forest paper backdrops (the four photo-tile colors are locked: `photo/saffron`, `photo/rose`, `photo/royal`, `photo/forest`). The paper is real — large-roll seamless — but laid across a real-home surface, not floating in a studio.
- 4-6 secondary lifestyle shots that don't go on a saturated tile (cream-canvas-friendly).
- 1 sober portrait — for kid-agent / consent / crisis-adjacent surfaces. No color tile, soft cream bg, late-afternoon north-window only.

### Direction style

- Candid + observational > posed. Photographer is invisible; the family forgets the camera.
- No "look at the camera and smile". No prompt-style direction ("pretend you're proud of him"). Set up the situation (reading a book, making a snack), then disappear.
- Continuous shooting; pick the moment in edit.

### Color grading + LUT

- A Hearth LUT (to be authored when the first shoot is booked) maps the camera RAW to the palette ladder in `DESIGN.tokens.md`. Subject tones land between `neutral/ink-700` and `neutral/ink-500`; warm-paper backgrounds clamp to the assigned `photo/*` hex within ΔE ≤ 5; cream canvases clamp to `neutral/cream-100` ± ΔE 3.
- Deliverables are 16-bit TIFF (post-grade) + RAW (untouched, for re-grading later). No JPEGs except as preview proxies.
- A Photoshop adjustment-layer template enforces the clamp; the colorist works inside it, never above it.

### Releases

- Model release + location release signed **before the shoot starts**. Templates live at `/spec/releases/` (out of scope for this doc).
- Children's releases co-signed by both legal guardians; copy of guardian ID retained in the asset's sidecar JSON.
- "Editorial use" is not enough — we license for app + marketing + web. The release covers all three.

### Budget signal (informational)

- Indie photographer day rate: ~$2.5–5K + retouching + casting. Cheaper than premium stock for the volume we'd need (50+ unique images for v1), and the result reads as a brand instead of as a portfolio.
- MJ-now → photographer-later is the right ramp. We don't pay for photography until we know which compositions are the keepers; MJ generates the working library, the photographer reshoots the proven hits.

### Migration mechanics

When a human shoot replaces an MJ asset:

1. Drop the new file at the same path the MJ asset occupied — `mvp/MVP/Assets.xcassets/Photo/<slot>.jpg` on iOS, `mvp-backend/cms/public/photo/<slot>.jpg` on CMS. Filename stable; calling code doesn't change.
2. Update the sidecar JSON: `source: midjourney` → `source: photographer-<name>-<date>`, `license: editorial-app-marketing`, `release_refs: [link to signed release on file]`.
3. Run the palette lint script — every replaced asset must still pass the hex-compliance check.
4. The uncanny test inverts: an MJ asset that passes here is one a real photo of a real family wouldn't make you flinch at; a photographed asset that passes is one that doesn't look posed.

### What stays MJ permanently

Some assets are forever-MJ — the cost or logistics of shooting them is unjustifiable:

- Abstract texture / paper / surface fills for compositing.
- Conceptual hero illustrations on the *Inner Life* parent category (mindfulness, spirituality) where literal photography would feel either preachy or off-tone.
- Time-of-day variants (golden hour AND blue hour AND midday) of the same scene, when the variation is for art-direction, not editorial truth.

The rest — every parent + kid + product + place — migrates to human photography on the long horizon.

## Render check

The implementation must match these compositions.

1. **Home / article hero.** Parent reading a hardcover picture book to a 4-year-old on warm hardwood, north-window light, 4:5, headline overlays upper-third in Fraunces on `ink/primary` over a `bg/canvas` scrim. Generated from prompt `hero/reading-corner` in `midjourney-prompts.md`.
2. **Category tile — raising-kids.** A stack of three hardcover children's books, centered on `photo/saffron` (`#E8A33C`), single key light upper-left, 1:1, no chrome inside the photo. From prompt `tile/saffron-play-and-toys`.
3. **Category tile — food-nutrition.** A stoneware bowl of olive-oil-glazed roasted carrots, top-down, on `photo/rose` (`#B86A60`), 1:1. From prompt `tile/rose-food-nutrition`.
4. **Sober portrait.** A child mid-thought in soft lamp glow, 4:5, no color tile, on `bg/sober`. From prompt `sober/portrait`.
5. **Crisis surface.** Type only. No image. `bg/sober` canvas, `ink/primary` composition. No prompt; by design.

---

status: ✅ active
owner: Miguel
last_updated: 2026-05-31
