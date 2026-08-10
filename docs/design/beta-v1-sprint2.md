# beta-v1 — Design Sprint 2 spec (experience: Circle · Coach · Planner · Article)

Extracted **once** from Figma `Wb072IjTsBT7Ooqc41UFbK`, page `754:4311`
(*Design sprint 2 - exprience (wip)*, Aug 5), via the REST API `/v1/files/:key/nodes` in a single
batched call, then walked locally. **This file is the source of truth for the build — do not
re-read Figma.** The Figma MCP under-reports this file (it lists 2 of 12 pages) and the View seat's
Tier-1 quota is roughly 6 calls/month, so if it ever must be re-read: batch every node id into ONE
`/nodes` call.

**2026-08-08: this file was REPLACED.** The previous version listed only layer names and copy
strings, which is why the first sprint-2 build guessed at type and shipped the wrong section
headers. This version is measured: fonts as `family weight size/lineHeight ls<letterSpacing>`,
fills as hex, plus radii, padding, gaps, auto-layout mode (`H`/`V`), `hz:`/`vy:` sizing
(FILL/HUG/FIXED), strokes and shadows. Frames are ordered by canvas x. Status bars are retained
because they carry the page ground; decorative status-bar vectors are trimmed.

Copy strings are verbatim, **typos included** ("artcile", "calendadr", "MPV Planner", "Llly").
Notes before building from it:
- Several labels are **Roboto**, which is NOT a shipped font family here — treat as Inter unless
  Greg says otherwise.
- `#3A4A2A` and `#4B4B4B` appear in these frames and are **not** in the Hearth token set — check
  contrast (`tools/lint-design-tokens.py`) before adopting either.
- The invite preview shows `share.mvparent.ai`; the shipped default is the Railway domain via
  `CIRCLE_INVITE_BASE_URL`. Domain still undecided.
- Every frame carries the same five-item tab bar (HOME · COACH · PLANNER · CIRCLE · SETTINGS).
  It is already built (`MainTabView.swift`) — the repeated `[Tab Bar]` blocks below are for
  reference, not re-implementation.

## Coverage — read this before trusting the file

**This file covers all 19 frames extracted from the page.** The ids are listed so a reader
can tell *coverage* from *completeness* without opening Figma. (The sprint-1 spec once claimed
authority over 13 of 31 screens; that is why this section is mandatory and guarded by
`tests/test_design_spec_coverage.py`. If you re-extract: **deep-fetch frame ids in batches, never the
page id alone** — a `/nodes` call on a page returns child names with no nested content.)

| node id | frame |
|---|---|
| `1007:3914` | artcile 01 |
| `754:5810` | Circle-000 |
| `754:5882` | Circle-001 |
| `754:5898` | Circle-002 |
| `754:5827` | Circle-003 |
| `754:5693` | Circle-004 |
| `754:5947` | Circle-005 |
| `754:5568` | coach-000 |
| `1008:4717` | coach-001 |
| `754:5520` | coach-002 |
| `754:6023` | contacts |
| `754:6094` | invite preview |
| `754:5987` | invite preview |
| `1026:10476` | planner 01 |
| `1026:10520` | planner 02 |
| `1026:10543` | planner 3 |
| `1026:10608` | planner 4 |
| `1026:10766` | planner 5 |
| `1026:10680` | planner 6 |


---


