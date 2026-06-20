# Surface — iOS (SwiftUI)

The iOS surface is the **primary** Hearth target. It is the screen a tired parent holds at 10:47pm. Everything in this file exists to make that moment feel held, editorial, and quiet. Touch over click. Photography over chrome. System font fallbacks never. Tokens always.

This file is the **only** place SwiftUI-specific overrides live. Component specs (`components/*.md`) describe the contract; this file describes how that contract is honoured in `mvp/MVP/`.

---

## Token → SwiftUI mapping

Tokens land in two files at implementation time: `mvp/MVP/Theme.swift` (colors, spacing, shape, motion) and `mvp/MVP/Theme+Typography.swift` (fonts). Nothing in any `View` file may declare a raw hex, raw point value, or raw font name — those are token violations and CI must fail on them (see `tools/lint-design-tokens.py` in the implementation roadmap).

### Colors → `Color` extensions

| Token | Swift accessor | Source primitive |
|---|---|---|
| `bg/canvas` | `Color.hearthCanvas` | `neutral/cream-100` |
| `bg/elevated` | `Color.hearthElevated` | `neutral/paper` |
| `bg/sober` | `Color.hearthSober` | `neutral/cream-50` |
| `ink/primary` | `Color.hearthInkPrimary` | `neutral/ink-900` |
| `ink/secondary` | `Color.hearthInkSecondary` | `neutral/ink-700` |
| `ink/muted` | `Color.hearthInkMuted` | `neutral/ink-500` |
| `ink/placeholder` | `Color.hearthInkPlaceholder` | `neutral/ink-300` |
| `ink/onPhoto-dark` | `Color.hearthInkOnPhotoDark` | `neutral/ink-900` |
| `ink/onPhoto-light` | `Color.hearthInkOnPhotoLight` | `neutral/paper` |
| `border/hairline` | `Color.hearthBorderHairline` | `neutral/cream-200` |
| `border/strong` | `Color.hearthBorderStrong` | `neutral/ink-300` |
| `accent/default` | `Color.hearthAccent` | `brand/olive-500` |
| `accent/press` | `Color.hearthAccentPress` | `brand/olive-700` |
| `accent/tint` | `Color.hearthAccentTint` | `brand/olive-100` |
| `focus/ring-on-light` | `Color.hearthFocusRingOnLight` | `brand/olive-500` |
| `focus/ring-on-photo` | `Color.hearthFocusRingOnPhoto` | `neutral/paper` |
| `photo/saffron` | `Color.hearthPhotoSaffron` | `photo/saffron` |
| `photo/rose` | `Color.hearthPhotoRose` | `photo/rose` |
| `photo/royal` | `Color.hearthPhotoRoyal` | `photo/royal` |
| `photo/forest` | `Color.hearthPhotoForest` | `photo/forest` |
| `status/success` | `Color.hearthStatusSuccess` | `status/success` |
| `status/warning` | `Color.hearthStatusWarning` | `status/warning` |
| `status/error` | `Color.hearthStatusError` | `status/error` |
| `status/error-tint` | `Color.hearthStatusErrorTint` | `status/error-tint` |
| `status/warning-tint` | `Color.hearthStatusWarningTint` | `status/warning-tint` |
| `status/success-tint` | `Color.hearthStatusSuccessTint` | `status/success-tint` |
| `status/info` | `Color.hearthStatusInfo` | `status/info` |

All accessors are computed from a single `init(hex:)` helper in `Theme.swift` that reads the primitive table once. No `Color(red:green:blue:)` literals anywhere else in the project.

### Spacing → `CGFloat` extensions

| Token | Swift accessor | Value |
|---|---|---|
| `spacing/0` | `CGFloat.hearth0` | `0` |
| `spacing/300` | `CGFloat.hearth300` | `8` |
| `spacing/400` | `CGFloat.hearth400` | `12` |
| `spacing/500` | `CGFloat.hearth500` | `16` |
| `spacing/600` | `CGFloat.hearth600` | `20` |
| `spacing/700` | `CGFloat.hearth700` | `24` |
| `spacing/800` | `CGFloat.hearth800` | `32` |
| `spacing/900` | `CGFloat.hearth900` | `40` |
| `spacing/1000` | `CGFloat.hearth1000` | `56` |

