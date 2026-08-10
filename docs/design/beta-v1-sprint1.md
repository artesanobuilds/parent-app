# beta-v1 — Design Sprint 1 spec (onboarding + dashboard + profile editors)

Extracted from Figma `Wb072IjTsBT7Ooqc41UFbK`, page `754:4310`
(*Design sprint1 - onboarding+dashboard (WIP)*) via the REST API
`/v1/files/:key/nodes`, then walked locally. Values are **measured**: fonts as
`family weight size/lineHeight ls<letterSpacing>`, fills as hex, plus radii, padding, gaps,
auto-layout mode (`H`/`V`), `hz:`/`vy:` sizing (FILL/HUG/FIXED), strokes and shadows.

## Coverage — read this before trusting the file

**This file covers all 31 real screens on the page.** The ids are listed below so a reader can
tell *coverage* from *completeness* without opening Figma.

> **2026-08-08: this file was REBUILT, and why that matters.** The previous version claimed to be
> "the source of truth — do not re-read Figma" while containing only **13 of 31** screens. The page
> fetch had been SHALLOW (`/nodes` on the page id returns child names with no nested content), so 18
> screens were never read at all — including `Onboarding - 2`, whose shipped build therefore matched
> nothing. The doc's own "do not re-read" header is what stopped anyone noticing. If you extract from
> Figma again: **deep-fetch the frame ids, in batches; never the page id alone**, and state coverage.
>
> **2026-08-09, ~13:47: three frames were RE-EXTRACTED — `choose a plan` (`754:4897`),
> `create your account` (`754:4943`) and `Onboarding - 001` (`754:4312`) — because the design
> itself changed between the morning extraction and Miguel's 1:47pm screenshot.** The splash's
> illustration changed entirely (a pencils-in-a-cup graphic → a coffee-mug-with-star mark), and
> `create your account` gained a new `mvptrophy 1` raster layer (a DIFFERENT trophy graphic, MVP
> text baked into the same asset) while its old standalone "MVP" wordmark text layer was deleted.
> Both new images were fetched via the raw image-fill/Images API for exact pixels, not a re-render,
> and installed as `OnboardingSplashMark.imageset` / `OnboardingTrophy.imageset`. **A design can
> change same-day, after a spec was already committed — re-check coverage AND freshness, not just
> completeness, before trusting a screen you haven't looked at recently.**

The page also carries 4 stray 24x24 icons and 6 loose text/vector notes that are not screens. Two of
those notes are design intent that appears in no frame: the For-You per-card feedback
("What we chose for you this week... / Show more like this / Don't show me this") and the
education-style option list (`Public Private Home school Charter Montessori Waldorf Forest Other`).

| node id | frame |
|---|---|
| `1006:2517` | account 02 |
| `1008:5111` | account 03 |
| `870:1234` | account01 |
| `754:4897` | choose a plan |
| `855:4157` | circle member |
| `855:4275` | co-parent 001 |
| `754:4943` | create your account |
| `869:981` | kid-001a |
| `858:4985` | kid-001b |
| `907:2949` | kid-001b |
| `855:3623` | kid-001c |
| `855:3839` | kid-002a |
| `754:4312` | Onboarding - 001 |
| `754:4317` | Onboarding - 2 |
| `890:1479` | Onboarding - 3 |
| `754:4437` | Onboarding - creating account |
| `754:4553` | Onboarding - Dashboard 1 |
| `754:4478` | Onboarding - Dashboard 2 |
| `754:4342` | Onboarding - kids a |
| `754:4355` | Onboarding - kids c |
| `890:1533` | Onboarding - kids e |
| `754:4386` | Onboarding - kids f |
| `890:1564` | Onboarding - kids g |
| `890:1511` | Onboarding - kidsb |
| `1004:1746` | Onboarding - need help with acitivities |
| `754:4417` | Onboarding - need help with dynamics |
| `754:4458` | Onboarding - welcome |
| `754:6516` | Onboarding - welcome |
| `869:1090` | Onboarding - welcome |
| `855:3939` | parent 001 |
| `855:4033` | parent 002 |

## Reading notes

- **Two display scales.** Funnel and person-name titles are Fraunces **w700 56/60 ls-1.12**; the two
  "need help with..." screens are **38/40 ls-0.38**. One shared token cannot serve both.
- Copy is verbatim, **typos included** — "Family roll" (role), "What do you in your free time?",
  `kid-002a` showing "Goals for Benjamin" on Lily's screen, "acitivities". Render the correction, not
  the typo.
- The activities grid draws "Nature" and "Parks" twice; treat as a slip, not a spec.
- The 1px input/chip strokes (`#C9C5BE`, `#E9E4DC`) are **decorative** — they measure 1.51:1 and
  1.22:1 against their grounds. Draw them, but do not treat them as the boundary indicator or
  register them as UI-contrast pairs.
- Canvas x-order IS the flow, and it places the profile editors AFTER Dashboard 1 — the "settings"
  screens are the tail of onboarding, not a Settings-only destination.
- Status bars are retained because they carry the page ground; decorative status-bar vectors are
  trimmed.

---


====================================================================================================
FRAME Onboarding - 001 — `754:4312` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  [Frame 204973884] FRAME 419.9x53.9 H gap13.9 pad13.9/13.9/13.9/13.9 vy:HUG hz:HUG
    TEXT "Most Valuable Parent"  [Inter w700 30.684207916259766/25.1 ls0.00 C #1E1E1E]
  [Layer_1] INSTANCE 276.0x375.0
    [Group] GROUP 276.0x89.4
      <Vector> VECTOR 112.8x89.4 #000000
      <Vector> VECTOR 86.8x89.4 #000000
      <Vector> VECTOR 83.5x89.4 #000000
    <Vector> VECTOR 108.7x10.1 #000000
    <Vector> VECTOR 108.7x253.1 #000000
    <Vector> VECTOR 57.9x159.1 #000000
    <Vector> VECTOR 71.6x68.1 #E89C2E
====================================================================================================
FRAME Onboarding - 2 — `754:4317` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 204973840] FRAME 380.0x660.0 V gap30.0 vy:HUG hz:FIXE
    [Frame 14] FRAME 380.0x179.0 V gap15.0 vy:HUG hz:FILL
      TEXT "Let’s get acquainted"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
      TEXT "A few quick questions so we can make MVP feel like it was made for your family."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 24] FRAME 380.0x451.0 V gap23.0 vy:HUG hz:FILL
      [Frame 1] FRAME 380.0x91.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "What should we call you?"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [Frame 2] FRAME 320.0x48.0 fill=#FCFBF8 H gap10.0 pad12.0/0/12.0/0 r32.0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Your first name "  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
      [Frame 17] FRAME 380.0x97.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "Your household"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [large input] INSTANCE 320.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FILL stroke #C9C5BE 1.0
          TEXT "Your "  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [arrow] INSTANCE 24.0x12.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x9.0 
      [Frame 24] FRAME 380.0x97.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "Education style"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [large input] INSTANCE 320.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FILL stroke #C9C5BE 1.0
          TEXT "Choose"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [arrow] INSTANCE 24.0x12.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x9.0 
      [Frame 25] FRAME 380.0x97.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "Location"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [large input] INSTANCE 320.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FILL stroke #C9C5BE 1.0
          TEXT "000000"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
  [Frame 16] FRAME 380.0x74.0 V gap10.0 vy:HUG hz:FIXE
    [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
      TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
    TEXT "Next: Your Children"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]

