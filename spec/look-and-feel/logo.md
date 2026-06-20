# Logo — Hearth

Three directions for the parent-app wordmark. One ships. The other two die honorable deaths.

The brief is the same across all three: **wordmark for a parenting wellness app called MVP; evocative of a quiet hearth; cream + ink + olive palette; must work at 24pt in the bottom-nav AND at 1024px on a launch screen, AND as a 1024×1024 App Store icon (mark-only crop OK for the icon).**

Tonal anchors: Wonder Valley's all-caps Fraunces wordmark; Rose LA's spare type+symbol pairing. Neither has a smiling baby in the logo. Neither should we.

## Direction A — Wordmark only (Fraunces display lockup)

**Visual.** All-caps `MVP` set in Fraunces ExtraBold, tight tracking (-2%), slight optical-size tweak at small sizes. `ink/primary` on `bg/canvas`. No mark, no symbol, no flame, no dot. Just the three letters carrying the whole identity.

**When it works.** This is the default recommendation. Reads as confident, editorial, grown-up — Wonder Valley energy. Scales cleanly from 24pt nav lockup to 1024px launch screen because there's nothing to break. Reinforces the editorial direction of the rest of the system (Fraunces as the display face).

**Drawbacks.** "MVP" as letterforms is structurally unbalanced — three letters, only one (V) has visual interest. The wordmark has nowhere to hide. Also: zero brand mark means no App Store icon other than the wordmark itself, which is cramped at 1024×1024 and tiny on a parent's home screen. Mitigation: icon is a single letter `M` in the same face, optically centered, on `photo/rose` or `photo/saffron`.

## Direction B — Wordmark + flame/hearth mark

**Visual.** Same `MVP` wordmark as Direction A, plus a small geometric flame-or-hearth glyph kerned to the left at the wordmark's cap height. Single-color: `ink/primary` on cream, `neutral/paper` (white) on photo tiles. The mark is abstract — a stylized flame inside an arch, or a single arched line implying a doorway — not literal fire, not literal house.

**When it works.** Reads as "the hearth of family content" without naming it. Gives us a brand mark that survives at 16×16 (favicon) and 1024×1024 (App Store icon) where the wordmark alone would crowd. Mark can stand alone in tight contexts (loading spinner, watermark on photos, sticker pack).

**Drawbacks.** Risk of cliché — flames and hearths in wellness branding are a crowded field. Risk of the glyph reading as a logo trope (the abstract-arch-with-a-thing-inside is everywhere from yoga studios to crypto wallets). The brand mark has to be drafted by an actual designer; AI sketches will land in cliché territory by default. Mitigation: design brief explicitly forbids the standard flame/arch/leaf forms; references go to mid-century Swiss marks rather than wellness-app generation.

## Direction C — Lowercase + dot

**Visual.** Lowercase `mvp.` with the period set in `accent/default` olive. Fraunces Regular, no tracking adjustment, generous counter spaces. Reads as a friendly bookshop sign.

**When it works.** Warmest of the three. Most approachable on the splash screen for a first-time tired parent. The olive dot is a tiny moment of color in an otherwise restrained mark — adds personality without a separate brand symbol. Maps to the "subscribe-friendly" Wonder Valley tone better than Direction A's editorial-confident tone.

**Drawbacks.** Lowercase reads younger and less authoritative — possibly a fit problem when the surface is health-adjacent or crisis-adjacent. The colored dot becomes a tiny technical liability: it has to render reliably at 16×16 favicon, in monochrome export, and on photo tiles where the olive will compete with `photo/rose`. Mitigation: monochrome fallback is `mvp` (no dot), reserved for the favicon and any single-color reproduction.

## Comparison

| | Direction A — wordmark | Direction B — wordmark + mark | Direction C — lowercase + dot |
|---|---|---|---|
| Register | editorial, confident | editorial + branded | warm, bookshop |
| App Store icon | weak (single-letter crop) | strong (mark alone) | medium (`.` crop) |
| 24pt nav legibility | strong | strong | strong |
| 1024px launch | strong | strong | strong |
| Standalone mark | none | yes | weak (`.` only) |
| Cliché risk | low | medium-high | low-medium |
| Time to first draft | hours | weeks (mark needs designer) | hours |
| Default recommendation | yes | only if we can fund a real mark | only if tonal calibration says "warmer" |

## Asset list (per direction)

Once a direction wins, the spec phase produces these under `spec/look-and-feel/logo/`:

```
wordmark.svg          1-color, scalable, viewBox tight to glyph bounds
mark.svg              Direction B only — standalone brand mark
icon-1024.png         App Store icon, 1024×1024, on a chosen photo/* bg
launch.svg            Launch-screen lockup, scaled for iPhone-class device
favicon.ico           16×16, 32×32, 48×48 multi-resolution
apple-touch-icon.png  180×180, rounded squircle handled by iOS
```

All exports go to `wordmark.svg` first; raster derivatives generated from it. SVG source kept in a single file with named layers (`wordmark`, `mark`, `dot`) so a designer can pull a single component without re-export.

## Midjourney prompts — concept sketches for the brand designer

These prompts generate rough concept sketches for the designer to riff on. They are NOT the production logo — they are reference moodboards. The actual wordmark is hand-drafted in Glyphs / Illustrator from Fraunces, not lifted from an AI render.

Use `--style raw` to suppress MJ's defaults; `--v 6` or `--v 7`. Cite hex from `DESIGN.tokens.md` for palette lock.

### Sketch A — wordmark only (concept reference)

