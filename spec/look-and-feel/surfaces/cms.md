# Surface — CMS (React + Tailwind)

The CMS at `mvp-backend/cms/` is the **secondary** Hearth target. It is the desktop tool an operator uses for an hour at a time to publish articles, moderate community posts, and inspect kid-agent transcripts. It is denser, more keyboard-driven, and more utilitarian than iOS — but it still feels like the same brand.

The same tokens. Different density, different hit-targets, different motion budget. The brand DNA — cream canvas, ink text, olive accent, editorial serif for headlines, mono for metadata — survives the trip from iPhone to 15" laptop.

This file is the **only** place CMS-specific overrides live. Component specs (`components/*.md`) describe the contract; this file describes how that contract is honoured in `mvp-backend/cms/`.

---

## Token → Tailwind mapping

Tokens land in three files at implementation time: `mvp-backend/cms/tailwind.config.ts` (the extend map), `mvp-backend/cms/src/styles/tokens.css` (CSS custom properties), and `mvp-backend/cms/src/styles/fonts.css` (`@font-face` declarations). Nothing in any `.tsx` file may declare a raw hex, raw px value, or arbitrary Tailwind value (`bg-[#...]`, `p-[13px]`, `text-[17px]`) — those are token violations and CI must fail on them via a custom ESLint rule (see `tools/lint-design-tokens.py` in the implementation roadmap).

### Colors → Tailwind class

| Token | Tailwind class | CSS variable |
|---|---|---|
| `bg/canvas` | `bg-canvas` | `--hearth-bg-canvas` |
| `bg/elevated` | `bg-elevated` | `--hearth-bg-elevated` |
| `bg/sober` | `bg-sober` | `--hearth-bg-sober` |
| `ink/primary` | `text-ink-primary` | `--hearth-ink-primary` |
| `ink/secondary` | `text-ink-secondary` | `--hearth-ink-secondary` |
| `ink/muted` | `text-ink-muted` | `--hearth-ink-muted` |
| `ink/placeholder` | `text-ink-placeholder` / `placeholder:text-ink-placeholder` | `--hearth-ink-placeholder` |
| `ink/onPhoto-dark` | `text-ink-on-photo-dark` | `--hearth-ink-on-photo-dark` |
| `ink/onPhoto-light` | `text-ink-on-photo-light` | `--hearth-ink-on-photo-light` |
| `border/hairline` | `border-hairline` | `--hearth-border-hairline` |
| `border/strong` | `border-strong` | `--hearth-border-strong` |
| `accent/default` | `bg-accent` / `text-accent` | `--hearth-accent` |
| `accent/press` | `bg-accent-press` / `active:bg-accent-press` | `--hearth-accent-press` |
| `accent/tint` | `bg-accent-tint` | `--hearth-accent-tint` |
| `focus/ring-on-light` | `ring-focus-light` (with `ring-2 ring-offset-2`) | `--hearth-focus-ring-on-light` |
| `focus/ring-on-photo` | `ring-focus-photo` (with `ring-2 ring-offset-2`) | `--hearth-focus-ring-on-photo` |
| `photo/saffron` | `bg-photo-saffron` | `--hearth-photo-saffron` |
| `photo/rose` | `bg-photo-rose` | `--hearth-photo-rose` |
| `photo/royal` | `bg-photo-royal` | `--hearth-photo-royal` |
| `photo/forest` | `bg-photo-forest` | `--hearth-photo-forest` |
| `status/success` | `text-success` / `bg-success` | `--hearth-status-success` |
| `status/warning` | `text-warning` / `bg-warning` | `--hearth-status-warning` |
| `status/error` | `text-error` / `bg-error` | `--hearth-status-error` |
| `status/error-tint` | `bg-error-tint` | `--hearth-status-error-tint` |
| `status/warning-tint` | `bg-warning-tint` | `--hearth-status-warning-tint` |
| `status/success-tint` | `bg-success-tint` | `--hearth-status-success-tint` |
| `status/info` | `text-info` / `bg-info` | `--hearth-status-info` |

