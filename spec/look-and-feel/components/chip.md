# Chip

Chips are the lightweight metadata primitive — tags, filters, categories. Three variants tune the affordance: tag chips are read-only, filter pills are toggleable, category chips are navigational. Minimum height 28 across all variants to keep them legible without dominating. Never use a chip where a button belongs — chips do not carry primary verbs.

## Variants

| Variant | Use | Shape | Affordance |
|---|---|---|---|
| `tag` | read-only metadata ("audiobook", "5 min") | `shape/sm` rounded rect | none — purely informational |
| `filter` | toggleable inclusion/exclusion in a list | `shape/pill` | tap to toggle on/off |
| `category` | navigates to a category surface | `shape/pill` | tap to navigate |

## States

| State | tag | filter | category |
|---|---|---|---|
| default | fill `accent/tint`, text `ink/primary` | fill `bg/elevated`, border `border/hairline`, text `ink/secondary` | fill `bg/elevated`, border `border/hairline`, text `ink/primary` |
| active | n/a | fill `ink/primary`, text `ink/onPhoto-light`, no border | n/a — chips navigate, not toggle |
| hover (CMS) | n/a | fill `accent/tint`, border `accent/default` | fill `accent/tint`, border `accent/default` |
| pressed | n/a | scale 0.97, `motion/fast` | scale 0.97 |
| focused | n/a | `focus/ring-on-light, focus/ring-on-photo` 2px outer | `focus/ring-on-light, focus/ring-on-photo` 2px outer |
| disabled | fill `border/hairline`, text `ink/placeholder` | text `ink/placeholder`, border `border/hairline` | text `ink/placeholder`, border `border/hairline` |
| with-count | "5 articles" inline in `type/caption-mono` | "audiobooks · 12" | "picture books · 24" |
| with-icon | leading 12px icon `ink/secondary` | leading 12px icon, color matches text | leading 12px icon `ink/secondary` |

## Sizes

| Size | Height | Pad X | Type token | Icon | Radius |
|---|---|---|---|---|---|
| `sm` | 28 | `spacing/400` (12) | `type/label` | 12pt | `shape/sm` (tag) / `shape/pill` (filter, category) |
| `md` | 32 | `spacing/500` (16) | `type/label` | 14pt | `shape/sm` (tag) / `shape/pill` (filter, category) |
| `lg` | 36 | `spacing/500` (16) | `type/title-md` | 16pt | `shape/pill` only |

`tag` chips never go `lg`. Filter and category default to `md`; `lg` is for hero-strip placements only.

## Rules

- Minimum height is 28. Below that, you have a label, not a chip.
- Tag chips are read-only — they do not navigate or toggle.
- Filter pills toggle; active filters fill `ink/primary` (high contrast), not `accent/default`.
- Category chips navigate; never use them as toggle filters.
- Labels are `type/label` UPPERCASE for `sm` / `md`; `type/title-md` sentence case for `lg`.
- One chip per metadatum — never stack two tags for the same property (no "5 min" + "short read").
- Filter strips show ALL state with a `quiet` "clear" affordance — never a checkbox to reset.
- Counts appear inline with a middle-dot separator: "audiobooks · 12". Never parentheses.
- Chips wrap in CMS, scroll horizontally on iOS — match the parent container's rule.
- On photo tiles, chips switch fill to `bg/elevated` @ 90% with `ink/primary` — never use a transparent fill with `ink/onPhoto-*` (the chrome must stay legible at chip-size type).
- Reduce-motion disables press scale; render instantly (every chip variant's `pressed` row collapses to `motion/instant`).
- `filter` "clear" affordance has a 44pt minimum hit area regardless of its 28-32pt visual height — pad outward.

## Render check

1. `tag` md on `article` card — "5 min · audiobook" pair beneath byline.
2. `filter` md strip — "all · picture books · audiobooks · poetry", "audiobooks" active in `ink/primary` fill.
3. `category` lg on library hero — "PICTURE BOOKS · 24" navigates to category surface.
4. `filter` md with count — "saved · 8" in `type/label` + `type/caption-mono`.
5. `tag` sm on `community` card — "advice" + "tweens" leading icons, `accent/tint` fill.

## Tokens used

```
bg/canvas, bg/elevated
ink/primary, ink/secondary, ink/muted, ink/placeholder, ink/onPhoto-dark, ink/onPhoto-light
border/hairline
accent/default, accent/tint
focus/ring-on-light, focus/ring-on-photo
shape/sm, shape/pill
spacing/400, spacing/500
type/label, type/title-md, type/caption-mono
motion/fast, motion/instant
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
