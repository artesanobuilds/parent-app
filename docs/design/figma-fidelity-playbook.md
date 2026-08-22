# Figma fidelity playbook

Process rules for translating a Figma frame into shipped SwiftUI, distilled
from three rounds of beta-v1 fidelity passes (2026-08-07 through 2026-08-09).
Round 3 specifically was triggered by Miguel asking "why aren't we getting
the results we need?" after two prior rounds still left visible drift — this
document is the answer, written down so it doesn't happen a fourth time.

There will be more Figma designs. Getting them right the first time is the
point of this file.

## The five root causes (round 3 postmortem)

Every drift Miguel found traced back to one of these:

1. **Partial translation.** A frame was walked into a measured spec, but the
   implementation matched structure and approximate styling, not every
   measured property — exact font weight, muted-vs-ink header color, stroke
   weight, button fill-vs-outline, per-edge padding.
2. **SF Symbol stand-ins.** A frame draws a specific vector glyph (tab icons,
   a coach mark, category chips); the build shipped an SF Symbol that was
   "close enough." It never is, once placed next to the real render.
3. **Whole-screen verification.** Confirming a screen "looks right" at a
   glance misses the detail drift that whole-screen glances are bad at
   catching — font weight and 2px padding differences don't register at
   thumbnail scale.
4. **Empty/first-run states treated as afterthoughts.** Frames design empty
   states explicitly (an empty-plan search card, a first-run dashboard
   prompt). Implementations leaked content-state chrome into them, or
   substituted ad-hoc copy/layout instead of the frame's own treatment.
5. **Scope holes.** Cross-cutting chrome (the tab bar, in this case) was
   never explicitly owned by any round's plan. Nothing shipped for it until
   a user complaint forced the question "wait, whose job was this?"

## The rules

### 1. Walk before you build

Any screen in scope of a Figma canvas gets its frame fetched and walked into
a measured spec **before** implementation starts. Batch every frame you need
into ONE `/v1/files/:key/nodes?ids=...` call — Figma view-seat quota is
tight; budget the whole work session's frames into that single call, not one
call per screen.

```bash
source ~/.zshenv   # FIGMA_TOKEN lives here
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/<FILE_KEY>/nodes?ids=<comma-separated ids>" \
  -o /tmp/fetch.json -w "http=%{http_code} bytes=%{size_download}\n"
python3 tools/figma-walk.py /tmp/fetch.json /tmp/spec.txt
```

If the call 429s: **stop and report.** Do not retry-loop against a quota
error — it doesn't resolve itself.