Page gutter = `.hearth700` (24pt). Section rhythm = `.hearth800`–`.hearth1000`. Never use `.padding(16)` — use `.padding(.hearth500)`.

### Shape → `RoundedRectangle` corner radii

| Token | Swift accessor | Value |
|---|---|---|
| `shape/none` | `CGFloat.hearthRadiusNone` | `0` |
| `shape/sm` | `CGFloat.hearthRadiusSm` | `4` |
| `shape/md` | `CGFloat.hearthRadiusMd` | `12` |
| `shape/lg` | `CGFloat.hearthRadiusLg` | `20` |
| `shape/xl` | `CGFloat.hearthRadiusXl` | `28` |
| `shape/pill` | `CGFloat.hearthRadiusPill` | `999` |

### Elevation → `View` modifier

`elevation/0` … `elevation/3` are exposed as a single `.hearthElevation(_:)` view modifier that applies a shadow with the primitive color baked in. Never call `.shadow(color:radius:x:y:)` directly.

---

## Typography → `Font` extensions

Three font families ship in the bundle: **Fraunces** (display), **Inter** (sans), **JetBrains Mono** (mono). All three are free, OFL/SIL-licensed, variable, and embedded — no runtime download, no Google CDN call.

### Font registration

1. Place TTF/OTF files in `mvp/MVP/Assets.xcassets/Fonts/` (Xcode asset-catalog Fonts folder). One variable file per family is sufficient:
   - `Fraunces[opsz,SOFT,WONK,wght].ttf`
   - `Inter[opsz,wght].ttf`
   - `JetBrainsMono[wght].ttf`
