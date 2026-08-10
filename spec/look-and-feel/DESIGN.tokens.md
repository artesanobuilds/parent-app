# DESIGN.tokens.md — Hearth Token Allowlist

This is the **only** file in the system where raw hex values, font names, spacing numbers, radii, and shadow definitions live. Every other file references tokens by name. If a value isn't named here, it doesn't exist in Hearth — open a discussion before adding.

Token naming uses `category/name` (e.g. `bg/canvas`, `ink/primary`, `accent/default`). Primitives are the raw values; semantics are the names code consumes. Always emit semantic tokens unless you're maintaining a primitive.

## Color — primitives

The raw palette. Code should rarely reference these directly — use the semantic layer below.

> **beta-v1 (2026-08-07).** Greg's `mvp-beta-v1` redesign moved the accent family
> olive → teal, added a second KID accent (saffron) for companion surfaces, added a
> dark voice surface, and **darkened the canvas** from `cream-100` to `cream-200`.
> That last change is the one to be careful about: it silently broke two pairs that
> passed on the lighter ground. `ink-500` and the accent-as-text case were both
> re-derived — see the notes under each. Values below are sampled pixel-accurately
> from the Figma renders; the variable *names* are unconfirmed until that file
> grants edit access.

| Token | Hex | Use |
|---|---|---|
| `neutral/cream-50` | `#FCFBF8` | **Dashboard 1 coach banner** — warmest ground, distinct from cream-100 |
| `neutral/cream-100` | `#F3F0EB` | **sober** surface (was the canvas pre-beta) |
| `neutral/cream-150` | `#F5F3EF` | **card / sheet ground** — the account sheet, and the INK on teal cards |
| `neutral/cream-200` | `#E9E4DC` | **canvas (default page bg)** |
| `neutral/cream-300` | `#DAD4CA` | hairline / divider — darkened so it stays visible on cream-200 |
| `neutral/warm-gray-400` | `#B8B4AC` | disabled control fill |
| `neutral/warm-gray-500` | `#989591` | **eyebrow ink** — FOR YOU / COMING UP item category labels |
| `neutral/gray-500` | `#858585` | neutral control fill — sign out (NOT the warm gray above) |
| `neutral/sage-200` | `#DAE0DF` | **selected** state — tab pill, segmented control. Warmer than `brand/teal-100`; do not substitute |
| `neutral/ink-900` | `#1A1A1A` | primary text on cream |
| `neutral/ink-800` | `#1E1E1E` | sheet headline + subtitle (account sheet) |
| `neutral/ink-header` | `#2B2925` | card/section header ink; also the sheet scrim |
| `neutral/ink-700` | `#2D2D2D` | softer primary text on cream |
| `neutral/ink-500` | `#666157` | muted text (warm gray). Was `#6F6A60`, which is **4.25:1 on cream-200 — an AA fail**. Do not revert. |
| `neutral/ink-300` | `#8A8275` | tertiary / placeholder (exactly 3.00:1 on cream-200 — at the UI floor, never for instruction text) |
| `neutral/paper` | `#FFFFFF` | elevated card bg |
| `funnel/button-charcoal` | `#4A4741` | **funnel primary-button fill** (sprint-1, 2026-08-08) — white on it = 9.26:1. Deliberately NOT the teal accent: the funnel reads sober and minimal; teal is the in-app accent |
| `funnel/border-input` | `#C9C5BE` | funnel pill input 1px stroke (1.51:1 on cream-50 — decorative, not a boundary indicator) |
| `funnel/border-chip` | `#E9E4DC` | funnel chip outline 1px stroke (1.22:1 on cream-50 — decorative, not a boundary indicator) |
| `brand/teal-deep` | `#0A5570` | deepest accent, **fill only** — the chat-input strip and the count badge on the Plan segment (sprint-2 measured). Cream on it = 7.44:1, paper = 8.25:1 |
| `brand/teal-700` | `#12556F` | accent press / dense use |
| `brand/teal-600` | `#1B7498` | accent as **text or icon on cream**. **Was `#186A8B` (4.78:1)**; set equal to teal-500 on 2026-08-07 for exact Figma fidelity — see the deviation note below |
| `brand/teal-500` | `#1B7498` | accent **fill** — CTAs, avatars (white on it = 5.25:1) |
| `brand/teal-100` | `#DCE9EF` | accent tint (chip bg) |
| `kid/saffron` | `#E89C2E` | companion avatars, kid monograms, kid-card borders |
| `kid/saffron-tint` | `#F8EBD6` | companion card ground |
| `surface/voice-navy` | `#2E3A5F` | kid voice-call full-bleed ground (shares its hex with `photo/royal` — intentional) |
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
| `bg/canvas` | `neutral/cream-200` | default page background |
| `bg/elevated` | `neutral/paper` | card / sheet background |
| `bg/sober` | `neutral/cream-100` | crisis-lock / kid-agent surface; quieter than canvas |
| `bg/coachBanner` | `neutral/cream-50` | Dashboard 1 coach banner — warmest ground |
| `bg/voice` | `surface/voice-navy` | kid voice-call surface — the only dark ground in a light-locked app |
| `bg/disabled` | `neutral/warm-gray-400` | inert control fill. Pair with `ink/secondary`; **white on it is 2.07:1** |
| `ink/primary` | `neutral/ink-900` | body text + headlines |
| `ink/secondary` | `neutral/ink-700` | secondary text + softer headlines |
| `ink/muted` | `neutral/ink-500` | metadata, captions, helper text |
| `ink/eyebrow` | `neutral/warm-gray-500` | FOR YOU / COMING UP item eyebrows (category labels) |
| `ink/placeholder` | `neutral/ink-300` | input placeholder, tertiary (UI ≥3:1, not for instruction text) |
| `ink/onPhoto-dark` | `neutral/ink-900` | text on warm/light tiles (`photo/saffron`, `photo/rose`, `kid/saffron`) — AA-pass |
| `ink/onPhoto-light` | `neutral/paper` | text on dark tiles (`photo/royal`, `photo/forest`, `bg/voice`) — AA-pass |
| `border/hairline` | `neutral/cream-300` | dividers, separators, input borders |
| `border/strong` | `neutral/ink-300` | strong dividers |
| `accent/default` | `brand/teal-500` | primary CTA **fill**, active state, avatar fill |
| `accent/onCanvas` | `brand/teal-600` | accent **text or icon drawn directly on cream** |
| `accent/press` | `brand/teal-700` | primary CTA pressed / active dense |
| `accent/tint` | `brand/teal-100` | chip background, accent-on-canvas fills |
| `accent/kid` | `kid/saffron` | companion avatar, kid monogram, kid-card border |
| `accent/kid-tint` | `kid/saffron-tint` | companion card ground |
| `focus/ring-on-light` | `brand/teal-600`, 2pt outset | focus ring on cream/paper surfaces (4.78:1) |
| `focus/ring-on-photo` | `neutral/paper`, 2pt outset | focus ring on saturated tiles and `bg/voice` |