Append the walked FRAME blocks to the relevant `docs/design/*.md` file, in
the same format the existing blocks use (open the file first, mirror the
structure exactly — a linter or a future session's grep may key off it).
This is what lets the NEXT session skip re-fetching: `docs/design/*.md` is
the source of truth once a frame has been walked, not the job tmp dir.

### 2. Translate every measured property, not the gist

A frame's "gist" — teal button, white card, calendar icon — is not the spec.
The spec is every one of these, each mapped to a token (or a documented
one-off literal if no token is within ~2pt/one-shade):

- Font family, weight, size, line-height, letter-spacing
- Fill (hex → the nearest Hearth token; if none exists, add one — don't
  reach for `Color(hex:)` inline, see rule 6)
- Stroke color AND weight (a 0.83pt stroke and a 1pt stroke read differently
  at small sizes — don't round to "has a stroke")
- Corner radius
- Padding, **per edge** — a card with pad (9, 9, 9, 9) is not the same as
  one with pad (20, 20, 20, 20), even if both "have padding"
- Stack gap (the space BETWEEN children, distinct from the container's own
  padding)

A section is done when every one of these is accounted for — matched to a
token or explicitly noted as a deliberate deviation with a reason. "It looks
right" is not a verification method; "every property has a token" is.

### 3. Every frame glyph ships as an exported vector

If the frame draws a specific icon — not a generic system glyph a designer
picked from SF Symbols, but a purpose-drawn shape — export it. One batched
`/images?ids=...&format=svg` call per work session, same quota discipline as
the `/nodes` fetch. Ship each as a template-rendering SVG imageset:

```json
{
  "images": [{ "filename": "your-icon.svg", "idiom": "universal" }],
  "info": { "author": "xcode", "version": 1 },
  "properties": {
    "preserves-vector-representation": true,
    "template-rendering-intent": "template"
  }
}
```

Template rendering means ONE asset tints correctly on any background
(white-on-teal selected, teal-on-white unselected) — you don't need a second
asset per color state. Verify each downloaded SVG is single-fill before
shipping (`grep 'fill="#' your-icon.svg`); multi-fill source art needs
normalizing to one color for the template mode to work.

SF Symbols are acceptable ONLY where the frame itself has no purpose-drawn
vector (a generic chevron, a system disclosure indicator) — and say so in a
comment, so a future pass doesn't wonder why it wasn't exported.

Record every exported glyph's node id → asset-name mapping in the relevant
`docs/design/*.md` file, next to its frame's walked spec. That table is the
re-export recipe if the glyph ever needs to change — a lookup, not a
re-derivation.

### 4. Empty and first-run states are designed states

If a frame explicitly draws an empty/first-run treatment, implement THAT
treatment for the empty state — not the content-state UI with placeholder
values, not the content-state UI with some rows hidden. Two failure
patterns, both real, both from this project:

- **Leaking content-state chrome into empty state**: a "0 next steps this
  week" summary strip, a List/Timeline toggle, and filter chips all showing
  above a "Nothing planned yet?" empty state — every one of those controls
  is meaningless with nothing to filter or toggle, and the frame doesn't
  draw them there.
- **Ad-hoc copy replacing the frame's own affordance**: swapping a frame's
  compact "Schedule an event" button for an unrelated bigger "Add event"
  card, because that's what existed before the fidelity pass touched it.

The one exception real-data-only and safety rules carve out: content that
would be **fabricated** (a fake saved-article list, invented account email)
still doesn't get drawn even if the frame shows sample content there — see
rule 5. Visual TREATMENT is still law; only literal fake values are dropped.

### 5. Sample content vs. treatment — know which one you're copying

Frames are full of placeholder content: sample names ("Greg", "Benjamin"),
photos, fake email addresses, invented "$59/year" pricing copy. None of that
is instruction to fabricate matching content in the shipped app — the
real-data-only rule (this project's standing call) decides what content
renders, never the frame's sample values. What IS instruction from the frame
is the **visual treatment**: the card shape, the button style, the type
scale, the icon. Separate the two explicitly when reading a frame; conflate
them and you either fabricate data or, overcorrecting, strip out real
visual fidelity along with the fake content.

### 6. Tokens only — new primitives are a normal outcome, not a workaround

A measured color that doesn't match an existing Hearth token is not
permission to write `Color(hex: "#4F5D3A")` inline. `tools/lint-design-tokens.py`
hard-gates this (`NO-INLINE` check) — any raw hex outside `Theme.swift` fails
the build gate. The correct move, every time: add the primitive to
`HearthPrimitives` in `Theme.swift`, add its semantic `Color` wrapper next to
the other tokens, document it in `spec/look-and-feel/DESIGN.tokens.md` in the
same table format, and reference the token everywhere. This is normal, not
an exception — round 3 added three new primitives (a planner-card border
gray, a planner search-accent green pair) this way with zero linter
friction. Run `python3 tools/lint-design-tokens.py` before considering any
Figma-sourced work done; it also re-runs the accessibility contrast audit,
which a new color pairing can silently break.

### 7. Verify per section, side-by-side, at matched scale — iterate to zero

Whole-screen glances do not catch the drift described in rule 3's root
cause. The loop that does:

1. Screenshot the simulator (`xcrun simctl io <UDID> screenshot`). The
   simulator renders at the device's native scale (commonly @3x — 1206px
   wide for a 402pt-wide device); Figma frames and `axe describe-ui` frames
   are in POINTS. Crop and scale the section under test to the frame's own
   width before comparing, or you're comparing at the wrong zoom.
2. Place it side-by-side with the matching crop of the reference render
   (`magick a.png b.png +append cmp.png`, or equivalent).
3. Read the composite at zoom. Compare, property by property (rule 2's
   list): font weight, size, color, spacing, radius, stroke, icon shape.
4. Fix → rebuild → repeat until there is **no visible difference**. "Close"
   is not done — this was Miguel's explicit standard for round 3, and it is
   the right standard: a stakeholder who took screenshots to point out drift
   will keep finding drift at "pretty close."

Do this per SECTION (a card, a tab bar, a composer), not once per whole
screen. A screen can look right in aggregate while three of its five
sections are each individually off — the aggregate glance is exactly what
misses that.

### 8. Cross-cutting chrome gets an explicit owner

Tab bars, composers, section-header components, shared button styles — the
things that appear on every screen or across many screens — are exactly
where scope holes hide, because no single screen's plan claims them. When
scoping a fidelity pass, explicitly list the cross-cutting components in
play and who's fixing them, even if the answer for most of them is "already
correct, no action." An unowned component doesn't get skipped because
someone decided it was fine; it gets skipped because nobody decided anything
about it.

### 9. LazyVGrid does not equalize row heights across differing cell content

A concrete instance of rule 2's discipline paying off: round 3's interest
tiles had DIFFERENT internal structure between selected and unselected
states (a badge row present only when unselected, different top/bottom
padding per state). `LazyVGrid` does not force every cell in a row to a
shared height — cells with taller intrinsic content are simply taller,
visibly so, not just top-aligned in a uniform row. If two states of the same
grid cell must render at the same height, either:
- keep an identical view hierarchy across states and only vary appearance
  (color, opacity, a `.hidden()`-equivalent) — not presence/absence of rows,
  or
- give every cell an explicit shared `minHeight`.

The safer default is the first: reserve the same layout slots always, and
toggle *visibility* (opacity, tint) rather than *existence* of a row.

## Known traps (each has cost real time in this repo)

- **Asset-catalog caching.** A newly added/renamed imageset may not show up
  after a rebuild alone — `xcrun simctl uninstall` (or `simctl erase` for a
  harder reset) before trusting a "the icon didn't change" observation.
- **Points vs. pixels.** Screenshots are native-resolution pixels (commonly
  @3x); `axe tap`/`describe-ui` frames and Figma frames are points. Prefer
  `axe tap --label` over hand-computed coordinates — it resolves the correct
  point internally.
- **The accent split.** `accentDefault` (fill) and `accentOnCanvas`
  (text/icon on cream) are deliberately different token NAMES for
  historical-AA reasons even when their hex values currently match — copy
  whichever token the neighboring, already-correct code uses; don't assume
  they're interchangeable.
- **SourceKit cross-file "cannot find type X" is a stale-index false
  positive**, not a real error — `xcodebuild` is the source of truth, always
  verify there before treating a SourceKit diagnostic as real.
- **Simulator auth walls block headless verification of anything past
  onboarding.** A DEBUG-only env-gated escape hatch (e.g.
  `UITEST_SKIP_SIGNIN`) can skip the sign-in WALL, but full onboarding still
  requires a real backend-confirmed account for `onboardingCompleted` to
  latch — a bypassed session can loop back to the paywall repeatedly without
  ever reaching post-onboarding tabs. Don't burn excessive turns fighting
  this loop; verify what you can screen-by-screen as you pass through it,
  and note in the report what remains for a human (or a real-auth session)
  to confirm.

## Checklist for the next fidelity pass

- [ ] Every frame in scope fetched in ONE batched `/nodes` call, walked, and
      appended to `docs/design/*.md`
- [ ] Every glyph the frames draw exported as a template SVG imageset in ONE
      batched `/images` call, node-id → asset-name table recorded
- [ ] Every measured property (rule 2's list) accounted for per component —
      not just structure and rough color
- [ ] Empty/first-run states implemented as their own designed state, no
      content-state chrome leaking in, no fabricated content
- [ ] Zero inline hex — new colors become primitives + semantic tokens +
      DESIGN.tokens.md entries; `python3 tools/lint-design-tokens.py` clean
- [ ] Per-section side-by-side verification at matched scale, iterated to
      zero visible difference — not a whole-screen glance
- [ ] Cross-cutting chrome (tab bars, composers, shared headers) explicitly
      listed and assigned, even if "already correct"