Every CSS variable is declared once in `:root` inside `tokens.css`. Tailwind's `extend.colors` reads each variable by name (`colors: { canvas: 'var(--hearth-bg-canvas)', ... }`) so Tailwind compiles short utility classes against the token table. Phase 2 dark-mode adds a `:root[data-theme="dark"]` override that flips the variables — no component code changes.

### Spacing → Tailwind class

CMS uses the same numeric scale as iOS but compresses page rhythm. Tailwind's default 4px-grid is replaced with the Hearth scale via `extend.spacing`.

| Token | Tailwind class | px value |
|---|---|---|
| `spacing/0` | `p-0` / `m-0` / `gap-0` | `0` |
| `spacing/300` | `p-300` | `8` |
| `spacing/400` | `p-400` | `12` |
| `spacing/500` | `p-500` | `16` |
| `spacing/600` | `p-600` | `20` |
| `spacing/700` | `p-700` | `24` |
| `spacing/800` | `p-800` | `32` |
| `spacing/900` | `p-900` | `40` |
| `spacing/1000` | `p-1000` | `56` |

Page gutter on CMS = `p-500` (16px). Section rhythm = `gap-700` to `gap-900`. **Tighter than iOS by design** — see the Density section below.

### Shape → Tailwind class

| Token | Tailwind class | px value |
|---|---|---|
| `shape/none` | `rounded-none` | `0` |
| `shape/sm` | `rounded-sm` | `4` |
| `shape/md` | `rounded-md` | `12` |
| `shape/lg` | `rounded-lg` | `20` |
| `shape/xl` | `rounded-xl` | `28` |
| `shape/pill` | `rounded-pill` | `9999` |

### Elevation → Tailwind class

`extend.boxShadow` exposes four utilities: `shadow-e0`, `shadow-e1`, `shadow-e2`, `shadow-e3`. Never write `shadow-[0_4px_12px_rgba(...)]` — that's a token violation.

---

## `tailwind.config.ts` extend

The config is the single source of truth that maps token names to Tailwind utilities. Sketch:

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--hearth-bg-canvas)',
        elevated: 'var(--hearth-bg-elevated)',
        sober: 'var(--hearth-bg-sober)',
        'ink-primary': 'var(--hearth-ink-primary)',
        'ink-secondary': 'var(--hearth-ink-secondary)',
        'ink-muted': 'var(--hearth-ink-muted)',
        'ink-placeholder': 'var(--hearth-ink-placeholder)',
        'ink-on-photo': 'var(--hearth-ink-on-photo)',
        hairline: 'var(--hearth-border-hairline)',
        strong: 'var(--hearth-border-strong)',
        accent: 'var(--hearth-accent)',
        'accent-press': 'var(--hearth-accent-press)',
        'accent-tint': 'var(--hearth-accent-tint)',
        focus: 'var(--hearth-focus-ring)',
        'photo-saffron': 'var(--hearth-photo-saffron)',
        'photo-rose': 'var(--hearth-photo-rose)',
        'photo-royal': 'var(--hearth-photo-royal)',
        'photo-forest': 'var(--hearth-photo-forest)',
        'photo-clay': 'var(--hearth-photo-clay)',
        'photo-sand': 'var(--hearth-photo-sand)',
        success: 'var(--hearth-status-success)',
        warning: 'var(--hearth-status-warning)',
        error: 'var(--hearth-status-error)',
        info: 'var(--hearth-status-info)',
      },
      spacing: {
        100: '2px', 200: '4px', 300: '8px', 400: '12px',
        500: '16px', 600: '20px', 700: '24px', 800: '32px',
        900: '40px', 1000: '56px', 1100: '72px', 1200: '96px',
      },
      borderRadius: { sm: '4px', md: '12px', lg: '20px', xl: '28px', pill: '9999px' },
      boxShadow: {
        e0: 'none',
        e1: '0 1px 2px rgba(26,26,26,0.06)',
        e2: '0 4px 12px rgba(26,26,26,0.08)',
        e3: '0 12px 32px rgba(26,26,26,0.12)',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SF Mono', 'monospace'],
      },
      fontSize: {
        'display-xl': ['80px', { lineHeight: '84px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'display-lg': ['56px', { lineHeight: '60px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'display-md': ['40px', { lineHeight: '44px', fontWeight: '600' }],
        'display-sm': ['28px', { lineHeight: '32px', fontWeight: '600' }],
        'title-lg':   ['20px', { lineHeight: '24px', fontWeight: '600' }],
        'title-md':   ['16px', { lineHeight: '22px', fontWeight: '600' }],
        'body-lg':    ['17px', { lineHeight: '26px', fontWeight: '400' }],
        'body-md':    ['15px', { lineHeight: '22px', fontWeight: '400' }],
        'body-sm':    ['13px', { lineHeight: '18px', fontWeight: '400' }],
        'label':      ['11px', { lineHeight: '14px', fontWeight: '600', letterSpacing: '0.06em' }],
        'caption-mono': ['12px', { lineHeight: '16px', fontWeight: '400' }],
      },
    },
  },
} satisfies Config
```

`display-xl` on CMS doubles to **80/84** (per the plan's note that CMS doubles the iOS hero size). All other type tokens match iOS exactly.

---

## Typography — self-hosted `@font-face`

Fonts are **self-hosted**, never loaded from the Google Fonts CDN. Two reasons: (1) data-locality — the CMS is occasionally used in offline-ish coffee-shop conditions; (2) no third-party network call leaks operator-IPs to Google.

### File layout

```
mvp-backend/cms/public/fonts/
  Fraunces[opsz,SOFT,WONK,wght].woff2
  Inter[opsz,wght].woff2
  JetBrainsMono[wght].woff2
