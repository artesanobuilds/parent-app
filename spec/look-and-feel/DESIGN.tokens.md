# DESIGN.tokens.md — Hearth Token Allowlist

This is the **only** file in the system where raw hex values, font names, spacing numbers, radii, and shadow definitions live. Every other file references tokens by name. If a value isn't named here, it doesn't exist in Hearth — open a discussion before adding.

Token naming uses `category/name` (e.g. `bg/canvas`, `ink/primary`, `accent/default`). Primitives are the raw values; semantics are the names code consumes. Always emit semantic tokens unless you're maintaining a primitive.

## Color — primitives

The raw palette. Code should rarely reference these directly — use the semantic layer below.

| Token | Hex | Use |
|---|---|---|
| `neutral/cream-50` | `#FAF7F2` | page bg (light) |
| `neutral/cream-100` | `#F3F0EB` | canvas (default) |
| `neutral/cream-200` | `#E9E4DC` | subtle hairline / disabled fill |
| `neutral/ink-900` | `#1A1A1A` | primary text on cream |
| `neutral/ink-700` | `#2D2D2D` | softer primary text on cream |
| `neutral/ink-500` | `#6F6A60` | muted text (warm gray) |
| `neutral/ink-300` | `#8A8275` | tertiary / placeholder (≥3:1 on cream; governed by WCAG 1.4.11) |
| `neutral/paper` | `#FFFFFF` | elevated card bg |
| `brand/olive-700` | `#3A4A2A` | accent press / dense use |
| `brand/olive-500` | `#4F5D3A` | accent default (CTAs) |
| `brand/olive-100` | `#E8EBDC` | accent tint (chip bg) |
| `photo/saffron` | `#E8A33C` | tile bg — energy / play |
| `photo/rose` | `#B86A60` | tile bg — emotional / care (terracotta family) |
| `photo/royal` | `#2E3A5F` | tile bg — focus / learning (desaturated ink-indigo) |
| `photo/forest` | `#2D3F2C` | tile bg — nature / outdoors |
| `status/success` | `#3D6B3D` | success state |
| `status/warning` | `#8A6420` | warning state (≥4.5:1 on cream) |
| `status/error` | `#A03A3A` | error state |
| `status/info` | `#2E3A5F` | info state (shares hex with photo/royal — intentional) |
| `status/error-tint` | `#F6E4E4` | error inline-background / toast (≥12:1 with ink/primary) |
| `status/warning-tint` | `#F5EAD2` | warning inline-background / toast |
| `status/success-tint` | `#DCE7DC` | success inline-background / toast |

## Color — semantic

The names code consumes. Component specs reference these exclusively.

| Token | Resolves to | Use |
|---|---|---|
| `bg/canvas` | `neutral/cream-100` | default page background |
| `bg/elevated` | `neutral/paper` | card / sheet background |
| `bg/sober` | `neutral/cream-50` | crisis-lock / kid-agent surface; quieter than canvas |
| `ink/primary` | `neutral/ink-900` | body text + headlines |
| `ink/secondary` | `neutral/ink-700` | secondary text + softer headlines |
| `ink/muted` | `neutral/ink-500` | metadata, captions, helper text |
| `ink/placeholder` | `neutral/ink-300` | input placeholder, tertiary (UI ≥3:1, not for instruction text) |
| `ink/onPhoto-dark` | `neutral/ink-900` | text on warm/light photo tiles (`photo/saffron`, `photo/rose`) — AA-pass |
| `ink/onPhoto-light` | `neutral/paper` | text on dark photo tiles (`photo/royal`, `photo/forest`) — AA-pass |
| `border/hairline` | `neutral/cream-200` | dividers, subtle separators, disabled fills |
| `border/strong` | `neutral/ink-300` | input borders, strong dividers |
| `accent/default` | `brand/olive-500` | primary CTA, active state |
| `accent/press` | `brand/olive-700` | primary CTA pressed / active dense |
| `accent/tint` | `brand/olive-100` | chip background, accent-on-canvas fills |
| `focus/ring-on-light` | `brand/olive-500`, 2pt outset | focus ring on cream/paper surfaces (6.24:1 AA) |
| `focus/ring-on-photo` | `neutral/paper`, 2pt outset | focus ring on saturated `photo/*` tiles (≥4.8:1 on shipped photo tokens) |

`focus/ring-on-light` is the default; `focus/ring-on-photo` is required on every `photo/*` overlay. Component specs MUST pick the variant per surface — there is no universal `focus/ring`.

## Typography — font stack

Free fonts only. Self-hosted at `spec/look-and-feel/fonts/`; never pulled from a CDN at runtime.

| Family | Role | Files | Fallback |
|---|---|---|---|
| **Fraunces** | Display (hero, h1, h2) | Variable, opsz + wght axes | `Georgia, serif` |
| **Inter** | Sans (body + UI) | Variable, wght axis | `-apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif` |
| **JetBrains Mono** | Mono (metadata only) | Regular + Medium | `ui-monospace, "SF Mono", monospace` |

## Typography — scale

| Token | Family | Size / Line | Tracking | Weight | Use |
|---|---|---|---|---|---|
| `type/display-xl` | Fraunces | 56 / 60 | -1% | 700 | hero headline (iPhone); 80/84 on CMS |
| `type/display-lg` | Fraunces | 40 / 44 | -1% | 700 | screen title |
| `type/display-md` | Fraunces | 28 / 32 | 0% | 600 | section header |
| `type/title-lg` | Inter | 20 / 24 | 0% | 600 | card title |
| `type/title-md` | Inter | 16 / 22 | 0% | 600 | inline header |
| `type/body-lg` | Inter | 17 / 26 | 0% | 400 | reading body (articles) |
| `type/body-md` | Inter | 15 / 22 | 0% | 400 | UI body (default) |
| `type/body-sm` | Inter | 13 / 18 | 0% | 400 | secondary text |
| `type/label` | Inter | 11 / 14 | +6% | 600 | UPPERCASE nav labels, tag chips |
| `type/caption-mono` | JetBrains Mono | 12 / 16 | 0% | 400 | byline, read-time, dates, metadata |