`focus/ring-on-light` is the default; `focus/ring-on-photo` is required on every `photo/*` overlay and on `bg/voice`. Component specs MUST pick the variant per surface — there is no universal `focus/ring`.

### The accent is split in NAME only — and that is deliberate

`accent/default` and `accent/onCanvas` currently resolve to the **same hex** (`#1B7498`).

The split exists because `#1B7498` behaves differently by surface: white on it is 5.25:1 (every primary button), but the same hex **as text on `bg/canvas` is 4.15:1 — an AA fail** for anything under 18.66px. `accent/onCanvas` was `#186A8B` (4.78:1, passing) until **2026-08-07**, when Miguel chose exact fidelity to Greg's Figma over the fix.

**Keep the two names.** They record *where* each colour is used, so reverting is a one-line change to `HearthPrimitives.teal600` rather than re-auditing every call site. The failing pairs are WAIVED with measured ratios in `tools/lint-design-tokens.py`, and the deviation is raised with Greg in the Figma eng-review comment.

Everything drawn on cream at small sizes — nav labels, "See all", inline links — is therefore below AA today. That is a known, recorded product decision, not drift.

### Known deviation — white on `accent/kid`

Greg's kid monogram is a white letter on saffron: **2.28:1**, below even the 3:1 large-text floor. It ships as drawn, on one condition — the monogram is decorative and never the sole carrier of its information, because the kid's name is always rendered adjacent to it. Any saffron surface carrying text that *is* the only carrier of its meaning must use `ink/onPhoto-dark` (7.65:1) instead.

### Per-kid accent

