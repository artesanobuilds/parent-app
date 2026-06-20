# Sheet

Sheets are the overlay primitive — modal, partial (iOS detents), action, and drawer. Backdrop is `neutral/ink-900` @ 40% opacity across all variants; sheet body is `bg/elevated`. Each variant trades how much the underlying surface remains visible. Sheets carry their own top-nav (handle on iOS, header on CMS) and a single dismiss affordance — never two.

## Variants

| Variant | Use | Surface | Dismiss |
|---|---|---|---|
| `modal` | blocking decision (confirm, edit profile) | `bg/elevated`, centered or fullscreen on iOS | `quiet` "close" top-right + backdrop tap |
| `partial` | non-blocking detail (article preview, post composer) | `bg/elevated`, iOS detents `[medium, large]` | drag handle + swipe-down + backdrop tap |
| `action` | short list of choices (share, more options) | `bg/elevated`, bottom-anchored, list rows | "cancel" row + backdrop tap |
| `drawer` | CMS-only side panel (filters, kid-agent config) | `bg/elevated`, slides from right, 420px | `quiet` "close" top-right + backdrop tap + Esc |

## States

| State | modal | partial | action | drawer |
|---|---|---|---|---|
| default | centered, backdrop 40% | detent `medium` (50%), backdrop 30% | bottom-anchored, backdrop 40% | slides right, backdrop 40% |
| expanded | n/a | detent `large` (92%), backdrop 50% | n/a | n/a |
| dismissing | fade + scale 0.96, `motion/base` | slide down, `motion/spring` | slide down, `motion/base` | slide right, `motion/base` |
| focused (input within) | sheet rises 16px above keyboard | detent escalates to `large` | n/a | scrollable column maintains focus |
| loading content | spinner centered, sheet chrome intact | spinner at detent `medium` | n/a | skeleton list in body |
| error | inline `empty` `error` block within sheet body | inline error block | "couldn't share — try again" row in `status/error` | inline error block |
| reduced-motion | fade only, `motion/fast`, no scale; backdrop blur disabled | fade only, no spring / no slide; detent set instantly | fade only | fade only, no slide |

## Sizes

| Size | modal width | partial detents (iOS) | action max items | drawer width |
|---|---|---|---|---|
| `sm` | 320 (CMS) | `[small, medium]` | 4 | 360 |
| `md` | 480 (CMS) | `[medium, large]` | 6 | 420 |
| `lg` | 640 (CMS) | `[large]` only | n/a — escalate to partial | 520 |

On iOS, modal goes fullscreen at viewport <375; on CMS, modal centers and caps at 90vh.

## Backdrop

Backdrop is `neutral/ink-900` at the opacities above. Backdrop blur is `motion/base` 8pt Gaussian on iOS (respects reduce-transparency). On CMS the backdrop is solid color, no blur. Tapping the backdrop dismisses on all variants except `modal` carrying a destructive decision — that requires the explicit close affordance.

## Rules

- One sheet at a time. Never stack sheets — escalate to a new screen instead.
- Modal sheets confirming destructive actions disable backdrop-dismiss; require explicit close.
- Partial sheets on iOS use `presentationDetents`; never set custom heights inline.
- Sheet header height is 56 + safe area; title `type/title-md` centered (iOS) / left (CMS).
- Drag handle (iOS partial only): 36×4, `ink/placeholder`, `shape/pill`, top-center, top inset 8.
- Action sheets max 6 rows. More than that, redesign — likely needs a partial sheet with a list.
- "Cancel" in action sheets is the LAST row, separated by `spacing/300` gap (iOS convention).
- Keyboard-open: partial sheets escalate detent to `large` to keep the focused field visible.
- Sheets get `elevation/3` (CMS) or no shadow on iOS — the backdrop carries the depth instead.
- Reduce-motion replaces spring transitions with `motion/fast` linear; no scale, no slide.
- Drawer (CMS) traps focus while open; Esc closes; first focusable element receives focus on mount.

## Render check

1. `modal` md on CMS — "delete this kid's data?" with `secondary` + `danger` modifier confirm + `secondary` cancel, backdrop dismiss disabled.
2. `partial` iOS detent `medium` — community post composer with `multiline` form, autosaving in caption-mono.
3. `action` iOS — share sheet with 4 rows (copy link, save, share, report) + cancel row.
4. `drawer` CMS — kid-agent config panel sliding from right, 420px wide, scrollable form column.
5. `partial` iOS detent `large` — article preview sheet with `article` standard layout inside, hero + body.

## Tokens used

```
bg/canvas, bg/elevated, bg/sober
ink/primary, ink/secondary, ink/muted, ink/placeholder, ink/onPhoto-light
neutral/ink-900
border/hairline
accent/default
status/error
focus/ring-on-light
shape/md, shape/lg, shape/pill
spacing/300, spacing/400, spacing/500, spacing/600, spacing/700
type/label, type/title-md, type/title-lg, type/body-md, type/caption-mono
motion/fast, motion/base, motion/spring, motion/instant
elevation/0, elevation/3
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