```

Source the variable WOFF2 files from the official OFL releases:
- Fraunces — https://github.com/undercase/Fraunces
- Inter — https://github.com/rsms/inter
- JetBrains Mono — https://github.com/JetBrains/JetBrainsMono

Vendor them into the repo. Pin the version in a `fonts.LICENSE` file alongside the WOFF2 binaries.

### `src/styles/fonts.css`

```css
@font-face {
  font-family: 'Fraunces';
  src: url('/fonts/Fraunces[opsz,SOFT,WONK,wght].woff2') format('woff2-variations');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter[opsz,wght].woff2') format('woff2-variations');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono[wght].woff2') format('woff2-variations');
  font-weight: 100 800;
  font-style: normal;
  font-display: swap;
}
```

`fonts.css` is imported once from `src/main.tsx` before `tokens.css`. `font-display: swap` prevents invisible-text on slow loads; the Inter fallback (`-apple-system`) is close enough in metrics that the swap is unobtrusive.

### Token → Tailwind class

| Token | Tailwind class | Stack |
|---|---|---|
| `type/display-xl` | `font-display text-display-xl` | Fraunces 80/84 -1% w600 |
| `type/display-lg` | `font-display text-display-lg` | Fraunces 56/60 -1% w600 |
| `type/display-md` | `font-display text-display-md` | Fraunces 40/44 w600 |
| `type/display-sm` | `font-display text-display-sm` | Fraunces 28/32 w600 |
| `type/title-lg` | `font-sans text-title-lg` | Inter 20/24 w600 |
| `type/title-md` | `font-sans text-title-md` | Inter 16/22 w600 |
| `type/body-lg` | `font-sans text-body-lg` | Inter 17/26 w400 |
| `type/body-md` | `font-sans text-body-md` | Inter 15/22 w400 |
| `type/body-sm` | `font-sans text-body-sm` | Inter 13/18 w400 |
| `type/label` | `font-sans text-label uppercase tracking-wider` | Inter 11/14 +6% w600 |
| `type/caption-mono` | `font-mono text-caption-mono` | JetBrains Mono 12/16 w400 |

Body type (`body-lg`, `body-md`) is the default for tables, forms, and chrome. Display tokens are reserved for screen titles and editorial pages — not for table headers or sidebar labels.

---

## Density

CMS is **denser** than iOS. Same tokens, smaller defaults across the board. The principle: a moderator scanning 40 community posts in a vertical list should not need to scroll three times the iOS distance.

| Surface | iOS default | CMS default | Token |
|---|---|---|---|
| Page gutter | 24pt | 16px | `spacing/500` (CMS) vs `spacing/700` (iOS) |
| Section rhythm | 32–40pt | 24–32px | `spacing/700`–`spacing/800` |
| Card padding | 20pt | 16px | `spacing/500` |
| Form row vertical padding | 16pt | 12px | `spacing/400` |
| Table cell padding | n/a | 8px / 12px | `spacing/300` vertical, `spacing/400` horizontal |
| List item min-height | 56pt | 40px | — (CMS lists are not touch targets) |
| Default button height (md) | 48pt | 36px | — |
| Button height (sm) | 44pt (min) | 28px | — |

Body type stays at `body-md` (15px) — never shrink type to gain density, shrink padding instead. The eye can scan dense rows of 15px Inter; it cannot scan 12px text without fatigue, and tired operators are the same humans as tired parents.

Touch targets on CMS are **not** subject to the 44pt floor. Default click targets are 28–36px tall. Touch-laptop / iPad-Safari users get the same density — Hearth CMS is desktop-first; if iPad Safari operators become a real cohort we add a `@media (pointer: coarse)` density override in Phase 2.

---

## Keyboard focus

Keyboard-first. Every interactive element must show focus.

### Focus ring

The global focus style is set once in `src/styles/focus.css`:

```css
:where(button, a, [role="button"], input, select, textarea, [tabindex]:not([tabindex="-1"]))
  :focus-visible {
  outline: 2px solid var(--hearth-focus-ring);
  outline-offset: 2px;
  border-radius: inherit;
}
```

Use `:focus-visible`, not `:focus` — mouse clicks should not flash the ring. The `outline-offset` gives the ring breathing room from the component's own border. Border-radius is inherited so the ring follows the shape of buttons, inputs, and chips.

### Tab order

| Region | Tab order rule |
|---|---|
| Top nav | left-to-right; logo is `tabindex=-1` (not interactive). |
| Sidebar | top-to-bottom; collapsible sections use `aria-expanded` + space/enter to toggle. |
| Main content | natural DOM order; never `tabindex` > 0. |
| Forms | label → input → label → input; submit button last. |
| Modal dialogs | trap focus inside the dialog; restore focus to the trigger on close (use a `useFocusTrap` hook). |

### Shortcuts

A minimal keyboard shortcut set, registered globally via a `useKeyboardShortcuts` hook:

| Shortcut | Action |
|---|---|
| `/` | focus the search input |
| `Cmd/Ctrl + K` | open the command palette |
| `Cmd/Ctrl + S` | save the current draft (in article editor) |
| `Esc` | close the topmost modal / dismiss the command palette |
| `?` | show the keyboard shortcut overlay |

Shortcuts are **discoverable** — every action that has a shortcut shows the key in its tooltip and in the command palette row.

---

## Motion

CMS motion budget is smaller than iOS — fewer springs, more `motion/fast`. Operators value snappiness over delight.

| Token | Tailwind / CSS | Use |
|---|---|---|
| `motion/instant` | `transition-none` | crisis-lock, reduce-motion |
| `motion/fast` | `transition-all duration-[120ms] ease-out` | hover, focus, press feedback |
| `motion/base` | `transition-all duration-200 ease-out` | menu open/close, tab switches |
| `motion/slow` | `transition-all duration-[320ms] ease-in-out` | sheet/dialog entrance |
| `motion/spring` | — (not used on CMS) | — |

iOS uses springs for press feedback; CMS uses `motion/fast` easeOut. Springs feel wrong with a mouse cursor.

### Reduce motion

Honour `@media (prefers-reduced-motion: reduce)` globally in `src/styles/motion.css`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0ms !important;
    scroll-behavior: auto !important;
  }
}
```

