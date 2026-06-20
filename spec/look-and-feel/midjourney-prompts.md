# Midjourney Prompts — Hearth (Production Library)

This is the production photography pipeline for Hearth v1. Each prompt below is ready to paste into Midjourney `/imagine`. Generations that pass both QA gates (palette compliance + uncanny test, see `photography.md`) ship as the canonical photography for the named surface.

Every prompt locks the palette by hex value and uses `--style raw --v 6` (upgrade to `--v 7` when available). The `--no` list aggressively excludes the AI-glossy register and the cliché list from `photography.md`.

Slug naming convention: `<surface>/<color-or-context>-<subject>`. iOS asset names PascalCase from slug; CMS public/photo/ kebab-case.

---

## 1. Home + onboarding hero — lifestyle

Editorial lifestyle photography. 4:5 portrait. Subject 35–55% of frame. Headline overlays upper-third on the surface layer, so negative space is non-negotiable.

### `hero/reading-corner`

```
/imagine: editorial documentary photograph, parent sitting
cross-legged on warm hardwood floor reading a hardcover picture
book to a four-year-old child, late afternoon north-facing
window light, warm cream walls color near #F3F0EB, slightly
desaturated kodak portra 400 film grain, magazine spread crop,
candid moment not posed, parent in soft olive sweater color
near #4F5D3A, child in muted earth tones, real lived-in room
with one houseplant and a wood side table, subject occupies
about 45 percent of frame with generous negative space upper
third for headline overlay, single light source, asymmetric
real faces, slight imperfection, mid-blink or mid-laugh
--ar 4:5 --style raw --v 6 --no AI-glossy, plastic skin,
glowing skin, perfect teeth, symmetric retouched face, melted
fingers, extra fingers, sunset, sunset cliche, lens flare,
fake bokeh, hand-on-heart, hands forming heart, newborn feet,
silhouette, stock photo smile, matching outfits, studio
seamless, white seamless paper, tired-mom-with-coffee, dad
juggling laptop, oversaturated, teal-orange grade, cinematic
LUT
```

Palette lock: cream wall near `bg/canvas` `#F3F0EB`; olive sweater near `accent/default` `#4F5D3A`. Aspect: 4:5.
Acceptance: room feels lived-in (visible scuff, one stray toy ok); parent face shows asymmetry and slight tiredness; negative space sits in upper third; no AI sheen on skin; book covers do not contain text.

### `hero/kitchen-counter-tween`

```
/imagine: editorial documentary photograph, parent leaning
against a kitchen counter listening intently to a tween
mid-sentence holding a glass of water, late golden hour through
a west-facing window, muted earth tones, kodak portra 400 film
stock aesthetic, warm cream walls near #F3F0EB, candid not
posed, parent in late thirties or forties with realistic
unretouched skin, tween about eleven or twelve, slight
imperfection in face, real lived-in kitchen with one wooden
cutting board and a stoneware mug, subject about 50 percent of
frame, generous negative space upper third
--ar 4:5 --style raw --v 6 --no AI-glossy, plastic skin,
glowing skin, perfect teeth, symmetric face, retouched, melted
fingers, sunset cliche, lens flare, fake bokeh, stock photo
smile, matching outfits, studio seamless, oversaturated, teal-
orange grade, cinematic LUT, food blogger styling, prop-heavy
```

Palette lock: cream wall near `bg/canvas` `#F3F0EB`. Aspect: 4:5.
Acceptance: tween is mid-speech (mouth open, mid-gesture); parent is listening, not performing listening; counter has 1–2 real objects, not 8 styled ones.

### `hero/back-of-parent-with-sleeping-infant`

