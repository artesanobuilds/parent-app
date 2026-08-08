# Cards

Cards are the primary content container. Five variants — each tunes the chrome/photo ratio for what's inside. Article and category lean editorial (photo dominates); post, sober and dashboard lean quiet (chrome quiets, photo retreats).

> **beta-v1 reversal.** Cards used to lift via `border/hairline` + `bg/elevated`, with shadows reserved for overlays. Greg's redesign puts a soft ambient shadow on every content card and no hairline at all. **`elevation/1` is now the card default; the hairline is demoted to dividers, separators, and input borders.** When converting an old surface, strip the `RoundedRectangle().stroke(border/hairline)` overlay and apply `elevation/1`. Photo tiles still use no shadow (the color block is the weight).

## Variants

| Variant | Use | Surface | Photo | Chrome |
|---|---|---|---|---|
| `article` | feed item linking to long-form | `bg/elevated` + `border/hairline` | 4:5 hero, edge-to-edge top | title `type/title-lg`, byline `type/caption-mono` |
| `category` | library tile, photo-bg "shop the look" | `photo/*` saturated fill | centered subject, 35–55% frame | label `type/label` UPPERCASE in `ink/onPhoto-dark` (warm tiles) or `ink/onPhoto-light` (dark tiles) |
| `post` | parent post in feed (formerly `community`) | `bg/elevated` + `border/hairline` | optional inline 16:9 | author `type/body-sm`, body `type/body-md` |
| `sober` | kid-agent / safety surface (formerly `kid-agent`) | `bg/sober` + `border/hairline` | NEVER | title `type/title-md`, body `type/body-md` |

Variant names describe what the card IS, not where it's used. `post` describes the content; `sober` describes the treatment (matches `bg/sober` and the sober-variant pattern in `DESIGN.md`). The old "no photo = revert to community" fallback is gone — if an `article` has no photo, fall back to `post`.

## States

| State | article | category | post | sober |
|---|---|---|---|---|
| default | photo + title + byline, hairline border | saturated fill, label bottom-left | author row, body, action row | warm icon + title + body, hairline border |
| hover (CMS) | title underline, scale 1.01 | label nudges up 2px, `motion/fast` | reaction row reveals counts | none — sober surface, no hover affordance |
| pressed | scale 0.99, photo dims 4% | scale 0.98, no dim | scale 0.99 | scale 0.99 only |
| focused | `focus/ring-on-light` 2px outer offset 4 | `focus/ring-on-photo` 2px outer offset 4 | `focus/ring-on-light` 2px outer offset 2 | `focus/ring-on-light` 1px outer offset 2 (sober) |
| loading | skeleton — see `empty.md` | skeleton — color block only | skeleton row | spinner ONLY — skeletons forbidden |
| empty (slot) | "saved articles will live here" `ink/muted` | "no categories yet" | "be the first to post" | "kid-agent is paused" sober copy |
| reduced-motion | no scale on press — substitute `border/strong` flash for 80ms via `motion/instant`; no hover scale; end-card slide-in disabled | label nudge disabled; press fill darken 2% in lieu of scale | reaction reveal renders statically | no transforms; native focus only |

## Sizes

| Size | Width | Photo aspect | Pad | Radius | Stack gap |
|---|---|---|---|---|---|
| `sm` | column 1/2 (CMS) / 156pt (iOS) | 1:1 | `spacing/400` (12) | `shape/md` | `spacing/300` (8) |
| `md` | column full (iOS) / 1/3 (CMS) | 4:5 article, 1:1 category | `spacing/500` (16) | `shape/lg` | `spacing/400` (12) |
| `lg` | hero | 16:9 article, 4:5 category | `spacing/600` (20) | `shape/xl` | `spacing/500` (16) |

`sober` never goes `lg`; always `md`. Sober means restrained, including footprint.

## Rules

- Photo on article + category is non-negotiable. No photo = use the `post` variant instead.
- Category tiles use ONE photo token per tile; do not gradient between two `photo/*` colors.
- Text overlaid on photo resolves to `ink/onPhoto-dark` on warm tiles (`photo/saffron`, `photo/rose`) and `ink/onPhoto-light` on dark tiles (`photo/royal`, `photo/forest`). `type/label` (11pt) MUST use the AA-pass variant — never substitute mid-tile.
- A library grid shows at most 3 distinct `photo/*` tokens visible above the fold (Rose LA discipline; no rainbow grids).
- `post` body truncates at 4 lines with a `quiet` "read more" — never ellipsis-only. The "read more" has a 44pt min hit area independent of its visual height (pad outward into the card gutter).
- Sober cards forbid: photo, saturated fill, decorative serif, hover affordance, skeleton loading.
- Tap target spans the whole card; secondary actions (save, share) sit outside the card hit area at 44pt min.
- Card padding scales with card size; never mix `md` chrome with `sm` photo.
- Cards never nest. If you want a card-in-card, you want a `sheet`.
- Radius is set per size; never override per instance. `shape/pill` is forbidden on cards.
- Cards lift via `border/hairline` + `bg/elevated` on canvas — **not shadow**. `elevation/1` is reserved; do not apply to cards.
- Reduce-motion collapses all card hover/press transforms to `motion/instant` (see states table).

## Render check

1. `article` md on `bg/canvas` — feed card with 4:5 hero, title `type/title-lg`, byline "by Jane Doe · 6 min", `border/hairline` + `bg/elevated` lift (no shadow).
2. `category` md on `photo/saffron` — library tile, single hardcover book centered, label "PICTURE BOOKS" in `ink/onPhoto-dark`.
3. `post` md with inline image — parent post, 3 reactions, "read more" `quiet` at bottom (44pt hit area).
4. `sober` md on `bg/sober` — "your kid-agent is ready", body explainer, `secondary` "open" CTA.
5. `category` lg on `photo/royal` — hero tile at top of library, oversize label in `ink/onPhoto-light`, focus uses `focus/ring-on-photo`.

## Tokens used

```
bg/canvas, bg/elevated, bg/sober
ink/primary, ink/secondary, ink/muted, ink/onPhoto-dark, ink/onPhoto-light
border/hairline, border/strong
accent/default
photo/saffron, photo/rose, photo/royal, photo/forest
focus/ring-on-light, focus/ring-on-photo
elevation/0
shape/md, shape/lg, shape/xl
spacing/300, spacing/400, spacing/500, spacing/600
type/label, type/title-md, type/title-lg, type/body-sm, type/body-md, type/caption-mono
motion/fast, motion/instant
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
