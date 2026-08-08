# Nav

Three navigation surfaces: bottom tab bar (iOS primary), top nav (article / detail context + CMS), and sub-nav chips (within-screen filtering). The tab bar holds the entire information architecture — five slots max. Top nav stays editorial: title centered, actions to the right, back arrow to the left. Sub-nav chips are horizontal-scroll on iOS, wrap on CMS.

## Variants

| Variant | Use | Surface | Height | Position |
|---|---|---|---|---|
| `tab-bar` | iOS primary nav | `bg/elevated` w/ hairline top | 64 + safe-area | bottom fixed |
| `top-nav` | screen header, back + title + action | `bg/canvas` (transparent on article hero) | 56 + safe-area | top fixed |
| `sub-nav` | within-screen filter / category strip | `bg/canvas` | 48 | beneath top-nav, scrolls with content |

## Tab bar slots (5 max) — beta-v1

| Slot | Icon | Label | Destination |
|---|---|---|---|
| 1 | house | `HOME` | the dashboard — coach nudge, kids, coming up, for you |
| 2 | message | `COACH` | the coaching agent |
| 3 | calendar | `PLAN` | the Chief-of-Staff activity board |
| 4 | person.2 | `CIRCLE` | parent community + DMs (carries the unread badge) |
| 5 | gearshape | `SETTINGS` | profile, library, saved, account |

**Five slots is a hard cap.** beta-v1 spent the sixth: `library` and `saved` moved into `SETTINGS`, and the library's primary route is now the ranked "for you" feed reached from the dashboard's `FOR YOU → See all`. Six labels needed `minimumScaleFactor` to survive a 375pt phone; five do not.

The raised center "ask" slot from the pre-beta spec is **gone** — there is no raised slot. The active tab is marked instead by a rounded-rect pill behind its icon, with the label in `accent/onCanvas` (the tab bar sits on canvas, so the fill hex would be an AA fail as text).

## States

| State | tab item | center "ask" | top-nav back | sub-nav chip |
|---|---|---|---|---|
| default | icon `ink/muted`, label `type/label` `ink/muted` | fill `accent/default`, icon `ink/onPhoto-light` | chevron `ink/primary`, no label | text `ink/secondary`, border `border/hairline` |
| active | icon `ink/primary`, label `ink/primary` w600 | fill `accent/press` while sheet open | n/a | fill `accent/tint`, text `ink/primary`, no border |
| pressed | scale 0.96, `motion/fast` | scale 0.98 | opacity 0.6 | scale 0.98 |
| focused | `focus/ring-on-light` inset 2px | `focus/ring-on-light` outer 2px | `focus/ring-on-light` outer 2px | `focus/ring-on-light` outer 2px |
| disabled | icon `ink/placeholder`, label `ink/placeholder` | never disabled — hide instead | hide | text `ink/placeholder`, no fill |
| with badge | dot `accent/default` 8px top-right of icon, no count | dot `status/warning` if kid-agent flagged | n/a | dot `accent/default` 6px top-right |
| reduced-motion | press scale removed (substitute `border/strong` flash 80ms); tab-switch crossfade disabled | scale → static fill `accent/press` swap | none | none |

Badge is a dot only — no numeric count. If you need a count, you need a sheet.

## Sizes

| Size | tab icon | tab label | top-nav title | sub-nav chip height |
|---|---|---|---|---|
| `iOS` | 24×24 | `type/label` 11/14 +6% | `type/title-md` centered | 32 |
| `CMS-compact` | 20×20 | `type/label` | `type/title-lg` left-aligned | 32 |
| `CMS-default` | 24×24 | `type/label` | `type/display-md` left-aligned | 36 |

Tab bar is iOS-only. CMS uses a left sidebar (out of scope of this file).

## Rules

- Five tab slots, period. Adding a sixth requires removing one.
- Center "ask" is always slot 3, always raised, always `shape/pill`.
- Top-nav title is centered on iOS, left-aligned on CMS — do not mix.
- Back arrow uses chevron, never "‹" or arrow-tail. Label-less unless screen depth >2.
- Sub-nav chips scroll horizontally on iOS — never wrap. Wrap on CMS only.
- Active sub-nav chip uses `accent/tint` fill, not `accent/default` — saturated fill is reserved for CTAs.
- Badge is a dot, never a number. If urgency requires a count, escalate to a sheet.
- Hairline at top of tab bar uses `border/hairline`; on dark/photo screens it lifts to `border/strong`.
- Reduce-motion disables tab-switch crossfade; render instantly.
- On article hero scroll, top-nav transitions from transparent to `bg/canvas` at scroll Y > hero height - 56.
- Tab labels are always visible — never icon-only.

## Render check

1. `tab-bar` iOS — five slots, "home" active, "ask" raised in `accent/default`, "community" with `accent/default` dot.
2. `top-nav` on `article` standard — transparent over hero, chevron back, no title; on scroll, fills with `bg/canvas` and reveals title.
3. `top-nav` on CMS — left-aligned `display-md` "library", `secondary` action button right.
4. `sub-nav` horizontal strip — "all · picture books · audiobooks · poetry" — "picture books" active in `accent/tint`.
5. `tab-bar` with kid-agent flagged — "you" slot carries `status/warning` dot.

## Tokens used

```
bg/canvas, bg/elevated
ink/primary, ink/secondary, ink/muted, ink/placeholder, ink/onPhoto-light
border/hairline, border/strong
accent/default, accent/press, accent/tint
status/warning
focus/ring-on-light
shape/md, shape/pill
spacing/300, spacing/400, spacing/500, spacing/600
type/label, type/title-md, type/title-lg, type/display-md
motion/fast, motion/base, motion/instant
elevation/0, elevation/1
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