```
/imagine: editorial intimate photograph, parent holding a
sleeping infant against their shoulder in a softly lit nursery,
shot from behind the parent so we see the baby's small hand
resting on the parent's shoulder blade, ambient lamp glow only,
warm cream walls near #F3F0EB, kodak portra 400 film aesthetic,
quiet domestic scene, no faces visible, single dim light source
upper-left, deep shadows kept not filled, slightly desaturated,
3am quiet
--ar 4:5 --style raw --v 6 --no AI-glossy, plastic skin,
glowing skin, melted fingers, extra fingers, lens flare, fake
bokeh, newborn feet in hands, hands forming heart, parent-hand-
holding-baby-hand-from-above, sunset cliche, stock photo,
nursery cliche, mason jars, fairy lights, oversaturated,
cinematic LUT
```

Palette lock: cream wall near `bg/canvas` `#F3F0EB`. Aspect: 4:5.
Acceptance: no faces (face-shy compositions hold up better against uncanny tests); baby's hand has correct finger count and joint geometry; light is single-source and dim; scene reads as 3am, not 3pm.

### `hero/onboarding-welcome-parent-portrait`

```
/imagine: editorial portrait photograph, single parent in their
late thirties standing in their own front doorway with afternoon
light spilling in, looking off-frame not at camera, varied
ethnicity, realistic unretouched skin with pores and slight
asymmetry, warm cream interior near #F3F0EB visible behind,
kodak portra 400 film stock, candid, slight imperfection in
expression, subject occupies 40 percent of frame, generous
negative space to the right for headline overlay
--ar 4:5 --style raw --v 6 --no AI-glossy, plastic skin,
glowing skin, perfect teeth, symmetric face, retouched, model-
agency cheekbones, melted fingers, sunset cliche, lens flare,
stock photo smile, matching outfits, studio seamless,
oversaturated, teal-orange grade, cinematic LUT
```

Palette lock: cream interior near `bg/canvas` `#F3F0EB`. Aspect: 4:5.
Acceptance: subject looks like a real person you'd see at a school pickup, not a model; pores visible; asymmetry visible; no studio-portrait energy.

---

## 2. Article hero photos — lifestyle templates

Used as banner imagery at the top of long-form articles. 16:9 for in-article banners; 4:5 for the homepage carousel rendition of the same content.

### `article/family-meal-evening`

```
/imagine: editorial documentary photograph, three-person family
eating dinner at a wooden table, candid mid-meal, parent passing
a stoneware bowl, child mid-bite, no posed smiling, late evening
warm tungsten lamp light supplemented by one window, warm cream
walls near #F3F0EB, kodak portra 400 film aesthetic, varied
ethnicities and ages, realistic unretouched skin, real lived-in
dining room with worn table, single stoneware bowl in clay
terracotta color near #B05A3C as the loudest object, slightly
desaturated overall, single key light source
--ar 16:9 --style raw --v 6 --no AI-glossy, plastic skin,
glowing skin, perfect teeth, symmetric face, retouched, melted
fingers, extra fingers, food-blogger styling, prop-heavy,
matching outfits, stock photo smile, mason jars, fairy lights,
sunset cliche, oversaturated, cinematic LUT, teal-orange grade
```

