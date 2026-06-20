# Article

The article view is where Hearth earns its editorial claim. Long-form parenting content read in a quiet moment — the chrome retreats, the photography opens up, the type stack does the heavy lifting. Fraunces for display, Inter for body, JetBrains Mono for the byline. Page gutter `spacing/700` on iOS. Reading column caps at 64ch on CMS so lines don't sprawl. No floating share rails, no autoplay video, no inline ads.

## Variants

| Variant | Use | Hero | Body |
|---|---|---|---|
| `standard` | default long-form article | 16:9 photo, full-bleed top | `type/body-lg`, single column |
| `essay` | longer-form personal essay | 4:5 portrait photo, inset gutter | `type/body-lg`, drop cap on first paragraph |
| `guide` | structured how-to with sections | 1:1 hero centered on `photo/*` tile | `type/body-lg` + `type/title-md` section heads |
| `sober` | kid-agent / crisis-linked content | NO photo, ink-only masthead | `type/body-lg` on `bg/sober`, no pull-quote |

## Sections (top to bottom)

| Section | Token | Notes |
|---|---|---|
| Hero photo | aspect per variant | full-bleed on `standard` / `guide`; insets `spacing/700` on `essay` |
| Eyebrow | `type/label` `ink/muted` | category, UPPERCASE, above the title |
| Title | `type/display-lg` `ink/primary` | Title Case, no period |
| Deck | `type/title-lg` `ink/secondary` | one sentence, optional |
| Byline | `type/caption-mono` `ink/muted` | "by Jane Doe · 6 min · may 31, 2026" |
| Body | `type/body-lg` `ink/primary` | paragraphs separated by `spacing/500`, no first-line indent |
| Pull-quote | `type/display-md` italic `ink/primary` | full-bleed inset, hairline rules top + bottom |
| Section header | `type/title-md` `ink/primary` | only on `guide` variant |
| Inline image | 4:5 default | caption beneath in `type/caption-mono` `ink/muted` |
| End card | `bg/sober` block | "next read" recommendation + author bio |

## States

| State | hero | body | pull-quote |
|---|---|---|---|
| loading | skeleton block at hero aspect | 8 lines skeleton, decreasing widths | hidden until body renders |
| empty | "this article moved — try the library" + `secondary` button | n/a | n/a |
| error | warm copy on `bg/sober`, retry `secondary` | n/a | n/a |
| reading | sticky progress bar `accent/default` 2px top | full | rendered inline |
| done | end card slides in at `motion/slow` | dimmed footer meta | retained |
| reduced-motion | end-card slide → static render at `motion/instant`; progress bar still draws but without ease | n/a | n/a |

## Sizes

| Size | Reading column | Body type | Hero | Surface |
|---|---|---|---|---|
| `iOS` | viewport - 2× `spacing/700` | `type/body-lg` (17/26) | full-bleed | `bg/canvas` |
| `CMS-sm` | 100% up to 720px | `type/body-lg` | full-bleed within container | `bg/canvas` |
| `CMS-lg` | max 64ch centered | `type/body-lg` (17/28 override) | bleed within 1200px frame | `bg/canvas` |

`sober` variant runs on `bg/sober` regardless of surface, and clamps the column tighter (max 56ch).

## Rules

- One title per article. Deck is optional, never required.
- Byline always in `type/caption-mono` — the only place mono runs in-article. Never substitute Inter.
- Pull-quotes are full-bleed inset; they break the reading column on purpose.
- Drop cap is `essay`-only, Fraunces, 4 lines tall, `ink/primary`.
- Section headers (`guide` only) get `spacing/800` above, `spacing/500` below.
- Body paragraphs are separated by vertical rhythm, never by an empty line of text.
- Inline images carry a caption in `type/caption-mono`; uncaptioned images are forbidden.
- Reading progress is a 2px top bar in `accent/default`; never a percentage badge.
- `sober` variant forbids: hero photo, pull-quote, drop cap, inline images, progress bar.
- Reduce-motion disables the end-card slide-in; render statically.
- Long-form articles use Title Case for the title (the one place in the product that does).

## Render check

1. `standard` on iOS — 16:9 hero, eyebrow "READING", title "The Case for Boring Books", byline "by Jane Doe · 6 min".
2. `essay` on CMS-lg — 4:5 inset hero, drop cap "P", reading column 64ch, one pull-quote two-thirds down.
3. `guide` with `photo/forest` 1:1 hero — title "Outdoor Afternoons Under $5", three section heads, two inline images. `type/label` eyebrow uses `ink/onPhoto-light` if overlaid; otherwise `ink/muted` on cream.
4. `sober` variant — kid-agent-linked explainer "What Your Kid-Agent Saw Today", no photo, `bg/sober`, 56ch column.
5. `standard` at end-state — end card with "next read" article-card-sm and author bio block.

## Tokens used

```
bg/canvas, bg/sober
ink/primary, ink/secondary, ink/muted, ink/onPhoto-dark, ink/onPhoto-light
border/hairline
accent/default
photo/saffron, photo/rose, photo/royal, photo/forest
shape/md, shape/lg
spacing/500, spacing/600, spacing/700, spacing/800, spacing/1000
type/label, type/display-md, type/display-lg, type/title-md, type/title-lg, type/body-lg, type/caption-mono
motion/slow, motion/instant
elevation/0
```

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