Kid cards take one of four accents: `kid/saffron`, `brand/teal-500`, `photo/rose`, `photo/forest`. The choice is derived from a **stable kid identifier** via a deterministic hash — never from list index (deleting the first kid would recolor every remaining one) and never from the display name (it would change on rename; same class of bug as name-as-dictionary-key).

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
| `type/display-hero` | Fraunces | 72 / 76 | -1% | 700 | beta-v1 warm-up progress numeral |
| `type/label` | Inter | 11 / 14 | +6% | 600 | UPPERCASE nav labels, tag chips |
| `type/label-serif` | Fraunces | 13 / 16 | +4% | 700 | **beta-v1 section headers** — `COACH`, `YOUR KIDS`, `COMING UP`, `FOR YOU`, `COMPANION`, `WHAT WE'VE LEARNED`. UPPERCASE, paired with a leading icon |
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
| `shape/sm` | 4 | tags, small markers |
| `shape/button` | 8 | **buttons / CTAs** (beta-v1: Greg's CTAs are tight rects, not capsules) |
| `shape/seeAll` | 10 | COMING UP "See all" affordance (Dashboard 1) |
| `shape/tile` | 12 | kid photo tile (Dashboard 1/2) |
| `shape/md` | 12 | inputs, small cards |
| `shape/lg` | 20 | primary cards |
| `shape/sheet` | 24 | account/profile sheet |
| `shape/section` | 28 | Home section card grounds (YOUR KIDS, coach banner) |
| `shape/xl` | 28 | hero tiles, modal sheets |
| `shape/pill` | 999 | selection + filter chips, avatar rings |

beta-v1 note: primary CTAs moved from `shape/pill` to `shape/button`. Chips stay `shape/pill`. If you are converting an old surface, that is the one substitution to make — a capsule button is now off-system.

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

**beta-v1 reverses the pre-beta rule.** Hearth used to lift cards with `border/hairline` + `bg/elevated` and reserve shadows for true overlays. Greg's dashboard and kid-settings sheet put a soft ambient shadow on every content card and no hairline at all. So the shadow is now the card default, and `border/hairline` is demoted to dividers, separators, and input borders.

The lounge posture still holds — the shadow is ambient and wide, not a hard drop. If a card reads as "lifted off the page" rather than "resting on it", the radius is too small or the alpha too high.

| Token | Value | Use |
|---|---|---|
| `elevation/0` | none | flat surfaces, photo tiles, full-bleed grounds |
| `elevation/1` | `0 3px 10px rgba(26,26,26,0.06)` | **card default** — content cards on `bg/canvas` |
| `elevation/2` | `0 4px 12px rgba(26,26,26,0.08)` | sticky nav, raised toast |
| `elevation/3` | `0 12px 32px rgba(26,26,26,0.12)` | modal sheet, partial sheet, drawer |

On iOS these are applied through `.hearthCardElevation()` / `.hearthNavElevation()` / `.hearthOverlayElevation()` in `Theme.swift` — never a raw `.shadow(...)`, so the recipe stays in one place.

The rgba base is `neutral/ink-900` at the noted alpha. This is a composed shadow recipe documented honestly — the alphas are not consumed elsewhere as color tokens.

## Tokens used (this file)

This is the source-of-truth file; it defines, not consumes. Every other Hearth file's "Tokens used" section will reference names from this allowlist.

## Rules

- Never inline a hex value outside this file. On iOS that means `Theme.swift`'s `HearthPrimitives` and nowhere else — enforced by the linter's `inline hex` check.
- Never invent a token name. Allowlist only.
- Reference semantic tokens (`ink/primary`) before primitives (`neutral/ink-900`).
- Spacing follows the scale; never `spacing/650`. If a one-off bigger gap is needed, compose with multiples in-spec — do not tokenize one-shots.
- Motion always specifies the `motion/instant` collapse path. Every component states table must include a `reduced-motion` row.
- `photo/*` tokens are color blocks, not theme-responsive — they do not invert in dark mode. Four tokens only: `saffron`, `rose`, `royal`, `forest`.
- Sober surfaces use `bg/sober`, not `bg/canvas`.
- `ink/onPhoto` is split: `ink/onPhoto-dark` on warm tiles (`photo/saffron`, `photo/rose`, `accent/kid`), `ink/onPhoto-light` on dark tiles (`photo/royal`, `photo/forest`, `bg/voice`). `type/label` (11pt) over a tile MUST resolve to the AA-pass variant.
- `focus/ring` is split into `focus/ring-on-light` and `focus/ring-on-photo`. Component specs pick the variant per surface.
- **`accent` is split too.** `accent/default` is a fill; `accent/onCanvas` is accent-colored text or icons on cream. Picking the wrong one is an AA fail, not a style preference.
- Cards lift with `elevation/1`, not a hairline. Hairlines are for dividers, separators, and input borders.
- Buttons use `shape/button`; chips use `shape/pill`. A capsule button is off-system.
- Contrast: **every token pair a surface actually renders is declared in `tools/lint-design-tokens.py` and gated by it**; AA-text floor 4.5:1, UI floor 3:1. Adding a surface that combines two tokens means adding the pair. A deliberate exception carries a written argument in the `note` field and is reported as WAIVED, never silently dropped.
- Display type uses the display serif; UI and reading use Inter; metadata uses JetBrains Mono. No fourth family. The display family is named once, in `HearthFontFamily.displaySerif`.
- Token additions require a discussion. Drift kills systems.

## Verifying

```
python3 tools/lint-design-tokens.py              # contrast + spec/code drift + inline-hex
python3 tools/lint-design-tokens.py --contrast   # contrast only
```

---

status: ✅ active
owner: Miguel
last_updated: 2026-08-07 (beta-v1 — teal accent, kid accent, voice surface, darker canvas, elevation rule reversal)
