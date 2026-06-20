# Hearth — Design System for parent-app

Hearth is the design system behind every Hearth-routed surface in parent-app — the iOS app and the CMS. Cream canvas, ink text, olive accent, photo tiles. Modern, minimalist, editorial. A steady hand on the shoulder of an overwhelmed parent — not boutique, not boring, not chirpy. The architecture is lifted from SonderMind's Iris 2.0: token-first, AI-routable, single source of truth. The brand language is our own — large editorial photography, one personality serif, aggressive whitespace, lowercase functional UI.

## How to load this in an AI agent session

Every Hearth session loads two files unconditionally. Component and surface specs load by intent — pull only what the task touches.

```
ALWAYS LOAD (every session):
  - spec/look-and-feel/DESIGN.md          # system prompt: principles, voice, rules
  - spec/look-and-feel/DESIGN.tokens.md   # canonical token allowlist

LOAD BY INTENT (only what the task touches):
  - components/buttons.md       when generating CTAs / actions / nav buttons
  - components/forms.md         when generating inputs / pickers / validation
  - components/cards.md         when generating article / category / community tiles
  - components/article.md       when generating long-form reading surfaces
  - components/nav.md           when generating tab bars / top nav / sub-nav
  - components/chip.md          when generating tags / filter pills / category chips
  - components/empty.md         when generating empty / loading / error / skeleton states
  - components/sheet.md         when generating modals / partial sheets / drawers
  - surfaces/ios.md             when emitting SwiftUI
  - surfaces/cms.md             when emitting Tailwind / React
  - photography.md              when briefing images / Midjourney prompts
  - voice.md                    when writing copy / error strings / headlines
  - logo.md                     when touching the wordmark / icon / launch screen
```

If the surface is ambiguous (iOS vs CMS vs brand-asset), ask before generating. Never invent a token — every value resolves to `DESIGN.tokens.md`.

## File tree

```
spec/look-and-feel/
├── README.md                  # this file — index + loading rules
├── DESIGN.md                  # system prompt (HEARTH, voice, photography, generation, shared patterns)
├── DESIGN.tokens.md           # canonical token allowlist (the ONLY place hex values live)
├── components/
│   ├── buttons.md             # primary / secondary / quiet (danger = modifier on secondary) · sm/md/lg
│   ├── forms.md               # text / select / checkbox / radio / date · states
│   ├── cards.md               # article / category / post / sober
│   ├── article.md             # long-form layout (hero, byline, body, pull-quote, end card)
│   ├── nav.md                 # bottom tab bar, top nav, sub-nav chips
│   ├── chip.md                # tag chips, filter pills, category chips
│   ├── empty.md               # empty / loading / error / skeleton
│   └── sheet.md               # modal, partial, action sheets, drawers
├── surfaces/
│   ├── ios.md                 # SwiftUI mapping, touch min 44, dark-mode posture
│   └── cms.md                 # Tailwind class mapping, density, keyboard focus
├── photography.md             # direction, shoot rules, color-block tiles
├── voice.md                   # copy tone, tense, emoji rules, headline rhythm
├── logo.md                    # three wordmark directions + execution brief
├── midjourney-prompts.md      # 12-15 prompts for hero + category tile imagery
├── fonts/                     # self-hosted Fraunces / Inter / JetBrains Mono
└── logo/                      # wordmark.svg, mark.svg, icon-1024.png, launch.svg
```

## Status table

| File | Status | Notes |
|---|---|---|
| `README.md` | ✅ active | this file |
| `DESIGN.md` | ✅ active | HEARTH principles + generation rules |
| `DESIGN.tokens.md` | ✅ active | full token allowlist; critic round may refine names |
| `components/buttons.md` | ✅ active | primary / secondary / quiet (danger = modifier on secondary) |
| `components/forms.md` | ✅ active | text / select / checkbox / radio / date |
| `components/cards.md` | ✅ active | article / category / post / sober |
| `components/article.md` | ✅ active | long-form reading layout |
| `components/nav.md` | 🔨 draft | bottom tab + top nav + sub-nav |
| `components/chip.md` | 🔨 draft | tag / filter / category chips |
| `components/empty.md` | 🔨 draft | empty / loading / error / skeleton |
| `components/sheet.md` | 🔨 draft | modal / partial / action / drawer |
| `surfaces/ios.md` | ✅ active | SwiftUI mapping |
| `surfaces/cms.md` | 🔨 draft | Tailwind + React mapping |
| `photography.md` | ✅ active | shoot direction + tile rules |
| `voice.md` | ✅ active | copy tone + emoji rules |
| `logo.md` | 🔨 draft | three directions, awaiting pick |
| `midjourney-prompts.md` | 🔨 draft | 6 of 12-15 prompts written |

🔨 files are usable but pending critic round + final pass. Anything marked 📅 planned is not yet drafted and should not be referenced as canon.

---

status: ✅ active
owner: Miguel
last_updated: 2026-05-31
