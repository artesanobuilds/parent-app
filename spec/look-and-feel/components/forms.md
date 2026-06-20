# Forms

Forms carry the highest cognitive load in the product — onboarding, kid setup, profile edits. Visual weight stays light; the input itself is the primitive, the label is the work. One field per row on iOS. Labels above, never floating, never inside. Helper text below in `ink/muted`; error text replaces (does not stack with) helper. Tired parents type at 11pm — generous targets, forgiving copy.

## Variants

| Variant | Use | Affordance | Notes |
|---|---|---|---|
| `text` | name, email, single-line free entry | underline or boxed (see size) | autocapitalize per semantic role |
| `select` | constrained list, ≤7 options | chevron-right disclosure | iOS picker sheet; CMS native `<select>` styled |
| `checkbox` | independent multi-pick + boolean consent | 18×18 box, `shape/sm` | label is the tap target |
| `radio` | mutually exclusive, ≤5 options | 18×18 circle | group label required |
| `date` | birthday, milestones, schedule | inline wheel (iOS) / native picker (CMS) | never free-text dates |
| `multiline` | journaling, post body, kid-agent notes | resizes to 6 rows, then scrolls | grow upward in sheets |

## States

| State | text / multiline | select | checkbox / radio | date |
|---|---|---|---|---|
| empty | placeholder `ink/placeholder`, border `border/hairline` | "select…" `ink/placeholder` | unfilled, border `border/strong` | placeholder format `MM / DD / YYYY` in `ink/placeholder` |
| filled | text `ink/primary`, border `border/hairline` | value `ink/primary`, chevron `ink/muted` | filled `accent/default`, check/dot `ink/onPhoto-light` | date `ink/primary`, mono token |
| focused | border `accent/default` 2px, ring `focus/ring-on-light` outer | border `accent/default` 2px | ring `focus/ring-on-light` 2px | border `accent/default` 2px |
| reduced-motion | focus ring renders instantly (no `motion/fast` ease-in); error/blur transitions collapse to `motion/instant` | same | same | same |
| error | border `status/error` 2px, helper → error copy | border `status/error` 2px | border `status/error`, label `status/error` | border `status/error` 2px |
| disabled | bg `border/hairline`, text `ink/placeholder` | text `ink/placeholder`, chevron faded | filled `border/strong`, no ring | text `ink/placeholder`, picker inert |

## Sizes

| Size | Height (single-line) | Pad X | Pad Y | Label type | Input type | Helper type |
|---|---|---|---|---|---|---|
| `sm` | 36 | `spacing/400` (12) | `spacing/300` (8) | `type/label` | `type/body-sm` | `type/caption-mono` |
| `md` | 44 | `spacing/500` (16) | `spacing/400` (12) | `type/label` | `type/body-md` | `type/body-sm` |
| `lg` | 52 | `spacing/500` (16) | `spacing/500` (16) | `type/title-md` | `type/body-lg` | `type/body-sm` |

`md` is the default on iOS (44 meets touch min). `multiline` follows `md` width + pad, height = `lineHeight * rows + 2 * padY`.

## Rules

- Labels live ABOVE the input. Never inside. Never floating.
- One field per row on iOS; CMS may pair two short fields (`zip` + `state`) on one row at ≥`md` viewport.
- Helper text and error text occupy the same vertical slot — never both.
- Errors are warm and specific: "we need a valid email to send your weekly digest" — not "invalid format".
- Required fields are marked with a trailing `·` in `accent/default`, never an asterisk.
- iOS keyboards match semantic role (`emailAddress`, `numberPad`, `oneTimeCode`); set `textContentType` for autofill.
- `select` with >7 options upgrades to a search-enabled `sheet/partial`, not a long picker.
- `date` never accepts free-text; always native picker. Display format follows locale; storage is ISO 8601.
- Checkbox/radio groups need a group label (`fieldset` legend / SwiftUI `.accessibilityElement(children: .combine)`).
- On sober surfaces (kid-agent setup, crisis intake): no inline validation animations — validate on blur only.
- Autosave drafts on `multiline` every 4s of idle; surface "saved" in `type/caption-mono` `ink/muted`.

## Render check

1. `text` md with helper — "email" field on onboarding step 2, helper "we'll send your weekly digest here".
2. `text` md error state — "this email looks off — try again?" in `status/error`, no shake animation.
3. `select` md — "kid's age" picker on kid-agent setup, opens partial sheet with 18 options.
4. `radio` group of 3 — "how often do you want check-ins?" daily / weekly / off.
5. `multiline` md autosaving — community post composer, "saved 3s ago" in caption-mono.

## Tokens used

```
bg/canvas, bg/elevated
ink/primary, ink/muted, ink/placeholder, ink/onPhoto-light
border/hairline, border/strong
accent/default, accent/tint
status/error
focus/ring-on-light
shape/sm, shape/md
spacing/300, spacing/400, spacing/500
type/label, type/title-md, type/body-sm, type/body-md, type/body-lg, type/caption-mono
motion/fast
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
