# Empty / Loading / Error / First-Run

The four "nothing to show" states. Each is a real composition — not an afterthought. A tired parent who hits a loading spinner or an empty list deserves the same care as one who hits a populated feed. Copy is warm, specific, and never blames the user. Kid-agent and crisis surfaces FORBID skeleton placeholders — they imply content is "coming" and that's a trust violation when none may exist.

## Variants

| Variant | Use | Surface | Composition |
|---|---|---|---|
| `empty` | a populated slot that has zero items | `bg/canvas` | warm icon + title + body + optional `secondary` CTA |
| `loading-spinner` | unknown duration, sober surface, or kid-agent | `bg/canvas` / `bg/sober` | centered spinner `accent/default`, no copy |
| `loading-skeleton` | known shape, light-mode list | `bg/canvas` | grey blocks matching real layout, `border/hairline` fill |
| `error` | request failed | `bg/canvas` | icon `status/error` + warm copy + retry `secondary` |
| `first-run` | onboarding-adjacent, never-populated slot | `bg/canvas` | hero illustration-equivalent (photo tile) + title + body + `primary` CTA |

## States (composition matrix)

| State | Icon / hero | Title | Body | Action |
|---|---|---|---|---|
| empty | `ink/muted` 24pt outline | `type/title-lg` `ink/primary` | `type/body-md` `ink/secondary`, 1-2 sentences | optional `secondary` md |
| loading-spinner | spinner 24pt `accent/default`, `motion/slow` rotation | none | optional "loading…" `type/caption-mono` `ink/muted` after 1.5s | none |
| loading-skeleton | n/a | block 60% width × 24h | 3 blocks 100%/85%/70% width × 16h | n/a |
| error | `status/error` 24pt | `type/title-lg` `ink/primary` | `type/body-md` `ink/secondary`, specific cause | `secondary` md "try again" |
| first-run | `photo/*` tile 1:1 | `type/display-md` `ink/primary` | `type/body-lg` `ink/secondary` | `primary` lg |

## Surface rules (the forbidden matrix)

| Surface | empty | loading-spinner | loading-skeleton | error | first-run |
|---|---|---|---|---|---|
| home / library / community | OK | OK | OK | OK | OK |
| `kid-agent` | OK | OK | **FORBIDDEN** | OK | OK |
| `crisis` | OK (sober copy) | OK | **FORBIDDEN** | OK (sober copy) | OK |
| `article` reading view | n/a | OK | OK | OK | n/a |

Skeleton placeholders on kid-agent or crisis surfaces are forbidden because they imply content will arrive — a guarantee we cannot honor on safety-critical paths.

## Sizes

| Size | Hero | Title | Body | Vertical pad |
|---|---|---|---|---|
| `inline` | 24pt icon | `type/title-md` | `type/body-sm` | `spacing/600` (20) |
| `block` | 48pt icon or 160×160 photo tile | `type/title-lg` | `type/body-md` | `spacing/800` (32) |
| `full` | 240×240 photo tile or `display-md` headline | `type/display-md` | `type/body-lg` | `spacing/1000` (40) |

## Rules

- Empty states get a warm icon, never a sad face, never an exclamation mark.
- Loading copy ("loading…") only appears after 1500ms — don't flash it for fast requests.
- Skeleton blocks match the real layout's grid; never use generic "lorem" boxes.
- Skeletons are forbidden on kid-agent and crisis surfaces — use spinner only.
- Error copy is specific and warm: "couldn't load articles — pull to refresh", not "Error 500" or "Something went wrong".
- Retry actions are `secondary`, never `primary` — the parent didn't fail, the request did.
- First-run surfaces always include a photo or photo-tile hero — never icon-only.
- Crisis-surface empty / error copy is sober: no exclamation marks, no "oops", no casual register.
- Spinner animates at `motion/slow` (320ms full rotation × indefinite); reduce-motion replaces with static dot pulse `motion/base`.
- Never combine skeleton + spinner on the same surface — pick one.
- Empty-state CTAs lead the parent somewhere useful — never just dismiss.

## Render check

1. `empty` block — library "saved" tab with zero items: bookmark icon `ink/muted`, "your saved articles will live here", `secondary` "browse library".
2. `loading-skeleton` inline — home feed loading three article cards, blocks matching `card/article` md.
3. `loading-spinner` on `bg/sober` — kid-agent session connecting, spinner centered, "loading…" after 1.5s in caption-mono.
4. `error` block — community feed failed: `status/error` icon, "couldn't load posts — your connection looks shaky", `secondary` "try again".
5. `first-run` full — kid-agent never-configured: 240×240 `photo/saffron` tile, `display-md` "set up your kid-agent", body explainer, `primary` lg "get started". Label on tile uses `ink/onPhoto-dark`.

## Tokens used

```
bg/canvas, bg/sober, bg/elevated
ink/primary, ink/secondary, ink/muted, ink/placeholder, ink/onPhoto-dark, ink/onPhoto-light
border/hairline
accent/default
status/error, status/warning
photo/saffron, photo/rose, photo/royal, photo/forest
shape/md, shape/lg
spacing/500, spacing/600, spacing/800, spacing/1000
type/display-md, type/title-md, type/title-lg, type/body-sm, type/body-md, type/body-lg, type/caption-mono
motion/base, motion/slow, motion/instant
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
