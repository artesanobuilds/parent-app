# Buttons

Buttons are the load-bearing CTA primitive. Three variants, three sizes, four+ interactive states. iOS hit target is `44pt` minimum regardless of visual height — pad the tap area, not the chrome. Labels are sentence-case for functional UI ("save changes"), Title Case only when echoing an article-level action.

> **beta-v1 changes.** Radius moved from `shape/pill` to **`shape/button` (8)** — Greg's CTAs are tight rects, not capsules. The accent is now teal and is **split**: `accent/default` is the FILL, `accent/onCanvas` is for accent-colored TEXT drawn on cream. A `quiet` button standalone on `bg/canvas` therefore takes `accent/onCanvas`, not `accent/default` — using the fill hex as text on canvas is 4.15:1, an AA fail. A disabled button uses `bg/disabled` with `ink/secondary`; **never white on `bg/disabled` (2.07:1)**.

## Variants

| Variant | Use | Fill | Label | Border |
|---|---|---|---|---|
| `primary` | one per screen — the verb the parent came for | `accent/default` | `ink/onPhoto-light` (5.25:1, AA-pass) | none |
| `secondary` | adjacent counter-verb (cancel, back) | `bg/elevated` | `ink/primary` | `border/hairline` 1px |
| `quiet` | inline action inside a card or row, toolbar / nav-adjacent (icon-only ok) | transparent | `accent/onCanvas` when standalone on canvas; `accent/default` when standalone on `bg/elevated`; inherits surface ink (`ink/primary` / `ink/secondary` / `ink/onPhoto-*`) when nested | none |
| `disabled` (modifier) | inert primary | `bg/disabled` | `ink/secondary` (6.66:1) | none |

`danger` is a **modifier on `secondary`**, not a variant: fill stays `bg/elevated`; label and border swap to `status/error`. There is no `danger primary` — destructive actions stay quiet until invoked. Color inheritance for `quiet` follows the surface the same way photo overlays do.

## States

| State | primary | secondary (incl. danger modifier) | quiet |
|---|---|---|---|
| default | fill `accent/default`, text `ink/onPhoto-light` | fill `bg/elevated`, border `border/hairline` (danger: text + border → `status/error`) | text inherits surface ink (or `accent/default` standalone) |
| hover (CMS) | fill `accent/press` | fill `neutral/cream-50`, border `border/strong` (danger: fill `status/error-tint`) | text → `ink/primary` (or `accent/press` standalone), underline |
| pressed | fill `accent/press`, scale 0.98 | fill `border/hairline` (danger: fill `status/error-tint`) | fill `border/hairline` |
| focused | `focus/ring-on-light` 2px outer (or `focus/ring-on-photo` when on a `photo/*` tile) | `focus/ring-on-light` 2px outer | per surface (light or photo) |
| disabled | fill `border/hairline`, text `ink/muted` | text `ink/muted`, border `border/hairline` | text `ink/muted` |
| loading | spinner `ink/onPhoto-light`, label hidden, width frozen | spinner `ink/secondary` | spinner inherits surface ink |
| reduced-motion | no scale on press — substitute `fill darken 4%`. focus ring renders instantly (no ease-in). loading spinner replaced by static `…` glyph in `type/caption-mono` | same | same |

## Sizes

| Size | Height | Horizontal pad | Type token | Icon | Radius | iOS hit-area |
|---|---|---|---|---|---|---|
| `sm` | 32 | `spacing/400` (12) | `type/label` | 14pt | `shape/md` | 44 (pad 6 top/bottom) |
| `md` | 40 | `spacing/500` (16) | `type/title-md` | 16pt | `shape/md` | 44 (pad 2 top/bottom) |
| `lg` | 48 | `spacing/600` (20) | `type/title-md` | 18pt | `shape/md` | 48 native |

Pill-shape (`shape/pill`) is a permitted override on `primary` and `secondary` lg-only — reserved for landing/marketing surfaces echoing Wonder Valley. Never pill on iOS in-app chrome.

## Rules

- One `primary` per screen, full stop. If you need two, one is `secondary`.
- Never combine `danger` with `primary` styling — `danger` is a modifier on `secondary`. Destructive actions stay quiet until invoked.
- Loading state freezes the button width; do not let labels shift the layout.
- Icon-left only; icon-right is reserved for "open external" affordances (use chevron, not arrow).
- `quiet` on a `photo/*` tile resolves its label to `ink/onPhoto-dark` on warm tiles (saffron, rose) and `ink/onPhoto-light` on dark tiles (royal, forest). Never use `ink/onPhoto-light` on a warm tile — fails AA.
- `primary` CTAs on a `photo/*` tile are forbidden on warm tiles (saffron, rose) — the `ink/onPhoto-light` label fails AA on the olive-on-warm composite. Use `quiet` or move the CTA off the tile.
- Disabled buttons remain in the tab order with `aria-disabled` (CMS); on iOS the tap is a no-op but VoiceOver reads "dimmed".
- On sober surfaces (kid-agent, crisis): only `secondary` and `quiet` are permitted — never `primary` saturated fill.
- Always pair iconography with a visible label; icon-only buttons require `aria-label` / SwiftUI `.accessibilityLabel`.
- Focus ring renders OUTSIDE the button bounds (offset 2px). Never inside. Pick `focus/ring-on-light` vs `focus/ring-on-photo` per surface.
- `shape/pill` is **forbidden on iOS in-app chrome**, full stop. Permitted only on CMS landing/marketing `primary` lg.
- Tap feedback uses `motion/fast`; scale-down only, no haptic on `quiet`.
- Under reduced-motion, scale press feedback is replaced by `fill darken 4%`; no scale, no spring.

## Render check

1. `primary` lg on `bg/canvas` — "continue" CTA at bottom of onboarding step.
2. `secondary` md + `primary` md side by side — "save draft" / "publish" pair in CMS toolbar.
3. `quiet` sm inside an `article` card — "read more" at the foot, label inherits `accent/default`.
4. `secondary` md with `danger` modifier inside a `sheet` — "end kid-agent session" confirmation, text + border `status/error`.
5. `quiet` lg on a `photo/royal` tile — "start reading" overlay; label `ink/onPhoto-light`, focus uses `focus/ring-on-photo`.

## Tokens used

```
accent/default, accent/press, accent/tint
bg/canvas, bg/elevated, bg/sober
ink/primary, ink/secondary, ink/muted, ink/onPhoto-dark, ink/onPhoto-light
border/hairline, border/strong
status/error, status/error-tint
focus/ring-on-light, focus/ring-on-photo
shape/md, shape/pill
spacing/400, spacing/500, spacing/600
type/label, type/title-md
motion/fast, motion/instant
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