Display sizes assume iPhone-class viewports. CMS doubles `display-xl` to 80/84; all other sizes are surface-agnostic.

## Spacing scale

Tokens in pt on iOS, px on CMS — 1:1 mapping. Nine steps, geometric. No hairline-gap step (use `spacing/300` or no gap) and no aspirational hero steps (compose with multiples in the spec if you ever need them).

| Token | Value | Common use |
|---|---|---|
| `spacing/0` | 0 | reset |
| `spacing/300` | 8 | inline gap, chip padding |
| `spacing/400` | 12 | small component padding |
| `spacing/500` | 16 | default component padding, list item gap |
| `spacing/600` | 20 | medium padding |
| `spacing/700` | 24 | **page gutter (iOS default — step 5)** |
| `spacing/800` | 32 | section vertical rhythm (min — step 6) |
| `spacing/900` | 40 | section vertical rhythm (default — step 6) |
| `spacing/1000` | 56 | section vertical rhythm (generous — step 7) |

Page gutter on iOS = `spacing/700`. Section vertical rhythm = `spacing/800`–`spacing/1000`. If a one-off hero gap demands 72/96, write `spacing/700 * 3` or `spacing/700 * 4` in the spec — do not tokenize one-shots.

## Shape — radius

| Token | Value | Use |
|---|---|---|
| `shape/none` | 0 | full-bleed, no rounding |
| `shape/sm` | 4 | chips, tags, small pills |
| `shape/md` | 12 | buttons, inputs, small cards |
| `shape/lg` | 20 | primary cards |
| `shape/xl` | 28 | hero tiles |
| `shape/pill` | 999 | filter pills, "shop now"-style CTAs (Wonder Valley move) |

Stroke widths are not tokenized — use `1pt` / `1px` for hairlines, `2pt` / `2px` for focus rings. If a third weight emerges, tokenize then.

## Motion

| Token | Value | Use |
|---|---|---|
| `motion/instant` | 0ms | reduced-motion fallback for every animation |
| `motion/fast` | 120ms ease-out | hover / press feedback, focus ring |
| `motion/base` | 200ms ease-out | default transition, sheet open |
| `motion/slow` | 320ms ease-in-out | page transitions, large state changes |
| `motion/spring` | `interactiveSpring(response: 0.4, dampingFraction: 0.85)` | iOS gesture-driven motion only |

`prefers-reduced-motion` (web) / `accessibilityReduceMotion` (iOS) collapses every token above to `motion/instant`. This is a hard branch — no exceptions, no opt-outs.

## Elevation — shadow

Lounge posture: chrome quiet, hairline + paper layering, not drop shadows. Cards on `bg/canvas` should prefer `border/hairline` + `bg/elevated` to lift. Shadows are reserved for true overlays (sheets, modals).

| Token | Value | Use |
|---|---|---|
| `elevation/0` | none | flat surfaces, photo tiles, cards on canvas (default — pair with `border/hairline` + `bg/elevated`) |
| `elevation/1` | reserved | **do not use for cards.** prefer `border/hairline` + `bg/elevated`. retained only for legacy / dark-mode review |
| `elevation/2` | `0 4px 12px rgba(26,26,26,0.08)` | sticky nav, raised toast |
| `elevation/3` | `0 12px 32px rgba(26,26,26,0.12)` | modal sheet, partial sheet, drawer |

The rgba base is `neutral/ink-900` at the noted alpha. This is a composed shadow recipe documented honestly — the alphas are not consumed elsewhere as color tokens.

## Tokens used (this file)

This is the source-of-truth file; it defines, not consumes. Every other Hearth file's "Tokens used" section will reference names from this allowlist.

## Rules

- Never inline a hex value outside this file.
- Never invent a token name. Allowlist only.
- Reference semantic tokens (`ink/primary`) before primitives (`neutral/ink-900`).
- Spacing follows the scale; never `spacing/650`. If a one-off bigger gap is needed, compose with multiples in-spec — do not tokenize one-shots.
- Motion always specifies the `motion/instant` collapse path. Every component states table must include a `reduced-motion` row.
- `photo/*` tokens are color blocks, not theme-responsive — they do not invert in dark mode. Four tokens only: `saffron`, `rose`, `royal`, `forest`.
- Sober surfaces use `bg/sober`, not `bg/canvas`.
- `ink/onPhoto` is split: `ink/onPhoto-dark` on warm tiles (saffron, rose), `ink/onPhoto-light` on dark tiles (royal, forest). `type/label` (11pt) over a photo tile MUST resolve to the AA-pass variant.
- `focus/ring` is split into `focus/ring-on-light` and `focus/ring-on-photo`. Component specs pick the variant per surface.
- Contrast: every token pair declared in a component spec is gated by `tools/lint-design-tokens.py --contrast`; AA-text floor 4.5:1, UI floor 3:1.
- Display type uses Fraunces; UI and reading use Inter; metadata uses JetBrains Mono. No fourth family.
- Token additions require a discussion. Drift kills systems.

---

status: ✅ active
owner: Miguel
last_updated: 2026-05-31