2. Add the **Fonts/** folder to the target's **Copy Bundle Resources** build phase (asset-catalog Fonts handles this automatically in Xcode 15+).
3. Declare in `mvp/MVP/Info.plist`:

   ```xml
   <key>UIAppFonts</key>
   <array>
     <string>Fraunces[opsz,SOFT,WONK,wght].ttf</string>
     <string>Inter[opsz,wght].ttf</string>
     <string>JetBrainsMono[wght].ttf</string>
   </array>
   ```
4. Verify at launch in a `#if DEBUG` block: enumerate `UIFont.familyNames` and assert `Fraunces`, `Inter`, `JetBrains Mono` are present. Crash fast in debug if missing — silent fallback to system fonts is a token violation.

### Token → `Font` accessor

| Token | Swift accessor | Family | Size / Line | Weight |
|---|---|---|---|---|
| `type/display-xl` | `Font.hearthDisplayXL` | Fraunces | 56 / 60 | 600 |
| `type/display-lg` | `Font.hearthDisplayLG` | Fraunces | 40 / 44 | 600 |
| `type/display-md` | `Font.hearthDisplayMD` | Fraunces | 28 / 32 | 600 |
| `type/title-lg` | `Font.hearthTitleLG` | Inter | 20 / 24 | 600 |
| `type/title-md` | `Font.hearthTitleMD` | Inter | 16 / 22 | 600 |
| `type/body-lg` | `Font.hearthBodyLG` | Inter | 17 / 26 | 400 |
| `type/body-md` | `Font.hearthBodyMD` | Inter | 15 / 22 | 400 |
| `type/body-sm` | `Font.hearthBodySM` | Inter | 13 / 18 | 400 |
| `type/label` | `Font.hearthLabel` | Inter | 11 / 14 | 600 |
| `type/caption-mono` | `Font.hearthCaptionMono` | JetBrains Mono | 12 / 16 | 400 |

Tracking and uppercase transforms for `type/label` happen at the call site (`.tracking(0.66).textCase(.uppercase)`). Line height is applied via `.lineSpacing(_:)` computed from the table above.

### Dynamic Type

Body tokens (`body-lg`, `body-md`, `body-sm`, `title-lg`, `title-md`) **must** respect Dynamic Type. Use `Font.custom("Inter", size: 17, relativeTo: .body)` rather than fixed-point `Font.custom("Inter", size: 17)`. Display tokens (`display-xl`, `display-lg`, `display-md`) opt out of Dynamic Type by using the fixed-size initializer — these are editorial hero compositions and must not reflow.

---

## Motion

Token → SwiftUI animation:

| Token | Swift accessor | Animation |
|---|---|---|
| `motion/instant` | `Animation.hearthInstant` | `.linear(duration: 0)` |
| `motion/fast` | `Animation.hearthFast` | `.easeOut(duration: 0.12)` |
| `motion/base` | `Animation.hearthBase` | `.easeOut(duration: 0.20)` |
| `motion/slow` | `Animation.hearthSlow` | `.easeInOut(duration: 0.32)` |
| `motion/spring` | `Animation.hearthSpring` | `.interactiveSpring(response: 0.4, dampingFraction: 0.85)` |

Press feedback on every interactive surface uses `.hearthSpring` with a `.scaleEffect(isPressed ? 0.97 : 1.0)`. Sheet presentation uses `.hearthBase`. Tab switches use `.hearthFast`. Crisis-lock surfaces use `.hearthInstant` — no animation, ever.

### Reduce motion

`@Environment(\.accessibilityReduceMotion) var reduceMotion` collapses every `Animation.hearth*` accessor to `.hearthInstant`. Implement once in `Theme.swift` as a single resolver and call it from every animation site — never branch on `reduceMotion` in a `View`.

---

## Touch targets

Hard floor: **44pt × 44pt** for every tappable region. This is non-negotiable and overrides any visual sizing instinct.

| Element | Visual size | Hit area | How |
|---|---|---|---|
| Icon button (chrome) | 24pt glyph | 44 × 44 | `.frame(width: 44, height: 44)` + `.contentShape(Rectangle())` |
| Tab bar item | 28pt glyph + label | 56 × 56 | tab bar height = `.hearth1000` |
| Filter chip | text + `.hearth400` padding | min 44 high | `.frame(minHeight: 44)` |
| Form field row | text + `.hearth500` padding | min 48 high | row padding `.hearth500` vertical |
| Inline link | text | full text bounds + `.hearth300` | `.padding(.vertical, .hearth300)` |

Buttons whose visual size is smaller than 44pt must extend their tap region via `.contentShape(Rectangle())` over a transparent `.frame(...)`. Verify in Accessibility Inspector → Audit.

Spacing between adjacent tap targets is at least `.hearth300` (8pt) — never let two 44pt regions touch.

---

## Navigation

`NavigationStack` only — no `NavigationView`. Every screen is a `NavigationStack` root or a pushed destination.

### Toolbar conventions

```swift
.toolbar {
    ToolbarItem(placement: .principal) {
        Text("Library").font(.hearthTitleLG).foregroundStyle(.hearthInkPrimary)
    }
    ToolbarItem(placement: .topBarTrailing) {
        Button { /* … */ } label: { Image(systemName: "magnifyingglass") }
            .tint(.hearthInkPrimary)
    }
}
.toolbarBackground(Color.hearthCanvas, for: .navigationBar)
.toolbarBackground(.visible, for: .navigationBar)
.navigationBarTitleDisplayMode(.inline)
```

| Convention | Rule |
|---|---|
| Title display mode | `.inline` for utility screens, `.large` for editorial roots (Library, Home). |
| Title font | inline uses `type/title-lg`; large uses `type/display-md` via `.toolbarTitleDisplayMode`. |
| Back chevron | system default; tint = `ink/primary`. Never custom-art the back button. |
| Trailing actions | max two, `ink/primary` tint, 44pt hit area. |
| Toolbar background | always `bg/canvas` visible; never translucent material on top of photography (it muddies the photo). |
| Tab bar | custom `HearthTabBar` view in `mvp/MVP/`; height `.hearth1000`; 56pt items; selected item olive, unselected `ink/muted`. |
| Sheet presentation | `.presentationDetents([.medium, .large])` + `.presentationDragIndicator(.visible)` + corner radius `shape/xl`. |

Modal sheets use `.sheet(item:)` over `.sheet(isPresented:)` whenever the sheet binds to a payload — fewer race conditions, cleaner state.

---

## Dark mode posture — Phase 2

Dark mode is **not** shipped at v1. Tokens are designed to support it (cream-canvas inversion to a warm-ink canvas, not to pure black), but no `.preferredColorScheme(.dark)` work lands in Phase 1.

Phase 1 posture:

```swift
@main
struct MVPApp: App {
    var body: some Scene {
        WindowGroup { RootView() }
            .preferredColorScheme(.light)   // lock to light until Phase 2
    }
}
```

Phase 2 will introduce a `bg/canvas-dark`, `ink/primary-dark`, etc. token set in `DESIGN.tokens.md` and a `@Environment(\.colorScheme)`-aware resolver in `Theme.swift`. No view-level dark logic — all branching happens in the token resolver.

Until then: every screenshot, every Xcode Preview, every TestFlight build is light-mode-locked. Crisis-lock and kid-agent surfaces honour the same light lock (sober surfaces are `bg/sober`, not a dark theme).

---

## Rules

- Never declare a raw hex color, point value, font name, or shadow tuple outside `Theme.swift` / `Theme+Typography.swift`.
- Every tappable region is ≥ 44pt × 44pt; verify in Accessibility Inspector before merge.
- Body-tier type tokens use `relativeTo:` so Dynamic Type works; display-tier tokens are fixed-size by design.
- Every `Animation.hearth*` accessor routes through the reduce-motion resolver — never branch on `accessibilityReduceMotion` in a `View`.
- Use `NavigationStack`, never `NavigationView`; toolbar background is always opaque `bg/canvas`.
- Sheets prefer `.sheet(item:)` over `.sheet(isPresented:)` whenever a payload exists.
- Crisis-lock and kid-agent surfaces use `bg/sober`, `motion/instant`, and disable all photography tiles.
- Lock the app to `.light` color scheme until Phase 2 dark-mode tokens land.
- Fail-fast in `#if DEBUG` if Fraunces / Inter / JetBrains Mono are not registered at launch.
- Spacing between adjacent tap targets is ≥ `.hearth300` (8pt) — adjacent 44pt regions never touch.