====================================================================================================
FRAME Onboarding - kids a — `754:4342` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 5] FRAME 376.0x60.0 V gap11.0 vy:HUG hz:FIXE
    [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
      [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
        [back arrow] INSTANCE 16.0x13.0
          <Vector> VECTOR 6.7x13.0 
          <Vector> VECTOR 16.0x0.0 
      [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
        [Frame 3] FRAME 365.0x26.0 r100.0 vy:FILL hz:FIXE
          [Frame 4] FRAME 77.0x26.0 fill=#2E3A5F r100.0
    TEXT "Greg’s children"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 1] FRAME 376.0x244.0 V gap22.0 vy:HUG hz:FIXE
    TEXT "Hi Gregory!"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
    TEXT "Now let's meet your kids. We just need their names, ages, and a sense of who they are."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [large input] INSTANCE 278.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FIXE stroke #C8C3B8 1.0
      TEXT "0"  [Inter w300 27.0/24.0 ls0.0 C #D8D8D8]
    TEXT "How many children?"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 16] FRAME 376.0x74.0 V gap10.0 vy:HUG hz:FIXE
    [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
      TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
    TEXT "Next: Child One"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]

====================================================================================================
FRAME Onboarding - kidsb — `890:1511` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 5] FRAME 376.0x60.0 V gap11.0 vy:HUG hz:FIXE
    [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
      [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
        [back arrow] INSTANCE 16.0x13.0
          <Vector> VECTOR 6.7x13.0 
          <Vector> VECTOR 16.0x0.0 
      [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
        [Frame 3] FRAME 365.0x26.0 r100.0 vy:FILL hz:FIXE
          [Frame 4] FRAME 77.0x26.0 fill=#2E3A5F r100.0
    TEXT "Greg’s children"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 1] FRAME 376.0x244.0 V gap22.0 vy:HUG hz:FIXE
    TEXT "Hi Gregory!"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
    TEXT "Now let's meet your kids. We just need their names, ages, and a sense of who they are."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [large input] INSTANCE 278.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FIXE stroke #C8C3B8 1.0
      TEXT "2"  [Inter w300 27.0/24.0 ls0.0 C #151412]
    TEXT "How many children?"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 16] FRAME 376.0x74.0 V gap10.0 vy:HUG hz:FIXE
    [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
      TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
    TEXT "Next: Child One"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]

====================================================================================================
FRAME Onboarding - kids c — `754:4355` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 3] FRAME 440.0x956.0
    [Frame 5] FRAME 376.0x60.0 V gap11.0 vy:HUG hz:FIXE
      [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
        [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
          [back arrow] INSTANCE 16.0x13.0
            <Vector> VECTOR 6.7x13.0 
            <Vector> VECTOR 16.0x0.0 
        [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
          [Frame 3] FRAME 365.0x26.0 r100.0 vy:FILL hz:FIXE
            [Frame 4] FRAME 154.0x26.0 fill=#2E3A5F r100.0
      TEXT "Child One "  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
    [Frame 22] FRAME 380.0x658.0 V gap24.0 vy:HUG hz:FIXE
      [Frame 21] FRAME 380.0x176.0 V gap12.0 vy:HUG hz:FILL
        TEXT "Tell us about your first"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
        TEXT "Just the basics for now — we'll learn more as we go."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
      [Frame 23] FRAME 42.0x1.0 fill=#6E6A62 vy:FIXE hz:FIXE
      [Frame 1] FRAME 380.0x433.0 V gap22.0 vy:HUG hz:FILL
        TEXT "Child one"  [Inter w900 24.0/24.0 ls0.0 C #1E1E1E]
        [Frame 10] FRAME 380.0x387.0 V gap45.0 vy:HUG hz:FILL
          [Frame 6] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
            TEXT "What should we call them?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
            [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
              TEXT "Name"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [Frame 7] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
            TEXT "How old are they?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
            [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
              TEXT "0"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [Frame 9] FRAME 380.0x125.0 V gap22.0 vy:HUG hz:FILL
            [Frame 204973871] FRAME 380.0x125.0 V gap6.0 vy:HUG hz:FILL
              [Frame 9] FRAME 380.0x29.0 V gap22.0 vy:FIXE hz:FILL
                TEXT "About child one"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
              [Frame 204973869] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
                [tag choice] INSTANCE 187.0x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                  [Frame 5] FRAME 84.0x18.0 H gap9.0 vy:HUG hz:HUG
                    [School] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 14.0x14.0 
                      <Vector> VECTOR 12.8x10.5 #1B7498
                    TEXT "Grade"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
                    [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
                      [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                        <Vector> VECTOR 12.0x6.0 #1B7498
                [tag choice] FRAME 187.0x42.0 fill=#FFFFFF H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                  [Frame 5] FRAME 115.0x18.0 H gap9.0 vy:HUG hz:HUG
                    [boy] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 10.5x10.5 #1B7498
                    [girl] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 7.0x11.1 #1B7498
                    TEXT "Gender"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
                    [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
                      [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                        <Vector> VECTOR 12.0x6.0 
              [Frame 204973870] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
                [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                  [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                    [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 13.2x12.1 #1B7498
                    TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
                [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                  [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                    [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 12.5x11.1 #1B7498
                    TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
                [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                  [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                    [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                      [Group] GROUP 18.0x18.0
                        <Vector> VECTOR 18.0x18.0 
                      [Group] GROUP 12.0x13.5
                        [Group] GROUP 12.0x13.5
                          [Group] GROUP 4.5x5.3
                            <Vector> VECTOR 4.5x5.3 #1B7498
                          [Group] GROUP 12.0x13.4
                            <Vector> VECTOR 12.0x13.4 #1B7498
                    TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 16] FRAME 376.0x82.0 V gap12.0 vy:FIXE hz:FIXE
      [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      TEXT "Next: Child Two"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]

====================================================================================================
FRAME Onboarding - kids e — `890:1533` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 3] FRAME 440.0x956.0
    [Frame 5] FRAME 376.0x60.0 V gap11.0 vy:HUG hz:FIXE
      [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
        [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
          [back arrow] INSTANCE 16.0x13.0
            <Vector> VECTOR 6.7x13.0 
            <Vector> VECTOR 16.0x0.0 
        [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
          [Frame 3] FRAME 365.0x26.0 r100.0 vy:FILL hz:FIXE
            [Frame 4] FRAME 154.0x26.0 fill=#2E3A5F r100.0
      TEXT "Child One "  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
    [Frame 22] FRAME 380.0x658.0 V gap24.0 vy:HUG hz:FIXE
      [Frame 21] FRAME 380.0x176.0 V gap12.0 vy:HUG hz:FILL
        TEXT "Tell us about your first"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
        TEXT "Just the basics for now — we'll learn more as we go."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
      [Frame 23] FRAME 42.0x1.0 fill=#6E6A62 vy:FIXE hz:FIXE
      [Frame 1] FRAME 380.0x433.0 V gap22.0 vy:HUG hz:FILL
        TEXT "Child one"  [Inter w900 24.0/24.0 ls0.0 C #1E1E1E]
        [Frame 10] FRAME 380.0x387.0 V gap45.0 vy:HUG hz:FILL
          [Frame 6] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
            TEXT "What should we call them?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
            [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
              TEXT "Benjamin"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [Frame 7] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
            TEXT "How old are they?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
            [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
              TEXT "5"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [Frame 204973871] FRAME 380.0x125.0 V gap6.0 vy:HUG hz:FILL
            [Frame 9] FRAME 380.0x29.0 V gap22.0 vy:FIXE hz:FILL
              TEXT "About child one"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
            [Frame 204973869] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
              [tag choice] INSTANCE 187.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                [Frame 5] FRAME 80.0x18.0 H gap9.0 vy:HUG hz:HUG
                  [School] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                    <Vector> VECTOR 14.0x14.0 
                    <Vector> VECTOR 12.8x10.5 #F5F3EF
                  TEXT "Pre-k"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
                  [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
                    [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 12.0x6.0 
              [tag choice] INSTANCE 187.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                [Frame 5] FRAME 70.0x18.0 H gap9.0 vy:HUG hz:HUG
                  [boy] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                    <Vector> VECTOR 10.5x10.5 #F5F3EF
                  TEXT "Boy"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
                  [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
                    [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                      <Vector> VECTOR 12.0x6.0 
            [Frame 204973870] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
              [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                  [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                    <Vector> VECTOR 13.2x12.1 #1B7498
                  TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
              [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                  [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                    <Vector> VECTOR 12.5x11.1 #1B7498
                  TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
              [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
                [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                  [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                    [Group] GROUP 18.0x18.0
                      <Vector> VECTOR 18.0x18.0 
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 12.0x13.5
                        [Group] GROUP 4.5x5.3
                          <Vector> VECTOR 4.5x5.3 #1B7498
                        [Group] GROUP 12.0x13.4
                          <Vector> VECTOR 12.0x13.4 #1B7498
                  TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 16] FRAME 376.0x82.0 V gap12.0 vy:FIXE hz:FIXE
      [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      TEXT "Next: Child Two"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]

====================================================================================================
FRAME Onboarding - kids f — `754:4386` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 3] FRAME 440.0x956.0
    [Frame 5] FRAME 376.0x60.0 V gap11.0 vy:HUG hz:FIXE
      [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
        [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
          [back arrow] INSTANCE 16.0x13.0
            <Vector> VECTOR 6.7x13.0 
            <Vector> VECTOR 16.0x0.0 
        [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
          [Frame 3] FRAME 365.0x26.0 r100.0 vy:FILL hz:FIXE
            [Frame 4] FRAME 154.0x26.0 fill=#2E3A5F r100.0
      TEXT "Child Two "  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
    [Frame 16] FRAME 376.0x74.0 V gap10.0 vy:HUG hz:FIXE
      [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      TEXT "Next: Family Challenges"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 22] FRAME 380.0x637.0 V gap24.0 vy:HUG hz:FIXE
    [Frame 21] FRAME 380.0x176.0 V gap12.0 vy:HUG hz:FILL
      TEXT "Tell us about your second"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
      TEXT "Same deal — name, age, and a little of their personality."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 23] FRAME 42.0x1.0 fill=#6E6A62 vy:FIXE hz:FIXE
    [Frame 1] FRAME 380.0x263.0 V gap22.0 vy:HUG hz:FILL
      TEXT "Child two"  [Inter w900 24.0/24.0 ls0.0 C #1E1E1E]
      [Frame 10] FRAME 380.0x217.0 V gap45.0 vy:HUG hz:FILL
        [Frame 6] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
          TEXT "What should we call them?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
          [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
            TEXT "Name"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
        [Frame 7] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
          TEXT "How old are they?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
          [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
            TEXT "0"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
    [Frame 9] FRAME 380.0x125.0 V gap22.0 vy:HUG hz:FILL
      [Frame 204973871] FRAME 380.0x125.0 V gap6.0 vy:HUG hz:FILL
        [Frame 9] FRAME 380.0x29.0 V gap22.0 vy:FIXE hz:FILL
          TEXT "About child two"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
        [Frame 204973869] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
          [tag choice] INSTANCE 187.0x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
            [Frame 5] FRAME 84.0x18.0 H gap9.0 vy:HUG hz:HUG
              [School] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 14.0x14.0 
                <Vector> VECTOR 12.8x10.5 #1B7498
              TEXT "Grade"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
              [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
                [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.0x6.0 #1B7498
          [tag choice] FRAME 187.0x42.0 fill=#FFFFFF H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
            [Frame 5] FRAME 115.0x18.0 H gap9.0 vy:HUG hz:HUG
              [boy] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 10.5x10.5 #1B7498
              [girl] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 7.0x11.1 #1B7498
              TEXT "Gender"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
              [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
                [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.0x6.0 
        [Frame 204973870] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
          [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
            [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
              [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 13.2x12.1 #1B7498
              TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
          [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
            [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
              [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 12.5x11.1 #1B7498
              TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
          [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
            [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
              [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                [Group] GROUP 18.0x18.0
                  <Vector> VECTOR 18.0x18.0 
                [Group] GROUP 12.0x13.5
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 4.5x5.3
                      <Vector> VECTOR 4.5x5.3 #1B7498
                    [Group] GROUP 12.0x13.4
                      <Vector> VECTOR 12.0x13.4 #1B7498
              TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]

====================================================================================================
FRAME Onboarding - kids g — `890:1564` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 3] FRAME 440.0x956.0
    [Frame 5] FRAME 376.0x60.0 V gap11.0 vy:HUG hz:FIXE
      [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
        [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
          [back arrow] INSTANCE 16.0x13.0
            <Vector> VECTOR 6.7x13.0 
            <Vector> VECTOR 16.0x0.0 
        [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
          [Frame 3] FRAME 365.0x26.0 r100.0 vy:FILL hz:FIXE
            [Frame 4] FRAME 154.0x26.0 fill=#2E3A5F r100.0
      TEXT "Child Two "  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
    [Frame 16] FRAME 376.0x74.0 V gap10.0 vy:HUG hz:FIXE
      [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      TEXT "Next: Family Challenges"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 22] FRAME 380.0x637.0 V gap24.0 vy:HUG hz:FIXE
    [Frame 21] FRAME 380.0x176.0 V gap12.0 vy:HUG hz:FILL
      TEXT "Tell us about your second"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
      TEXT "Same deal — name, age, and a little of their personality."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 23] FRAME 42.0x1.0 fill=#6E6A62 vy:FIXE hz:FIXE
    [Frame 1] FRAME 380.0x263.0 V gap22.0 vy:HUG hz:FILL
      TEXT "Child two"  [Inter w900 24.0/24.0 ls0.0 C #1E1E1E]
      [Frame 10] FRAME 380.0x217.0 V gap45.0 vy:HUG hz:FILL
        [Frame 6] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
          TEXT "What should we call them?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
          [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
            TEXT "Lily"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
        [Frame 7] FRAME 330.0x86.0 V gap8.0 vy:HUG hz:FIXE
          TEXT "How old are they?"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
          [large input] INSTANCE 330.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r24.0 vy:FIXE hz:FILL stroke #C8C3B8 1.0
            TEXT "2"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
    [Frame 204973871] FRAME 380.0x125.0 V gap6.0 vy:HUG hz:FILL
      [Frame 9] FRAME 380.0x29.0 V gap22.0 vy:FIXE hz:FILL
        TEXT "About child two"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
      [Frame 204973869] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
        [tag choice] INSTANCE 187.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
          [Frame 5] FRAME 65.0x18.0 H gap9.0 vy:HUG hz:HUG
            [School] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 14.0x14.0 
              <Vector> VECTOR 12.8x10.5 #F5F3EF
            TEXT "NA"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
            [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
              [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 12.0x6.0 
        [tag choice] INSTANCE 187.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
          [Frame 5] FRAME 68.0x18.0 H gap9.0 vy:HUG hz:HUG
            [girl] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 7.0x11.1 #F5F3EF
            TEXT "Girl"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
            [Frame 6] FRAME 14.0x8.0 V gap10.0 vy:HUG hz:FIXE
              [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 12.0x6.0 
      [Frame 204973870] FRAME 380.0x42.0 H gap6.0 vy:HUG hz:FILL
        [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
          [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
            [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.2x12.1 #1B7498
            TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
        [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
          [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
            [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 12.5x11.1 #1B7498
            TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
        [tag item] INSTANCE 122.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
          [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
            [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
              [Group] GROUP 18.0x18.0
                <Vector> VECTOR 18.0x18.0 
              [Group] GROUP 12.0x13.5
                [Group] GROUP 12.0x13.5
                  [Group] GROUP 4.5x5.3
                    <Vector> VECTOR 4.5x5.3 #1B7498
                  [Group] GROUP 12.0x13.4
                    <Vector> VECTOR 12.0x13.4 #1B7498
            TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]

====================================================================================================
FRAME kid-001b — `858:4985` — 440.0x1847.0 fill=#FFFFFF V gap21.0 pad60.0/0/90.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Benjamin’s settings"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 354.0x323.0 fill=IMAGE+GRADIENT_LINEAR+#FFFFFF @0.50 V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 96.4x26.0 fill=#151412 H gap6.0 pad6.0/10.0/6.0/10.0 r18.599998474121094 vy:HUG hz:HUG DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Upload new"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x1380.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [Frame 204973859] FRAME 250.0x36.7 H gap10.0 vy:HUG hz:FIXE
      [small button] FRAME 120.0x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
        [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
          [Frame] FRAME 20.0x20.0
            <Vector> VECTOR 15.0x15.0 #E3E3E3
        TEXT "Save"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
      [small button] FRAME 120.0x35.7 fill=#858585 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
        TEXT "Cancel"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    [Frame 204973858] FRAME 380.0x120.0 fill=#FFFFFF H gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      TEXT "Benjamin "  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x307.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x307.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Son"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x53.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Birthday:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "April 25, 2021"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Grade:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Pre-K"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 9] FRAME 320.0x102.0 V gap22.0 pad20.0/0/0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          TEXT "Personality"  [Inter w700 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 9] FRAME 330.0x42.0 G vy:HUG hz:FIXE
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  [Group] GROUP 18.0x18.0
                    <Vector> VECTOR 18.0x18.0 
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 4.5x5.3
                        <Vector> VECTOR 4.5x5.3 #1B7498
                      [Group] GROUP 12.0x13.4
                        <Vector> VECTOR 12.0x13.4 #1B7498
                TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 13.2x12.1 #1B7498
                TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.5x11.1 #1B7498
                TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 53] FRAME 380.0x594.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "What makes Benjamin special"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x114.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973863] FRAME 16.0x98.0 V gap10.0 pad6.0/0/6.0/0 vy:FILL hz:FIXE
          [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973862] FRAME 302.0x98.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 302.0x74.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Comics, sports, funny animals, sticks, carrots, ⏎ pizza, cheese sticks, running and jumping, ⏎ turtles, slime"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 60] FRAME 320.0x96.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x80.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 258.0x80.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 258.0x56.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Clowns, big dogs, mean people, baths, ⏎ loud noises, mean people"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 64] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 236.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 236.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Dinners, social events, school work"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 65] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 208.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 208.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Math, reading, sense of humor"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 66] FRAME 320.0x96.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x80.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 287.0x80.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Goals for Benjamin"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 287.0x56.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "More math puzzles and reading challenges, ⏎ interacting with other kids, fear of water"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME kid-001b — `907:2949` — 440.0x1847.0 fill=#FFFFFF V gap21.0 pad60.0/0/90.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Benjamin’s settings"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 354.0x323.0 fill=IMAGE+GRADIENT_LINEAR+#FFFFFF @0.50 V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 96.4x26.0 fill=#151412 H gap6.0 pad6.0/10.0/6.0/10.0 r18.599998474121094 vy:HUG hz:HUG DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Upload new"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x1380.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [Frame 204973859] FRAME 250.0x36.7 H gap10.0 vy:HUG hz:FIXE
      [small button] FRAME 120.0x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
        [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
          [Frame] FRAME 20.0x20.0
            <Vector> VECTOR 15.0x15.0 #E3E3E3
        TEXT "Save"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
      [small button] FRAME 120.0x35.7 fill=#858585 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
        TEXT "Cancel"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    [Frame 204973858] FRAME 380.0x120.0 fill=#FFFFFF H gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      TEXT "Benjamin "  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x371.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x371.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Son"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x53.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Birthday:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "April 25, 2021"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Grade:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Pre-K"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 9] FRAME 320.0x166.0 V gap22.0 pad20.0/0/0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          TEXT "More about Benjamin"  [Inter w700 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 9] FRAME 330.0x42.0 G vy:HUG hz:FIXE
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  [Group] GROUP 18.0x18.0
                    <Vector> VECTOR 18.0x18.0 
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 4.5x5.3
                        <Vector> VECTOR 4.5x5.3 #1B7498
                      [Group] GROUP 12.0x13.4
                        <Vector> VECTOR 12.0x13.4 #1B7498
                TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 13.2x12.1 #1B7498
                TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.5x11.1 #1B7498
                TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
          [tag item] INSTANCE 320.0x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FIXE hz:FILL stroke #1B7498 0.5
            [Frame 5] FRAME 32.0x18.0 H gap4.0 vy:HUG hz:HUG
              TEXT "More"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 53] FRAME 380.0x522.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "What makes Benjamin special"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973863] FRAME 16.0x62.0 V gap10.0 pad6.0/0/6.0/0 vy:FILL hz:FIXE
          [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973862] FRAME 250.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 250.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Examples: Berries, kittens, silly songs"  [Inter w400 13.0/18.0 ls0.0 L #989591]
      [Frame 60] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 230.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 230.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Examples: green food, loud noises"  [Inter w400 13.0/18.0 ls0.0 L #989591]
      [Frame 64] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 141.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 141.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Examples: bathtime"  [Inter w400 13.0/18.0 ls0.0 L #989591]
      [Frame 65] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 118.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 118.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Examples: math"  [Inter w400 13.0/18.0 ls0.0 L #989591]
      [Frame 66] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 122.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Goals for Benjamin"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 122.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Examples: social"  [Inter w400 13.0/18.0 ls0.0 L #989591]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME kid-002a — `855:3839` — 440.0x1460.0 fill=#FFFFFF V pad60.0/0/60.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Lily’s profile and plan"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 440.0x401.0 fill=IMAGE+GRADIENT_LINEAR V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 62.0x26.0 fill=#151412 H gap6.0 pad6.0/6.0/6.0/6.0 r18.599998474121094 vy:HUG hz:FIXE DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Edit"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x1383.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    TEXT "Lily"  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 204973854] FRAME 380.0x190.0 V gap30.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Frame 204973857] FRAME 380.0x190.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Lily’s Week"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        TEXT "Readiness camp (date)  ⏎ All school picnic ⏎ Ballet class"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973855] FRAME 380.0x154.0 V gap30.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Frame 204973857] FRAME 380.0x154.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Lily’s Master Plan"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        TEXT "All the things"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 52] FRAME 380.0x606.0 V gap30.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Frame 204973857] FRAME 380.0x606.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Lily’s profile"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x53.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Birthday:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "June 2, 2024"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Grade:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Pre-K"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 9] FRAME 320.0x102.0 V gap22.0 pad20.0/0/0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          TEXT "Personality"  [Inter w700 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 9] FRAME 320.0x42.0 G vy:HUG hz:FILL
            [tag item] INSTANCE 103.3x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  [Group] GROUP 18.0x18.0
                    <Vector> VECTOR 18.0x18.0 
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 4.5x5.3
                        <Vector> VECTOR 4.5x5.3 #1B7498
                      [Group] GROUP 12.0x13.4
                        <Vector> VECTOR 12.0x13.4 #1B7498
                TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 103.3x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 13.2x12.1 #1B7498
                TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 103.3x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.5x11.1 #1B7498
                TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
        [Frame 58] FRAME 320.0x33.0 H gap10.0 vy:FIXE hz:FILL
          TEXT "What makes Lily special"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 59] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 6.0x12.0 
          TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 60] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 6.0x12.0 
          TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 61] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 6.0x12.0 
          TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 62] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 6.0x12.0 
          TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 63] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL
          [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 6.0x12.0 
          TEXT "Goals for Lily"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME account01 — `870:1234` — 440.0x1714.0 fill=#E9E4DC 
====================================================================================================
  [Container] FRAME 440.0x1582.0 V gap18.0 pad0/30.0/0/30.0 vy:FIXE hz:FIXE
    [Status Bar] FRAME 440.0x62.0 H gap154.0 pad21.0/0/19.0/0 vy:HUG hz:FIXE
      [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
        TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #000000]
      [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
        <Cellular Connection> VECTOR 19.2x12.2 #000000
        <Wifi> VECTOR 17.1x12.3 #000000
        [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
          [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #000000 1.0
          <Cap> VECTOR 1.3x4.1 #000000
          [Capacity] RECTANGLE 21.0x9.0 fill=#000000 r2.5
    [Container] FRAME 380.0x568.7 V gap12.0 vy:HUG hz:FILL
      [Container] FRAME 380.0x46.0 V gap10.0 pad0/0/10.0/0 vy:HUG hz:FILL
        [Icon Container] FRAME 37.0x36.0 fill=#1B7498 V gap4.8 pad11.5/11.5/11.5/11.5 r48.0 vy:FIXE hz:HUG
          TEXT "G"  [Fraunces w700 18.239999771118164/19.2 ls-0.18 C #FFFFFF]
      [Container] FRAME 380.0x245.0 fill=#F5F3EF V gap12.0 pad24.0/30.0/0/30.0 r32.0 vy:FIXE hz:FILL
        TEXT "YOUR KIDS"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        [Card Container] FRAME 348.0x153.0 H gap12.0 vy:HUG hz:HUG
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30+GRADIENT_LINEAR V gap7.4 pad17.7/17.7/17.7/17.7 vy:FILL hz:FIXE
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Benjamin"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30 V gap7.4 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FILL
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Lily"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
      [Frame 28] FRAME 380.0x253.7 fill=#F5F3EF V gap8.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL GLASS rNone None DROP_SHADOW r10.0 #000000
        [Frame 39] FRAME 320.0x22.0 H gap12.0 vy:HUG hz:FILL
          [coach] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
            [Layer_1] FRAME 13.7x17.8
              <Vector> VECTOR 6.8x7.0 #1B7498
              <Vector> VECTOR 2.2x2.3 #1B7498
              <Vector> VECTOR 1.4x1.4 #1B7498
              <Vector> VECTOR 6.0x8.0 #1B7498
              <Vector> VECTOR 7.3x7.8 #1B7498
          TEXT "COACH  •  This morning"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
        TEXT "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."  [Inter w400 17.0/26.0 ls0.0 L #6E6A62]
        [Frame 40] FRAME 320.0x35.7 V gap10.0 vy:HUG hz:FILL
          [small button] FRAME 136.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
            TEXT "Try this with Ben "  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [For You] FRAME 380.0x536.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FILL
      [Title Container] FRAME 126.9x34.0 H gap12.0 pad0/0/12.0/0 vy:HUG hz:HUG
        [For You Icon] INSTANCE 21.9x15.3 vy:FIXE hz:FIXE
          <Vector> VECTOR 21.9x15.3 #6E6A62
        TEXT "FOR YOU"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Articles Container] FRAME 340.0x469.0 V gap24.0 vy:HUG hz:FILL
        [Article] FRAME 340.0x229.0 V gap9.0 pad0/0/32.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Care · 2 min"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Article Content] FRAME 340.0x170.0 V gap14.0 vy:HUG hz:FILL
            TEXT "When bedtime becomes a negotiation"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Article] FRAME 340.0x216.0 V gap9.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "This week"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973837] FRAME 340.0x111.0 V gap13.0 vy:HUG hz:FILL
            TEXT "Tips on surviving the day"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "The big birthday parting is coming in 3 days"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Action Container] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#F5F3EF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [Container] FRAME 380.0x338.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FIXE
      [Section Title] FRAME 340.0x22.0 H gap12.0 vy:HUG hz:FILL
        [Section Icon] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1D7FA6
        TEXT "COMING UP"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Card Container] FRAME 340.0x283.0 V gap13.0 vy:HUG hz:FILL
        [Card] FRAME 340.0x113.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL stroke #8E8A83 1.0
          TEXT "Soccer camp starts on Friday"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
          TEXT "Get Ben ready! Camp begins on Aug 8, 7am."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Card] FRAME 340.0x157.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "Lily and Ben birthday outing"  [Fraunces w600 28.0/32.0 ls0.0 L #2B2925]
          TEXT "Going to the zoo with the kids. Aug 4, 2pm."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Card] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE
      [Tab 1] FRAME 66.7x52.0 fill=#000000 @0.00 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0 GLASS rNone None
        [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
          <Vector> VECTOR 15.8x17.8 #1B7498
        TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 3] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 12.1x14.9
            <Vector> VECTOR 6.0x5.9 #1B7498
            <Vector> VECTOR 1.9x1.9 #1B7498
            <Vector> VECTOR 1.2x1.2 #1B7498
            <Vector> VECTOR 5.3x6.7 #1B7498
            <Vector> VECTOR 6.5x6.5 #1B7498
        TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 5] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1B7498
        TEXT "PLANNER"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 2] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1B7498
        TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x21.0 #1B7498
        TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973867] FRAME 440.0x1714.0 fill=#2B2925 @0.40
    [profile] INSTANCE 400.0x530.1 fill=#F5F3EF V gap10.0 pad30.0/30.0/30.0/30.0 r24.0 vy:HUG hz:FIXE
      [Frame 204973866] FRAME 340.0x14.0 H gap10.0 vy:HUG hz:FILL
        [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 14.0x14.0 #4A4741
      TEXT "Hi Greg!"  [Fraunces w700 38.0/40.0 ls-0.38 L #1E1E1E]
      TEXT "No recent activity. Your history and saved articles can be found here."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 204973867] FRAME 340.0x40.7 H gap10.0 vy:HUG hz:FILL
        [small button] FRAME 165.0x40.7 fill=#FFFFFF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL stroke #1B7498 0.834434449672699
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #1B7498
          TEXT "Saved"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
        [small button] FRAME 165.0x40.7 fill=#FFFFFF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL stroke #1B7498 0.834434449672699
          [history] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x18.0 #1B7498
          TEXT "History"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
      [Frame 204973868] FRAME 340.0x178.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r18.0 vy:HUG hz:FILL
        TEXT "Account"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
        [Frame 204973844] FRAME 300.0x110.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Username: ⏎ MVP Email: ⏎ Password: Plan ⏎ Billing"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "MVPDad_GregH ⏎ MVP_GregH@mvp.com ⏎ ****** ⏎ Family ⏎ Annual"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973859] FRAME 340.0x111.4 V gap10.0 pad30.0/0/0/0 vy:HUG hz:FILL
        [small button] FRAME 340.0x35.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
          TEXT "Cancel"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
        [small button] FRAME 340.0x35.7 fill=#858585 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
          TEXT "Sign out"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]

====================================================================================================
FRAME account 02 — `1006:2517` — 440.0x2216.0 fill=#E9E4DC 
====================================================================================================
  [Container] FRAME 440.0x1582.0 V gap18.0 pad0/30.0/0/30.0 vy:FIXE hz:FIXE
    [Status Bar] FRAME 440.0x62.0 H gap154.0 pad21.0/0/19.0/0 vy:HUG hz:FIXE
      [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
        TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #000000]
      [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
        <Cellular Connection> VECTOR 19.2x12.2 #000000
        <Wifi> VECTOR 17.1x12.3 #000000
        [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
          [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #000000 1.0
          <Cap> VECTOR 1.3x4.1 #000000
          [Capacity] RECTANGLE 21.0x9.0 fill=#000000 r2.5
    [Container] FRAME 380.0x568.7 V gap12.0 vy:HUG hz:FILL
      [Container] FRAME 380.0x46.0 V gap10.0 pad0/0/10.0/0 vy:HUG hz:FILL
        [Icon Container] FRAME 37.0x36.0 fill=#1B7498 V gap4.8 pad11.5/11.5/11.5/11.5 r48.0 vy:FIXE hz:HUG
          TEXT "G"  [Fraunces w700 18.239999771118164/19.2 ls-0.18 C #FFFFFF]
      [Container] FRAME 380.0x245.0 fill=#F5F3EF V gap12.0 pad24.0/30.0/0/30.0 r32.0 vy:FIXE hz:FILL
        TEXT "YOUR KIDS"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        [Card Container] FRAME 348.0x153.0 H gap12.0 vy:HUG hz:HUG
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30+GRADIENT_LINEAR V gap7.4 pad17.7/17.7/17.7/17.7 vy:FILL hz:FIXE
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Benjamin"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30 V gap7.4 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FILL
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Lily"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
      [Frame 28] FRAME 380.0x253.7 fill=#F5F3EF V gap8.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL GLASS rNone None DROP_SHADOW r10.0 #000000
        [Frame 39] FRAME 320.0x22.0 H gap12.0 vy:HUG hz:FILL
          [coach] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
            [Layer_1] FRAME 13.7x17.8
              <Vector> VECTOR 6.8x7.0 #1B7498
              <Vector> VECTOR 2.2x2.3 #1B7498
              <Vector> VECTOR 1.4x1.4 #1B7498
              <Vector> VECTOR 6.0x8.0 #1B7498
              <Vector> VECTOR 7.3x7.8 #1B7498
          TEXT "COACH  •  This morning"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
        TEXT "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."  [Inter w400 17.0/26.0 ls0.0 L #6E6A62]
        [Frame 40] FRAME 320.0x35.7 V gap10.0 vy:HUG hz:FILL
          [small button] FRAME 136.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
            TEXT "Try this with Ben "  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [For You] FRAME 380.0x536.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FILL
      [Title Container] FRAME 126.9x34.0 H gap12.0 pad0/0/12.0/0 vy:HUG hz:HUG
        [For You Icon] INSTANCE 21.9x15.3 vy:FIXE hz:FIXE
          <Vector> VECTOR 21.9x15.3 #6E6A62
        TEXT "FOR YOU"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Articles Container] FRAME 340.0x469.0 V gap24.0 vy:HUG hz:FILL
        [Article] FRAME 340.0x229.0 V gap9.0 pad0/0/32.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Care · 2 min"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Article Content] FRAME 340.0x170.0 V gap14.0 vy:HUG hz:FILL
            TEXT "When bedtime becomes a negotiation"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Article] FRAME 340.0x216.0 V gap9.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "This week"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973837] FRAME 340.0x111.0 V gap13.0 vy:HUG hz:FILL
            TEXT "Tips on surviving the day"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "The big birthday parting is coming in 3 days"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Action Container] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#F5F3EF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [Container] FRAME 380.0x338.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FIXE
      [Section Title] FRAME 340.0x22.0 H gap12.0 vy:HUG hz:FILL
        [Section Icon] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1D7FA6
        TEXT "COMING UP"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Card Container] FRAME 340.0x283.0 V gap13.0 vy:HUG hz:FILL
        [Card] FRAME 340.0x113.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL stroke #8E8A83 1.0
          TEXT "Soccer camp starts on Friday"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
          TEXT "Get Ben ready! Camp begins on Aug 8, 7am."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Card] FRAME 340.0x157.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "Lily and Ben birthday outing"  [Fraunces w600 28.0/32.0 ls0.0 L #2B2925]
          TEXT "Going to the zoo with the kids. Aug 4, 2pm."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Card] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE
      [Tab 1] FRAME 66.7x52.0 fill=#000000 @0.00 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0 GLASS rNone None
        [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
          <Vector> VECTOR 15.8x17.8 #1B7498
        TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 3] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 12.1x14.9
            <Vector> VECTOR 6.0x5.9 #1B7498
            <Vector> VECTOR 1.9x1.9 #1B7498
            <Vector> VECTOR 1.2x1.2 #1B7498
            <Vector> VECTOR 5.3x6.7 #1B7498
            <Vector> VECTOR 6.5x6.5 #1B7498
        TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 5] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1B7498
        TEXT "PLANNER"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 2] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1B7498
        TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x21.0 #1B7498
        TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973867] FRAME 440.0x2216.0 fill=#2B2925 @0.40
    [profile] INSTANCE 400.0x1888.7 fill=#F5F3EF V gap10.0 pad30.0/30.0/30.0/30.0 r24.0 vy:HUG hz:FIXE
      [Frame 204973866] FRAME 340.0x14.0 H gap10.0 vy:HUG hz:FILL
        [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 14.0x14.0 #4A4741
      TEXT "Hi Greg!"  [Fraunces w700 38.0/40.0 ls-0.38 L #1E1E1E]
      TEXT "Browse your recent activity"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 204973867] FRAME 340.0x40.7 H gap10.0 vy:HUG hz:FILL
        [small button] FRAME 165.0x40.7 fill=#DAE0DF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL stroke #1B7498 0.834434449672699
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #1B7498
          TEXT "Saved"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
        [small button] FRAME 165.0x40.7 fill=#FFFFFF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL stroke #1B7498 0.834434449672699
          [history] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x18.0 #1B7498
          TEXT "History"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
      [Article] FRAME 340.0x238.0 fill=#1B7498 V gap9.0 pad20.0/20.0/20.0/20.0 r18.0 vy:FIXE hz:FILL
        [Frame 204973869] FRAME 300.0x24.0 H gap10.0 vy:HUG hz:FILL
          [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.6x20.6 #F5F3EF
          TEXT "Care · 2 min"  [Inter w700 13.0/18.0 ls0.0 L #F5F3EF]
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #F5F3EF
        [Frame 204973838] FRAME 300.0x170.0 V gap14.0 vy:HUG hz:FILL
          TEXT "When bedtime becomes a negotiation"  [Fraunces w700 38.0/40.0 ls-0.38 L #F5F3EF]
          TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #F5F3EF]
      [Article] FRAME 340.0x238.0 fill=#1B7498 V gap9.0 pad20.0/20.0/20.0/20.0 r18.0 vy:FIXE hz:FILL
        [Frame 204973869] FRAME 300.0x24.0 H gap10.0 vy:HUG hz:FILL
          [Vector] INSTANCE 21.9x15.3 vy:FIXE hz:FIXE
            <Vector> VECTOR 21.9x15.3 #F5F3EF
          TEXT "Adventure · 5 min"  [Inter w700 13.0/18.0 ls0.0 L #F5F3EF]
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #F5F3EF
        [Frame 204973838] FRAME 300.0x170.0 V gap14.0 vy:HUG hz:FILL
          TEXT "How to plan the perfect nature outing"  [Fraunces w700 38.0/40.0 ls-0.38 L #F5F3EF]
          TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #F5F3EF]
      [Article] FRAME 340.0x209.0 fill=#1B7498 V gap9.0 pad20.0/20.0/20.0/20.0 r18.0 vy:FIXE hz:FILL
        [Frame 204973869] FRAME 300.0x24.0 H gap10.0 vy:HUG hz:FILL
          [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.6x20.6 #F5F3EF
          TEXT "Swim camp · Aug. 2, 2026"  [Inter w700 13.0/18.0 ls0.0 L #F5F3EF]
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #F5F3EF
        [Frame 204973838] FRAME 300.0x130.0 V gap14.0 vy:HUG hz:FILL
          TEXT "Summer Swim camp 2026"  [Fraunces w700 38.0/40.0 ls-0.38 L #F5F3EF]
          TEXT "Camp is only one month away - are the kids ready?"  [Inter w400 13.0/18.0 ls0.0 L #F5F3EF]
      [Article] FRAME 340.0x201.0 fill=#1B7498 V gap9.0 pad20.0/20.0/20.0/20.0 r18.0 vy:FIXE hz:FILL
        [Frame 204973869] FRAME 300.0x24.0 H gap10.0 vy:HUG hz:FILL
          [camp] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 20.1x14.2 #F5F3EF
          TEXT "Summer camps · 5 min"  [Inter w700 13.0/18.0 ls0.0 L #F5F3EF]
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #F5F3EF
        [Frame 204973838] FRAME 300.0x112.0 V gap14.0 vy:HUG hz:FILL
          TEXT "The best camps near you"  [Fraunces w700 38.0/40.0 ls-0.38 L #F5F3EF]
          TEXT "A list of the the best camps for your family"  [Inter w400 13.0/18.0 ls0.0 L #F5F3EF]
      [Frame 204973885] FRAME 340.0x420.7 V gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
        [Frame 204973886] FRAME 340.0x18.0 H gap10.0 vy:HUG hz:FILL
          TEXT "Family interests"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
          TEXT "See all"  [Inter w400 13.0/18.0 ls0.0 R #2B2925]
        [Frame 204973883] FRAME 340.0x372.7 G vy:FIXE hz:FIXE
          [Frame 204973873] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [brush] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 35.2x33.5 #F5F3EF
              TEXT "Arts & crafts"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973874] FRAME 108.9x119.8 fill=#FFFFFF V gap8.4 pad6.7/14.2/8.4/14.2 r10.049260139465332 vy:FILL hz:FILL stroke #1B7498 0.8894035816192627
            [Frame 204973882] FRAME 78.6x20.1 H gap8.4 vy:HUG hz:FILL
              [addcircle] INSTANCE 20.1x20.1 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.7x16.7 #E8EAED
            [Frame 5] FRAME 78.6x69.5 V gap3.3 vy:FIXE hz:FILL
              [library] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 35.2x19.5 #1B7498
                <Vector> VECTOR 35.2x12.6 #1B7498
              TEXT "Museums"  [Inter w400 14.236452102661133/21.8 ls0.0 C #1B7498]
          [Frame 204973875] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [hike] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 21.2x30.0 #F5F3EF
              TEXT "Hiking"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973876] FRAME 108.9x119.8 fill=#FFFFFF V gap8.4 pad6.7/14.2/8.4/14.2 r10.049260139465332 vy:FILL hz:FILL stroke #1B7498 0.8894035816192627
            [Frame 204973882] FRAME 78.6x20.1 H gap8.4 vy:HUG hz:FILL
              [addcircle] INSTANCE 20.1x20.1 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.7x16.7 #E8EAED
            [Frame 5] FRAME 78.6x66.2 V gap3.3 vy:FIXE hz:FILL
              [garden] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.3x27.9 #1B7498
              TEXT "Gardens"  [Inter w400 14.236452102661133/21.8 ls0.0 C #1B7498]
          [Frame 204973877] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [nature] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.4x27.9 #F5F3EF
              TEXT "Nature"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973878] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [park] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 26.4x27.9 #F5F3EF
              TEXT "Parks"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973879] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [robot] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 32.2x26.5 #F5F3EF
              TEXT "Science"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973880] FRAME 108.9x119.8 fill=#FFFFFF V gap8.4 pad6.7/14.2/8.4/14.2 r10.049260139465332 vy:FILL hz:FILL stroke #1B7498 0.8374384045600891
            [Frame 204973882] FRAME 78.7x20.1 H gap8.4 vy:HUG hz:FILL
              [addcircle] INSTANCE 20.1x20.1 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.7x16.7 #E8EAED
            [Frame 5] FRAME 78.7x63.6 V gap3.3 vy:FIXE hz:FILL
              [swimming] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.3x25.1 #1B7498
              TEXT "Sports"  [Inter w400 14.236452102661133/21.8 ls0.0 C #1B7498]
          [Frame 204973881] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [rocket] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.4x28.0 #F5F3EF
              TEXT "Parks"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
      [Frame 204973884] FRAME 340.0x198.0 V gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
        [Frame 204973868] FRAME 340.0x178.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r18.0 vy:HUG hz:FILL
          TEXT "Account"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
          [Frame 204973844] FRAME 300.0x110.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Username: ⏎ MVP Email: ⏎ Password: Plan ⏎ Billing"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "MVPDad_GregH ⏎ MVP_GregH@mvp.com ⏎ ****** ⏎ Family ⏎ Annual"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973859] FRAME 340.0x111.4 V gap10.0 pad30.0/0/0/0 vy:HUG hz:FILL
        [small button] FRAME 340.0x35.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
          TEXT "Cancel"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
        [small button] FRAME 340.0x35.7 fill=#858585 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
          TEXT "Sign out"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]

====================================================================================================
FRAME account 03 — `1008:5111` — 440.0x2216.0 fill=#E9E4DC 
====================================================================================================
  [Container] FRAME 440.0x1582.0 V gap18.0 pad0/30.0/0/30.0 vy:FIXE hz:FIXE
    [Status Bar] FRAME 440.0x62.0 H gap154.0 pad21.0/0/19.0/0 vy:HUG hz:FIXE
      [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
        TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #000000]
      [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
        <Cellular Connection> VECTOR 19.2x12.2 #000000
        <Wifi> VECTOR 17.1x12.3 #000000
        [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
          [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #000000 1.0
          <Cap> VECTOR 1.3x4.1 #000000
          [Capacity] RECTANGLE 21.0x9.0 fill=#000000 r2.5
    [Container] FRAME 380.0x568.7 V gap12.0 vy:HUG hz:FILL
      [Container] FRAME 380.0x46.0 V gap10.0 pad0/0/10.0/0 vy:HUG hz:FILL
        [Icon Container] FRAME 37.0x36.0 fill=#1B7498 V gap4.8 pad11.5/11.5/11.5/11.5 r48.0 vy:FIXE hz:HUG
          TEXT "G"  [Fraunces w700 18.239999771118164/19.2 ls-0.18 C #FFFFFF]
      [Container] FRAME 380.0x245.0 fill=#F5F3EF V gap12.0 pad24.0/30.0/0/30.0 r32.0 vy:FIXE hz:FILL
        TEXT "YOUR KIDS"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        [Card Container] FRAME 348.0x153.0 H gap12.0 vy:HUG hz:HUG
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30+GRADIENT_LINEAR V gap7.4 pad17.7/17.7/17.7/17.7 vy:FILL hz:FIXE
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Benjamin"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30 V gap7.4 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FILL
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Lily"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
      [Frame 28] FRAME 380.0x253.7 fill=#F5F3EF V gap8.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL GLASS rNone None DROP_SHADOW r10.0 #000000
        [Frame 39] FRAME 320.0x22.0 H gap12.0 vy:HUG hz:FILL
          [coach] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
            [Layer_1] FRAME 13.7x17.8
              <Vector> VECTOR 6.8x7.0 #1B7498
              <Vector> VECTOR 2.2x2.3 #1B7498
              <Vector> VECTOR 1.4x1.4 #1B7498
              <Vector> VECTOR 6.0x8.0 #1B7498
              <Vector> VECTOR 7.3x7.8 #1B7498
          TEXT "COACH  •  This morning"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
        TEXT "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."  [Inter w400 17.0/26.0 ls0.0 L #6E6A62]
        [Frame 40] FRAME 320.0x35.7 V gap10.0 vy:HUG hz:FILL
          [small button] FRAME 136.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
            TEXT "Try this with Ben "  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [For You] FRAME 380.0x536.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FILL
      [Title Container] FRAME 126.9x34.0 H gap12.0 pad0/0/12.0/0 vy:HUG hz:HUG
        [For You Icon] INSTANCE 21.9x15.3 vy:FIXE hz:FIXE
          <Vector> VECTOR 21.9x15.3 #6E6A62
        TEXT "FOR YOU"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Articles Container] FRAME 340.0x469.0 V gap24.0 vy:HUG hz:FILL
        [Article] FRAME 340.0x229.0 V gap9.0 pad0/0/32.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Care · 2 min"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Article Content] FRAME 340.0x170.0 V gap14.0 vy:HUG hz:FILL
            TEXT "When bedtime becomes a negotiation"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Article] FRAME 340.0x216.0 V gap9.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "This week"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973837] FRAME 340.0x111.0 V gap13.0 vy:HUG hz:FILL
            TEXT "Tips on surviving the day"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "The big birthday parting is coming in 3 days"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Action Container] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#F5F3EF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [Container] FRAME 380.0x338.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FIXE
      [Section Title] FRAME 340.0x22.0 H gap12.0 vy:HUG hz:FILL
        [Section Icon] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1D7FA6
        TEXT "COMING UP"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Card Container] FRAME 340.0x283.0 V gap13.0 vy:HUG hz:FILL
        [Card] FRAME 340.0x113.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL stroke #8E8A83 1.0
          TEXT "Soccer camp starts on Friday"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
          TEXT "Get Ben ready! Camp begins on Aug 8, 7am."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Card] FRAME 340.0x157.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "Lily and Ben birthday outing"  [Fraunces w600 28.0/32.0 ls0.0 L #2B2925]
          TEXT "Going to the zoo with the kids. Aug 4, 2pm."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Card] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE
      [Tab 1] FRAME 66.7x52.0 fill=#000000 @0.00 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0 GLASS rNone None
        [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
          <Vector> VECTOR 15.8x17.8 #1B7498
        TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 3] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 12.1x14.9
            <Vector> VECTOR 6.0x5.9 #1B7498
            <Vector> VECTOR 1.9x1.9 #1B7498
            <Vector> VECTOR 1.2x1.2 #1B7498
            <Vector> VECTOR 5.3x6.7 #1B7498
            <Vector> VECTOR 6.5x6.5 #1B7498
        TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 5] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1B7498
        TEXT "PLANNER"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 2] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1B7498
        TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x21.0 #1B7498
        TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973867] FRAME 440.0x2216.0 fill=#2B2925 @0.40
    [profile] INSTANCE 400.0x1773.7 fill=#F5F3EF V gap10.0 pad30.0/30.0/30.0/30.0 r24.0 vy:HUG hz:FIXE
      [Frame 204973866] FRAME 340.0x14.0 H gap10.0 vy:HUG hz:FILL
        [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 14.0x14.0 #4A4741
      TEXT "Hi Greg!"  [Fraunces w700 38.0/40.0 ls-0.38 L #1E1E1E]
      TEXT "Browse your recent activity"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 204973867] FRAME 340.0x40.7 H gap10.0 vy:HUG hz:FILL
        [small button] FRAME 165.0x40.7 fill=#FFFFFF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL stroke #1B7498 0.834434449672699
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #1B7498
          TEXT "Saved"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
        [small button] FRAME 165.0x40.7 fill=#DAE0DF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL stroke #1B7498 0.834434449672699
          [history] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x18.0 #1B7498
          TEXT "History"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
      [Frame 204973885] FRAME 340.0x1231.7 V gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
        [Frame 204973889] FRAME 340.0x18.0 H gap10.0 vy:HUG hz:FILL
          TEXT "In your Circle"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
          TEXT "Go to Circle"  [Inter w400 13.0/18.0 ls0.0 R #2B2925]
        [Frame 204973797] FRAME 340.0x145.0 fill=#FFFFFF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
          [Frame 204973868] FRAME 322.0x36.0 H gap10.0 vy:HUG hz:FILL
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973867] FRAME 322.0x109.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
            [Frame 204973798] FRAME 304.0x51.0 V gap9.0 vy:HUG hz:FILL
              TEXT "Gifts for the party this weekend"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
              TEXT "M started this — 4 replies"  [Inter w400 15.0/22.0 ls0.0 L #575757]
            [Frame 204973866] FRAME 104.0x28.0 H gap10.0 vy:HUG hz:HUG
              [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "G"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
              [directions_run_FILL0_wght400_GRAD0_opsz48 2] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "S"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
              [directions_run_FILL0_wght400_GRAD0_opsz48 3] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "M"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973887] FRAME 340.0x145.0 fill=#FFFFFF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
          [Frame 204973868] FRAME 322.0x36.0 H gap10.0 vy:HUG hz:FILL
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973867] FRAME 322.0x109.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
            [Frame 204973798] FRAME 304.0x51.0 V gap9.0 vy:HUG hz:FILL
              TEXT "Gifts for the party this weekend"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
              TEXT "M started this — 4 replies"  [Inter w400 15.0/22.0 ls0.0 L #575757]
            [Frame 204973866] FRAME 104.0x28.0 H gap10.0 vy:HUG hz:HUG
              [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "G"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
              [directions_run_FILL0_wght400_GRAD0_opsz48 2] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "S"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
              [directions_run_FILL0_wght400_GRAD0_opsz48 3] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "M"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973888] FRAME 340.0x145.0 fill=#FFFFFF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
          [Frame 204973868] FRAME 322.0x36.0 H gap10.0 vy:HUG hz:FILL
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973867] FRAME 322.0x109.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
            [Frame 204973798] FRAME 304.0x51.0 V gap9.0 vy:HUG hz:FILL
              TEXT "Gifts for the party this weekend"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
              TEXT "M started this — 4 replies"  [Inter w400 15.0/22.0 ls0.0 L #575757]
            [Frame 204973866] FRAME 104.0x28.0 H gap10.0 vy:HUG hz:HUG
              [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "G"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
              [directions_run_FILL0_wght400_GRAD0_opsz48 2] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "S"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
              [directions_run_FILL0_wght400_GRAD0_opsz48 3] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
                TEXT "M"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973890] FRAME 340.0x38.0 H gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
          TEXT "Coach advice"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
          TEXT "Chat with the coach"  [Inter w400 13.0/18.0 ls0.0 R #2B2925]
        [Frame 204973796] FRAME 337.0x123.0 fill=#FFFFFF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
          [Frame 204973868] FRAME 319.0x36.0 H gap10.0 vy:HUG hz:FILL
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973867] FRAME 319.0x87.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
            [Frame 204973880] FRAME 301.0x67.0 H gap10.0 vy:HUG hz:FILL
              [Frame 204973798] FRAME 253.7x67.0 V gap9.0 vy:HUG hz:FILL
                TEXT "Dinner plans for the kids"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
                TEXT "sheet-pan tacos worked for both kids — saved for next week"  [Inter w400 15.0/22.0 ls0.0 L #575757]
              [Frame] FRAME 37.3x32.0 H gap13.3 pad4.0/6.7/4.0/6.7 vy:HUG hz:HUG
                [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 14.0x18.0 #B4CDD4
        [Frame 204973891] FRAME 337.0x107.0 fill=#FFFFFF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
          [Frame 204973868] FRAME 319.0x36.0 H gap10.0 vy:HUG hz:FILL
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973867] FRAME 319.0x71.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
            [Frame 204973880] FRAME 301.0x51.0 H gap10.0 vy:HUG hz:FILL
              [Frame 204973798] FRAME 301.0x51.0 V gap9.0 vy:HUG hz:FILL
                TEXT "Kelsy's birthday party"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
                TEXT "Gift ideas for 5-year old girls"  [Inter w400 15.0/22.0 ls0.0 L #575757]
        [Frame 204973886] FRAME 340.0x38.0 H gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
          TEXT "Family interests"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
          TEXT "See all"  [Inter w400 13.0/18.0 ls0.0 R #2B2925]
        [Frame 204973883] FRAME 340.0x372.7 G vy:FIXE hz:FIXE
          [Frame 204973873] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [brush] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 35.2x33.5 #F5F3EF
              TEXT "Arts & crafts"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973874] FRAME 108.9x119.8 fill=#FFFFFF V gap8.4 pad6.7/14.2/8.4/14.2 r10.049260139465332 vy:FILL hz:FILL stroke #1B7498 0.8894035816192627
            [Frame 204973882] FRAME 78.6x20.1 H gap8.4 vy:HUG hz:FILL
              [addcircle] INSTANCE 20.1x20.1 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.7x16.7 #E8EAED
            [Frame 5] FRAME 78.6x69.5 V gap3.3 vy:FIXE hz:FILL
              [library] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 35.2x19.5 #1B7498
                <Vector> VECTOR 35.2x12.6 #1B7498
              TEXT "Museums"  [Inter w400 14.236452102661133/21.8 ls0.0 C #1B7498]
          [Frame 204973875] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [hike] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 21.2x30.0 #F5F3EF
              TEXT "Hiking"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973876] FRAME 108.9x119.8 fill=#FFFFFF V gap8.4 pad6.7/14.2/8.4/14.2 r10.049260139465332 vy:FILL hz:FILL stroke #1B7498 0.8894035816192627
            [Frame 204973882] FRAME 78.6x20.1 H gap8.4 vy:HUG hz:FILL
              [addcircle] INSTANCE 20.1x20.1 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.7x16.7 #E8EAED
            [Frame 5] FRAME 78.6x66.2 V gap3.3 vy:FIXE hz:FILL
              [garden] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.3x27.9 #1B7498
              TEXT "Gardens"  [Inter w400 14.236452102661133/21.8 ls0.0 C #1B7498]
          [Frame 204973877] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [nature] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.4x27.9 #F5F3EF
              TEXT "Nature"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973878] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [park] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 26.4x27.9 #F5F3EF
              TEXT "Parks"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973879] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [robot] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 32.2x26.5 #F5F3EF
              TEXT "Science"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
          [Frame 204973880] FRAME 108.9x119.8 fill=#FFFFFF V gap8.4 pad6.7/14.2/8.4/14.2 r10.049260139465332 vy:FILL hz:FILL stroke #1B7498 0.8374384045600891
            [Frame 204973882] FRAME 78.7x20.1 H gap8.4 vy:HUG hz:FILL
              [addcircle] INSTANCE 20.1x20.1 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.7x16.7 #E8EAED
            [Frame 5] FRAME 78.7x63.6 V gap3.3 vy:FIXE hz:FILL
              [swimming] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.3x25.1 #1B7498
              TEXT "Sports"  [Inter w400 14.236452102661133/21.8 ls0.0 C #1B7498]
          [Frame 204973881] FRAME 108.9x119.8 fill=#1B7498 V gap8.4 pad26.8/14.2/20.1/14.2 r10.049260139465332 vy:FILL hz:FILL
            [Frame 5] FRAME 80.4x72.9 V gap3.3 vy:FILL hz:FILL
              [rocket] INSTANCE 35.2x33.5 vy:FIXE hz:FIXE
                <Vector> VECTOR 29.4x28.0 #F5F3EF
              TEXT "Parks"  [Inter w400 14.236452102661133/21.8 ls0.0 C #F5F3EF]
      [Frame 204973884] FRAME 340.0x198.0 V gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
        [Frame 204973868] FRAME 340.0x178.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r18.0 vy:HUG hz:FILL
          TEXT "Account"  [Inter w700 13.0/18.0 ls0.0 L #2B2925]
          [Frame 204973844] FRAME 300.0x110.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Username: ⏎ MVP Email: ⏎ Password: Plan ⏎ Billing"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "MVPDad_GregH ⏎ MVP_GregH@mvp.com ⏎ ****** ⏎ Family ⏎ Annual"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973859] FRAME 340.0x111.4 V gap10.0 pad30.0/0/0/0 vy:HUG hz:FILL
        [small button] FRAME 340.0x35.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
          TEXT "Cancel"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
        [small button] FRAME 340.0x35.7 fill=#858585 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
          TEXT "Sign out"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]

====================================================================================================
FRAME parent 002 — `855:4033` — 440.0x1407.0 fill=#FFFFFF V pad60.0/0/60.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Primary parent"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 440.0x401.0 fill=IMAGE+GRADIENT_LINEAR V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 62.0x26.0 fill=#151412 H gap6.0 pad6.0/6.0/6.0/6.0 r18.599998474121094 vy:HUG hz:FIXE DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Edit"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x940.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [small button] FRAME 126.4x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
      [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.7x13.7 #E3E3E3
      TEXT "Edit parent"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    TEXT "Carol"  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x232.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x232.0 fill=#FFFFFF V gap30.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x4.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
        TEXT "Mom"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973857] FRAME 320.0x84.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "MVP name"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "MVP Carol"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973856] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Family roll"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Primary parent"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Email"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "mvp-carol"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
    [Frame 53] FRAME 380.0x302.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "More about Carol"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 60] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 61] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 62] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 63] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Goals for parent"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]
====================================================================================================
FRAME choose a plan — `754:4897` — 402.0x1218.0 fill=#FFFFFF V vy:FIXE hz:FIXE
====================================================================================================
  [section-hero] FRAME 402.0x1218.0 fill=#F5F3EF V gap28.0 pad60/30/0/30 vy:FIXE hz:FIXE
    TEXT "MVP"  [Fraunces w700 81.23077392578125/100.2 ls-4.06 R #1E1E1E]
    TEXT "Pick a plan and start your free trial today!"  [Inter w700 32.0/38.7 ls-0.64 C #000000]
    TEXT "monthly  |  annual"  [Inter w400 22.0/26.6 ls-0.44 C #000000]
    [plans] FRAME 342.0x832.1 V gap30.0 vy:HUG hz:FILL
      [plan card 1] FRAME 342.0x378.1 fill=#FFFFFF V gap24.0 pad30/30/30/30 r24.0 vy:HUG hz:FILL DROP_SHADOW r30.0 #000000
        [plan name] FRAME 49.0x31.0 H gap10.0 pad0/0/10/0 vy:HUG hz:HUG stroke #000000 1.0
          TEXT "Basic"  [Roboto w700 14.0/21.0 ls2.10 C #6B6B6B]
        TEXT "$59 per-year"  [Roboto w700 24.0/26.4 ls0.00 C #000000]
        [USPS] FRAME 282.0x116.0 V gap12.0 pad0/30/0/30 vy:HUG hz:FILL
          [Frame 237] FRAME 222.0x20.0 H gap16.0 vy:HUG hz:FILL
            [Component 7] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "Annual membership"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
          [Frame 240] FRAME 222.0x20.0 H gap16.0 vy:HUG hz:FILL
            [Component 7] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "7-day free trial"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
          [Frame 236] FRAME 222.0x20.0 H gap16.0 vy:HUG hz:FILL
            [Component 8] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "AI coach"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
          [Frame 235] FRAME 222.0x20.0 H gap16.0 vy:HUG hz:FILL
            [Component 9] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "Team feedback"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
        [buy button] FRAME 282.0x73.1 V gap10.0 pad20/0/0/0 vy:HUG hz:FILL
          [Frame 181] FRAME 282.0x53.1 fill=#1B7498 H gap7.3 pad14.5/14.5/14.5/14.5 r58.106834411621094 vy:HUG hz:FILL
            TEXT "Buy"  [Roboto w600 15.979378700256348/24.0 ls0.00 C #FFFFFF]
      [plan card 2] FRAME 342.0x378.1 fill=#FFFFFF V gap24.0 pad30/30/30/30 r24.0 vy:HUG hz:FILL DROP_SHADOW r30.0 #000000
        [plan name] FRAME 58.0x31.0 H gap10.0 pad0/0/10/0 vy:HUG hz:HUG stroke #000000 1.0
          TEXT "Family"  [Roboto w700 14.0/21.0 ls2.10 C #151412]
        TEXT "$139 per-year"  [Roboto w700 24.0/26.4 ls0.00 C #000000]
        [usps] FRAME 282.0x116.0 V gap12.0 pad0/30/0/30 vy:HUG hz:FILL
          [Frame 237] FRAME 222.0x20.0 H gap13.0 vy:HUG hz:FILL
            [Component 7] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "Annual membership"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
          [Frame 241] FRAME 222.0x20.0 H gap13.0 vy:HUG hz:FILL
            [Component 7] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "7-day free trial"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
          [Frame 235] FRAME 222.0x20.0 H gap13.0 vy:HUG hz:FILL
            [Component 9] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "AI Coach "  [Roboto w600 12.0/18.0 ls0.00 L #000000]
          [Frame 234] FRAME 222.0x20.0 H gap13.0 vy:HUG hz:FILL
            [Component 10] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 20.0x20.0 #4C4B47
              <Vector> VECTOR 10.1x7.4 #FFFFFF
            TEXT "Team feedback"  [Roboto w600 12.0/18.0 ls0.00 L #000000]
        [buy button] FRAME 282.0x73.1 V gap10.0 pad20/0/0/0 vy:HUG hz:FILL
          [Frame 181] FRAME 282.0x53.1 fill=#1B7498 H gap7.3 pad14.5/14.5/14.5/14.5 r58.106834411621094 vy:HUG hz:FILL
            TEXT "Buy"  [Roboto w600 15.979378700256348/24.0 ls0.00 C #FFFFFF]
      TEXT "Purchases will open Stripe in a new tab. "  [Arial w700 14.0/16.1 ls0.00 C #666666]
====================================================================================================
FRAME create your account — `754:4943` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  [mvptrophy 1] RECTANGLE 340.0x425.0 fill=IMAGE
  [Frame 204973833] FRAME 440.0x956.0 H gap10.0 pad32/10/0/10 vy:FIXE hz:FIXE
    [sign up] FRAME 420.0x553.0 fill=#FFFFFF V gap16.0 pad60/30/60/30 r16.0,16.0,0.0,0.0 vy:FIXE hz:FILL DROP_SHADOW r30.0 #000000
      [Frame 204973648] FRAME 360.0x40.0 V gap3.0 vy:HUG hz:FILL
        [Frame 204973431] FRAME 360.0x40.0 V vy:HUG hz:FILL
          TEXT "Create account"  [Inter w400 27.231950759887695/33.0 ls0.00 C #000000]
      [Frame 204973868] FRAME 360.0x116.0 V gap16.0 vy:HUG hz:FILL
        [Frame 204973428] FRAME 360.0x50.0 fill=#2B2925 H gap6.0 pad16/25.5/16/25.5 r100.0 vy:HUG hz:FILL stroke #D0D0D0 0.8509984612464905
          [google] FRAME 18.0x18.0 vy:FIXE hz:FIXE
            <vector> VECTOR 7.7x7.4 #4285F4
            <vector> VECTOR 12.5x6.3 #34A853
            <vector> VECTOR 3.5x7.1 #FBBC05
            <vector> VECTOR 12.6x6.3 #EB4335
          TEXT "Continue with Google"  [Roboto w700 14.0/16.4 ls0.00 C #FFFFFF]
        [Frame 204973651] FRAME 360.0x50.0 fill=#2B2925 H gap6.0 pad16/25.5/16/25.5 r100.0 vy:HUG hz:FILL stroke #D0D0D0 0.8509984612464905
          [apple-logo-svgrepo-com 1] FRAME 18.0x18.0 vy:FIXE hz:FIXE
            [Group] GROUP 14.7x18.0
              [Group] GROUP 14.7x18.0
                <Vector> VECTOR 3.6x4.2 #FFFFFF
                <Vector> VECTOR 14.7x13.7 #FFFFFF
          TEXT "Sign up with Apple"  [Roboto w700 14.0/16.4 ls0.00 C #FFFFFF]
      [Frame 204973423] FRAME 360.0x50.2 H gap8.5 vy:FIXE hz:FILL
        [Frame 204973426] FRAME 360.0x16.0 H gap8.5 vy:HUG hz:FILL
          [Rectangle 2] RECTANGLE 91.5x0.9 fill=#D9D9D9 vy:FIXE hz:FILL
          [Frame 204973425] FRAME 160.0x16.0 V gap8.5 pad0/17/0/17 vy:HUG hz:HUG
            TEXT "Or sign up with email"  [Roboto w400 13.48923110961914/15.8 ls0.00 C #000000]
          [Rectangle 1] RECTANGLE 91.5x0.9 fill=#D9D9D9 vy:FIXE hz:FILL
      [Frame 204973422] FRAME 360.0x51.1 H gap8.5 pad12.8/25.5/12.8/25.5 r3.403993844985962 vy:FIXE hz:FILL stroke #D0D0D0 0.8509984612464905
        TEXT "Email address*"  [Barlow w400 13.48923110961914/16.2 ls0.00 L #000000]
      [Frame 204973650] FRAME 360.0x84.8 V gap12.0 vy:HUG hz:FILL
        [Frame 204973424] FRAME 360.0x46.8 V gap8.5 vy:FIXE hz:FILL
          [Frame 204972989] FRAME 360.0x47.7 fill=#FFFFFF H gap6.8 pad8.7/4.9/8.7/4.9 r85.09984588623047 vy:FIXE hz:FILL stroke #8E8A83 0.5423396825790405
            TEXT "Sign up with email"  [Roboto w700 13.615975379943848/16.0 ls0.00 C #000000]
        [Frame 204973422] FRAME 360.0x26.0 H gap8.5 pad10/10/0/10 vy:HUG hz:FILL
          TEXT "Already have an account? Sign in"  [Roboto w400 13.48923110961914/15.8 ls0.00 C #000000]
====================================================================================================
FRAME Onboarding - 3 — `890:1479` — 440.0x956.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 204973840] FRAME 380.0x660.0 V gap30.0 vy:HUG hz:FIXE
    [Frame 14] FRAME 380.0x179.0 V gap15.0 vy:HUG hz:FILL
      TEXT "Let’s get acquainted"  [Fraunces w700 56.0/60.0 ls-1.12 C #1E1E1E]
      TEXT "A few quick questions so we can make MVP feel like it was made for your family."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 24] FRAME 380.0x451.0 V gap23.0 vy:HUG hz:FILL
      [Frame 1] FRAME 380.0x91.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "What should we call you?"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [Frame 2] FRAME 320.0x48.0 fill=#FCFBF8 H gap10.0 pad12.0/0/12.0/0 r32.0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Gregory"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
      [Frame 17] FRAME 380.0x97.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "Your household"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [large input] INSTANCE 320.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FILL stroke #C9C5BE 1.0
          TEXT "Married"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [arrow] INSTANCE 24.0x12.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x9.0 
      [Frame 24] FRAME 380.0x97.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "Education style"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [large input] INSTANCE 320.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FILL stroke #C9C5BE 1.0
          TEXT "Home school"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
          [arrow] INSTANCE 24.0x12.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.0x9.0 
      [Frame 25] FRAME 380.0x97.0 V gap3.0 pad0/30.0/0/30.0 vy:HUG hz:FILL
        TEXT "Location"  [Inter w800 16.0/22.0 ls0.0 C #1E1E1E]
        [large input] INSTANCE 320.0x56.0 fill=#FFFFFF H gap10.0 pad12.0/32.0/12.0/32.0 r32.0 vy:FIXE hz:FILL stroke #C9C5BE 1.0
          TEXT "98332"  [Inter w300 20.0/24.0 ls0.0 C #6E6A62]
  [Frame 16] FRAME 380.0x74.0 V gap10.0 vy:HUG hz:FIXE
    [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
      TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
    TEXT "Next: Your Children"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]

====================================================================================================
FRAME Onboarding - need help with dynamics — `754:4417` — 440.0x956.0 fill=#F3F0EB stroke #000000 1.0
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 11] FRAME 376.0x55.0 V gap6.0 vy:HUG hz:FIXE
    [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
      [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
        [back arrow] INSTANCE 16.0x13.0
          <Vector> VECTOR 6.7x13.0 
          <Vector> VECTOR 16.0x0.0 
      [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
        [Frame 3] FRAME 337.0x26.0 r100.0 vy:FILL hz:FILL
          [Frame 4] FRAME 360.0x26.0 fill=#1B7498 r100.0
    TEXT "Almost there"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 16] FRAME 376.0x74.0 V gap10.0 vy:HUG hz:FIXE
    [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
      TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
    TEXT "Next: Meet the coach"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 79] FRAME 415.0x605.0 V vy:FIXE hz:FIXE
    [Frame 1] FRAME 415.0x173.0 V gap10.0 vy:FIXE hz:FILL
      TEXT "What’s on your mind?"  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
      TEXT "Pick what feels true right now. No right answers — just your reality."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 20] FRAME 305.0x421.0 V gap10.0 vy:FIXE hz:FIXE
      [tag item] INSTANCE 305.0x52.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:FILL stroke #E9E4DC 1.0
        [Frame 5] FRAME 168.0x28.0 H gap4.0 vy:HUG hz:HUG
          [morning] INSTANCE 28.0x28.0 vy:FIXE hz:FIXE
            [Group 2] GROUP 23.3x17.8
              <Vector> VECTOR 23.3x17.8 #1B7498
          TEXT "Morning routines"  [Inter w400 17.0/26.0 ls0.0 C #1B7498]
      [tag item] INSTANCE 305.0x52.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:FILL stroke #E9E4DC 1.0
        [Frame 5] FRAME 159.0x28.0 H gap4.0 vy:HUG hz:HUG
          [night] INSTANCE 28.0x28.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.3x17.1 #1B7498
          TEXT "Bedtime battles"  [Inter w400 17.0/26.0 ls0.0 C #1B7498]
      [tag item] INSTANCE 305.0x52.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:FILL stroke #E9E4DC 1.0
        [Frame 5] FRAME 137.0x28.0 H gap4.0 vy:HUG hz:HUG
          [emotions] INSTANCE 28.0x28.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.5x12.0 #1B7498
          TEXT "Big emotions"  [Inter w400 17.0/26.0 ls0.0 C #1B7498]
      [tag item] INSTANCE 305.0x52.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:FILL stroke #E9E4DC 1.0
        [Frame 5] FRAME 128.0x28.0 H gap4.0 vy:HUG hz:HUG
          [screentime] INSTANCE 28.0x28.0 vy:FIXE hz:FIXE
            [Group 3] GROUP 16.4x15.0
              <Vector (Stroke)> VECTOR 13.5x9.9 #1B7498
              <Vector (Stroke)> VECTOR 1.6x3.7 #1B7498
              <Vector (Stroke)> VECTOR 5.2x1.6 #1B7498
              <Vector (Stroke)> VECTOR 6.1x9.0 #1B7498
          TEXT "Screen time"  [Inter w400 17.0/26.0 ls0.0 C #1B7498]
      [tag item] INSTANCE 305.0x52.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:FILL stroke #E9E4DC 1.0
        [Frame 5] FRAME 167.0x28.0 H gap4.0 vy:HUG hz:HUG
          [School] INSTANCE 28.0x28.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 25.7x21.0 #1B7498
          TEXT "School struggles"  [Inter w400 17.0/26.0 ls0.0 C #1B7498]
      [tag item] INSTANCE 305.0x52.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:FILL stroke #E9E4DC 1.0
        [Frame 5] FRAME 172.0x28.0 H gap4.0 vy:HUG hz:HUG
          [alone] INSTANCE 28.0x28.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 17.9x17.9 #1B7498
          TEXT "Feeling alone in it"  [Inter w400 17.0/26.0 ls0.0 C #1B7498]

====================================================================================================
FRAME Onboarding - need help with acitivities — `1004:1746` — 440.0x956.0 fill=#F3F0EB stroke #000000 1.0
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 11] FRAME 376.0x55.0 V gap6.0 vy:HUG hz:FIXE
    [progress] INSTANCE 376.0x31.0 H gap4.0 vy:HUG hz:FILL
      [Frame 1] FRAME 31.0x31.0 fill=#F3F0EB r100.0 vy:FIXE hz:FIXE
        [back arrow] INSTANCE 16.0x13.0
          <Vector> VECTOR 6.7x13.0 
          <Vector> VECTOR 16.0x0.0 
      [Frame 2] FRAME 341.0x30.0 fill=#FFFFFF H gap10.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
        [Frame 3] FRAME 337.0x26.0 r100.0 vy:FILL hz:FILL
          [Frame 4] FRAME 360.0x26.0 fill=#1B7498 r100.0
    TEXT "Almost there"  [Inter w700 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 16] FRAME 376.0x130.0 V gap10.0 vy:HUG hz:FIXE
    [button] INSTANCE 364.0x46.0 fill=#4A4741 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
      TEXT "Continue"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
    [button] INSTANCE 364.0x46.0 fill=#F5F3EF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
      TEXT "Skip"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]
    TEXT "Next: Meet the coach"  [Inter w400 13.0/18.0 ls0.0 C #1E1E1E]
  [Frame 79] FRAME 415.0x605.0 V vy:FIXE hz:FIXE
    [Frame 1] FRAME 415.0x173.0 V gap10.0 vy:FIXE hz:FILL
      TEXT "What do you in your free time?"  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
      TEXT "Looking for more? Select what describes your family routine."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 204973883] FRAME 382.3x419.0 G vy:FIXE hz:FIXE
      [Frame 204973873] FRAME 122.4x134.6 fill=#1B7498 V gap9.4 pad30.1/16.0/22.6/16.0 r11.29887580871582 vy:FILL hz:FILL
        [Frame 5] FRAME 90.4x81.9 V gap3.8 vy:FILL hz:FILL
          [brush] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 39.5x37.7 #F5F3EF
          TEXT "Arts & crafts"  [Inter w400 16.00674057006836/24.5 ls0.0 C #F5F3EF]
      [Frame 204973874] FRAME 122.4x134.6 fill=#FFFFFF V gap9.4 pad7.5/16.0/9.4/16.0 r11.29887580871582 vy:FILL hz:FILL stroke #1B7498 1.0
        [Frame 204973882] FRAME 88.4x22.6 H gap9.4 vy:HUG hz:FILL
          [addcircle] INSTANCE 22.6x22.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.8x18.8 #E8EAED
        [Frame 5] FRAME 88.4x78.2 V gap3.8 vy:FIXE hz:FILL
          [library] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 39.5x22.0 #1B7498
            <Vector> VECTOR 39.5x14.1 #1B7498
          TEXT "Museums"  [Inter w400 16.00674057006836/24.5 ls0.0 C #1B7498]
      [Frame 204973875] FRAME 122.4x134.6 fill=#1B7498 V gap9.4 pad30.1/16.0/22.6/16.0 r11.29887580871582 vy:FILL hz:FILL
        [Frame 5] FRAME 90.4x81.9 V gap3.8 vy:FILL hz:FILL
          [hike] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 23.9x33.7 #F5F3EF
          TEXT "Hiking"  [Inter w400 16.00674057006836/24.5 ls0.0 C #F5F3EF]
      [Frame 204973876] FRAME 122.4x134.6 fill=#FFFFFF V gap9.4 pad7.5/16.0/9.4/16.0 r11.29887580871582 vy:FILL hz:FILL stroke #1B7498 1.0
        [Frame 204973882] FRAME 88.4x22.6 H gap9.4 vy:HUG hz:FILL
          [addcircle] INSTANCE 22.6x22.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.8x18.8 #E8EAED
        [Frame 5] FRAME 88.4x74.4 V gap3.8 vy:FIXE hz:FILL
          [garden] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 33.0x31.4 #1B7498
          TEXT "Gardens"  [Inter w400 16.00674057006836/24.5 ls0.0 C #1B7498]
      [Frame 204973877] FRAME 122.4x134.6 fill=#1B7498 V gap9.4 pad30.1/16.0/22.6/16.0 r11.29887580871582 vy:FILL hz:FILL
        [Frame 5] FRAME 90.4x81.9 V gap3.8 vy:FILL hz:FILL
          [nature] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 33.0x31.4 #F5F3EF
          TEXT "Nature"  [Inter w400 16.00674057006836/24.5 ls0.0 C #F5F3EF]
      [Frame 204973878] FRAME 122.4x134.6 fill=#1B7498 V gap9.4 pad30.1/16.0/22.6/16.0 r11.29887580871582 vy:FILL hz:FILL
        [Frame 5] FRAME 90.4x81.9 V gap3.8 vy:FILL hz:FILL
          [park] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 29.7x31.4 #F5F3EF
          TEXT "Parks"  [Inter w400 16.00674057006836/24.5 ls0.0 C #F5F3EF]
      [Frame 204973879] FRAME 122.4x134.6 fill=#1B7498 V gap9.4 pad30.1/16.0/22.6/16.0 r11.29887580871582 vy:FILL hz:FILL
        [Frame 5] FRAME 90.4x81.9 V gap3.8 vy:FILL hz:FILL
          [robot] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 36.3x29.8 #F5F3EF
          TEXT "Science"  [Inter w400 16.00674057006836/24.5 ls0.0 C #F5F3EF]
      [Frame 204973880] FRAME 122.4x134.6 fill=#FFFFFF V gap9.4 pad7.5/16.0/9.4/16.0 r11.29887580871582 vy:FILL hz:FILL stroke #1B7498 0.9415730237960815
        [Frame 204973882] FRAME 88.5x22.6 H gap9.4 vy:HUG hz:FILL
          [addcircle] INSTANCE 22.6x22.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 18.8x18.8 #E8EAED
        [Frame 5] FRAME 88.5x71.6 V gap3.8 vy:FIXE hz:FILL
          [swimming] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 33.0x28.2 #1B7498
          TEXT "Nature"  [Inter w400 16.00674057006836/24.5 ls0.0 C #1B7498]
      [Frame 204973881] FRAME 122.4x134.6 fill=#1B7498 V gap9.4 pad30.1/16.0/22.6/16.0 r11.29887580871582 vy:FILL hz:FILL
        [Frame 5] FRAME 90.4x81.9 V gap3.8 vy:FILL hz:FILL
          [rocket] INSTANCE 39.5x37.7 vy:FIXE hz:FIXE
            <Vector> VECTOR 33.0x31.5 #F5F3EF
          TEXT "Parks"  [Inter w400 16.00674057006836/24.5 ls0.0 C #F5F3EF]

====================================================================================================
FRAME Onboarding - creating account — `754:4437` — 440.0x1000.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  TEXT "Getting everything ready for you, Greg."  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
  TEXT "Getting to know your family"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
  TEXT "Bringing your coach up to speed"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
  TEXT "Sketching your first plan"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
  TEXT "Securing your family's space"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
  TEXT "79"  [Fraunces w700 144.29652404785156/177.9 ls-5.77 C #1E1E1E]
  TEXT "%"  [Fraunces w700 78.42202758789062/96.7 ls-7.84 C #1E1E1E]
  <Ellipse 2> ELLIPSE 285.0x285.0 
  [Frame 66] FRAME 355.0x6.0 fill=#1B7498
  [Frame 67] FRAME 355.0x6.0 fill=#1B7498
  [Frame 68] FRAME 355.0x6.0 fill=#1B7498
  [Frame 69] FRAME 355.0x6.0 fill=#4A4741
  [Frame 70] FRAME 120.0x6.0 fill=#1B7498
  [Layer_1] FRAME 34.0x34.0
    <Vector> VECTOR 34.0x34.0 #1B7498
  [Layer_1] FRAME 34.0x34.0
    <Vector> VECTOR 34.0x34.0 #1B7498
  [Layer_1] FRAME 34.0x34.0
    <Vector> VECTOR 34.0x34.0 #1B7498
  [Status Bar] FRAME 440.0x61.0 H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5

====================================================================================================
FRAME Onboarding - welcome — `754:4458` — 440.0x1000.0 fill=#F3F0EB 
====================================================================================================
  <Ellipse 1> ELLIPSE 544.0x544.0 GRADIENT_RADIAL
  [Frame 29] FRAME 362.0x826.0 V gap14.0 vy:HUG hz:FIXE
    [Frame 1] FRAME 362.0x196.0 V gap20.0 vy:FIXE hz:FILL
      TEXT "You’re all set, Gregory."  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
      TEXT "Here’s what we've got — and what's waiting for you and your family!"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
    [Frame 26] FRAME 362.0x158.0 V gap8.0 pad0/0/20.0/0 vy:HUG hz:FILL
      TEXT "Your family"  [Fraunces w600 28.0/32.0 ls0.0 L #1E1E1E]
      [Frame 204973852] FRAME 362.0x90.0 V gap6.0 vy:HUG hz:FILL
        TEXT "Two parents, Two CoParents "  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
        TEXT "Benjamin, 5 · Lily, 2"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
        TEXT "Gig Harbor, Wa. 98332"  [Inter w400 17.0/26.0 ls0.0 L #1E1E1E]
    [Frame 25] FRAME 362.0x352.0 V gap15.0 vy:HUG hz:FILL
      TEXT "Here’s what’s waiting for you:"  [Fraunces w600 28.0/32.0 ls0.0 L #1E1E1E]
      [Frame 204973839] FRAME 362.0x273.0 V gap15.0 vy:HUG hz:FILL
        TEXT "Free family plan for 7 days"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
        TEXT "A coach who already knows Benjamin and Lily"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
        TEXT "A coach who already knows Ben and Lily"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Expert-backed articles, filtered for your family"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
        TEXT "A community of parents who get it"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Advice built around what you're actually dealing with"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
    [Frame 65] FRAME 362.0x78.0 V gap10.0 vy:FIXE hz:FILL
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Take me home"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  [Status Bar] FRAME 440.0x61.0 H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5

====================================================================================================
FRAME Onboarding - Dashboard 1 — `754:4553` — 440.0x1818.0 fill=#F3F0EB 
====================================================================================================
  [content] FRAME 440.0x1724.0 V gap16.0 pad0/24.0/22.0/24.0 vy:FIXE hz:FIXE
    [Your Kids] FRAME 392.0x321.0 fill=#FFFFFF @0.50 V gap12.0 pad24.0/24.0/24.0/24.0 r28.0 vy:HUG hz:FILL
      TEXT "YOUR KIDS"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      TEXT "Help us get to know your kids a little more:"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Kids Cards Container] FRAME 344.0x151.0 H gap12.0 vy:FIXE hz:FILL
        [Kid Card] FRAME 166.0x151.0 fill=#1B7498 V gap12.0 pad20.0/12.0/20.0/12.0 r12.0 vy:FIXE hz:FILL
          [Kid Details Container] FRAME 142.0x83.7 V gap24.0 vy:HUG hz:FILL
            [Kid Info Container] FRAME 142.0x83.7 V gap16.0 vy:HUG hz:FILL
              TEXT "Benjamin   "  [Fraunces w600 28.0/32.0 ls0.0 C #FFFFFF]
              [small button] FRAME 132.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #F5F3EF 1.0
                TEXT "Set up Benjamin"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
        [Kid Card] FRAME 166.0x151.0 fill=#1B7498 V gap12.0 pad20.0/12.0/20.0/12.0 r12.0 vy:FIXE hz:FILL
          [Kid Details Container] FRAME 142.0x83.7 V gap16.0 vy:HUG hz:FILL
            [Kid Info Container] FRAME 142.0x83.7 V gap16.0 vy:HUG hz:FILL
              TEXT "Lily"  [Fraunces w600 28.0/32.0 ls0.0 C #FFFFFF]
              [small button] FRAME 94.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #F5F3EF 1.0
                TEXT "Set up Lily"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
      [button] INSTANCE 344.0x46.0 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL stroke #1B7498 1.0
        TEXT "+ Add another child"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]
    [Coming Up] FRAME 380.0x331.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FIXE
      [Title Container] FRAME 340.0x22.0 H gap9.0 vy:HUG hz:FILL
        [Coming Up Icon] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #8E8A83
        TEXT "COMING UP"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Events Container] FRAME 340.0x276.0 V gap13.0 vy:HUG hz:FILL
        [Event Container] FRAME 340.0x276.0 V gap3.0 pad0/0/24.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Coach found these activities and events near you"  [Inter w800 16.0/22.0 ls0.0 L #151412]
          [Event Info Container] FRAME 340.0x205.0 V gap8.0 vy:HUG hz:FILL
            [Event Icon Container] FRAME 340.0x38.0 H gap10.0 pad8.0/0/8.0/0 vy:HUG hz:FILL
              [Event Icon] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 20.1x14.2 #1B7498
              TEXT "Local camp name and dates"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
            [Event Icon Container] FRAME 340.0x40.0 H gap10.0 pad8.0/0/8.0/0 vy:HUG hz:FILL
              [Event Icon] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 14.5x21.5 #1B7498
              TEXT "Nature walk name and dates"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
            [Event Icon Container] FRAME 340.0x34.0 H gap10.0 pad8.0/0/8.0/0 vy:HUG hz:FILL
              [Event Icon] INSTANCE 19.0x17.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 19.0x9.9 #1B7498
                <Vector> VECTOR 19.0x6.4 #1B7498
              TEXT "Book reading club name and dates"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
            [Add Event Container] FRAME 340.0x69.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL
              [Add Event Button Container] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
                [small button] FRAME 147.0x35.7 fill=#F5F3EF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 0.834434449672699
                  TEXT "Schedule an event"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [For You] FRAME 392.0x563.0 fill=#FFFFFF @0.50 V gap6.0 pad30.0/30.0/30.0/30.0 r28.0 vy:HUG hz:FILL
      [Title Container] FRAME 321.9x28.0 H gap9.0 pad0/0/6.0/0 vy:HUG hz:HUG
        [For You Icon] INSTANCE 21.9x15.3 vy:FIXE hz:FIXE
          <Vector> VECTOR 21.9x15.3 #6E6A62
        TEXT "FOR YOU THIS WEEK"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Articles Container] FRAME 332.0x469.0 V gap24.0 vy:HUG hz:FILL
        [Article] FRAME 332.0x229.0 V gap9.0 pad0/0/32.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Care · 2 min"  [Inter w700 13.0/18.0 ls0.0 L #989591]
          [Frame 204973838] FRAME 332.0x170.0 V gap14.0 vy:HUG hz:FILL
            TEXT "When bedtime becomes a negotiation"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Article] FRAME 332.0x216.0 V gap9.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "This week"  [Inter w700 13.0/18.0 ls0.0 L #989591]
          [Frame 204973837] FRAME 332.0x111.0 V gap13.0 vy:HUG hz:FILL
            TEXT "Tips on surviving the day"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "The big birthday party is coming in 3 days"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Action Container] FRAME 332.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#FFFFFF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [coach banner] FRAME 392.0x220.0 fill=#FCFBF8 V gap8.0 pad30.0/30.0/30.0/30.0 r28.0 vy:HUG hz:FILL
      [Frame 39] FRAME 332.0x22.0 H gap12.0 vy:HUG hz:FILL
        [coach] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 13.7x17.8
            <Vector> VECTOR 6.8x7.0 #1B7498
            <Vector> VECTOR 2.2x2.3 #1B7498
            <Vector> VECTOR 1.4x1.4 #1B7498
            <Vector> VECTOR 6.0x8.0 #1B7498
            <Vector> VECTOR 7.3x7.8 #1B7498
        TEXT "COACH  •  Just now"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
      TEXT "Hi Greg. I'm here to help with the hard-to-figure-out parts of raising Benjamin and Lily. Let's start by setting up a companion for each of them — a friend you configure and watch over."  [Inter w400 17.0/26.0 ls0.0 L #6E6A62]
  [Frame 204973872] FRAME 440.0x166.0
    [Tab Bar] INSTANCE 440.0x93.0 fill=#F5F3EF H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #FFFFFF 1.0
      [Tab 1] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0 GLASS rNone None
        [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
          <Vector> VECTOR 15.8x17.8 #1B7498
        TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 3] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 12.1x14.9
            <Vector> VECTOR 6.0x5.9 #1B7498
            <Vector> VECTOR 1.9x1.9 #1B7498
            <Vector> VECTOR 1.2x1.2 #1B7498
            <Vector> VECTOR 5.3x6.7 #1B7498
            <Vector> VECTOR 6.5x6.5 #1B7498
        TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 5] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1B7498
        TEXT "PLANNER"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 2] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1B7498
        TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x21.0 #1B7498
        TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Frame 204973842] FRAME 376.0x42.0 fill=#FFFFFF H gap10.0 pad10.0/10.0/10.0/20.0 r100.0 vy:HUG hz:FIXE
      [Frame 39] FRAME 346.0x22.0 H gap12.0 vy:HUG hz:FILL
        [coach] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 13.7x17.8
            <Vector> VECTOR 6.8x7.0 #1B7498
            <Vector> VECTOR 2.2x2.3 #1B7498
            <Vector> VECTOR 1.4x1.4 #1B7498
            <Vector> VECTOR 6.0x8.0 #1B7498
            <Vector> VECTOR 7.3x7.8 #1B7498
        TEXT "COACH  •  Check your family settings"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
  [Container] FRAME 440.0x61.0 fill=#F5F3EF V vy:HUG hz:FIXE
    [Status Bar] FRAME 440.0x61.0 H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
      [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
        TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
      [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
        <Cellular Connection> VECTOR 19.2x12.2 #151412
        <Wifi> VECTOR 17.1x12.3 #151412
        [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
          [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
          <Cap> VECTOR 1.3x4.1 #151412
          [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [profile] FRAME 440.0x59.0 V gap10.0 pad0/24.0/0/24.0 vy:FIXE hz:FIXE
    [Frame 204973842] FRAME 392.0x56.0 H pad10.0/10.0/10.0/20.0 r100.0 vy:HUG hz:FILL
      [avatar with chip] FRAME 37.0x36.0 vy:FIXE hz:FIXE
        [Profile Image] FRAME 38.0x36.0 fill=#1B7498 V gap4.8 pad11.5/11.5/11.5/11.5 r48.0 vy:FIXE hz:HUG
          TEXT "G"  [Fraunces w700 18.239999771118164/19.2 ls-0.18 C #FFFFFF]
        [chip] INSTANCE 11.0x11.0 DROP_SHADOW r1.0 #000000
          <Ellipse 4> ELLIPSE 9.0x9.0 #F5F3EF

====================================================================================================
FRAME Onboarding - welcome — `754:6516` — 440.0x2192.0 fill=#F3F0EB 
====================================================================================================
  [Frame 29] FRAME 376.0x2093.0 V gap23.0 vy:HUG hz:FIXE
    [icon_settings] INSTANCE 40.0x41.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 40.0x41.0 #4A4741
    [Frame 1] FRAME 376.0x164.0 V gap22.0 vy:HUG hz:FILL
      TEXT "Your MVP Family Plan is almost ready "  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
      TEXT "Review your family settings message"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 204973848] FRAME 376.0x1704.0 V gap12.0 vy:HUG hz:FILL
      [Frame 204973845] FRAME 376.0x278.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Your MVP  information"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Your plan includes a custom MVP username and email"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x110.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Username: ⏎ MVP Email: ⏎ Password: Plan ⏎ Billing"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "MVPDad_GregH ⏎ MVP_GregH@mvp.com ⏎ ****** ⏎ Family ⏎ Annual"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973851] FRAME 376.0x238.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Family structure"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Tell us about the parenting setup..."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x88.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Parent 1 ⏎ Parent 2 ⏎ Parent 3 ⏎ Parent 4"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "Dad ⏎ Mom ⏎ Dad ⏎ Step mom"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "Me ⏎ Spouse ⏎ CoParent ⏎ CoParent"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973846] FRAME 376.0x256.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
              [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Your family"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Your plan includes a custom MVP username and email"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x88.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Parent  ⏎ Parent ⏎ Son ⏎ Daughter"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "Greg ⏎ Teri ⏎ Benjamin ⏎ Lily"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "Dad ⏎ Mom ⏎ Son ⏎ Daughter"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973847] FRAME 376.0x278.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Your circle"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Your MVP Circle includes anyone that you rely on for help"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x110.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Armelle F. ⏎ Grandma Gerry ⏎ Uncle Tom ⏎ Geoff M. ⏎ Twila B."  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "mvpNanny ⏎ mvpGerry ⏎ mvpUncle ⏎ mvpNeighbor ⏎ mvpAunt"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973848] FRAME 376.0x194.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Care givers"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Care givers are.."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x44.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Armelle ⏎ Nana Gerry"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "mvpNanny ⏎ mpvGrandmaGerry"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973849] FRAME 376.0x194.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Language at home"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Do you speak one or several languages at home?"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x44.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Primary language ⏎ Secondary language"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "Spanish ⏎ English"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
      [Frame 204973850] FRAME 376.0x194.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Divider] FRAME 316.0x20.0 V gap10.0 vy:HUG hz:FILL
              [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "MVP coach settings"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        TEXT "Set up how you want the coach to respond"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Frame 204973844] FRAME 316.0x44.0 H gap23.0 vy:HUG hz:FILL
          TEXT "Voice ⏎ Personality"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          TEXT "Default - Male ⏎ Default - Genuine"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
    [Frame 204973843] FRAME 270.0x115.0 V gap23.0 vy:HUG hz:HUG
      [Frame 65] FRAME 270.0x46.0 V gap10.0 vy:FIXE hz:FIXE
        [button] INSTANCE 252.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
          TEXT "Looks good!"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 252.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Set up later"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]
  [Status Bar] FRAME 440.0x61.0 H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5

====================================================================================================
FRAME kid-001a — `869:981` — 440.0x1847.0 fill=#FFFFFF V gap21.0 pad60.0/0/60.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Benjamin’s settings"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 204973859] FRAME 250.0x36.7 H gap10.0 vy:HUG hz:FIXE
    [small button] FRAME 120.0x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
      [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
        [Frame] FRAME 20.0x20.0
          <Vector> VECTOR 15.0x15.0 #E3E3E3
      TEXT "Save"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    [small button] FRAME 120.0x35.7 fill=#858585 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:FILL
      TEXT "Cancel"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
  [Frame 39] FRAME 354.0x323.0 fill=#989591 V gap10.0 pad17.7/17.7/17.7/17.7 r32.0 vy:FIXE hz:FIXE
    [Frame 56] FRAME 96.4x26.0 fill=#151412 H gap6.0 pad6.0/10.0/6.0/10.0 r18.599998474121094 vy:HUG hz:HUG DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Upload new"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  TEXT "Add a photo of Benjamin"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
  [Frame 50] FRAME 440.0x1380.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [Frame 204973858] FRAME 380.0x120.0 fill=#FFFFFF H gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      TEXT "Benjamin "  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x307.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x307.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Son"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x53.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Birthday:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "April 25, 2021"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Grade:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Pre-K"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 9] FRAME 320.0x102.0 V gap22.0 pad20.0/0/0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          TEXT "Personality"  [Inter w700 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 9] FRAME 330.0x42.0 G vy:HUG hz:FIXE
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  [Group] GROUP 18.0x18.0
                    <Vector> VECTOR 18.0x18.0 
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 4.5x5.3
                        <Vector> VECTOR 4.5x5.3 #1B7498
                      [Group] GROUP 12.0x13.4
                        <Vector> VECTOR 12.0x13.4 #1B7498
                TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 13.2x12.1 #1B7498
                TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.5x11.1 #1B7498
                TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 53] FRAME 380.0x594.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "What makes Benjamin special"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x114.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973863] FRAME 16.0x98.0 V gap10.0 pad6.0/0/6.0/0 vy:FILL hz:FIXE
          [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973862] FRAME 302.0x98.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 302.0x74.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Comics, sports, funny animals, sticks, carrots, ⏎ pizza, cheese sticks, running and jumping, ⏎ turtles, slime"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 60] FRAME 320.0x96.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x80.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 258.0x80.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 258.0x56.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Clowns, big dogs, mean people, baths, ⏎ loud noises, mean people"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 64] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 236.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 236.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Dinners, social events, school work"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 65] FRAME 320.0x78.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x62.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 208.0x62.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 208.0x38.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "Math, reading, sense of humor"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
      [Frame 66] FRAME 320.0x96.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [Frame 204973861] FRAME 16.0x80.0 V gap10.0 pad6.0/6.0/6.0/6.0 vy:FILL hz:FIXE
          [arrow] INSTANCE 4.0x8.0 vy:FIXE hz:FILL
            <Vector> VECTOR 12.0x6.0 
        [Frame 204973860] FRAME 287.0x80.0 V gap6.0 vy:HUG hz:HUG
          TEXT "Goals for Benjamin"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 204973864] FRAME 287.0x56.0 H gap10.0 pad10.0/10.0/10.0/10.0 r12.0 vy:HUG hz:HUG stroke #1B7498 0.5
            TEXT "More math puzzles and reading challenges, ⏎ interacting with other kids, fear of water"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME kid-001c — `855:3623` — 440.0x1460.0 fill=#FFFFFF V pad60.0/0/90.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Benjamin’s settings"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 440.0x401.0 fill=IMAGE+GRADIENT_LINEAR V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 62.0x26.0 fill=#151412 H gap6.0 pad6.0/6.0/6.0/6.0 r18.599998474121094 vy:HUG hz:FIXE DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Edit"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x993.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [small button] FRAME 115.4x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
      [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.7x13.7 #E3E3E3
      TEXT "Edit child"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    TEXT "Benjamin "  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x307.0 V gap16.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Frame 204973857] FRAME 380.0x307.0 fill=#FFFFFF V gap16.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x20.0 V gap10.0 vy:HUG hz:FILL
          [pencile] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 13.7x13.7 #1B7498
        TEXT "Son"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x53.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Birthday:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "April 25, 2021"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Grade:"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Pre-K"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 9] FRAME 320.0x102.0 V gap22.0 pad20.0/0/0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          TEXT "Personality"  [Inter w700 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 9] FRAME 330.0x42.0 G vy:HUG hz:FIXE
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  [Group] GROUP 18.0x18.0
                    <Vector> VECTOR 18.0x18.0 
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 4.5x5.3
                        <Vector> VECTOR 4.5x5.3 #1B7498
                      [Group] GROUP 12.0x13.4
                        <Vector> VECTOR 12.0x13.4 #1B7498
                TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 13.2x12.1 #1B7498
                TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.5x11.1 #1B7498
                TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 53] FRAME 380.0x302.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "What makes Benjamin special"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 60] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 61] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 62] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 63] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Goals for Benjamin"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME Onboarding - Dashboard 2 — `754:4478` — 440.0x1868.0 fill=#E9E4DC 
====================================================================================================
  [Container] FRAME 440.0x1623.7 V gap18.0 pad0/30.0/0/30.0 vy:HUG hz:FIXE
    [Status Bar] FRAME 440.0x62.0 H gap154.0 pad21.0/0/19.0/0 vy:HUG hz:FIXE
      [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
        TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #000000]
      [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
        <Cellular Connection> VECTOR 19.2x12.2 #000000
        <Wifi> VECTOR 17.1x12.3 #000000
        [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
          [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #000000 1.0
          <Cap> VECTOR 1.3x4.1 #000000
          [Capacity] RECTANGLE 21.0x9.0 fill=#000000 r2.5
    [Container] FRAME 380.0x303.0 V gap12.0 vy:HUG hz:FILL
      [Container] FRAME 380.0x46.0 V gap10.0 pad0/0/10.0/0 vy:HUG hz:FILL
        [Icon Container] FRAME 37.0x36.0 fill=#1B7498 V gap4.8 pad11.5/11.5/11.5/11.5 r48.0 vy:FIXE hz:HUG
          TEXT "G"  [Fraunces w700 18.239999771118164/19.2 ls-0.18 C #FFFFFF]
      [Container] FRAME 380.0x245.0 fill=#F5F3EF V gap12.0 pad24.0/30.0/0/30.0 r28.0 vy:FIXE hz:FILL DROP_SHADOW r3.0 #000000
        TEXT "YOUR KIDS"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
        [Card Container] FRAME 348.0x153.0 H gap12.0 vy:HUG hz:HUG
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r12.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30+GRADIENT_LINEAR V gap7.4 pad17.7/17.7/17.7/17.7 vy:FILL hz:FIXE
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Benjamin"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
          [Kid Card] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r12.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
            [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30 V gap7.4 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FILL
              [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
                [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
                  <Vector> VECTOR 3.9x4.0 #F5F3EF
              TEXT "Lily"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
    [Container] FRAME 380.0x338.0 V gap13.0 pad20.0/20.0/0/20.0 vy:HUG hz:FIXE
      [Section Title] FRAME 340.0x22.0 H gap12.0 vy:HUG hz:FILL
        [Section Icon] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #6E6A62
        TEXT "COMING UP"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Card Container] FRAME 340.0x283.0 V gap13.0 vy:HUG hz:FILL
        [Card] FRAME 340.0x113.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL stroke #8E8A83 1.0
          TEXT "Soccer camp starts on Friday"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
          TEXT "Get Ben ready! Camp begins on Aug 8, 7am."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Card] FRAME 340.0x157.0 V gap3.0 pad0/0/12.0/0 vy:HUG hz:FILL
          TEXT "Lily and Benjamin birthday outing"  [Fraunces w600 28.0/32.0 ls0.0 L #2B2925]
          TEXT "Going to the zoo with the kids. Aug 4, 2pm."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Card] FRAME 340.0x57.0 V gap10.0 vy:FIXE hz:FILL
            [small button] FRAME 69.0x35.7 fill=#FFFFFF H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
              TEXT "See all"  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [For You] FRAME 380.0x484.0 fill=#FFFFFF V gap6.0 pad28.0/30.0/28.0/30.0 r28.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Title Container] FRAME 123.9x28.0 H gap9.0 pad0/0/6.0/0 vy:HUG hz:HUG
        [For You Icon] INSTANCE 21.9x15.3 vy:FIXE hz:FIXE
          <Vector> VECTOR 21.9x15.3 #6E6A62
        TEXT "FOR YOU"  [Inter w800 16.0/22.0 ls0.0 L #6E6A62]
      [Articles Container] FRAME 320.0x394.0 V gap24.0 vy:HUG hz:FILL
        [Article] FRAME 320.0x229.0 V gap9.0 pad0/0/32.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Care · 2 min"  [Inter w700 13.0/18.0 ls0.0 L #989591]
          [Article Content] FRAME 320.0x170.0 V gap14.0 vy:HUG hz:FILL
            TEXT "When bedtime becomes a negotiation"  [Fraunces w700 38.0/40.0 ls-0.38 L #2B2925]
            TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
        [Article] FRAME 320.0x141.0 V gap9.0 pad0/0/32.0/0 vy:HUG hz:FILL stroke #C9C5BE 1.0
          TEXT "Mealtime · 1 min"  [Inter w700 13.0/18.0 ls0.0 L #989591]
          [Article Content] FRAME 320.0x82.0 V gap14.0 vy:HUG hz:FILL
            TEXT "Green food is good food"  [Fraunces w600 28.0/32.0 ls0.0 L #2B2925]
            TEXT "What to do when the third glass of water isn't about water"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Article] FRAME 380.0x253.7 fill=#F5F3EF V gap8.0 pad30.0/30.0/30.0/30.0 r28.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
      [Section Title] FRAME 320.0x22.0 H gap12.0 vy:HUG hz:FILL
        [Section Icon] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 13.7x17.8
            <Vector> VECTOR 6.8x7.0 #1B7498
            <Vector> VECTOR 2.2x2.3 #1B7498
            <Vector> VECTOR 1.4x1.4 #1B7498
            <Vector> VECTOR 6.0x8.0 #1B7498
            <Vector> VECTOR 7.3x7.8 #1B7498
        TEXT "COACH  •  This morning"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
      TEXT "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."  [Inter w400 17.0/26.0 ls0.0 L #6E6A62]
      [Action Container] FRAME 320.0x35.7 V gap10.0 vy:HUG hz:FILL
        [small button] FRAME 136.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
          TEXT "Try this with Ben "  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
    [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE
      [Tab 1] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL GLASS rNone None
        [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
          <Vector> VECTOR 15.8x17.8 #1B7498
        TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 3] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 12.1x14.9
            <Vector> VECTOR 6.0x5.9 #1B7498
            <Vector> VECTOR 1.9x1.9 #1B7498
            <Vector> VECTOR 1.2x1.2 #1B7498
            <Vector> VECTOR 5.3x6.7 #1B7498
            <Vector> VECTOR 6.5x6.5 #1B7498
        TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 5] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
          <Vector> VECTOR 18.6x20.6 #1B7498
        TEXT "PLANNER"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 2] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1B7498
        TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
      [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
        [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x21.0 #1B7498
        TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]

====================================================================================================
FRAME Onboarding - welcome — `869:1090` — 440.0x1959.0 fill=#F3F0EB+#000000 @0.20 
====================================================================================================
  [Main Container] FRAME 380.0x568.7 V gap12.0 vy:HUG hz:FIXE
    [Header Container] FRAME 380.0x46.0 V gap10.0 pad0/0/10.0/0 vy:HUG hz:FILL
      [Profile Container] FRAME 37.0x36.0 fill=#1B7498 V gap4.8 pad11.5/11.5/11.5/11.5 r48.0 vy:FIXE hz:HUG
        TEXT "G"  [Fraunces w700 18.239999771118164/19.2 ls-0.18 C #FFFFFF]
    [Kids Container] FRAME 380.0x245.0 fill=#F5F3EF V gap12.0 pad24.0/30.0/0/30.0 r32.0 vy:FIXE hz:FILL
      TEXT "YOUR KIDS"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Cards Container] FRAME 348.0x153.0 H gap12.0 vy:HUG hz:HUG
        [Card Container] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
          [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30+GRADIENT_LINEAR V gap7.4 pad17.7/17.7/17.7/17.7 vy:FILL hz:FIXE
            [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
              [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 3.9x4.0 #F5F3EF
                <Vector> VECTOR 3.9x4.0 #F5F3EF
                <Vector> VECTOR 3.9x4.0 #F5F3EF
            TEXT "Benjamin"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
        [Card Container] FRAME 168.0x153.0 fill=#F5F3EF V gap12.0 r16.0 vy:FIXE hz:FIXE stroke #1B7498 0.5
          [Kid Image] FRAME 168.0x153.0 fill=IMAGE+#000000 @0.30 V gap7.4 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FILL
            [Kid Card Divider] FRAME 132.6x4.0 V gap10.0 vy:FIXE hz:FILL
              [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 3.9x4.0 #F5F3EF
                <Vector> VECTOR 3.9x4.0 #F5F3EF
                <Vector> VECTOR 3.9x4.0 #F5F3EF
            TEXT "Lily"  [Fraunces w600 28.0/32.0 ls0.0 C #F5F3EF]
    [Coach Container] FRAME 380.0x253.7 fill=#F5F3EF V gap8.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL GLASS rNone None DROP_SHADOW r10.0 #000000
      [Coach Header] FRAME 320.0x22.0 H gap12.0 vy:HUG hz:FILL
        [Coach Image] INSTANCE 15.0x20.0 vy:FIXE hz:FIXE
          [Layer_1] FRAME 13.7x17.8
            <Vector> VECTOR 6.8x7.0 #1B7498
            <Vector> VECTOR 2.2x2.3 #1B7498
            <Vector> VECTOR 1.4x1.4 #1B7498
            <Vector> VECTOR 6.0x8.0 #1B7498
            <Vector> VECTOR 7.3x7.8 #1B7498
        TEXT "COACH  •  This morning"  [Inter w800 16.0/22.0 ls0.0 L #1B7498]
      TEXT "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."  [Inter w400 17.0/26.0 ls0.0 L #6E6A62]
      [Button Container] FRAME 320.0x35.7 V gap10.0 vy:HUG hz:FILL
        [small button] FRAME 136.0x35.7 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG stroke #1B7498 1.0
          TEXT "Try this with Ben "  [Inter w800 13.350951194763184/18.4 ls0.0 C #1B7498]
  [Rectangle 3] RECTANGLE 440.0x538.0 fill=#000000 @0.20
  [Container] FRAME 436.0x1698.0 fill=#F5F3EF V gap10.0 pad30.0/30.0/30.0/30.0 r56.0,56.0,0.0,0.0 vy:HUG hz:HUG
    [Container] FRAME 376.0x14.0 H gap10.0 vy:HUG hz:FILL
      [Icon] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 14.0x14.0 #4A4741
    [Container] FRAME 376.0x1614.0 V gap23.0 vy:HUG hz:FIXE
      [Container] FRAME 376.0x1614.0 V gap12.0 vy:HUG hz:FILL
        [Card] FRAME 376.0x262.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "Your MVP  information"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Your plan includes a custom MVP username and email"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x110.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Username: ⏎ MVP Email: ⏎ Password: Plan ⏎ Billing"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "MVPDad_GregH ⏎ MVP_GregH@mvp.com ⏎ ****** ⏎ Family ⏎ Annual"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Card] FRAME 376.0x222.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "MVP parents"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Tell us about the parenting setup..."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x88.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Parent ⏎ Parent ⏎ Parent ⏎ Parent"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Dad ⏎ Mom ⏎ Step dad ⏎ Birth mom"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Me ⏎ Spouse ⏎ CoParent ⏎ CoParent"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Card] FRAME 376.0x240.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "Your family"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Your plan includes a custom MVP username and email"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x88.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Parent  ⏎ Parent ⏎ Son ⏎ Daughter"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Greg ⏎ Teri ⏎ Benjamin ⏎ Lily"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Dad ⏎ Mom ⏎ Son ⏎ Daughter"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Card] FRAME 376.0x262.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "Your circle"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Your MVP Circle includes anyone that you rely on for help"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x110.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Armelle F. ⏎ Grandma Gerry ⏎ Uncle Tom ⏎ Geoff M. ⏎ Twila B."  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "mvpNanny ⏎ mvpGerry ⏎ mvpUncle ⏎ mvpNeighbor ⏎ mvpAunt"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Card] FRAME 376.0x200.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "Care givers"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Care givers are.."  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x66.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Alice ⏎ Armelle ⏎ Nana Gerry"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "mvpNanny1 ⏎ mvpNanny2 ⏎ mpvGrandmaGerry"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Card] FRAME 376.0x178.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "Language at home"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Do you speak one or several languages at home?"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x44.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Primary language ⏎ Secondary language"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Spanish ⏎ English"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Card] FRAME 376.0x178.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL DROP_SHADOW r3.0 #000000
          [Kid Card Divider] FRAME 316.0x4.0 V gap10.0 vy:HUG hz:FILL
            [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
              <Vector> VECTOR 3.9x4.0 #1B7498
          TEXT "MVP coach settings"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
          TEXT "Set up how you want the coach to respond"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
          [Container] FRAME 316.0x44.0 H gap23.0 vy:HUG hz:FILL
            TEXT "Voice ⏎ Personality"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Default - Male ⏎ Default - Genuine"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
  [Status Bar] FRAME 440.0x61.0 H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Tab Bar] INSTANCE 436.0x93.0 fill=#F3F0EB H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE DROP_SHADOW r3.0 #000000
    [Tab 1] FRAME 62.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 62.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "PLANNER"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 62.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 92.0x52.0 fill=#DAE0DF V gap3.0 pad8.0/12.0/9.0/12.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #0A5570
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #0A5570]

====================================================================================================
FRAME parent 001 — `855:3939` — 440.0x1407.0 fill=#FFFFFF V pad60.0/0/60.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Primary parent"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 440.0x401.0 fill=IMAGE+GRADIENT_LINEAR V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 62.0x26.0 fill=#151412 H gap6.0 pad6.0/6.0/6.0/6.0 r18.599998474121094 vy:HUG hz:FIXE DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Edit"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x940.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [small button] FRAME 126.4x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
      [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.7x13.7 #E3E3E3
      TEXT "Edit parent"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    TEXT "Gregory"  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x232.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x232.0 fill=#FFFFFF V gap30.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x4.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
        TEXT "Dad"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x84.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "MVP name"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Mike"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973856] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Family roll"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Primary parent"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Email"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "mvp-gregory"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
    [Frame 53] FRAME 380.0x302.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "More about Gregory"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 60] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 61] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 62] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 63] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Goals for parent"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME co-parent 001 — `855:4275` — 440.0x1407.0 fill=#FFFFFF V pad60.0/0/60.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Primary parent"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 440.0x401.0 fill=IMAGE+GRADIENT_LINEAR V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 62.0x26.0 fill=#151412 H gap6.0 pad6.0/6.0/6.0/6.0 r18.599998474121094 vy:HUG hz:FIXE DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Edit"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x940.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [small button] FRAME 126.4x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
      [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.7x13.7 #E3E3E3
      TEXT "Edit parent"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    TEXT "Mona"  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x232.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x232.0 fill=#FFFFFF V gap30.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x4.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
        TEXT "Step Mom "  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973857] FRAME 320.0x84.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "MVP name"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Mona"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973856] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Family roll"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "co-parent"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Email"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "mvp-mona"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
    [Frame 53] FRAME 380.0x346.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "More about Mona"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 60] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 61] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 62] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 64] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Goals for Mona"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 63] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Co-Parent goals"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]

====================================================================================================
FRAME circle member — `855:4157` — 440.0x1460.0 fill=#FFFFFF V pad60.0/0/60.0/0 r24.0,24.0,0.0,0.0 vy:FIXE hz:FIXE
====================================================================================================
  [Frame 49] FRAME 440.0x42.0 H gap10.0 pad0/30.0/20.0/30.0 vy:HUG hz:FILL stroke #C8C3B8 1.0
    TEXT "Circle member setting"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
    [Vector] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 14.0x14.0 #4A4741
  [Frame 39] FRAME 440.0x401.0 fill=IMAGE+GRADIENT_LINEAR V gap10.0 pad17.7/17.7/17.7/17.7 vy:FIXE hz:FIXE
    [Frame 56] FRAME 62.0x26.0 fill=#151412 H gap6.0 pad6.0/6.0/6.0/6.0 r18.599998474121094 vy:HUG hz:FIXE DROP_SHADOW r6.199999809265137 #000000
      [camera] INSTANCE 13.4x12.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.4x12.0 #DAE0DF
      TEXT "Edit"  [Inter w400 10.074999809265137/13.9 ls0.0 C #DAE0DF]
  [Frame 50] FRAME 440.0x993.0 fill=#E9E4DC V gap20.0 pad24.0/30.0/24.0/30.0 vy:FIXE hz:FILL
    [small button] FRAME 137.4x36.7 fill=#1B7498 H gap8.3 pad8.3/12.5/8.3/12.5 r10.013213157653809 vy:HUG hz:HUG
      [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 13.7x13.7 #E3E3E3
      TEXT "Edit member"  [Inter w800 13.350951194763184/18.4 ls0.0 C #FFFFFF]
    TEXT "Alice"  [Fraunces w700 56.0/60.0 ls-1.12 L #1E1E1E]
    [Frame 52] FRAME 380.0x333.0 V gap30.0 vy:HUG hz:FILL
      [Frame 204973857] FRAME 380.0x333.0 fill=#FFFFFF V gap30.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
        [Kid Card Divider] FRAME 320.0x4.0 V gap10.0 vy:HUG hz:FILL
          [Kid Card Settings] INSTANCE 19.0x4.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
            <Vector> VECTOR 3.9x4.0 #1B7498
        TEXT "Nanny"  [Inter w600 24.0/24.0 ls0.0 L #1E1E1E]
        [Frame 204973856] FRAME 320.0x53.0 V gap9.0 vy:HUG hz:FILL
          [Frame 204973854] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "MVP name"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "Mike"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
          [Frame 204973855] FRAME 320.0x22.0 H gap30.0 vy:HUG hz:FILL
            TEXT "Email"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
            TEXT "mvp-mike"  [Inter w500 16.0/22.0 ls0.0 L #1E1E1E]
        [Frame 9] FRAME 320.0x102.0 V gap22.0 pad20.0/0/0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
          TEXT "Personality"  [Inter w700 13.0/18.0 ls0.0 L #1E1E1E]
          [Frame 9] FRAME 330.0x42.0 G vy:HUG hz:FIXE
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 70.0x18.0 H gap4.0 vy:HUG hz:HUG
                [Local fire department] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  [Group] GROUP 18.0x18.0
                    <Vector> VECTOR 18.0x18.0 
                  [Group] GROUP 12.0x13.5
                    [Group] GROUP 12.0x13.5
                      [Group] GROUP 4.5x5.3
                        <Vector> VECTOR 4.5x5.3 #1B7498
                      [Group] GROUP 12.0x13.4
                        <Vector> VECTOR 12.0x13.4 #1B7498
                TEXT "Spirited"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 92.0x18.0 H gap4.0 vy:HUG hz:HUG
                [partly_cloudy_day_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 13.2x12.1 #1B7498
                TEXT "Easy-going"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [tag item] INSTANCE 106.7x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:FILL hz:FILL stroke #1B7498 0.5
              [Frame 5] FRAME 78.0x18.0 H gap4.0 vy:HUG hz:HUG
                [heart_smile_18dp_E8EAED_FILL0_wght100_GRAD0_opsz20 1] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
                  <Vector> VECTOR 12.5x11.1 #1B7498
                TEXT "Sensitive"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 53] FRAME 380.0x302.0 fill=#FFFFFF V gap10.0 pad30.0/30.0/30.0/30.0 r32.0 vy:HUG hz:FILL
      [Frame 58] FRAME 320.0x22.0 H gap10.0 vy:HUG hz:FILL
        TEXT "More about Alice"  [Inter w800 16.0/22.0 ls0.0 L #1E1E1E]
      [Frame 59] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Likes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 60] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Dislikes"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 61] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Challenges"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 62] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Excels at"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
      [Frame 63] FRAME 320.0x34.0 H gap6.0 pad4.0/0/12.0/0 vy:HUG hz:FILL stroke #C8C3B8 1.0
        [arrow] INSTANCE 8.0x16.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x12.0 
        TEXT "Goals for Alice"  [Inter w400 13.0/18.0 ls0.0 L #1E1E1E]
    [Frame 204973853] FRAME 364.0x104.0 V gap12.0 vy:HUG hz:HUG
      [button] INSTANCE 364.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Save"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 364.0x46.0 fill=#FFFFFF V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE stroke #1B7498 1.0
        TEXT "Cancel"  [Inter w800 16.0/22.0 ls0.0 C #1B7498]