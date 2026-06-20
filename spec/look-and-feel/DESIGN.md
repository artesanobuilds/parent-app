# DESIGN.md — Hearth System Prompt

This is the system prompt every Hearth-routed AI session loads first. It establishes the principles, the voice, the photography direction, the generation rules, and the shared state patterns every component inherits. Pair it with `DESIGN.tokens.md` — the two together are the minimum context for any Hearth output.

Hearth's job is to make an overwhelmed parent feel held. Cream canvas, ink text, olive accent, photo tiles. Editorial weight, quiet chrome. We borrow the architecture from SonderMind's Iris 2.0; the brand language is ours.

## HEARTH principles

Every Hearth output must satisfy all six. If a generation can only satisfy five, it is not Hearth.

### H — Held

Every screen should feel like a steady hand on the shoulder of an overwhelmed parent. Visual weight reduces stress; it never adds to it. Generous whitespace, one clear next action per screen, no competing CTAs, no decorative motion that demands attention. When in doubt, remove. The parent is already tired before they opened the app — don't make them work to find the thing.

### E — Editorial

Content first; chrome quiet; photography earns its space. Tiles are little magazine spreads, not UI widgets. The serif (Fraunces) carries headlines; the sans (Inter) carries reading and UI; the mono (JetBrains Mono) is metadata only. Layout breathes — page gutter is `spacing/700` (24pt) on iOS, section rhythm is `spacing/800` to `spacing/1000`. We lean on whitespace harder than typical apps because Rose LA and Wonder Valley do, and that's the league we're playing in.

### A — Adaptive

Touch min 44pt on iOS. Respects `prefers-reduced-motion` (web) and `accessibilityReduceMotion` (iOS) — every animation collapses to `motion/instant` when the OS asks. Dark mode supported in Phase 2; tokens are designed to invert cleanly. WCAG 2.1 AA minimum on every shipped token pair. Cognitive accessibility is non-negotiable — clear hierarchy, one decision per surface, no jargon, no surprise modals. Tired parents have less working memory; design for that.

### R — Real

No stock illustrations. No chirpy mascots. No "Sarah, mom of two!" stock photos. Photography looks like the actual parents who use the app — varied bodies, ages, skin tones, photographed in their actual kitchens / yards / floors. Side-lit, warm, slightly golden. Subjects occupy 35–55% of the frame. The single most consequential brand decision; if a photo could appear in a competitor's ad, it doesn't belong here.

### T — Trustworthy

Kid-agent, crisis-lock, and safety surfaces use *sober* variants of every component. No playful animations, no saturated photo tiles, no decorative serifs in the chrome. Same tokens, restrained applications. `bg/sober` instead of `bg/canvas`; no `motion/spring`; no `photo/*` color blocks; Inter only, no Fraunces display. Crisis copy has no exclamation marks, no "oops", no casual register. When a parent is scared, the app gets quieter.

### H — Hearth

Gathering place: warmth without saccharin. Cream not white. Olive not mint. Ink not pure black on most surfaces. The name is the brief — a hearth is warm, central, communal, slow. If a screen feels like a hospital intake form or a venture-funded onboarding wizard, it's failing this principle.

## Voice rules (summary)

Full spec in `voice.md`. The shorthand:

- Lowercase functional UI. Sentence-case for paragraphs. **Title Case Headlines** only inside long-form articles.
- Active voice. Second person to the parent ("you've got this", not "parents will find").
- No emoji in chrome. Emoji acceptable inside category tiles as a temporary stand-in for photography during dev.
- Errors are warm and specific: `couldn't load articles — pull to refresh`, not `Error 500`.
- Crisis surface copy is sober — never "oops", never exclamation marks, never casual register.
- No corporate hedging. No "We believe…" intros. No "delightful" or "magical". Be the friend who's already done this.

## Photography rules (summary)

Full spec in `photography.md`. The shorthand:

- Always shot, never illustrated. No flat illustration, no Notion-style emoji-only tiles in production.
- Real-looking people, real rooms. Editorial casting, never studio backdrops.
- One-product-per-tile composition: when a tile shows a "thing", it sits centered against a saturated `photo/*` color block. Rose LA edibles is the template.
- Side-lit, warm, slightly golden. Late-afternoon north-window energy.
- Crop tight, but with negative space inside the frame. Subject 35–55% of the frame.
- No price tags, no UI elements baked into the photo, no captions burned in.
- Avoid baby clichés: no newborn-feet-in-parent-hands, no sunset silhouettes, no "tired mom with coffee".
- Crisis surface: no photography at all. Type only.

## Generation rules

Numbered, in order. Every Hearth-routed AI generation obeys these.