Never branch on `prefers-reduced-motion` in a component — let the global rule do it.

---

## Layout primitives

The CMS app shell is a fixed three-region layout. Components compose inside the `<Main>` region.

| Region | Width | Background | Content |
|---|---|---|---|
| `<TopNav>` | 100% × 56px | `bg/canvas`, `border-b border-hairline` | logo, env badge, user menu |
| `<Sidebar>` | 240px × full | `bg/canvas`, `border-r border-hairline` | nav links, collapsible groups |
| `<Main>` | flex-1 × full | `bg/elevated` | scrollable page content, page gutter `p-500` |

Editor surfaces (article editor, kid-agent prompt synthesis) expand to full width by hiding the sidebar via a `?focus=1` query param.

---

## Rules

- Never declare a raw hex color, raw px value, or arbitrary Tailwind value (`bg-[#...]`, `p-[13px]`) outside `tailwind.config.ts` / `tokens.css`.
- All fonts are self-hosted via `@font-face`; never link to the Google Fonts CDN.
- Use `:focus-visible`, not `:focus`; outline-offset 2px; pick `focus/ring-on-light` for cream/paper surfaces, `focus/ring-on-photo` for `photo/*` overlays.
- Honour `prefers-reduced-motion` via the global CSS rule — never branch in component code.
- CMS density is tighter than iOS: smaller padding, smaller default buttons, but body type stays at `body-md`.
- No 44pt touch floor on CMS — default click targets are 28–36px; iPad pointer-coarse override is Phase 2.
- Display type (`display-xl`, `display-lg`) is for page hero only; never for table headers or sidebar labels.
- Springs are forbidden on CMS — use `motion/fast` easeOut for press / hover; `motion/base` for menus.
- Modal dialogs trap focus and restore focus on close; the topmost dialog is the only one that takes `Esc`.
- Every shortcut is discoverable via tooltip + `?` overlay; never ship a hidden shortcut.