---

## Render check

The implementation must render these five canonical compositions and they must look right next to each other in an Xcode Preview gallery (`Theme_Previews.swift`).

1. **Home root.** `NavigationStack` + large title "Library" in Fraunces, `bg/canvas`, two-column category-tile grid (saffron + forest photo tiles), bottom `HearthTabBar` with five items, selected = olive.
2. **Article reader.** Hero photo full-bleed top, byline in `type/caption-mono` over `ink/muted`, body in `type/body-lg` Inter with `.lineSpacing` matching token, end card (next-article CTA) at bottom.
3. **Kid-agent chat (sober).** `bg/sober`, no photography, `type/body-md`, send button = `accent/default` filled, no animations beyond `motion/instant`, 44pt tap targets visible in the Xcode debug overlay.
4. **Crisis lock screen.** `bg/sober`, single `type/display-md` headline in `ink/primary`, one olive button "Call support", no photo, no motion, no chrome.
5. **Settings sheet.** `.sheet(item:)` presentation, drag indicator visible, corner radius `shape/xl`, `bg/elevated`, form rows at 48pt min height, primary action pinned bottom with safe-area `.hearth500` padding.

Each composition must pass the Accessibility Inspector audit with zero contrast or hit-target findings before it is considered "rendered."

---

## Tokens used

| Layer | Tokens |
|---|---|
| Color | `bg/canvas`, `bg/elevated`, `bg/sober`, `ink/primary`, `ink/secondary`, `ink/muted`, `ink/placeholder`, `ink/onPhoto-dark`, `ink/onPhoto-light`, `border/hairline`, `border/strong`, `accent/default`, `accent/press`, `accent/tint`, `focus/ring-on-light`, `focus/ring-on-photo`, `photo/saffron`, `photo/rose`, `photo/royal`, `photo/forest`, `status/success`, `status/warning`, `status/error`, `status/error-tint`, `status/warning-tint`, `status/success-tint`, `status/info` |
| Type | `type/display-xl`, `type/display-lg`, `type/display-md`, `type/title-lg`, `type/title-md`, `type/body-lg`, `type/body-md`, `type/body-sm`, `type/label`, `type/caption-mono` |
| Spacing | `spacing/0`, `spacing/300` through `spacing/1000` (9-step scale) |
| Shape | `shape/none`, `shape/sm`, `shape/md`, `shape/lg`, `shape/xl`, `shape/pill` |
| Motion | `motion/instant`, `motion/fast`, `motion/base`, `motion/slow`, `motion/spring` |
| Elevation | `elevation/0`, `elevation/1`, `elevation/2`, `elevation/3` |

---

status: 🔨 draft
owner: Miguel
last_updated: 2026-05-31