1. **Never emit a hex value outside `DESIGN.tokens.md`.** All colors resolve to a semantic token (`bg/canvas`, `ink/primary`, `accent/default`). If you need a color that doesn't exist as a token, stop and ask — do not invent.
2. **Never invent a token.** Token names are an allowlist. If the name you want isn't in `DESIGN.tokens.md`, the answer is to use an existing token or open a discussion to add one — not to ship a one-off.
3. **Ask before generating if the surface is ambiguous.** iOS vs CMS vs brand-asset have different conventions. If the request doesn't name a surface, ask.
4. **Reference, don't copy.** When emitting code, reference tokens by name (`Color.hearthAccentDefault`, `bg-canvas`). Don't paste a hex even if you know it.
5. **One CTA per screen.** If a generation produces two primary buttons on the same surface, demote one to secondary or drop it.
6. **Reduced-motion is a hard branch.** Every motion-using component must specify the `motion/instant` collapse path. No exceptions.
7. **Sober variant for kid-agent / crisis-lock / safety surfaces.** When the task touches these, switch to the sober palette before generating chrome.
8. **No raw `Color(hex:)` / `bg-[#...]` / inline styles.** These are linted out in implementation. Don't produce them in spec output either.
9. **Cite the token used.** Every component spec ends with a "Tokens used" section. Generations that introduce new compositions must list the tokens they consume.
10. **When in doubt, reduce.** Fewer variants, fewer colors, fewer animations. Hearth fails by addition more often than by subtraction.
11. **Every component spec includes a `reduced-motion` row** in its states table — every motion cell maps to `motion/instant` (or a non-motion equivalent like `fill darken 4%`). Specs without this row fail review.
12. **Every interactive sub-element inside a card** (tertiary "read more", save/share icon buttons, inline links) has a 44pt minimum hit area independent of its visual height — pad outward into the card gutter.

## Loading rules

Mirrors the Iris 2.0 model. Every Hearth-routed session loads two files unconditionally and pulls component / surface specs only when the task touches them.

```
ALWAYS LOAD:
  - spec/look-and-feel/DESIGN.md          (this file)
  - spec/look-and-feel/DESIGN.tokens.md   (token allowlist)

LOAD BY INTENT:
  - components/<name>.md     when generating that component family
  - surfaces/ios.md          when emitting SwiftUI
  - surfaces/cms.md          when emitting Tailwind / React
  - photography.md           when briefing images
  - voice.md                 when writing copy
```

Order matters. `DESIGN.md` establishes the rules; `DESIGN.tokens.md` provides the allowlist; component / surface specs are governed by both. A spec that contradicts `DESIGN.md` is wrong, not the other way around.

## Shared patterns

The state patterns every component inherits. Specific components override only when the spec explicitly says so.

### Focus

| Surface | Treatment |
|---|---|
| iOS / CMS — control on cream / paper | `focus/ring-on-light` 2pt/2px outset, `motion/fast`, keyboard / `:focus-visible` only |
| iOS / CMS — control on `photo/*` tile | `focus/ring-on-photo` 2pt/2px outset, same activation |
| Sober surface | `focus/ring-on-light` at 1pt / 1px to reduce visual weight |

### Error

| Surface | Treatment |
|---|---|
| Inline (form field) | `border/strong` → `status/error`, helper text `ink/secondary` → `status/error`, copy warm + specific |
| Toast / banner | `status/error-tint` fill, `status/error` 1pt left rule, `ink/primary` body |
| Full screen | `bg/sober`, Inter only, no photography, single CTA `accent/default` |

### Loading

| Mode | Treatment |
|---|---|
| Skeleton | `border/hairline` shapes at component silhouette; subtle 1.2s pulse; collapses to static block under reduced-motion |
| Spinner | Only used inside buttons mid-action; never as a full-screen loader on cream canvas |
| Suspense (full-screen) | `bg/canvas`, centered wordmark at `type/display-md`, no spinner |

### Empty

| Variant | Treatment |
|---|---|
| First-use empty | Single Fraunces headline (`type/display-md`), one sentence Inter body, one `accent/default` CTA |
| Filtered empty | `ink/secondary` one-liner + a `quiet` button to clear filters; no illustration |
| Sober empty | Same structure, no Fraunces, all Inter; for kid-agent / crisis-lock |

### Dark mode posture

Phase 2 ship. Tokens are designed to invert, not flip. Cream → near-black warm gray (not `#000`); ink → cream; olive accent stays olive but lightened one step. Photography tiles are unchanged — `photo/*` color blocks are brand constants, not theme-responsive. Do not generate dark-mode tokens speculatively; wait for the Phase 2 spec turn.

---

status: ✅ active
owner: Miguel
last_updated: 2026-05-31