```
/imagine: minimal editorial wordmark "MVP" set in a warm display
serif similar to Fraunces ExtraBold, all caps, tight tracking,
black ink color #1A1A1A on cream paper background color #F3F0EB,
flat single-color, no embellishment, no flourish, no shadow,
typography specimen sheet, swiss design reference, magazine
masthead aesthetic, no other graphical elements
--ar 1:1 --style raw --v 6 --no flame, fire, leaf, baby, family,
icon, ornament, sunburst, gradient, glow, drop-shadow, 3d, bevel,
embossed, distressed, vintage, retro, hand-drawn, sketch
```

Acceptance: a clean three-letter `MVP` on cream, single color, no decoration. The designer will redraw the actual wordmark from Fraunces.

### Sketch B — wordmark + abstract mark (concept reference)

```
/imagine: minimal editorial brand lockup, the letters "MVP" set
in a warm display serif similar to Fraunces ExtraBold all caps,
black ink color #1A1A1A on cream paper background #F3F0EB,
beside a small abstract geometric mark suggestive of a doorway
or arch or contained flame, single line weight, mid-century swiss
modernist, no literal fire, no literal house, no leaf, no heart,
flat single-color, no gradient
--ar 3:1 --style raw --v 6 --no realistic flame, realistic fire,
literal house, leaf, heart, family silhouette, baby, hand-drawn,
sketch, distressed, vintage, gradient, glow, 3d, bevel, embossed,
wellness cliche, yoga studio mark, crypto wallet mark
```

Acceptance: a clean wordmark beside a single geometric form — abstract, single-weight stroke, mid-century rather than wellness-cliché.

### Sketch C — lowercase + dot (concept reference)

```
/imagine: minimal editorial wordmark "mvp." set in a warm display
serif similar to Fraunces Regular, lowercase, generous counter
spaces, black ink #1A1A1A with the period in olive green #4F5D3A
on cream paper background #F3F0EB, flat single-color, friendly
bookshop sign aesthetic, no embellishment
--ar 1:1 --style raw --v 6 --no flame, fire, baby, family,
ornament, glow, gradient, drop-shadow, 3d, bevel, hand-drawn,
sketch, distressed, vintage
```

Acceptance: lowercase `mvp.` with a single colored dot, no decoration, reading as a quiet bookshop sign.

### Sketch D — App Store icon explorations (Direction B only)

```
/imagine: app store icon design exploration, single abstract
geometric mark centered on a saturated background, mark in cream
paper color #F3F0EB on background of either saffron #E8A33C or
clay terracotta #B05A3C, the mark is an abstract doorway or
contained flame, single line weight, mid-century swiss modernist,
flat single-color, no realism, magazine masthead aesthetic
--ar 1:1 --style raw --v 6 --no realistic flame, literal house,
literal hearth, leaf, heart, baby, gradient, glow, 3d, bevel,
drop-shadow, wellness cliche
```

Acceptance: 4-up grid of mark explorations on saffron and rose tiles. Designer picks 1–2 to hand-draft.

## Tokens used

```
ink/primary
ink/onPhoto-dark
ink/onPhoto-light
bg/canvas
bg/elevated
accent/default
accent/press
photo/saffron
photo/rose
type/display-xl
type/display-lg
shape/none
```

## Rules

- Wordmark is hand-drafted from Fraunces in Glyphs or Illustrator. MJ output is reference only.
- Single-color reproduction is the test of every lockup — if it fails in 1-color, it fails.
- The wordmark must legibility-test at 24pt nav size AND at 1024px launch size before it ships.
- App Store icon never includes the App Store typography rendering — icon is mark + bg only, no wordmark inside the icon.
- No gradient, no glow, no bevel, no drop-shadow on any lockup, ever.
- The dot (Direction C) is `accent/default` olive only; never `status/info` blue or any `photo/*` color.
- Lockups on photo tiles pick the AA-pass `ink/onPhoto-*` variant per tile (dark on saffron/rose, light on royal/forest); lockups on `bg/canvas` use `ink/primary`.
- Reject any sketch that reads as wellness-cliché (yoga-studio arch, crypto-wallet flame, hand-on-heart, leaf-around-a-letter).
- The mark (Direction B only) must work at 16×16 favicon size or it doesn't ship.
- Final lockup files live under `spec/look-and-feel/logo/`; no inline raster assets in app code.

## Render check

The implementation must match these compositions once a direction is picked.

1. **Bottom-nav lockup, iOS.** Wordmark at 24pt height, `ink/primary` on `bg/canvas`, centered above the active-tab indicator. No mark in this position regardless of direction.
2. **Launch screen, iOS.** Wordmark at 64pt (Direction A/C) or wordmark+mark at 64pt cap-height (Direction B), centered on `bg/canvas`, vertically biased to the upper third.
3. **App Store icon, 1024×1024.** Mark (Direction B) OR single-letter wordmark crop (Direction A) OR `mvp.` lockup (Direction C) centered on `photo/saffron` or `photo/rose` saturated background, `ink/onPhoto-dark` for the glyph.
4. **Favicon, 16×16.** Mark (Direction B) or `M` glyph (Direction A) or `m` glyph (Direction C). Single-color black on cream. No gradient.
5. **Photo-overlay watermark.** Wordmark at 12pt height, `ink/onPhoto-light` at 70% opacity (or `ink/onPhoto-dark` on warm tiles), bottom-left of a lifestyle hero photo. Never on a crisis surface; never larger than 14pt as a watermark.

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