Palette lock: walls near `bg/canvas` `#F3F0EB`; stoneware bowl near `photo/clay` `#B05A3C`. Aspect: 16:9.
Acceptance: family looks like they eat together regularly (table has wear; chairs don't match); no one is looking at the camera; the clay bowl is the visual anchor.

### `article/couch-reading-quiet`

```
/imagine: editorial documentary photograph, parent reclining on
a worn linen couch in a sunny living room reading a hardcover
book, one foot tucked up, late afternoon north-window light,
warm cream walls near #F3F0EB, kodak portra 400 film stock,
deep shadows kept not filled, slight imperfection in pose,
realistic unretouched skin, slightly desaturated, single light
source, the book cover is blank no text or graphic
--ar 16:9 --style raw --v 6 --no AI-glossy, plastic skin,
glowing skin, perfect teeth, symmetric face, retouched, melted
fingers, lens flare, fake bokeh, book cover text, book cover
graphic, sunset cliche, stock photo smile, oversaturated,
cinematic LUT, teal-orange grade, IKEA showroom, designer
showroom
```

Palette lock: walls near `bg/canvas` `#F3F0EB`. Aspect: 16:9.
Acceptance: couch is worn, not new; light is angled side-light; book cover is blank (MJ cannot render book titles without producing gibberish); parent's pose is slightly slumped, not magazine-poised.

### `article/walk-in-nature`

```
/imagine: editorial documentary photograph, parent and child
walking on a dirt path through dappled forest light, shot from
behind so we see them from waist up walking away from camera,
late afternoon golden filtered light through trees, forest
greens dominant near #2D3F2C, candid not posed, varied
ethnicities, kodak portra 400 film stock, slightly desaturated,
the place is the subject not the people, subject occupies 25
percent of frame
--ar 16:9 --style raw --v 6 --no AI-glossy, sunset cliche, lens
flare, fake bokeh, stock photo, family-running-toward-camera,
silhouette against sky, holding-hands-from-above, matching
outfits, oversaturated, cinematic LUT, teal-orange grade,
hyper-saturated golden hour
```

Palette lock: forest greens near `photo/forest` `#2D3F2C`. Aspect: 16:9.
Acceptance: shot from behind (sidesteps uncanny face issues); the path and trees dominate; light is dappled not blasting; no holding-hands-shot-from-above.

---

## 3. Category-tile photography — palette-locked

One prompt per `photo/*` color, mapped to a taxonomy parent. 1:1 square. Subject dead-center, occupying 30–45% of frame, single key light upper-left, drop shadow tight.

The taxonomy coverage across these six tiles plus the lifestyle prompts above covers all 11 taxonomy parents: pregnancy-babies (royal), raising-kids (saffron), school-activities (saffron), family-life (rose), health-kids (sand), health-parents (sand), food-nutrition (clay), care-village (sand), home-style-products (clay), out-in-world (forest), inner-life (rose).

### `tile/saffron-play-and-toys`

```
/imagine: editorial product still life photograph, a single
wooden Brio train car centered on a flat saturated saffron paper
background color exactly #E8A33C, no other dominant colors in
frame, no teal, no orange-blue cinematic grade, single key light
from upper left casting a tight dramatic shadow to the lower
right, kodak portra 400 film stock aesthetic, magazine product
photography, kinfolk magazine reference, slightly desaturated
overall, subject occupies about 35 percent of square, dead
centered
--ar 1:1 --style raw --v 6 --no AI-glossy, plastic, oversaturated,
teal-orange grade, cinematic LUT, gradient background, textured
background, multiple objects, cluster of toys, baby in pumpkin,
hands in frame, text in frame, logo in frame, lens flare, fake
bokeh, white seamless, studio seamless
```

Palette lock: background `photo/saffron` `#E8A33C`. Aspect: 1:1. Taxonomy: raising-kids, school-activities.
Acceptance: the saffron is a flat saturated paper field with no gradient; the train car is a single object centered; shadow is dramatic and asymmetric; no other objects in frame; no hands.

### `tile/rose-care-and-tenderness`

```
/imagine: editorial product still life photograph, a single
ceramic mug, hand-thrown with a slightly imperfect form, in a
muted cream glaze, centered on a flat saturated dusty rose paper
background color exactly #C76F6B, no other dominant colors in
frame, single key light from upper left casting a tight dramatic
shadow to the lower right, kodak portra 400 film stock
aesthetic, magazine product photography, slightly desaturated,
subject occupies about 35 percent of square, dead centered
--ar 1:1 --style raw --v 6 --no AI-glossy, plastic, oversaturated,
teal-orange grade, cinematic LUT, gradient background, multiple
objects, hands in frame, steam, text on mug, logo on mug, lens
flare, fake bokeh, white seamless, studio seamless, perfect
symmetry
```

Palette lock: background `photo/rose` `#C76F6B`. Aspect: 1:1. Taxonomy: family-life, inner-life.
Acceptance: mug is hand-thrown (asymmetric, imperfect); cream glaze reads warm against rose; no logo or text on the mug; one object only.

### `tile/royal-focus-and-learning`

```
/imagine: editorial product still life photograph, a single
hardcover composition notebook with a blank black cover and a
worn spine, centered on a flat saturated royal blue paper
background color exactly #2B3A8C, no other dominant colors in
frame, single key light from upper left casting a tight dramatic
shadow to the lower right, kodak portra 400 film stock
aesthetic, magazine product photography, slightly desaturated,
subject occupies about 35 percent of square, dead centered
--ar 1:1 --style raw --v 6 --no AI-glossy, plastic, oversaturated,
teal-orange grade, cinematic LUT, gradient background, multiple
objects, stack of notebooks, hands in frame, pen, pencil, text
on cover, logo on cover, lens flare, fake bokeh, white seamless,
studio seamless
```

Palette lock: background `photo/royal` `#2B3A8C`. Aspect: 1:1. Taxonomy: school-activities (academic), pregnancy-babies (sleep / calm).
Acceptance: deep saturated royal blue, not navy; one notebook only; cover blank (MJ cannot render text without producing gibberish); spine shows real wear.

### `tile/forest-nature-and-outdoors`

```
/imagine: editorial product still life photograph, a single
sprig of fresh rosemary centered on a flat saturated deep forest
green paper background color exactly #2D3F2C, no other dominant
colors in frame, single key light from upper left casting a
tight dramatic shadow to the lower right, kodak portra 400 film
stock aesthetic, botanical magazine reference, slightly
desaturated overall, subject occupies about 30 percent of
square, dead centered
--ar 1:1 --style raw --v 6 --no AI-glossy, plastic, oversaturated,
teal-orange grade, cinematic LUT, gradient background, multiple
sprigs, bouquet, hands in frame, text in frame, logo in frame,
lens flare, fake bokeh, white seamless, studio seamless,
hyper-real botanical illustration
```

Palette lock: background `photo/forest` `#2D3F2C`. Aspect: 1:1. Taxonomy: out-in-world, food-nutrition (gardens).
Acceptance: forest background is flat and saturated; rosemary is a single sprig with realistic needle geometry; the shadow does its work.

### `tile/clay-food-nutrition`

```
/imagine: editorial product still life photograph, a single
stoneware bowl filled with olive-oil-glazed roasted carrots
shot top-down, centered on a flat saturated terracotta clay
paper background color exactly #B05A3C, no other dominant
colors in frame, single key light from upper left casting a
tight dramatic shadow to the lower right, kodak portra 400 film
stock aesthetic, cup of jo and wonder valley reference, slightly
desaturated overall, subject occupies about 45 percent of
square, dead centered
--ar 1:1 --style raw --v 6 --no AI-glossy, plastic, oversaturated,
teal-orange grade, cinematic LUT, gradient background, multiple
bowls, cutlery, hands in frame, garnish-overkill, sprigs of
herbs everywhere, text in frame, logo in frame, lens flare,
fake bokeh, white seamless, studio seamless, food-blogger
overstyling
```

Palette lock: background `photo/clay` `#B05A3C`. Aspect: 1:1. Taxonomy: food-nutrition, home-style-products.
Acceptance: terracotta background is flat and saturated; bowl is hand-thrown stoneware; carrots are real-shaped (not all uniform); minimal garnish; one bowl only.

### `tile/sand-care-and-wellness`

```
/imagine: editorial product still life photograph, a single
clear glass of water on a folded cream linen napkin, centered
on a flat saturated warm sand paper background color exactly
#D9C7A8, no other dominant colors in frame, single key light
from upper left casting a tight gentle shadow to the lower
right, kodak portra 400 film stock aesthetic, magazine product
photography, slightly desaturated overall, subject occupies
about 35 percent of square, dead centered
--ar 1:1 --style raw --v 6 --no AI-glossy, plastic, oversaturated,
teal-orange grade, cinematic LUT, gradient background, multiple
objects, hands in frame, lemon slice, mint sprig, text in frame,
logo in frame, lens flare, fake bokeh, white seamless, studio
seamless, wellness cliche
```

Palette lock: background `photo/sand` `#D9C7A8`. Aspect: 1:1. Taxonomy: care-village, health-parents (wellness), health-kids (wellness).
Acceptance: sand background is flat and warm; glass refracts the sand color gently; linen has visible weave; no lemon-slice-and-mint-sprig wellness cliché.

---

## 4. Kid-agent surface — sober variant

Single warm portrait. No color tile. `bg/sober` canvas. Used as the chat-surface header art and the kid-agent profile illustration. One prompt, used as-is.

### `kid-agent/sober-portrait`

```
/imagine: editorial portrait photograph, a single child about
eight to ten years old sitting cross-legged on a worn linen
couch looking off-frame in quiet thought, soft ambient lamp glow
as the single light source, warm cream sober canvas walls near
#FAF7F2, kodak portra 400 film stock aesthetic, varied
ethnicity, realistic unretouched skin with the natural texture
of a real child's face, asymmetric features, slight imperfection
in expression, no posed smiling, quiet domestic interior, subject
occupies about 45 percent of frame, generous negative space upper
third, slightly desaturated, no other objects competing for
attention
--ar 4:5 --style raw --v 6 --no AI-glossy, plastic skin, glowing
skin, perfect teeth, symmetric retouched face, model-agency
child, posed smile, child-actor headshot, melted fingers, extra
fingers, sunset cliche, lens flare, fake bokeh, color tile, color
block background, oversaturated, teal-orange grade, cinematic LUT,
toy cluttered scene
```

Palette lock: sober walls near `bg/sober` `#FAF7F2`. Aspect: 4:5.
Acceptance: child looks like a real kid (not a child actor); looking off-frame (no eye-contact uncanny risk); single soft light; background is the muted sober cream; no decorative color tile; no toys cluttering frame.

---

## 5. Crisis surface

**No prompts. By design.**

Crisis screens are type-only. A photograph in a crisis context is a tonal violation regardless of how well it's shot. The `bg/sober` canvas, `ink/primary` type, and generous whitespace carry the surface. Do not generate imagery for these screens, even as exploration. See `photography.md` "Crisis surface — rule" and `voice.md` "Crisis-surface tone."

---

## Tokens used

```
photo/saffron
photo/rose
photo/royal
photo/forest
photo/clay
photo/sand
bg/canvas
bg/sober
accent/default
ink/primary
ink/onPhoto
```

## Rules

- Every prompt cites at least one hex from `DESIGN.tokens.md` for palette lock.
- Every prompt uses `--style raw --v 6` (upgrade to `--v 7` when available); never default MJ styling.
- Every prompt includes the AI-glossy and cliché `--no` list.
- Every generation passes palette QA (ΔE ≤ 6 from target hex) before it ships.
- Every generation passes the uncanny test (real-family, real-kid, real-room) before it ships.
- Tile prompts: one subject, dead-center, 30–45% of frame, single key light upper-left.
- Lifestyle prompts: subject 25–55% of frame depending on context, generous negative space in upper third.
- Faces are preferred from behind, off-frame, or partial — sidesteps MJ's uncanny-face failure mode.
- Book covers, mug logos, notebook text: keep blank — MJ cannot render readable text without gibberish.
- Three failed generations on a single prompt → revise the prompt; do not keep rolling.

## Render check

The implementation must match these compositions from the prompt library.

1. **Home hero carousel slot 1.** From `hero/reading-corner` — parent + 4-year-old on hardwood, 4:5, headline overlay upper-third.
2. **Category tile, raising-kids row.** From `tile/saffron-play-and-toys` — wooden train on `photo/saffron`, 1:1.
3. **Category tile, food-nutrition row.** From `tile/clay-food-nutrition` — stoneware bowl on `photo/clay`, 1:1.
4. **Article banner.** From `article/family-meal-evening` — family dinner with clay bowl as anchor, 16:9.
5. **Kid-agent chat header.** From `kid-agent/sober-portrait` — child mid-thought, 4:5, on `bg/sober`. No tile.

---

status: ✅ active
owner: Miguel
last_updated: 2026-05-31