---

## Render check

The implementation must render these five canonical compositions and they must look right in a Storybook gallery (`stories/Surface.stories.tsx`).

1. **App shell.** `<TopNav>` (canvas, hairline border, env badge, user menu) + `<Sidebar>` (240px, nav links, collapsible "Content" / "Community" / "Safety" groups) + `<Main>` (elevated bg, `p-500` gutter). Focus ring visible on tab through nav.
2. **Article list.** Dense table inside `<Main>`: header row `text-label uppercase text-ink-muted`, body rows `text-body-md text-ink-primary`, hairline dividers, hover state `bg-canvas`, focus ring on row, row height 40px.
3. **Article editor.** Full-width `?focus=1` layout, page hero in `text-display-md font-display`, body editor in `text-body-lg font-sans` with 720px max-width, save button (`bg-accent text-ink-on-photo`) pinned top-right, mono caption shows last-saved timestamp.
4. **Moderation queue (sober).** `bg-sober`, no photography, no accent color except for "Take down" destructive button (`text-error border-error`), `text-body-md`, focus rings visible, queue rows scannable at 36px height.
5. **Modal dialog.** Confirmation dialog centered, `bg-elevated rounded-xl shadow-e3`, 480px wide, focus-trapped, primary action `bg-accent`, secondary `border-strong text-ink-primary`, `Esc` dismisses.

Each composition must pass an `axe-core` audit with zero contrast or focus findings before it is considered "rendered."

---

## Tokens used

| Layer | Tokens |
|---|---|
| Color | `bg/canvas`, `bg/elevated`, `bg/sober`, `ink/primary`, `ink/secondary`, `ink/muted`, `ink/placeholder`, `ink/onPhoto-dark`, `ink/onPhoto-light`, `border/hairline`, `border/strong`, `accent/default`, `accent/press`, `accent/tint`, `focus/ring-on-light`, `focus/ring-on-photo`, `photo/saffron`, `photo/rose`, `photo/royal`, `photo/forest`, `status/success`, `status/warning`, `status/error`, `status/error-tint`, `status/warning-tint`, `status/success-tint`, `status/info` |
| Type | `type/display-xl` (80/84 on CMS), `type/display-lg`, `type/display-md`, `type/display-sm`, `type/title-lg`, `type/title-md`, `type/body-lg`, `type/body-md`, `type/body-sm`, `type/label`, `type/caption-mono` |
| Spacing | `spacing/0`, `spacing/300` through `spacing/1000` (9-step scale) |
| Shape | `shape/none`, `shape/sm`, `shape/md`, `shape/lg`, `shape/xl`, `shape/pill` |
| Motion | `motion/instant`, `motion/fast`, `motion/base`, `motion/slow` (no `motion/spring` on CMS) |
| Elevation | `elevation/0`, `elevation/1`, `elevation/2`, `elevation/3` |

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