====================================================================================================
FRAME artcile 01 — `1007:3914` — 440.0x2515.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Frame 14] FRAME 380.0x2270.0 V gap15.0 pad10.0/0/20.0/0 vy:FIXE hz:FIXE
    [Frame 204973878] FRAME 380.0x32.0 H gap10.0 vy:HUG hz:FILL
      [Frame] FRAME 37.3x32.0 H gap13.3 pad4.0/6.7/4.0/6.7 vy:HUG hz:HUG
        [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 14.0x18.0 #C8C3B8
    TEXT "WE TRIED IT · Ages 3–7 · 4 min"  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
    TEXT "A rainy Saturday, nothing bought"  [Fraunces w700 38.0/40.0 ls-0.38 L #1E1E1E]
    TEXT "Four things to do with tape, a bedsheet, and whatever's in the recycling."  [Inter w400 15.0/22.0 ls0.0 L #1E1E1E]
    [Rectangle 1] RECTANGLE 378.0x290.0 fill=#151412 vy:FIXE hz:FIXE
    TEXT "It's 9:40am, it's raining, and you have maybe seven hours to fill. These four are in order of how long they last."  [Fraunces w400 22.0/33.0 ls0.0 L #2B2925]
    [Frame 204973914] FRAME 380.0x270.0 V gap12.0 vy:HUG hz:FILL
      TEXT "1. tape roads"  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
      TEXT "You need: painter's tape. Buys you: forty minutes, sometimes two hours. Lay roads across the floor — around the couch, under the table, up one wall. Then hand over the cars and leave. The building is the activity; the driving is the bonus. Where it goes wrong: regular masking tape pulls up finish on wood floors. Painter's tape only."  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
    [Frame 204973915] FRAME 380.0x570.0 V gap12.0 vy:HUG hz:FILL
      TEXT "2. The box that becomes something"  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
      TEXT "You need:  one large cardboard box, a marker. Buys you: thirty minutes, plus a week of it living in your hallway.  Don't tell them what it is. Ask them. A four-year-old will make a decision faster than you will. Where it goes wrong: if you cut the windows yourself, it becomes your project. Let it be ugly."  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
      [Rectangle 1] RECTANGLE 378.0x290.0 fill=#151412 vy:FIXE hz:FIXE
    [Frame 204973916] FRAME 380.0x270.0 V gap12.0 vy:HUG hz:FILL
      TEXT "3. bedsheet fort, with a rule"  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
      TEXT "You need: painter's tape. Buys you: forty minutes, sometimes two hours. Lay roads across the floor — around the couch, under the table, up one wall. Then hand over the cars and leave. The building is the activity; the driving is the bonus. Where it goes wrong: regular masking tape pulls up finish on wood floors. Painter's tape only."  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
    [Frame 204973917] FRAME 380.0x270.0 V gap12.0 vy:HUG hz:FILL
      TEXT "4. floor is lava, timed"  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
      TEXT "You need: painter's tape. Buys you: forty minutes, sometimes two hours. Lay roads across the floor — around the couch, under the table, up one wall. Then hand over the cars and leave. The building is the activity; the driving is the bonus. Where it goes wrong: regular masking tape pulls up finish on wood floors. Painter's tape only."  [Inter w900 24.0/24.0 ls0.0 L #2B2925]
    [Frame 65] FRAME 376.0x143.0 V gap10.0 pad0/0/20.0/0 vy:FILL hz:FIXE
      TEXT "Miguel Alvarado · tested on an actual rainy Saturday with his two little ones in San Francisco"  [Inter w300 12.0/22.0 ls0.0 C #1E1E1E]
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973889] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/20.0/20.0/20.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 399.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973918] FRAME 187.0x26.0 H gap6.0 vy:FIXE hz:HUG
        [stamp] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 6.0x11.0 
          <Vector> VECTOR 16.0x5.0 
          <Vector> VECTOR 14.0x0.0 
        [Frame 204973887] FRAME 157.0x26.0 H gap13.0 vy:HUG hz:HUG
          TEXT "MVP Recommends"  [Inter w700 17.0/26.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME Circle-000 — `754:5810` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
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
  [Frame 14] FRAME 380.0x300.0 V gap15.0 vy:HUG hz:FIXE
    [Vector] INSTANCE 86.0x71.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 86.0x71.0 #1D7FA6
    TEXT "Gather your circle"  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
    TEXT "Your circle are the people who show up for Ben & Lily — grandparents, sitters, close friends. bring them into one place."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 65] FRAME 376.0x78.0 V gap10.0 vy:FIXE hz:FIXE
      [button] INSTANCE 238.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FIXE
        TEXT "Invite someone"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]

====================================================================================================
FRAME planner 01 — `1026:10476` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
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
  [Frame 14] FRAME 380.0x272.0 V gap13.0 pad20.0/0/0/0 vy:HUG hz:FIXE
    [planner-xl] INSTANCE 48.0x48.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 36.0x40.0 #1B7498
    TEXT "MPV Planner"  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
    [Segmented control] INSTANCE 358.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FIXE
      [Button 1] FRAME 175.0x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
        [Frame 66] FRAME 57.0x26.0 H gap10.0 vy:FIXE hz:HUG
          [planner edit] INSTANCE 19.0x19.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.8x15.8 #1B7498
          TEXT "Plan"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
      [Button 3] FRAME 175.0x32.0 H pad3.0/6.0/3.0/6.0 vy:FILL hz:FILL
        [Frame 67] FRAME 118.0x24.0 H gap3.0 vy:HUG hz:HUG
          [coach] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            [Layer_1] FRAME 12.1x14.9
              <Vector> VECTOR 6.0x5.9 #1B7498
              <Vector> VECTOR 1.9x1.9 #1B7498
              <Vector> VECTOR 1.2x1.2 #1B7498
              <Vector> VECTOR 5.3x6.7 #1B7498
              <Vector> VECTOR 6.5x6.5 #1B7498
          TEXT "Ask the coach"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
    [Frame 204973900] FRAME 380.0x89.0 H gap10.0 pad20.0/0/0/0 vy:HUG hz:HUG
      TEXT "Nothing planned yet? ⏎ Find a few options — nothing is booked or shared until you say so."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
  [Frame 204973799] FRAME 380.0x174.0 fill=#F5F3EF V gap8.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973867] FRAME 362.0x20.0 H gap10.0 pad0/9.0/0/9.0 vy:HUG hz:FILL
      [seach large] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.0x15.0 #4F5D3A
      TEXT "Find activities"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
    [Frame 204973884] FRAME 357.0x34.0 H gap8.0 vy:HUG hz:HUG
      [Frame 204973882] FRAME 238.0x34.0 fill=#FFFFFF H gap10.0 pad10.0/9.0/10.0/9.0 r12.0 vy:HUG hz:FIXE stroke #DAE0DF 1.0
        [Frame 204973880] FRAME 220.0x14.0 H gap10.0 vy:HUG hz:FILL
          TEXT "Where to:"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
          TEXT "Zip code..."  [Inter w400 14.0/14.0 ls-0.14 L #DAE0DF]
      [Frame 204973883] FRAME 111.0x34.0 fill=#FFFFFF H gap10.0 pad10.0/9.0/10.0/9.0 r12.0 vy:HUG hz:FIXE stroke #DAE0DF 1.0
        [Frame 204973880] FRAME 93.0x14.0 H gap10.0 vy:HUG hz:FILL
          TEXT "25 mi"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
          [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 12.0x6.0 
    [Frame 204973881] FRAME 362.0x39.0 H gap4.0 vy:HUG hz:FILL
      [tag item] INSTANCE 86.1x39.0 fill=#1B7498 H gap8.0 pad11.0/14.7/11.0/14.7 r22.016000747680664 vy:HUG hz:FILL
        [Frame 5] FRAME 54.2x17.0 H gap3.7 vy:HUG hz:HUG
          [camp] INSTANCE 16.5x16.5 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.1x10.6 #F5F3EF
          TEXT "Camp"  [Inter w400 11.925333976745605/16.5 ls0.0 C #F5F3EF]
      [tag item] INSTANCE 88.0x39.0 fill=#FCFBF8 H gap8.0 pad11.0/14.7/11.0/14.7 r22.016000747680664 vy:HUG hz:FILL stroke #1B7498 0.9173333644866943
        [Frame 5] FRAME 63.2x17.0 H gap3.7 vy:HUG hz:HUG
          [camp] INSTANCE 16.5x16.5 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.1x10.6 #1B7498
          TEXT "Activity"  [Inter w400 11.925333976745605/16.5 ls0.0 C #1B7498]
      [tag item] INSTANCE 88.0x39.0 fill=#FCFBF8 H gap8.0 pad11.0/14.7/11.0/14.7 r22.016000747680664 vy:HUG hz:FILL stroke #1B7498 0.9173333644866943
        [Frame 5] FRAME 42.2x17.0 H gap3.7 vy:HUG hz:HUG
          [location] INSTANCE 16.5x16.5 vy:FIXE hz:FIXE
            <Vector> VECTOR 11.0x13.8 #1B7498
          TEXT "Trip"  [Inter w400 11.925333976745605/16.5 ls0.0 C #1B7498]
      [tag item] INSTANCE 88.0x39.0 fill=#FCFBF8 H gap8.0 pad11.0/14.7/11.0/14.7 r22.016000747680664 vy:HUG hz:FILL stroke #1B7498 0.9173333644866943
        [Frame 5] FRAME 64.2x17.0 H gap3.7 vy:HUG hz:HUG
          [schoolwork] INSTANCE 16.5x16.5 vy:FIXE hz:FIXE
            <Vector> VECTOR 9.4x9.4 #1B7498
          TEXT "Classes"  [Inter w400 11.925333976745605/16.5 ls0.0 C #1B7498]
    [tag item] INSTANCE 362.0x39.0 fill=#1B7498 H gap8.0 pad11.0/14.7/11.0/14.7 r22.016000747680664 vy:HUG hz:FILL
      [Frame 5] FRAME 78.0x17.0 H gap3.7 vy:HUG hz:HUG
        TEXT "Find activities"  [Inter w400 11.925333976745605/16.5 ls0.0 C #F5F3EF]
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973800] FRAME 380.0x76.0 fill=#F5F3EF V gap-18.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973885] FRAME 340.0x36.0 H gap10.0 vy:HUG hz:FILL
      [camera] INSTANCE 18.0x16.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.0x16.0 #1B7498
      TEXT "Paste a camp email or snap a flyer —  I'll pull out the details and track it."  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
  [Frame 204973886] FRAME 380.0x46.0 V gap6.0 vy:HUG hz:FIXE
    TEXT "Planning for Ben & Lily"  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    TEXT "Edit kids and interests"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]

====================================================================================================
FRAME coach-000 — `754:5568` — 440.0x813.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
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
  [Frame 14] FRAME 380.0x410.0 V gap15.0 vy:HUG hz:FIXE
    [coach] INSTANCE 80.0x80.0 vy:FIXE hz:FIXE
      [Layer_1] FRAME 54.0x66.4
        <Vector> VECTOR 26.8x26.2 #1B7498
        <Vector> VECTOR 8.6x8.4 #1B7498
        <Vector> VECTOR 5.4x5.2 #1B7498
        <Vector> VECTOR 23.6x29.6 #1B7498
        <Vector> VECTOR 28.7x28.9 #1B7498
    TEXT "Meet your coach"  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
    TEXT "Sleep, tantrums, dinner, the days that feel like too much. your coach knows Ben and Llly and remembers what you've already tried."  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 65] FRAME 376.0x158.0 V gap10.0 vy:HUG hz:FIXE
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "Easy dinner ideas for tonight"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "Bedtime is a fight right now"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "How do I talk to Lily about..."  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  [chatinput] INSTANCE 440.0x70.0 fill=#0A5570 H pad12.0/18.0/12.0/18.0 r16.0,16.0,0.0,0.0 vy:HUG hz:FIXE
    [icon.attach] INSTANCE 33.1x33.1 vy:FIXE hz:FIXE
      <Vector> VECTOR 26.3x26.3 #FFFFFF
    [input] FRAME 370.9x46.0 fill=#FFFFFF H gap15.0 pad12.0/16.0/12.0/16.0 r8.0 vy:HUG hz:FILL
      TEXT "Ask the coach for help"  [Inter w400 14.0/16.9 ls0.0 L #BCBCBC]
      [icon.microphone] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 19.8x20.1 #3D6B3D
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
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
FRAME planner 02 — `1026:10520` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
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
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 14] FRAME 380.0x506.0 V gap13.0 pad20.0/0/0/0 vy:HUG hz:FIXE
    [planner-xl] INSTANCE 48.0x48.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 36.0x40.0 #1B7498
    TEXT "MPV Planner"  [Fraunces w700 38.0/40.0 ls-0.38 C #1E1E1E]
    [Segmented control] INSTANCE 358.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FIXE
      [Button 1] FRAME 175.0x32.0 H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
        [Frame 66] FRAME 57.0x26.0 H gap10.0 vy:FIXE hz:HUG
          [planner edit] INSTANCE 19.0x19.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.8x15.8 #1B7498
          TEXT "Plan"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
      [Button 3] FRAME 175.0x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r100.0 vy:FILL hz:FILL
        [Frame 67] FRAME 118.0x24.0 H gap3.0 vy:HUG hz:HUG
          [coach] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            [Layer_1] FRAME 12.1x14.9
              <Vector> VECTOR 6.0x5.9 #1B7498
              <Vector> VECTOR 1.9x1.9 #1B7498
              <Vector> VECTOR 1.2x1.2 #1B7498
              <Vector> VECTOR 5.3x6.7 #1B7498
              <Vector> VECTOR 6.5x6.5 #1B7498
          TEXT "Ask the coach"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
    TEXT "Ask the coach ⏎ Find camps, sort out coverage gaps, or decide between options. I see the whole family plan. ⏎ "  [Inter w400 15.0/22.0 ls0.0 C #1E1E1E]
    [Frame 65] FRAME 376.0x214.0 V gap10.0 vy:HUG hz:FIXE
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "Camps & school breaks"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "Classes & sports "  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "Weekend outings"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
      [button] INSTANCE 376.0x46.0 fill=#1B7498 V gap10.0 pad12.0/159.0/12.0/159.0 r12.0 vy:HUG hz:FILL
        TEXT "Family trips — dates, packing, not bookings"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  [chatinput] INSTANCE 440.0x70.0 fill=#0A5570 H pad12.0/18.0/12.0/18.0 r16.0,16.0,0.0,0.0 vy:HUG hz:FIXE
    [icon.attach] INSTANCE 33.1x33.1 vy:FIXE hz:FIXE
      <Vector> VECTOR 26.3x26.3 #FFFFFF
    [input] FRAME 370.9x46.0 fill=#FFFFFF H gap15.0 pad12.0/16.0/12.0/16.0 r8.0 vy:HUG hz:FILL
      TEXT "Just ask if you already have an idea"  [Inter w400 14.0/16.9 ls0.0 L #BCBCBC]
      [icon.microphone] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 19.8x20.1 #3D6B3D

====================================================================================================
FRAME invite preview — `754:6094` — 440.0x874.0 fill=#E9E4DC 
====================================================================================================
  [Frame 204973790] FRAME 440.0x102.0 V gap10.0 vy:FIXE hz:FIXE
    [Global Button] INSTANCE 343.0x35.0 fill=#A4A4A4 H gap8.0 pad8.0/16.0/8.0/16.0 r8.0 vy:HUG hz:FIXE
      TEXT "Invite selected"  [Roboto w600 16.0/18.8 ls0.0 L #FFFFFF]
  [Frame 204973826] FRAME 438.0x259.0 V gap12.0 pad30.0/30.0/30.0/30.0 vy:HUG hz:FIXE
    TEXT "Add contacts"  [Roboto w700 20.0/23.4 ls0.0 L #4B4B4B]
    [Frame 204973682] FRAME 221.0x32.0 H gap8.0 vy:FIXE hz:FIXE
      [Contacts] INSTANCE 32.0x32.0 r133.33334350585938 vy:FIXE hz:FIXE
        <Vector> VECTOR 21.3x13.3 #7D7D7D
      TEXT "add contact"  [Roboto w400 17.0/25.5 ls0.0 L #3D6B3D]
    [Frame 204973796] FRAME 221.0x32.0 H gap8.0 vy:FIXE hz:FIXE
      [import] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
        [Group] GROUP 17.8x21.3
          <Vector> VECTOR 17.8x16.1 #3D6B3D
          <Vector> VECTOR 8.1x14.6 #3D6B3D
      TEXT "Import CSV"  [Roboto w400 17.0/25.5 ls0.0 L #3D6B3D]
    [Frame 204973797] FRAME 221.0x32.0 H gap8.0 vy:FIXE hz:FIXE
      [Frame 204973863] FRAME 29.0x21.3 H gap10.0 vy:HUG hz:FIXE
        [linkedin] INSTANCE 21.3x21.3 vy:FIXE hz:FIXE
          <Vector> VECTOR 21.3x21.3 #0A5570
          [Group] GROUP 12.0x11.8
            <Vector> VECTOR 3.0x11.8 #FEFFFC
            <Vector> VECTOR 7.8x8.0 #FEFFFC
      TEXT "Connect to LinkedIn"  [Roboto w400 17.0/25.5 ls0.0 L #3D6B3D]
    [Frame 204973795] FRAME 378.0x32.0 H gap8.0 vy:HUG hz:FILL
      [Frame 204973794] FRAME 173.0x32.0 H gap8.0 vy:HUG hz:HUG
        [copy link] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 13.0x17.0 #3D6B3D
        TEXT "Copy link to invite"  [Roboto w400 17.0/25.5 ls0.0 L #3D6B3D]
      [Frame] FRAME 24.0x24.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.0x14.0 
        <Vector> VECTOR 6.0x6.0 
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973889] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973890] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME coach-001 — `1008:4717` — 440.0x1145.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
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
  [Frame 204973850] FRAME 362.0x768.0 V gap16.0 vy:HUG hz:HUG
    [user] FRAME 324.0x50.0 H vy:HUG hz:HUG
      [Frame 204973406] FRAME 324.0x50.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:HUG
        TEXT "I need help with dinner ideas for Ben & Lily"  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
    [coach] FRAME 362.0x77.0 V gap10.0 vy:HUG hz:FIXE
      [Frame 204973731] FRAME 362.0x77.0 H vy:FIXE hz:FILL
        [Frame 204973719] FRAME 362.0x77.0 H vy:FIXE hz:FILL
          [Frame 204973406] FRAME 362.0x66.0 H gap16.0 pad16.0/0/16.0/0 r12.0,12.0,12.0,8.0 vy:FIXE hz:FILL
            TEXT "Got it. quick question — are they picky, or open to trying new things tonight?""  [Roboto w400 14.0/18.2 ls0.0 L #696969]
    [user] FRAME 324.0x68.0 H vy:HUG hz:HUG
      [Frame 204973406] FRAME 324.0x68.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:HUG
        TEXT "Ben will eat anything. Lily's going through a beige-food phase."  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
    [coach] FRAME 362.0x77.0 V gap10.0 vy:HUG hz:FIXE
      TEXT "classic. here's one that usually works for both — deconstructed, so Lily can keep things separate and Ben can pile it on."  [Roboto w400 14.0/18.2 ls0.0 L #696969]
    [coach] FRAME 362.0x432.0 fill=#F5F3EF V gap10.0 pad20.0/20.0/20.0/20.0 r16.0 vy:HUG hz:FIXE
      [Frame 204973879] FRAME 322.0x392.0 V vy:HUG hz:FILL
        [Frame 204973878] FRAME 322.0x32.0 H gap10.0 vy:HUG hz:FILL
          [Frame] FRAME 37.3x32.0 H gap13.3 pad4.0/6.7/4.0/6.7 vy:HUG hz:HUG
            [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 14.0x18.0 #DAE0DF
        TEXT "Sheet-pan chicken and veggie tacos Serves 4, 25 minutes ⏎ 500g chicken thighs, cut into strips ⏎ 1 bell pepper, sliced ⏎ 1 zucchini, sliced ⏎ 2 tsp cumin ⏎ 1 tsp paprika ⏎ olive oil, salt ⏎ 8 small tortillas ⏎ toppings on the side: shredded cheese, sour cream, lime ⏎ toss chicken and veggies with oil and spices, spread on a sheet pan, roast at 220°C for 18–20 minutes. serve everything separately so Lily can build a plain tortilla with just chicken and cheese, and Ben can load his up. ⏎ Want me to save this one, or find a few more like it?"  [Inter w400 14.0/18.2 ls0.0 L #2D2D2D]
  [Frame 204973876] FRAME 386.0x57.0 H gap10.0 pad0/10.0/20.0/10.0 vy:HUG hz:FIXE stroke #585853 1.0
    [Frame 204973877] FRAME 37.0x37.0 H gap10.0 vy:HUG hz:HUG
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
    [Frame 204973871] FRAME 319.0x14.0 H gap10.0 pad0/10.0/0/10.0 vy:HUG hz:FILL
      TEXT "Dinner plans for the kids"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
  [chatinput] INSTANCE 440.0x70.0 fill=#0A5570 H pad12.0/18.0/12.0/18.0 r16.0,16.0,0.0,0.0 vy:HUG hz:FIXE
    [icon.attach] INSTANCE 33.1x33.1 vy:FIXE hz:FIXE
      <Vector> VECTOR 26.3x26.3 #FFFFFF
    [input] FRAME 370.9x46.0 fill=#FFFFFF H gap15.0 pad12.0/16.0/12.0/16.0 r8.0 vy:HUG hz:FILL
      TEXT "I need help with dinner ideas for Ben & Lily"  [Inter w400 14.0/16.9 ls0.0 L #000000]
      [icon.microphone] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 19.8x20.1 #3D6B3D
  [Frame 204973881] FRAME 53.0x24.0 H gap5.0 vy:HUG hz:HUG
    [Frame] FRAME 24.0x24.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 20.1x18.5 #6E6A62
    [Frame] FRAME 24.0x24.0 vy:FIXE hz:FIXE
      <Vector> VECTOR 20.1x18.5 #6E6A62
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
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
FRAME planner 3 — `1026:10543` — 440.0x863.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973892] FRAME 439.0x659.0 V gap10.0 pad20.0/20.0/20.0/20.0 vy:FIXE hz:FIXE
    [Frame 204973891] FRAME 399.0x623.7 V gap10.0 vy:HUG hz:FILL
      [Segmented control] INSTANCE 399.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
        [Button 1] FRAME 195.5x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
          [Frame 66] FRAME 57.0x26.0 H gap10.0 vy:FIXE hz:HUG
            [planner edit] INSTANCE 19.0x19.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 15.8x15.8 #1B7498
            TEXT "Plan"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
        [Button 3] FRAME 195.5x32.0 H pad3.0/6.0/3.0/6.0 vy:FILL hz:FILL
          [Frame 67] FRAME 118.0x24.0 H gap3.0 vy:HUG hz:HUG
            [coach] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
              [Layer_1] FRAME 12.1x14.9
                <Vector> VECTOR 6.0x5.9 #1B7498
                <Vector> VECTOR 1.9x1.9 #1B7498
                <Vector> VECTOR 1.2x1.2 #1B7498
                <Vector> VECTOR 5.3x6.7 #1B7498
                <Vector> VECTOR 6.5x6.5 #1B7498
            TEXT "Ask the coach"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973900] FRAME 399.0x76.0 fill=#F5F3EF V gap-18.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
        [Frame 204973890] FRAME 340.0x36.0 H gap20.0 vy:HUG hz:HUG
          [Frame 204973885] FRAME 266.0x36.0 H gap10.0 vy:HUG hz:FIXE stroke #E9E4DC 1.0
            TEXT "2 next steps this week ⏎ $0 confirmed · 1 cost TBD · 2 tracked"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
          [Frame 204973886] FRAME 54.0x18.0 H gap10.0 vy:HUG hz:HUG
            TEXT "View"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
            [back arrow] INSTANCE 14.0x11.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 5.8x11.0 
              <Vector> VECTOR 14.0x0.0 
      [Frame 204973901] FRAME 399.0x36.0 V gap10.0 vy:HUG hz:FILL
        [Segmented control] INSTANCE 171.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FIXE
          [Button 1] FRAME 81.5x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
            [Frame 66] FRAME 24.0x26.0 H gap10.0 vy:FIXE hz:HUG
              TEXT "List"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
          [Button 3] FRAME 81.5x32.0 H pad3.0/6.0/3.0/6.0 vy:FILL hz:FILL
            [Frame 67] FRAME 55.0x18.0 H gap3.0 vy:HUG hz:HUG
              TEXT "Timeline"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973899] FRAME 399.0x34.7 H gap6.0 vy:HUG hz:FILL
        [tag choice] INSTANCE 45.8x34.7 fill=#1B7498 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #E9E4DC 0.8195489048957825
          [Frame 5] FRAME 13.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "All"  [Inter w400 10.654135704040527/14.8 ls0.0 C #F5F3EF]
        [tag choice] INSTANCE 55.8x34.7 fill=#FCFBF8 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
          [Frame 5] FRAME 23.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "New"  [Inter w400 10.654135704040527/14.8 ls0.0 C #1B7498]
        [tag choice] INSTANCE 94.8x34.7 fill=#FCFBF8 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
          [Frame 5] FRAME 62.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "Deciding (3)"  [Inter w400 10.654135704040527/14.8 ls0.0 C #1B7498]
        [tag choice] INSTANCE 115.8x34.7 fill=#FCFBF8 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
          [Frame 5] FRAME 83.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "Needs action (1)"  [Inter w400 10.654135704040527/14.8 ls0.0 C #1B7498]
      [Frame 204973800] FRAME 399.0x92.0 fill=#F5F3EF H gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
        [Frame 204973867] FRAME 297.0x52.0 H gap10.0 pad0/9.0/0/9.0 vy:HUG hz:FIXE
          [seach large] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.0x15.0 #4F5D3A
          [Frame 204973902] FRAME 268.0x52.0 V gap10.0 vy:HUG hz:FIXE
            TEXT "Find more activities"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
            TEXT "98332 · 25 mi · camps, classes & more ⏎ "  [Inter w400 14.0/14.0 ls-0.14 L #3A4A2A]
        [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 12.0x6.0 
      [Frame 204973801] FRAME 399.0x221.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:FIXE hz:FILL
        [Frame 204973895] FRAME 209.0x30.0 H gap10.0 vy:HUG hz:HUG
          [Frame 204973893] FRAME 102.0x30.0 H gap10.0 r100.0 vy:HUG hz:HUG
            [Frame 204973894] FRAME 102.0x30.0 fill=#DAE0DF H pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
              TEXT "Lily & Ben"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
          [Frame 204973894] FRAME 97.0x30.0 fill=#F5EAD2 H gap10.0 pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
            TEXT "Deciding"  [Inter w700 13.0/18.0 ls0.0 L #6F6A60]
        [Frame 204973896] FRAME 359.0x89.0 V gap3.0 vy:HUG hz:FILL
          [Frame 204973898] FRAME 359.0x47.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            [Frame 204973897] FRAME 359.0x36.0 H gap3.0 vy:HUG hz:FILL
              [Frame 204973885] FRAME 245.0x36.0 H gap10.0 vy:HUG hz:FILL
                TEXT "University Place 3-Day Sports Mini Camps"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
              [Frame 204973895] FRAME 111.0x30.0 H gap10.0 r100.0 vy:HUG hz:FIXE
                [Frame 204973894] FRAME 68.0x30.0 fill=#DAE0DF H pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
                  TEXT "75%"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
          TEXT "Camp · YMCA / City of University Place"  [Inter w400 13.0/18.0 ls0.0 L #6E6A62]
          TEXT "Gig Harbor · Jun 22 – Aug 28"  [Inter w400 13.0/18.0 ls0.0 L #6E6A62]
        [Frame 204973899] FRAME 235.0x42.0 H gap10.0 vy:HUG hz:HUG
          [tag choice] INSTANCE 105.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:HUG stroke #E9E4DC 1.0
            [Frame 5] FRAME 73.0x18.0 H gap9.0 vy:HUG hz:HUG
              [check] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 14.0x10.5 #F5F3EF
              TEXT "Planned"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
          [tag choice] INSTANCE 120.0x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:HUG stroke #1B7498 1.0
            [Frame 5] FRAME 88.0x18.0 H gap9.0 vy:HUG hz:HUG
              TEXT "Ask the coach"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973903] FRAME 238.0x68.0 V gap10.0 pad20.0/0/0/0 vy:HUG hz:HUG
        [button] INSTANCE 238.0x48.0 fill=#1B7498 H gap10.0 pad12.0/159.0/12.0/159.0 r100.0 vy:HUG hz:FIXE
          [addcircle] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 20.0x20.0 #F5F3EF
          TEXT "Plan something new"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973889] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 198.0x32.0 H gap13.0 vy:HUG hz:HUG
        [planner-xl] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.0x26.7 #1B7498
        TEXT "MPV Planner"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME coach-002 — `754:5520` — 440.0x813.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
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
  [Frame 204973796] FRAME 380.0x123.0 fill=#F5F3EF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973868] FRAME 362.0x36.0 H gap10.0 vy:HUG hz:FILL
      [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
        [dots] GROUP 16.0x4.0
          <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
    [Frame 204973867] FRAME 362.0x87.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
      [Frame 204973880] FRAME 344.0x67.0 H gap10.0 vy:HUG hz:FILL
        [Frame 204973798] FRAME 296.7x67.0 V gap9.0 vy:HUG hz:FILL
          TEXT "Dinner plans for the kids"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
          TEXT "sheet-pan tacos worked for both kids — saved for next week"  [Inter w400 15.0/22.0 ls0.0 L #575757]
        [Frame] FRAME 37.3x32.0 H gap13.3 pad4.0/6.7/4.0/6.7 vy:HUG hz:HUG
          [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 14.0x18.0 #1B7498
  [Frame 204973797] FRAME 380.0x107.0 fill=#F5F3EF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973868] FRAME 362.0x36.0 H gap10.0 vy:HUG hz:FILL
      [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
        [dots] GROUP 16.0x4.0
          <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
    [Frame 204973867] FRAME 362.0x71.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
      [Frame 204973880] FRAME 344.0x51.0 H gap10.0 vy:HUG hz:FILL
        [Frame 204973798] FRAME 344.0x51.0 V gap9.0 vy:HUG hz:FILL
          TEXT "Kelsy's birthday party"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
          TEXT "Gift ideas for 5-year old girls"  [Inter w400 15.0/22.0 ls0.0 L #575757]
  [Frame 204973798] FRAME 380.0x107.0 fill=#F5F3EF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973868] FRAME 362.0x36.0 H gap10.0 vy:HUG hz:FILL
      [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
        [dots] GROUP 16.0x4.0
          <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
    [Frame 204973867] FRAME 362.0x71.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
      [Frame 204973880] FRAME 344.0x51.0 H gap10.0 vy:HUG hz:FILL
        [Frame 204973798] FRAME 344.0x51.0 V gap9.0 vy:HUG hz:FILL
          TEXT "Dinner advice"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
          TEXT "3 dinner ideas, no beige-food fights"  [Inter w400 15.0/22.0 ls0.0 L #575757]
  [Frame 204973799] FRAME 380.0x107.0 fill=#F5F3EF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973868] FRAME 362.0x36.0 H gap10.0 vy:HUG hz:FILL
      [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
        [dots] GROUP 16.0x4.0
          <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
    [Frame 204973867] FRAME 362.0x71.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
      [Frame 204973880] FRAME 344.0x51.0 H gap10.0 vy:HUG hz:FILL
        [Frame 204973798] FRAME 344.0x51.0 V gap9.0 vy:HUG hz:FILL
          TEXT "Bedtime battles"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
          TEXT "talked through Lily's bedtime pushback"  [Inter w400 15.0/22.0 ls0.0 L #575757]
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
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
FRAME invite preview — `754:5987` — 440.0x874.0 fill=#E9E4DC 
====================================================================================================
  [Frame 204973790] FRAME 440.0x102.0 V gap10.0 vy:FIXE hz:FIXE
    [Global Button] INSTANCE 343.0x35.0 fill=#A4A4A4 H gap8.0 pad8.0/16.0/8.0/16.0 r8.0 vy:HUG hz:FIXE
      TEXT "Invite selected"  [Roboto w600 16.0/18.8 ls0.0 L #FFFFFF]
  [Frame 204973827] FRAME 440.0x595.0 V gap12.0 pad30.0/30.0/30.0/30.0 vy:HUG hz:FIXE
    TEXT "Contacts"  [Inter w700 20.0/24.2 ls0.0 L #4B4B4B]
    [Frame 204973682] FRAME 221.0x32.0 H gap8.0 vy:FIXE hz:FIXE
      [Contacts] INSTANCE 32.0x32.0 r133.33334350585938 vy:FIXE hz:FIXE
        <Vector> VECTOR 21.3x13.3 #6B6B6B
      TEXT "add contact"  [Roboto w400 17.0/25.5 ls0.0 L #6B6B6B]
    [Frame 204973791] FRAME 380.0x455.0 V gap8.0 vy:FIXE hz:FILL
      [Frame 204973795] FRAME 380.0x32.0 H gap8.0 vy:HUG hz:FILL
        [Frame 204973794] FRAME 173.0x32.0 H gap8.0 vy:HUG hz:HUG
          [copy link] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 9.0x11.0 #3A4A2A
          TEXT "Copy link to invite"  [Roboto w400 17.0/25.5 ls0.0 L #3A4A2A]
        [Frame] FRAME 24.0x24.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.0x14.0 
          <Vector> VECTOR 6.0x6.0 
      [Frame 204973796] FRAME 380.0x440.0 fill=#F5F3EF V gap10.0 pad24.0/24.0/24.0/24.0 r12.0 vy:FIXE hz:FILL stroke #A4A4A4 1.0
        TEXT "https://share.mvparent.ai/invite"  [Roboto w400 12.0/18.0 ls0.0 L #575757]
        [Frame 204973799] FRAME 332.0x341.0 V gap10.0 pad16.0/16.0/16.0/16.0 vy:HUG hz:FILL
          [Frame 204973798] FRAME 300.0x116.0 V gap3.0 vy:FIXE hz:FILL
            TEXT "share.mvparent.ai"  [Inter w600 14.0/14.0 ls0.84 L #3A4A2A]
            TEXT "Greg and Teri invited you to their circle on MVP"  [Inter w500 12.0/18.0 ls0.0 L #575757]
            TEXT "Heather wants you in their circle — a place to share what works for Ben & Lily." ⏎ "  [Inter w400 15.0/22.0 ls0.0 L #575757]
          [Frame 204973797] FRAME 300.0x183.0 fill=#6B6B6B vy:FIXE hz:FILL
            TEXT "MVP"  [Fraunces w700 85.9459457397461/106.0 ls-4.3 R #F5F3EF]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME planner 4 — `1026:10608` — 440.0x1342.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973892] FRAME 439.0x1083.1 V gap10.0 pad20.0/20.0/20.0/20.0 vy:HUG hz:FIXE
    TEXT "CAMP FOR LILY & BENJAMIN"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
    TEXT "Tom Taylor YMCA Summer Day Camp"  [Fraunces w600 24.0/32.0 ls0.0 L #1E1E1E]
    TEXT "YMCA of Pierce and Kitsap Counties"  [Inter w400 14.0/14.0 ls-0.14 L #3A4A2A]
    [Frame 204973911] FRAME 398.6x28.1 V gap9.3 vy:HUG hz:HUG
      [Frame 204973895] FRAME 398.6x28.1 H gap9.3 vy:HUG hz:HUG
        [Frame 204973893] FRAME 94.0x28.1 H gap9.3 r92.57540893554688 vy:HUG hz:HUG
          [Frame 204973894] FRAME 94.0x28.1 fill=#DAE0DF H pad5.6/18.5/5.6/18.5 r92.57540893554688 vy:HUG hz:HUG
            TEXT "Lily & Ben"  [Inter w700 12.03480339050293/16.7 ls0.0 L #1B7498]
        [Frame 204973894] FRAME 183.0x28.1 fill=#F5EAD2 H gap9.3 pad5.6/18.5/5.6/18.5 r92.57540893554688 vy:HUG hz:HUG
          TEXT "Registered, needs action"  [Inter w700 12.03480339050293/16.7 ls0.0 L #6F6A60]
        [Frame 204973894] FRAME 103.0x28.1 fill=#DAE0DF H pad5.6/18.5/5.6/18.5 r92.57540893554688 vy:HUG hz:HUG
          TEXT "75% Match"  [Inter w700 12.03480339050293/16.7 ls0.0 L #1B7498]
    [Frame 204973891] FRAME 399.0x511.0 V gap10.0 vy:HUG hz:FILL
      [Frame 204973801] FRAME 399.0x511.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL
        [Frame 204973896] FRAME 359.0x419.0 V gap3.0 vy:HUG hz:FILL
          [Frame 204973898] FRAME 359.0x33.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            TEXT "FOR"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Lily · fits ages 7–12"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          [Frame 204973899] FRAME 359.0x99.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            TEXT "DATES"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Jun 22 – Aug 28, 2026 ⏎ ⚠ Overlaps Rialto Beach trip, Aug 15–17 ⏎ "  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          [Frame 204973900] FRAME 359.0x121.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            TEXT "SCHEDULE"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "All Week Camp, Mon–Fri; weekly themes, age 7+ specialty add-ons. Registration open through August. ⏎ "  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          [Frame 204973901] FRAME 359.0x99.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            TEXT "LOCATION"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "Tom Taylor Family YMCA 10550 Harbor Hill Dr, Gig Harbor · 6 mi ⏎ "  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
          [Frame 204973902] FRAME 359.0x55.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            TEXT "COST"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
            TEXT "TBD — I'll track it once you register"  [Inter w400 15.0/22.0 ls0.0 L #6E6A62]
        [Frame 204973899] FRAME 235.0x42.0 H gap10.0 vy:HUG hz:HUG
          [tag choice] INSTANCE 105.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:HUG stroke #E9E4DC 1.0
            [Frame 5] FRAME 73.0x18.0 H gap9.0 vy:HUG hz:HUG
              [check] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 14.0x10.5 #F5F3EF
              TEXT "Planned"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
          [tag choice] INSTANCE 120.0x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:HUG stroke #1B7498 1.0
            [Frame 5] FRAME 88.0x18.0 H gap9.0 vy:HUG hz:HUG
              TEXT "Ask the coach"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [Frame 204973904] FRAME 399.0x120.0 fill=#F5F3EF H gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
      [Frame 204973902] FRAME 359.0x80.0 V gap10.0 vy:HUG hz:FILL
        TEXT "Why it matched"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
        TEXT "Weekly drop-in fits your flexible-weeks preference, Lily's age band, and it's the closest full-day option to home. ⏎ "  [Inter w400 14.0/14.0 ls-0.14 L #3A4A2A]
    [Frame 204973912] FRAME 399.0x170.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FIXE
      [Frame 204973896] FRAME 359.0x130.0 V gap3.0 vy:HUG hz:FILL
        [Frame 204973898] FRAME 359.0x29.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
          [Frame 204973897] FRAME 359.0x18.0 H gap3.0 vy:HUG hz:FILL
            [Frame 204973885] FRAME 359.0x18.0 H gap10.0 vy:HUG hz:FILL
              TEXT "Still to do"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
        [Frame 204973909] FRAME 359.0x98.0 V gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
          [check circle] INSTANCE 104.0x20.0 H gap6.0 vy:HUG hz:HUG
            [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 16.0x16.0 #1B7498
            TEXT "Register Ben"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
          [check circle] INSTANCE 102.0x20.0 H gap6.0 vy:HUG hz:HUG
            [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 16.0x16.0 #1B7498
            TEXT "Register Lily"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
          [check circle] INSTANCE 213.0x18.0 H gap6.0 vy:HUG hz:HUG
            <Vector> VECTOR 16.0x16.0 #1B7498
            TEXT "Forward the confirmation email"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
    [button] INSTANCE 399.0x48.0 fill=#1B7498 H gap10.0 pad12.0/159.0/12.0/159.0 r100.0 vy:HUG hz:FILL
      [check] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.0x18.0 #F5F3EF
      TEXT "Mark next step done"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  TEXT "Moves to All set once nothing is left. ⏎ "  [Inter w400 14.0/14.0 ls-0.14 C #3A4A2A]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973889] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 pad0/20.0/0/20.0 vy:HUG hz:FILL
      [Frame 204973910] FRAME 235.0x37.0 H gap12.0 vy:HUG hz:FIXE
        [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
          <Vector> VECTOR 7.7x15.4 #1B7498
        [Frame 204973887] FRAME 65.0x26.0 H gap13.0 vy:HUG hz:HUG
          TEXT "Activity"  [Inter w700 17.0/26.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME contacts — `754:6023` — 440.0x874.0 fill=#E9E4DC 
====================================================================================================
  [Frame 204973826] FRAME 440.0x622.0 V gap12.0 pad30.0/20.0/30.0/20.0 vy:FIXE hz:FIXE
    [Frame 204973864] FRAME 400.0x32.0 H gap10.0 vy:HUG hz:FILL
      TEXT "Contacts"  [Roboto w700 20.0/23.4 ls0.0 L #4B4B4B]
      [Frame 204973865] FRAME 66.0x32.0 H gap10.0 vy:HUG hz:HUG
        TEXT "Add"  [Roboto w700 13.0/16.9 ls0.0 L #4B4B4B]
        [add] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
          [group] GROUP 16.0x16.0
            <Vector> VECTOR 16.0x16.0 
            <Vector> VECTOR 6.4x0.0 
            <Vector> VECTOR 0.0x6.4 
    [content] FRAME 400.0x537.0 H gap12.0 pad24.0/0/0/0 vy:HUG hz:FILL
      [all contacts] FRAME 374.0x348.0 V vy:HUG hz:FILL stroke #DAE0DF 1.0
        [contatct] FRAME 374.0x58.0 V pad6.0/20.0/16.0/20.0 vy:HUG hz:FILL
          [Frame 204973788] FRAME 334.0x36.0 H gap12.0 vy:HUG hz:FILL
            [avatar - default] FRAME 36.0x36.0 r100.0 vy:FIXE hz:FIXE
              [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
                TEXT "CN"  [Inter w700 16.0/0.0 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
        [contatct] FRAME 374.0x58.0 V pad6.0/20.0/16.0/20.0 vy:HUG hz:FILL
          [Frame 204973788] FRAME 334.0x36.0 H gap12.0 vy:HUG hz:FILL
            [avatar - default] FRAME 36.0x36.0 r100.0 vy:FIXE hz:FIXE
              [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
                TEXT "CN"  [Inter w700 16.0/0.0 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
        [contatct] FRAME 374.0x58.0 V pad6.0/20.0/16.0/20.0 vy:HUG hz:FILL
          [Frame 204973788] FRAME 334.0x36.0 H gap12.0 vy:HUG hz:FILL
            [avatar - default] FRAME 36.0x36.0 r100.0 vy:FIXE hz:FIXE
              [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
                TEXT "CN"  [Inter w700 16.0/0.0 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
        [contatct] FRAME 374.0x58.0 V pad6.0/20.0/16.0/20.0 vy:HUG hz:FILL
          [Frame 204973788] FRAME 334.0x36.0 H gap12.0 vy:HUG hz:FILL
            [avatar - default] FRAME 36.0x36.0 r100.0 vy:FIXE hz:FIXE
              [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
                TEXT "CN"  [Inter w700 16.0/0.0 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
        [contatct] FRAME 374.0x58.0 V pad6.0/20.0/16.0/20.0 vy:HUG hz:FILL
          [Frame 204973788] FRAME 334.0x36.0 H gap12.0 vy:HUG hz:FILL
            [avatar - default] FRAME 36.0x36.0 r100.0 vy:FIXE hz:FIXE
              [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
                TEXT "CN"  [Inter w700 16.0/0.0 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
        [contatct] FRAME 374.0x58.0 V pad6.0/20.0/16.0/20.0 vy:HUG hz:FILL
          [Frame 204973788] FRAME 334.0x36.0 H gap12.0 vy:HUG hz:FILL
            [avatar - default] FRAME 36.0x36.0 r100.0 vy:FIXE hz:FIXE
              [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
                TEXT "CN"  [Inter w700 16.0/0.0 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
      [quick nav] FRAME 14.0x513.0 V gap10.0 pad0/10.0/0/10.0 vy:FIXE hz:FIXE
        TEXT "A ⏎ B C D E F G H I J K L M N O P Q R S T U V W X Y Z"  [Arial w400 10.0/20.0 ls0.0 L #6B6B6B]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]

====================================================================================================
FRAME planner 5 — `1026:10766` — 440.0x1209.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 14] FRAME 440.0x1076.0 V gap13.0 pad20.0/20.0/0/20.0 vy:FIXE hz:FIXE
    [Segmented control] INSTANCE 400.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
      [Button 1] FRAME 196.0x32.0 H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
        [Frame 66] FRAME 57.0x26.0 H gap10.0 vy:FIXE hz:HUG
          [planner edit] INSTANCE 19.0x19.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.8x15.8 #1B7498
          TEXT "Plan"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
        [Frame 68] FRAME 14.0x14.0 vy:FIXE hz:FIXE
          [chip] FRAME 17.0x13.0 fill=#0A5570 r100.0
            TEXT "2"  [Inter w400 7.0/8.5 ls0.0 C #F5F3EF]
      [Button 3] FRAME 196.0x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r100.0 vy:FILL hz:FILL
        [Frame 67] FRAME 118.0x24.0 H gap3.0 vy:HUG hz:HUG
          [coach] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            [Layer_1] FRAME 12.1x14.9
              <Vector> VECTOR 6.0x5.9 #1B7498
              <Vector> VECTOR 1.9x1.9 #1B7498
              <Vector> VECTOR 1.2x1.2 #1B7498
              <Vector> VECTOR 5.3x6.7 #1B7498
              <Vector> VECTOR 6.5x6.5 #1B7498
          TEXT "Ask the coach"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
    [Frame 204973905] FRAME 362.0x701.0 V gap13.0 pad30.0/0/0/0 vy:HUG hz:HUG
      [user] FRAME 362.0x50.0 H vy:HUG hz:FIXE
        [Frame 204973406] FRAME 324.0x50.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:HUG
          TEXT "What can we do with the kids this weekend?"  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
      [coach] FRAME 362.0x55.0 V gap10.0 vy:HUG hz:FIXE
        [Frame 204973731] FRAME 362.0x55.0 H vy:FIXE hz:FILL
          [Frame 204973719] FRAME 362.0x77.0 H vy:FIXE hz:FILL
            [Frame 204973406] FRAME 362.0x66.0 H gap16.0 pad16.0/0/16.0/0 r12.0,12.0,12.0,8.0 vy:FIXE hz:FILL
              TEXT "Got it. quick question — How much time do you have?"  [Roboto w400 14.0/18.2 ls0.0 L #696969]
      [user] FRAME 362.0x50.0 H vy:HUG hz:FIXE
        [Frame 204973406] FRAME 74.0x50.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:HUG
          TEXT "All day"  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
      [coach] FRAME 362.0x292.0 fill=#F5F3EF V gap10.0 pad20.0/20.0/20.0/20.0 r16.0 vy:HUG hz:FIXE
        [Frame 204973879] FRAME 322.0x210.0 V vy:HUG hz:FILL
          [Frame 204973878] FRAME 322.0x24.0 H gap3.0 vy:HUG hz:FILL
            [Frame] FRAME 37.3x24.0 H gap13.3 pad0/6.7/0/6.7 vy:HUG hz:HUG
              [favorites] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 14.0x18.0 #1B7498
          [Frame 204973907] FRAME 322.0x186.0 V gap9.0 vy:HUG hz:FILL
            [Frame 204973906] FRAME 322.0x42.0 V gap6.0 vy:HUG hz:FILL
              TEXT "Weekend outing with the kids"  [Inter w700 14.0/18.2 ls0.0 L #2D2D2D]
              TEXT "3 family-friendly ideas near 98332:"  [Inter w400 14.0/18.2 ls0.0 L #2D2D2D]
            TEXT " Children's Museum of Tacoma — indoor, sensory-friendly; great rain backup. ⏎ Briscot Farm outing — simple outdoor animal time. ⏎ Salmon run at Ballard Locks — free, low-pressure."  [Inter w400 14.0/18.2 ls0.0 L #2D2D2D]
            TEXT "My pick: the museum if weather turns."  [Inter w400 14.0/18.2 ls0.0 L #2D2D2D]
        [button] INSTANCE 322.0x32.0 fill=#FFFFFF H gap6.7 pad8.0/106.0/8.0/106.0 r66.66667175292969 vy:HUG hz:FILL stroke #1B7498 0.6666666865348816
          [addcircle] INSTANCE 16.0x16.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 13.3x13.3 #1B7498
          TEXT "Add Museum to  calendadr"  [Inter w800 10.666666984558105/14.7 ls0.0 C #1B7498]
      [coach] FRAME 362.0x135.0 fill=#F5F3EF V gap10.0 pad20.0/20.0/20.0/20.0 r16.0 vy:HUG hz:FIXE
        TEXT "Added Children's Museum of Tacoma to the plan for Lily — Saturday, Aug 8 at 11:00 AM, set as a 2-hour outing. "  [Inter w400 14.0/18.2 ls0.0 L #2D2D2D]
        [button] INSTANCE 322.0x31.0 fill=#FFFFFF H gap6.7 pad8.0/106.0/8.0/106.0 r66.66667175292969 vy:HUG hz:FILL stroke #1B7498 0.6666666865348816
          TEXT "View plan"  [Inter w800 10.666666984558105/14.7 ls0.0 C #1B7498]
      [Frame 204973881] FRAME 53.0x24.0 H gap5.0 vy:HUG hz:HUG
        [Frame] FRAME 24.0x24.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x18.5 #6E6A62
        [Frame] FRAME 24.0x24.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 20.1x18.5 #6E6A62
  [Frame 204973889] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 198.0x32.0 H gap13.0 vy:HUG hz:HUG
        [planner-xl] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.0x26.7 #1B7498
        TEXT "MPV Planner"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
  [Frame 204973908] FRAME 440.0x132.0 V vy:HUG hz:FIXE
    [chatinput] INSTANCE 440.0x70.0 fill=#0A5570 H pad12.0/18.0/12.0/18.0 r16.0,16.0,0.0,0.0 vy:HUG hz:FILL
      [icon.attach] INSTANCE 33.1x33.1 vy:FIXE hz:FIXE
        <Vector> VECTOR 26.3x26.3 #FFFFFF
      [input] FRAME 370.9x46.0 fill=#FFFFFF H gap15.0 pad12.0/16.0/12.0/16.0 r8.0 vy:HUG hz:FILL
        TEXT "What can we do with the kids the weekend?"  [Inter w400 14.0/16.9 ls0.0 L #4A4741]
        [icon.microphone] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 19.8x20.1 #3D6B3D
    [Frame 204973904] FRAME 440.0x62.0 fill=#0A5570 H gap6.0 pad10.0/20.0/20.0/50.0 vy:FIXE hz:FILL
      [tag choice] INSTANCE 68.8x34.7 fill=#0A5570 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
        [Frame 5] FRAME 36.0x15.0 H gap7.4 vy:HUG hz:HUG
          TEXT "Camps"  [Inter w400 10.654135704040527/14.8 ls0.0 C #F5F3EF]
      [tag choice] INSTANCE 72.8x34.7 fill=#0A5570 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
        [Frame 5] FRAME 40.0x15.0 H gap7.4 vy:HUG hz:HUG
          TEXT "Classes"  [Inter w400 10.654135704040527/14.8 ls0.0 C #DAE0DF]
      [tag choice] INSTANCE 71.8x34.7 fill=#0A5570 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
        [Frame 5] FRAME 39.0x15.0 H gap7.4 vy:HUG hz:HUG
          TEXT "Outings"  [Inter w400 10.654135704040527/14.8 ls0.0 C #DAE0DF]
      [tag choice] INSTANCE 57.8x34.7 fill=#0A5570 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
        [Frame 5] FRAME 25.0x15.0 H gap7.4 vy:HUG hz:HUG
          TEXT "Trips"  [Inter w400 10.654135704040527/14.8 ls0.0 C #DAE0DF]

====================================================================================================
FRAME Circle-001  — `754:5882` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Frame 204973796] FRAME 380.0x111.0 fill=#F5F3EF V gap10.0 pad24.0/24.0/24.0/24.0 r12.0 vy:FIXE hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973798] FRAME 332.0x71.0 V gap9.0 vy:FIXE hz:FILL
      TEXT "Start the conversation"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
      TEXT "Ask your circle for advice, share a win, or just check in."  [Inter w400 15.0/22.0 ls0.0 L #575757]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]

====================================================================================================
FRAME planner 6 — `1026:10680` — 440.0x1159.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Tab Bar] INSTANCE 440.0x96.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:HUG hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 15.8x17.8 vy:FIXE hz:FIXE
        <Vector> VECTOR 15.8x17.8 #1B7498
      TEXT "HOME"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 3] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [coach] INSTANCE 18.0x18.0 vy:FIXE hz:FIXE
        [Layer_1] FRAME 12.1x14.9
          <Vector> VECTOR 6.0x5.9 #1B7498
          <Vector> VECTOR 1.9x1.9 #1B7498
          <Vector> VECTOR 1.2x1.2 #1B7498
          <Vector> VECTOR 5.3x6.7 #1B7498
          <Vector> VECTOR 6.5x6.5 #1B7498
      TEXT "COACH"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 5] FRAME 84.0x55.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [Vector] INSTANCE 18.6x20.6 vy:FIXE hz:FIXE
        <Vector> VECTOR 18.6x20.6 #1B7498
      TEXT "Planner"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 2] FRAME 77.3x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x55.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973892] FRAME 439.0x936.0 V gap10.0 pad20.0/20.0/20.0/20.0 vy:FIXE hz:FIXE
    [Frame 204973891] FRAME 399.0x894.7 V gap10.0 vy:HUG hz:FILL
      [Segmented control] INSTANCE 399.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FILL
        [Button 1] FRAME 195.5x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
          [Frame 66] FRAME 57.0x26.0 H gap10.0 vy:FIXE hz:HUG
            [planner edit] INSTANCE 19.0x19.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 15.8x15.8 #1B7498
            TEXT "Plan"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
        [Button 3] FRAME 195.5x32.0 H pad3.0/6.0/3.0/6.0 vy:FILL hz:FILL
          [Frame 67] FRAME 118.0x24.0 H gap3.0 vy:HUG hz:HUG
            [coach] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
              [Layer_1] FRAME 12.1x14.9
                <Vector> VECTOR 6.0x5.9 #1B7498
                <Vector> VECTOR 1.9x1.9 #1B7498
                <Vector> VECTOR 1.2x1.2 #1B7498
                <Vector> VECTOR 5.3x6.7 #1B7498
                <Vector> VECTOR 6.5x6.5 #1B7498
            TEXT "Ask the coach"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973900] FRAME 399.0x76.0 fill=#F5F3EF V gap-18.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
        [Frame 204973890] FRAME 340.0x36.0 H gap20.0 vy:HUG hz:HUG
          [Frame 204973885] FRAME 266.0x36.0 H gap10.0 vy:HUG hz:FIXE stroke #E9E4DC 1.0
            TEXT "2 next steps this week ⏎ $0 confirmed · 1 cost TBD · 2 tracked"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
          [Frame 204973886] FRAME 54.0x18.0 H gap10.0 vy:HUG hz:HUG
            TEXT "View"  [Inter w400 13.0/18.0 ls0.0 L #1B7498]
            [back arrow] INSTANCE 14.0x11.0 vy:FIXE hz:FIXE
              <Vector> VECTOR 5.8x11.0 
              <Vector> VECTOR 14.0x0.0 
      [Frame 204973901] FRAME 399.0x36.0 V gap10.0 vy:HUG hz:FILL
        [Segmented control] INSTANCE 171.0x36.0 fill=#DAE0DF H gap4.0 pad2.0/2.0/2.0/2.0 r100.0 vy:FIXE hz:FIXE
          [Button 1] FRAME 81.5x32.0 fill=#FFFFFF H pad3.0/6.0/3.0/6.0 r20.0 vy:FILL hz:FILL
            [Frame 66] FRAME 24.0x26.0 H gap10.0 vy:FIXE hz:HUG
              TEXT "List"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
          [Button 3] FRAME 81.5x32.0 H pad3.0/6.0/3.0/6.0 vy:FILL hz:FILL
            [Frame 67] FRAME 55.0x18.0 H gap3.0 vy:HUG hz:HUG
              TEXT "Timeline"  [Inter w700 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973899] FRAME 399.0x34.7 H gap6.0 vy:HUG hz:FILL
        [tag choice] INSTANCE 45.8x34.7 fill=#1B7498 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #E9E4DC 0.8195489048957825
          [Frame 5] FRAME 13.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "All"  [Inter w400 10.654135704040527/14.8 ls0.0 C #F5F3EF]
        [tag choice] INSTANCE 55.8x34.7 fill=#FCFBF8 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
          [Frame 5] FRAME 23.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "New"  [Inter w400 10.654135704040527/14.8 ls0.0 C #1B7498]
        [tag choice] INSTANCE 94.8x34.7 fill=#FCFBF8 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
          [Frame 5] FRAME 62.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "Deciding (3)"  [Inter w400 10.654135704040527/14.8 ls0.0 C #1B7498]
        [tag choice] INSTANCE 115.8x34.7 fill=#FCFBF8 H gap8.2 pad9.8/16.4/9.8/16.4 r19.669174194335938 vy:HUG hz:HUG stroke #1B7498 0.8195489048957825
          [Frame 5] FRAME 83.0x15.0 H gap7.4 vy:HUG hz:HUG
            TEXT "Needs action (1)"  [Inter w400 10.654135704040527/14.8 ls0.0 C #1B7498]
      [Frame 204973800] FRAME 399.0x92.0 fill=#F5F3EF H gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
        [Frame 204973867] FRAME 297.0x52.0 H gap10.0 pad0/9.0/0/9.0 vy:HUG hz:FIXE
          [seach large] INSTANCE 20.0x20.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 15.0x15.0 #4F5D3A
          [Frame 204973902] FRAME 268.0x52.0 V gap10.0 vy:HUG hz:FIXE
            TEXT "Find more activities"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
            TEXT "98332 · 25 mi · camps, classes & more ⏎ "  [Inter w400 14.0/14.0 ls-0.14 L #3A4A2A]
        [arrow] INSTANCE 16.0x8.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 12.0x6.0 
      [Frame 204973801] FRAME 399.0x221.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:FIXE hz:FILL
        [Frame 204973895] FRAME 209.0x30.0 H gap10.0 vy:HUG hz:HUG
          [Frame 204973893] FRAME 102.0x30.0 H gap10.0 r100.0 vy:HUG hz:HUG
            [Frame 204973894] FRAME 102.0x30.0 fill=#DAE0DF H pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
              TEXT "Lily & Ben"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
          [Frame 204973894] FRAME 97.0x30.0 fill=#F5EAD2 H gap10.0 pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
            TEXT "Deciding"  [Inter w700 13.0/18.0 ls0.0 L #6F6A60]
        [Frame 204973896] FRAME 359.0x89.0 V gap3.0 vy:HUG hz:FILL
          [Frame 204973898] FRAME 359.0x47.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            [Frame 204973897] FRAME 359.0x36.0 H gap3.0 vy:HUG hz:FILL
              [Frame 204973885] FRAME 245.0x36.0 H gap10.0 vy:HUG hz:FILL
                TEXT "University Place 3-Day Sports Mini Camps"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
              [Frame 204973895] FRAME 111.0x30.0 H gap10.0 r100.0 vy:HUG hz:FIXE
                [Frame 204973894] FRAME 68.0x30.0 fill=#DAE0DF H pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
                  TEXT "75%"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
          TEXT "Camp · YMCA / City of University Place"  [Inter w400 13.0/18.0 ls0.0 L #6E6A62]
          TEXT "Gig Harbor · Jun 22 – Aug 28"  [Inter w400 13.0/18.0 ls0.0 L #6E6A62]
        [Frame 204973899] FRAME 235.0x42.0 H gap10.0 vy:HUG hz:HUG
          [tag choice] INSTANCE 105.0x42.0 fill=#1B7498 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:HUG stroke #E9E4DC 1.0
            [Frame 5] FRAME 73.0x18.0 H gap9.0 vy:HUG hz:HUG
              [check] INSTANCE 14.0x14.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 14.0x10.5 #F5F3EF
              TEXT "Planned"  [Inter w400 13.0/18.0 ls0.0 C #F5F3EF]
          [tag choice] INSTANCE 120.0x42.0 fill=#FCFBF8 H gap10.0 pad12.0/16.0/12.0/16.0 r24.0 vy:HUG hz:HUG stroke #1B7498 1.0
            [Frame 5] FRAME 88.0x18.0 H gap9.0 vy:HUG hz:HUG
              TEXT "Ask the coach"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973904] FRAME 399.0x261.0 fill=#FFFFFF V gap10.0 pad20.0/20.0/20.0/20.0 r12.0 vy:HUG hz:FILL
        [Frame 204973895] FRAME 236.0x30.0 H gap10.0 vy:HUG hz:HUG
          [Frame 204973893] FRAME 102.0x30.0 H gap10.0 r100.0 vy:HUG hz:HUG
            [Frame 204973894] FRAME 102.0x30.0 fill=#DAE0DF H pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
              TEXT "Lily & Ben"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
          [Frame 204973894] FRAME 124.0x30.0 fill=#F5EAD2 H gap10.0 pad6.0/20.0/6.0/20.0 r100.0 vy:HUG hz:HUG
            TEXT "Needs action"  [Inter w700 13.0/18.0 ls0.0 L #6F6A60]
        [Frame 204973896] FRAME 359.0x181.0 V gap3.0 vy:HUG hz:FILL
          [Frame 204973898] FRAME 359.0x29.0 H gap3.0 pad0/0/10.0/0 vy:HUG hz:FILL stroke #F3F0EB 1.0
            [Frame 204973897] FRAME 359.0x18.0 H gap3.0 vy:HUG hz:FILL
              [Frame 204973885] FRAME 359.0x18.0 H gap10.0 vy:HUG hz:FILL
                TEXT "Rialto Beach family trip"  [Inter w700 13.0/18.0 ls0.0 L #1B7498]
          TEXT "Trip · Jun 22 – Aug 28"  [Inter w400 13.0/18.0 ls0.0 L #6E6A62]
          [Frame 204973909] FRAME 359.0x128.0 V gap10.0 pad20.0/0/0/0 vy:HUG hz:FILL
            [check circle] INSTANCE 86.0x20.0 H gap6.0 vy:HUG hz:HUG
              [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.0x16.0 #1B7498
              TEXT "Pack toys"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [check circle] INSTANCE 145.0x20.0 H gap6.0 vy:HUG hz:HUG
              [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.0x16.0 #1B7498
              TEXT "Meds & documents"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [check circle] INSTANCE 93.0x20.0 H gap6.0 vy:HUG hz:HUG
              [Frame] FRAME 20.0x20.0 vy:FIXE hz:FIXE
                <Vector> VECTOR 16.0x16.0 #1B7498
              TEXT "Book room"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
            [check circle] INSTANCE 121.0x18.0 H gap6.0 vy:HUG hz:HUG
              <Vector> VECTOR 16.0x16.0 #1B7498
              TEXT "Download maps"  [Inter w400 13.0/18.0 ls0.0 C #1B7498]
      [Frame 204973903] FRAME 238.0x68.0 V gap10.0 pad20.0/0/0/0 vy:HUG hz:HUG
        [button] INSTANCE 238.0x48.0 fill=#1B7498 H gap10.0 pad12.0/159.0/12.0/159.0 r100.0 vy:HUG hz:FIXE
          [addcircle] INSTANCE 24.0x24.0 vy:FIXE hz:FIXE
            <Vector> VECTOR 20.0x20.0 #F5F3EF
          TEXT "Plan something new"  [Inter w800 16.0/22.0 ls0.0 C #FFFFFF]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973889] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 198.0x32.0 H gap13.0 vy:HUG hz:HUG
        [planner-xl] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.0x26.7 #1B7498
        TEXT "MPV Planner"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME Circle-002 — `754:5898` — 440.0x841.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Frame 204973874] FRAME 380.0x602.0 V gap23.0 vy:HUG hz:FIXE
    [Frame 204973869] FRAME 380.0x198.0 V gap6.0 vy:HUG hz:FILL
      TEXT "New conversation"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
      [Frame 204973870] FRAME 380.0x178.0 V gap9.0 vy:HUG hz:FILL
        [Frame 204973796] FRAME 380.0x59.0 fill=#F5F3EF V gap10.0 pad24.0/24.0/24.0/24.0 r12.0 vy:FIXE hz:FILL stroke #A4A4A4 1.0
          TEXT "Dinner with Ben & Lily"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
        [Frame 204973797] FRAME 380.0x110.0 fill=#F5F3EF V gap10.0 pad24.0/24.0/24.0/24.0 r12.0 vy:FIXE hz:FILL stroke #A4A4A4 1.0
          TEXT "I need dinner ideas for the kids tonight. What’s on your plates?"  [Inter w400 17.0/26.0 ls0.0 L #3A4A2A]
    [Frame 204973873] FRAME 380.0x317.0 V gap15.0 vy:HUG hz:FILL
      [Frame 204973872] FRAME 380.0x261.0 V gap11.0 vy:HUG hz:FILL
        TEXT "Invite to the conversation"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
        [Frame 204973798] FRAME 380.0x236.0 fill=#F5F3EF V gap10.0 pad24.0/24.0/24.0/24.0 r12.0 vy:HUG hz:FILL stroke #A4A4A4 1.0
          [Frame 204973788] FRAME 334.0x42.0 H gap12.0 pad0/0/6.0/0 vy:HUG hz:FIXE stroke #DAE0DF 1.0
            [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
              TEXT "M"  [Inter w700 16.0/19.4 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973789] FRAME 334.0x42.0 H gap12.0 pad0/0/6.0/0 vy:HUG hz:FIXE stroke #DAE0DF 1.0
            [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
              TEXT "H"  [Inter w700 16.0/19.4 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973790] FRAME 334.0x42.0 H gap12.0 pad0/0/6.0/0 vy:HUG hz:FIXE stroke #DAE0DF 1.0
            [Frame 204973791] FRAME 36.0x36.0 fill=#151412 V gap10.0 r100.0 vy:FIXE hz:FIXE
              TEXT "T"  [Inter w700 16.0/19.4 ls0.0 C #FFFFFF]
            [Frame 204973682] FRAME 238.0x22.0 V gap4.9 vy:HUG hz:FILL
              TEXT "Contact name"  [Inter w400 15.0/22.0 ls0.0 L #1B7498]
            [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
              [dots] GROUP 16.0x4.0
                <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
                <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
          [Frame 204973791] FRAME 334.0x32.0 H gap12.0 vy:HUG hz:FIXE
            TEXT "Add circle members"  [Roboto w700 13.0/16.9 ls0.0 L #4B4B4B]
            [add] INSTANCE 32.0x32.0 vy:FIXE hz:FIXE
              [group] GROUP 16.0x16.0
                <Vector> VECTOR 16.0x16.0 
                <Vector> VECTOR 6.4x0.0 
                <Vector> VECTOR 0.0x6.4 
      [Global Button] INSTANCE 380.0x41.0 fill=#FAF7F2 @0.30 H gap8.0 pad8.0/16.0/8.0/16.0 r8.0 vy:FIXE hz:FILL stroke #1B7498 1.0
        TEXT "Start a discussion"  [Roboto w600 16.0/18.8 ls0.0 L #1B7498]
    [Global Button] INSTANCE 380.0x41.0 fill=#E9E4DC H gap8.0 pad8.0/16.0/8.0/16.0 r8.0 vy:FIXE hz:FILL
      TEXT "Cancel"  [Roboto w600 16.0/18.8 ls0.0 L #151412]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME Circle-003  — `754:5827` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [chatinput] INSTANCE 440.0x70.0 fill=#0A5570 H pad12.0/18.0/12.0/18.0 r16.0,16.0,0.0,0.0 vy:HUG hz:FIXE
    [input] FRAME 404.0x46.0 fill=#FFFFFF H gap15.0 pad12.0/16.0/12.0/16.0 r8.0 vy:HUG hz:FILL
      TEXT "I need help with dinner ideas for Ben & Lily"  [Inter w400 14.0/16.9 ls0.0 L #292929]
      [icon.microphone] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 19.8x20.1 #3D6B3D
  [Frame 204973850] FRAME 362.0x166.0 V gap16.0 vy:HUG hz:FIXE
    [Frame 204973852] FRAME 362.0x50.0 H vy:HUG hz:FILL
      [Frame 204973719] FRAME 334.0x50.0 H vy:HUG hz:FILL
        [Frame 204973406] FRAME 326.0x50.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:FILL
          [Frame 204973407] FRAME 292.0x18.0 V gap9.0 vy:HUG hz:FIXE
            TEXT "I need help with dinner ideas for Ben & Lily"  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
        [Frame 204973720] FRAME 8.0x50.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
          <Vector 2> VECTOR 8.0x13.0 #0A5570
      [Frame 204973721] FRAME 28.0x50.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
        [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#0A5570 r100.0 vy:FIXE hz:FIXE stroke #0A5570 1.0
          TEXT "G"  [Roboto w900 17.0/0.0 ls0.0 L #FFFFFF]
    [Frame 204973850] FRAME 362.0x100.0 V gap10.0 pad0/10.0/0/10.0 vy:HUG hz:FILL
      [Frame 204973731] FRAME 342.0x77.0 H vy:FIXE hz:FILL
        [Frame 204973721] FRAME 28.0x77.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
          [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
            TEXT "T"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973719] FRAME 314.0x77.0 H vy:FIXE hz:FILL
          [Frame 204973720] FRAME 8.0x77.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
            <Vector 2> VECTOR 8.0x13.0 #FFFFFF
          [Frame 204973406] FRAME 306.0x66.0 fill=#FFFFFF H gap16.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:FIXE hz:FILL
            TEXT "I’m making crispy brussel sprouts with cheesy noodles tonight!"  [Roboto w400 14.0/18.2 ls0.0 L #696969]
      [reactions] FRAME 342.0x13.0 H gap56.0 pad0/0/0/39.0 vy:HUG hz:FILL
        [Frame 204973735] FRAME 49.9x12.6 H gap6.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x9.5 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x10.5 
            <Vector> VECTOR 4.2x1.1 
            <Vector> VECTOR 0.0x0.0 
            <Vector> VECTOR 0.0x0.0 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 9.5x10.5 
        [Frame 204973734] FRAME 43.6x13.0 H gap5.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 2.6x5.3 
            <Vector> VECTOR 8.4x3.2 
          TEXT "Reply"  [Roboto w700 10.0/13.0 ls0.0 L #6B6B6B]
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [Frame 204973913] FRAME 251.0x37.0 H gap11.0 vy:HUG hz:HUG
        [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
          <Vector> VECTOR 7.7x15.4 #1B7498
        [Frame 204973887] FRAME 203.0x26.0 H gap13.0 vy:HUG hz:HUG
          TEXT "Dinner plans for the kids"  [Inter w700 17.0/26.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME Circle-004  — `754:5693` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Frame 204973850] FRAME 362.0x464.0 V gap16.0 vy:HUG hz:FIXE
    [Frame 204973852] FRAME 362.0x50.0 H vy:HUG hz:FILL
      [Frame 204973719] FRAME 334.0x50.0 H vy:HUG hz:FILL
        [Frame 204973406] FRAME 326.0x50.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:FILL
          [Frame 204973407] FRAME 292.0x18.0 V gap9.0 vy:HUG hz:FIXE
            TEXT "I need help with dinner ideas for Ben & Lily"  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
        [Frame 204973720] FRAME 8.0x50.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
          <Vector 2> VECTOR 8.0x13.0 #0A5570
      [Frame 204973721] FRAME 28.0x50.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
        [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#0A5570 r100.0 vy:FIXE hz:FIXE stroke #0A5570 1.0
          TEXT "G"  [Roboto w900 17.0/0.0 ls0.0 L #FFFFFF]
    [Frame 204973850] FRAME 362.0x100.0 V gap10.0 pad0/10.0/0/10.0 vy:HUG hz:FILL
      [Frame 204973731] FRAME 342.0x77.0 H vy:FIXE hz:FILL
        [Frame 204973721] FRAME 28.0x77.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
          [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
            TEXT "T"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973719] FRAME 314.0x77.0 H vy:FIXE hz:FILL
          [Frame 204973720] FRAME 8.0x77.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
            <Vector 2> VECTOR 8.0x13.0 #FFFFFF
          [Frame 204973406] FRAME 306.0x66.0 fill=#FFFFFF H gap16.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:FIXE hz:FILL
            TEXT "I’m making crispy brussel sprouts with cheesy noodles tonight!"  [Roboto w400 14.0/18.2 ls0.0 L #696969]
      [reactions] FRAME 342.0x13.0 H gap56.0 pad0/0/0/39.0 vy:HUG hz:FILL
        [Frame 204973735] FRAME 49.9x12.6 H gap6.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x9.5 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x10.5 
            <Vector> VECTOR 4.2x1.1 
            <Vector> VECTOR 0.0x0.0 
            <Vector> VECTOR 0.0x0.0 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 9.5x10.5 
        [Frame 204973734] FRAME 43.6x13.0 H gap5.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 2.6x5.3 
            <Vector> VECTOR 8.4x3.2 
          TEXT "Reply"  [Roboto w700 10.0/13.0 ls0.0 L #6B6B6B]
    [Frame 204973853] FRAME 362.0x100.0 V gap10.0 pad0/10.0/0/10.0 vy:HUG hz:FILL
      [Frame 204973731] FRAME 342.0x77.0 H vy:FIXE hz:FILL
        [Frame 204973721] FRAME 28.0x77.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
          [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
            TEXT "M"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973719] FRAME 314.0x77.0 H vy:FIXE hz:FILL
          [Frame 204973720] FRAME 8.0x77.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
            <Vector 2> VECTOR 8.0x13.0 #FFFFFF
          [Frame 204973406] FRAME 306.0x66.0 fill=#FFFFFF H gap16.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:FIXE hz:FILL
            TEXT "Thursdays are waffle nights for us"  [Roboto w400 14.0/18.2 ls0.0 L #696969]
      [reactions] FRAME 342.0x13.0 H gap56.0 pad0/0/0/39.0 vy:HUG hz:FILL
        [Frame 204973735] FRAME 49.9x12.6 H gap6.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x9.5 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x10.5 
            <Vector> VECTOR 4.2x1.1 
            <Vector> VECTOR 0.0x0.0 
            <Vector> VECTOR 0.0x0.0 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 9.5x10.5 
        [Frame 204973734] FRAME 43.6x13.0 H gap5.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 2.6x5.3 
            <Vector> VECTOR 8.4x3.2 
          TEXT "Reply"  [Roboto w700 10.0/13.0 ls0.0 L #6B6B6B]
    [Frame 204973854] FRAME 362.0x100.0 V gap10.0 pad0/10.0/0/10.0 vy:HUG hz:FILL
      [Frame 204973731] FRAME 342.0x77.0 H vy:FIXE hz:FILL
        [Frame 204973721] FRAME 28.0x77.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
          [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
            TEXT "H"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [Frame 204973719] FRAME 314.0x77.0 H vy:FIXE hz:FILL
          [Frame 204973720] FRAME 8.0x77.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
            <Vector 2> VECTOR 8.0x13.0 #FFFFFF
          [Frame 204973406] FRAME 306.0x66.0 fill=#FFFFFF H gap16.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:FIXE hz:FILL
            TEXT "Can’t go wrong with a veggie pizza"  [Roboto w400 14.0/18.2 ls0.0 L #696969]
      [reactions] FRAME 342.0x13.0 H gap56.0 pad0/0/0/39.0 vy:HUG hz:FILL
        [Frame 204973735] FRAME 49.9x12.6 H gap6.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x9.5 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 10.5x10.5 
            <Vector> VECTOR 4.2x1.1 
            <Vector> VECTOR 0.0x0.0 
            <Vector> VECTOR 0.0x0.0 
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 9.5x10.5 
        [Frame 204973734] FRAME 43.6x13.0 H gap5.0 vy:HUG hz:HUG
          [Frame] FRAME 12.6x12.6 vy:FIXE hz:FIXE
            <Vector> VECTOR 2.6x5.3 
            <Vector> VECTOR 8.4x3.2 
          TEXT "Reply"  [Roboto w700 10.0/13.0 ls0.0 L #6B6B6B]
    [Frame 204973851] FRAME 362.0x50.0 H vy:HUG hz:FILL
      [Frame 204973719] FRAME 334.0x50.0 H vy:HUG hz:FILL
        [Frame 204973406] FRAME 326.0x50.0 fill=#0A5570 H gap10.0 pad16.0/16.0/16.0/16.0 r12.0,12.0,12.0,8.0 vy:HUG hz:FILL
          [Frame 204973407] FRAME 292.0x18.0 V gap9.0 vy:HUG hz:FIXE
            TEXT "Thanks for all you ideas!"  [Roboto w400 14.0/18.2 ls0.0 L #F5F3EF]
        [Frame 204973720] FRAME 8.0x50.0 H gap10.0 pad12.0/0/12.0/0 vy:FILL hz:HUG
          <Vector 2> VECTOR 8.0x13.0 #0A5570
      [Frame 204973721] FRAME 28.0x50.0 H gap10.0 pad0/0/6.0/0 vy:FILL hz:HUG
        [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#0A5570 r100.0 vy:FIXE hz:FIXE stroke #0A5570 1.0
          TEXT "G"  [Roboto w900 17.0/0.0 ls0.0 L #FFFFFF]
  [chatinput] INSTANCE 440.0x70.0 fill=#0A5570 H pad12.0/18.0/12.0/18.0 r16.0,16.0,0.0,0.0 vy:HUG hz:FIXE
    [input] FRAME 404.0x46.0 fill=#FFFFFF H gap15.0 pad12.0/16.0/12.0/16.0 r8.0 vy:HUG hz:FILL
      TEXT "I need help with dinner ideas for Ben & Lily"  [Inter w400 14.0/16.9 ls0.0 L #292929]
      [icon.microphone] INSTANCE 22.0x22.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 19.8x20.1 #3D6B3D
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [Frame 204973913] FRAME 251.0x37.0 H gap11.0 vy:HUG hz:HUG
        [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
          <Vector> VECTOR 7.7x15.4 #1B7498
        [Frame 204973887] FRAME 203.0x26.0 H gap13.0 vy:HUG hz:HUG
          TEXT "Dinner plans for the kids"  [Inter w700 17.0/26.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

====================================================================================================
FRAME Circle-005  — `754:5947` — 440.0x792.0 fill=#E9E4DC stroke #000000 1.0
====================================================================================================
  [Frame 204973796] FRAME 380.0x145.0 fill=#F5F3EF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973868] FRAME 362.0x36.0 H gap10.0 vy:HUG hz:FILL
      [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
        [dots] GROUP 16.0x4.0
          <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
    [Frame 204973867] FRAME 362.0x109.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
      [Frame 204973798] FRAME 344.0x51.0 V gap9.0 vy:HUG hz:FILL
        TEXT "Dinner plans for the kids"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
        TEXT "3 replies · last from Teri"  [Inter w400 15.0/22.0 ls0.0 L #575757]
      [Frame 204973866] FRAME 104.0x28.0 H gap10.0 vy:HUG hz:HUG
        [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
          TEXT "T"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [directions_run_FILL0_wght400_GRAD0_opsz48 2] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
          TEXT "M"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [directions_run_FILL0_wght400_GRAD0_opsz48 3] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
          TEXT "H"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
  [Frame 204973797] FRAME 380.0x145.0 fill=#F5F3EF V gap-18.0 pad9.0/9.0/9.0/9.0 r12.0 vy:HUG hz:FIXE stroke #A4A4A4 1.0
    [Frame 204973868] FRAME 362.0x36.0 H gap10.0 vy:HUG hz:FILL
      [menu - dots] INSTANCE 36.0x36.0 vy:FIXE hz:FIXE
        [dots] GROUP 16.0x4.0
          <Ellipse 3> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 4> ELLIPSE 4.0x4.0 #A4A4A4
          <Ellipse 5> ELLIPSE 4.0x4.0 #A4A4A4
    [Frame 204973867] FRAME 362.0x109.0 V gap10.0 pad10.0/9.0/10.0/9.0 vy:HUG hz:FILL
      [Frame 204973798] FRAME 344.0x51.0 V gap9.0 vy:HUG hz:FILL
        TEXT "Gifts for the party this weekend"  [Inter w600 14.0/14.0 ls-0.14 L #3A4A2A]
        TEXT "M started this — 4 replies"  [Inter w400 15.0/22.0 ls0.0 L #575757]
      [Frame 204973866] FRAME 104.0x28.0 H gap10.0 vy:HUG hz:HUG
        [directions_run_FILL0_wght400_GRAD0_opsz48 1] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
          TEXT "G"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [directions_run_FILL0_wght400_GRAD0_opsz48 2] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
          TEXT "S"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
        [directions_run_FILL0_wght400_GRAD0_opsz48 3] FRAME 28.0x28.0 fill=#1B7498 r100.0 vy:FIXE hz:FIXE stroke #1B7498 1.0
          TEXT "M"  [Inter w900 14.0/0.0 ls0.0 C #F5F3EF]
  [Tab Bar] INSTANCE 440.0x93.0 H gap8.0 pad16.0/20.0/25.0/20.0 vy:FIXE hz:FIXE stroke #F5F3EF 1.0
    [Tab 1] FRAME 66.7x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL stroke #FFFFFF 1.0
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
    [Tab 2] FRAME 66.7x52.0 fill=#DAE0DF V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:FILL
      [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
        <Vector> VECTOR 24.9x20.5 #1B7498
      TEXT "CIRCLE"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
    [Tab 6] FRAME 84.0x52.0 V gap3.0 pad8.0/8.0/9.0/8.0 r100.0 vy:FILL hz:HUG
      [icon_settings] INSTANCE 20.1x21.0 vy:FIXE hz:FIXE
        <Vector> VECTOR 20.1x21.0 #1B7498
      TEXT "SETTINGS"  [Inter w600 11.0/14.0 ls0.66 C #1B7498]
  [Status Bar] FRAME 440.0x61.0 fill=#F5F3EF H gap154.0 pad21.0/0/19.0/0 vy:FIXE hz:FIXE
    [Time] FRAME 143.0x22.0 H gap10.0 pad1.5/0/0/0 vy:FIXE hz:FILL
      TEXT "9:41"  [SF Pro w590 17.0/22.0 ls0.0 C #151412]
    [Levels] FRAME 143.0x22.0 H gap7.0 pad1.0/1.0/0/0 vy:FIXE hz:FILL
      <Cellular Connection> VECTOR 19.2x12.2 #151412
      <Wifi> VECTOR 17.1x12.3 #151412
      [Frame] FRAME 27.3x13.0 vy:FIXE hz:FIXE
        [Border] RECTANGLE 25.0x13.0 r4.300000190734863 stroke #151412 1.0
        <Cap> VECTOR 1.3x4.1 #151412
        [Capacity] RECTANGLE 21.0x9.0 fill=#151412 r2.5
  [Frame 204973891] FRAME 439.0x67.0 fill=#F5F3EF V gap10.0 pad10.0/10.0/20.0/10.0 vy:HUG hz:FIXE
    [Frame 204973888] FRAME 419.0x37.0 H gap57.0 vy:HUG hz:FILL
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        <Vector> VECTOR 7.7x15.4 #1B7498
      [Frame 204973887] FRAME 106.9x32.0 H gap13.0 vy:HUG hz:HUG
        [Vector] INSTANCE 24.9x20.5 vy:FIXE hz:FIXE
          <Vector> VECTOR 24.9x20.5 #1D7FA6
        TEXT "Circle"  [Fraunces w600 24.0/32.0 ls0.0 C #1E1E1E]
      [back] INSTANCE 37.0x37.0 fill=#FFFFFF r100.0 vy:FIXE hz:FIXE DROP_SHADOW r15.0 #000000
        [menu-dots] INSTANCE 10.1x2.1
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498
          <Vector> VECTOR 2.1x2.1 #1B7498

---

## Round 2 addendum — Dashboard fidelity, consolidated Settings, member sheets, account sheets

Extracted 2026-08-09 from canvas `754:4310` (*Design sprint1 - onboarding+dashboard (WIP)*), via
ONE batched `/nodes` call (12 frame ids). Triggered by Miguel's phone walk-through finding Home
layout drift, an inert "Check your family settings" link, and a request to consolidate Settings
into the card-based screen shown below. Same rules as above: this file is authoritative, do not
re-read Figma without batching every id into one call.

| node id | frame | used for |
|---|---|---|
| `754:4553` | Onboarding - Dashboard 1 | Home fidelity (Step 3) |
| `754:4458` | Onboarding - welcome (short variant) | not used — superseded by `754:6516` |
| `754:6516` | Onboarding - welcome (7-card settings) | **the** Settings-tab-root frame (Step 4) |
| `869:1090` | Onboarding - welcome (alt/earlier draft) | reference only, do not build from |
| `855:3939` | parent 001 | member sheet — primary parent (Step 5) |
| `855:4033` | parent 002 | member sheet — primary parent, second (Step 5) |
| `855:4275` | co-parent 001 | member sheet — co-parent, adds Co-Parent goals (Step 5) |
| `855:4157` | circle member | member sheet — nanny/other role, adds Personality chips (Step 5) |
| `870:1234` | account01 | account sheet, no-activity state (Step 6) |
| `1006:2517` | account 02 | account sheet, Saved-tab state (Step 6) |
| `1008:5111` | account 03 | account sheet, History-tab state (Step 6) |
| `1004:1746` | Onboarding - need help with acitivities [sic] | interest-tile icons (Step 2c) |

### FRAME Onboarding - Dashboard 1 — `754:4553` — 440x1818, ground #F5F3EF

Right-aligned header row @(324,83): avatar circle "G" initial, Fraunces 700 18.24/19 ls-0.18,
white text. YOUR KIDS section header @(51,157) "YOUR KIDS" Inter 800 16/22 #1E1E1E; kid tiles
`Alkina`/`Ceiba` Fraunces 600 28/32 white-on-teal. COACH row @(78,420) "COACH • This morning"
Inter 800 16/22 #1B7498 (this proves the header-detail slot is meant to carry a live label, not
the static "Check your family settings" string — see Step 3). Coach comment body Inter 400 17/26
#6E6A62. FOR YOU header Inter 800 16/22 #6E6A62 (note: muted color here vs #1E1E1E on COMING UP —
FOR YOU's eyebrow is deliberately quieter). Article rows: eyebrow "Care · 2 min" Inter 400 13/18
#1E1E1E, title Fraunces 700 38/40 ls-0.38 #2B2925, subtitle Inter 400 13/18. COMING UP header
Inter 800 16/22 #1E1E1E; card title Fraunces 700 38/40, description Inter 400 13/18; "See all"
pill white bg, teal Inter 800 13.35/18 label.

### FRAME Onboarding - welcome (7-card settings root) — `754:6516` — 440x2192, ground #F3F0EB

```
[Onboarding - welcome] FRAME 440x2192 fill=#F3F0EB
  [Frame 29] FRAME 376x2093 V gap23.0 pad0/0/0/0                          — page content column, gutter 32
    [icon_settings] INSTANCE 40x41 fill=#4A4741                          — gearshape header icon, centered
    [Frame 1] FRAME 376x164 V gap22.0                                     — title block
      TEXT "Your MVP Family Plan is almost ready"  [Fraunces w700 38.0/40.0 ls-0.38 #1E1E1E]
      TEXT "Review your family settings message"  [Inter w400 15.0/22.0 ls0.0 #1E1E1E]
    [Frame 204973848] FRAME 376x1704 V gap12.0                            — the 7 cards, gap12 between
      [card: Your MVP information] FRAME 376xH fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        [pencil-edit] INSTANCE 20x20 top-right — teal #1B7498 14x14 vector
        TEXT "Your MVP  information"  [Inter w800 16.0/22.0 #1E1E1E]        — card title, note double-space typo in Figma copy
        TEXT "Your plan includes a custom MVP username and email"  [Inter w400 13.0/18.0 #1E1E1E]
        [row] FRAME H gap23.0                                             — label col | value col
          TEXT "Username:\nMVP Email:\nPassword:\nPlan\nBilling"  [Inter w400 15.0/22.0 #6E6A62]  — label col
          TEXT "MVPDad_GregH\nMVP_GregH@mvp.com\n******\nFamily\nAnnual"  [Inter w400 15.0/22.0 #6E6A62]  — value col (FAKE placeholder — real-data-only rule drops Email/Password rows, see Step 4b card 1)
      [card: Family structure] FRAME 376x238 fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        TEXT "Family structure" / "Tell us about the parenting setup..."
        3-column row: "Parent 1..4" | "Dad/Mom/Dad/Step mom" | "Me/Spouse/CoParent/CoParent"
      [card: Your family] FRAME 376x256 fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        TEXT "Your family" / "Your plan includes a custom MVP username and email"
        3-column row: "Parent/Parent/Son/Daughter" | "Greg/Teri/Benjamin/Lily" | "Dad/Mom/Son/Daughter"
      [card: Your circle] FRAME 376x278 fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        TEXT "Your circle" / "Your MVP Circle includes anyone that you rely on for help"
        2-column row: names | "mvpNanny/mvpGerry/mvpUncle/mvpNeighbor/mvpAunt"
      [card: Care givers] FRAME 376x194 fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        TEXT "Care givers" / "Care givers are.."
        2-column row: "Armelle/Nana Gerry" | "mvpNanny/mpvGrandmaGerry"
      [card: Language at home] FRAME 376x194 fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        TEXT "Language at home" / "Do you speak one or several languages at home?"
        2-column row: "Primary language/Secondary language" | "Spanish/English"
      [card: MVP coach settings] FRAME 376x194 fill=#FFFFFF r32.0 V gap10.0 pad30/30/30/30
        TEXT "MVP coach settings" / "Set up how you want the coach to respond"
        2-column row: "Voice/Personality" | "Default - Male/Default - Genuine"  — Voice row DROPPED per real-data-only rule (Step 4b card 7)
    [Frame 204973843] FRAME 270x115 V gap23.0                             — footer, ONBOARDING-ONLY, not part of the settings-tab build
      [button] fill=#1B7498 r12.0  TEXT "Looks good!"  [Inter w800 16.0/22.0 #FFFFFF]
      [button] fill=#FFFFFF stroke=#1B7498 1.0 r12.0  TEXT "Set up later"  [Inter w800 16.0/22.0 #1B7498]
```

Card anatomy (repeats across all 7): white `#FFFFFF` card, radius 32 (nearest Hearth token:
`.hearthRadiusSection` 28 — use 28, the app's established section-card radius, not a new one-off
32), inner padding 30 (nearest token `.hearth800` 32; the app already accepts ±2pt token
substitution per the cheat sheet), row gap 10 (`.hearth400`≈12, closest token), card-to-card gap
12 (`.hearth400`), page gutter 32 (`.hearth800`). Title Inter ExtraBold 16/22 `#1E1E1E` →
`inkDisplay`-ish; body/description Inter Regular 13/18 `#1E1E1E`; label/value column text Inter
Regular 15/22 `#6E6A62` → `inkSecondary`. Pencil edit affordance: 20×20 tap target, teal 14×14
vector glyph, top-right of each card (map to SF Symbol `pencil`, teal `accentDefault`).

### FRAME member sheets — `855:3939` parent 001, `855:4033` parent 002, `855:4275` co-parent 001, `855:4157` circle member

All four share one skeleton: photo header (full-bleed top image, ~394×394) with a bottom-right
"Edit" pill (camera icon + "Edit" label, dark translucent fill) → "Edit parent"/"Edit member"
button (teal fill, white Inter 800 15/22 label, radius 12, full-width minus gutter) → Fraunces 700
~40pt display name → role card (white, radius 20, padding ~24): role title (e.g. "Dad", "Step
Mom", "Nanny") Inter 700 ~20pt, then label/value rows "MVP name" / "Family roll" [sic, Figma
typo — do not copy the typo into UI copy, use "Family role"] / "Email", each Inter 400 15/22
`#6E6A62` — plus a `···` overflow-menu glyph top-right of the card. Then "More about {name}" card
(white, radius 20): eyebrow-less disclosure rows "Likes / Dislikes / Challenges / Excels at /
Goals for {name}" each Inter 400 15/22 `#1E1E1E` with a `>` chevron, divider between rows. The
`circle member` frame additionally has a "Personality" chip row (3 pill chips: Spirited /
Easy-going / Sensitive, selected = teal fill white text, unselected = white fill teal stroke —
identical chip visual language to `KidSettingsSheet`'s temperament group) directly under the role
card, before "More about". The `co-parent 001` frame's "More about" list ends with "Co-Parent
goals" instead of "Goals for {name}" (7th row, matches backend `co_parent_goals`). Footer: two
full-width stacked buttons, "Save" (teal fill) then "Cancel" (white, teal stroke), radius 12 each.

### FRAME account sheets — `870:1234` account01, `1006:2517` account 02, `1008:5111` account 03

Confirms the current `AccountSheetView` build closely: `account01` = neither Saved/History tab
selected, "No recent activity. Your history and saved articles can be found here." subline, NO
family-interests grid, Account card shows the same fake Username/Email/Password/Plan/Billing rows
as the settings card (real-data-only rule applies here too — see Step 6). `account 02` = Saved
tab selected, teal article cards. `account 03` (not walked in full here — same shell as 02 with
History tab selected showing Circle + Coach-advice rows, per the account-03 screenshot Miguel
sent). All three share: header "Hi Greg!" Fraunces 700 38/40 ls-0.38, Saved/History toggle (Inter
800 13.35/18 teal labels, selected = `bgSelected` fill + teal stroke), footer Cancel (teal fill)
+ Sign out (grey fill) full-width stacked buttons.

### FRAME interest icons — `1004:1746` Onboarding - need help with acitivities [sic]

3×3 tile grid, tiles 137×137, radius 12 (≈`.hearthRadiusTile`), selected = `#1B7498` fill white
icon, unselected = white fill teal-stroke `#1B7498` icon + a small `+` badge top-right (circle
outline, unfilled — indicates "tap to add"). Tile label Inter 700 ~15pt, white on selected / teal
on unselected. Nine tiles in reading order: Arts & crafts (paintbrush), Museums (columned
building), Hiking (person w/ pole), Gardens (potted flower in a frame), Nature (bee/flower
cluster), Parks (fir tree), Science (robot head), Nature (swimmer — mislabeled/duplicate in the
Figma source, this tile's icon is a swim stroke; treat its canonical option as "Sports"), Parks
(rocket — second "Parks" duplicate, canonical option undetermined, flag in Step 2c and default to
skipping icon-mapping for whichever `ProfileOptions.familyActivityOptions` entry has no clean
match). Icon vector node ids are nested inside each tile's `INSTANCE` — re-open `round2_spec.txt`
(job tmp dir, this session) or re-walk node `1004:1746` to get the leaf vector ids for the Step-2c
SVG export; they were not hand-copied into this doc to keep it scannable.

**Changelog**: round-2 frames (dashboard fidelity, consolidated settings, member sheets, account
sheets, interest icons) extracted 2026-08-09 in one batched `/nodes` call, addendum appended same
day. Source: Miguel's 4pm phone walk-through feedback.
