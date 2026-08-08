#!/usr/bin/env python3
"""Hearth design-token linter.

The token allowlist (`spec/look-and-feel/DESIGN.tokens.md`) has always claimed to
be gated by this script. It never existed. The beta-v1 redesign is what made it
worth writing: darkening the canvas from cream-100 to cream-200 silently pushed
`ink/muted` and accent-as-text BELOW the AA floor, and nothing caught it — the
pairs still "used tokens", they just no longer passed. Token discipline alone
does not buy accessibility; the pairs have to be checked.

Three checks:

  1. CONTRAST   — every declared (foreground, background) pair meets its floor.
  2. DRIFT      — the hexes in `Theme.swift`'s HearthPrimitives are exactly the
                  set documented in DESIGN.tokens.md. Catches a primitive added
                  to code but never written down, or a doc value left stale.
  3. NO-INLINE  — no Swift file outside Theme.swift declares a raw hex color.
                  This is Hearth rule #1 and it is the one that actually rots.

Usage:
    python3 tools/lint-design-tokens.py              # all checks
    python3 tools/lint-design-tokens.py --contrast   # contrast only

Exit code 0 = clean, 1 = at least one violation.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOKENS_DOC = REPO / "spec" / "look-and-feel" / "DESIGN.tokens.md"
THEME_SWIFT = REPO / "mvp" / "MVP" / "Theme.swift"
SWIFT_ROOT = REPO / "mvp" / "MVP"

AA_TEXT = 4.5   # WCAG 1.4.3 normal text
UI_FLOOR = 3.0  # WCAG 1.4.11 non-text contrast / large text

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")


# ── contrast maths (WCAG 2.1 relative luminance) ─────────────────────

def _channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ── the declared pairs ───────────────────────────────────────────────
#
# Every pair a shipped surface actually renders. Adding a surface that
# combines two tokens means adding the pair here — that is the point.
# `note` documents a deliberate, argued exception; those are reported but
# do not fail the build.

CANVAS = "#E9E4DC"
SOBER = "#F3F0EB"
PAPER = "#FFFFFF"
VOICE = "#2E3A5F"
TEAL_FILL = "#1B7498"
# Was #186A8B (4.78:1, AA-passing). Miguel chose exact-Figma fidelity over the
# accessibility fix on 2026-08-07, so text and fill are now the same value and
# the on-canvas text pairs below are WAIVED with their measured ratios.
TEAL_TEXT = "#1B7498"
SAFFRON = "#E89C2E"
SAFFRON_TINT = "#F8EBD6"
DISABLED = "#B8B4AC"
INK_900 = "#1A1A1A"
INK_700 = "#2D2D2D"
INK_500 = "#666157"
INK_300 = "#8A8275"
CARD_CREAM = "#F5F3EF"
TAB_SELECTED = "#DAE0DF"
INK_800 = "#1E1E1E"
INK_HEADER = "#2B2925"
NEUTRAL_500 = "#858585"

PAIRS: list[tuple[str, str, str, float, str | None]] = [
    # (label, foreground, background, floor, deliberate-exception note)
    ("ink/primary on canvas",            INK_900,   CANVAS,       AA_TEXT, None),
    ("ink/secondary on canvas",          INK_700,   CANVAS,       AA_TEXT, None),
    ("ink/muted on canvas",              INK_500,   CANVAS,       AA_TEXT, None),
    ("ink/muted on paper",               INK_500,   PAPER,        AA_TEXT, None),
    ("ink/muted on sober",               INK_500,   SOBER,        AA_TEXT, None),
    ("ink/placeholder on canvas",        INK_300,   CANVAS,       UI_FLOOR, None),
    ("ink/primary on paper",             INK_900,   PAPER,        AA_TEXT, None),

    # The accent split. The fill and the on-canvas text variant are
    # different hexes precisely because one value cannot serve both.
    ("paper on accent/default (button)", PAPER,     TEAL_FILL,    AA_TEXT, None),
    ("accent/onCanvas as text on canvas", TEAL_TEXT, CANVAS,      AA_TEXT,
     "Matches Greg's Figma exactly (#1B7498 as drawn). Miguel's explicit call 2026-08-07, choosing design fidelity over the AA fix: #186A8B measured 4.78:1 and was visually indistinguishable. Revert by changing ONE primitive (HearthPrimitives.teal600) if this is revisited. Raised with Greg in the Figma eng-review comment."),
    ("accent/onCanvas as text on paper",  TEAL_TEXT, PAPER,       AA_TEXT, None),

    # beta-v1 sprint-1 fidelity pass (2026-08-08) — measured Figma values.
    ("ink/onCard on accent/default",      CARD_CREAM, TEAL_FILL,  AA_TEXT, None),
    ("accent/onCanvas on tab-selected",   TEAL_TEXT, TAB_SELECTED, AA_TEXT,
     "Matches Greg's Figma exactly (#1B7498 as drawn). Miguel's explicit call 2026-08-07, choosing design fidelity over the AA fix: #186A8B measured 4.78:1 and was visually indistinguishable. Revert by changing ONE primitive (HearthPrimitives.teal600) if this is revisited. Raised with Greg in the Figma eng-review comment."),
    ("ink/display on card",               INK_800,   CARD_CREAM,  AA_TEXT, None),
    ("ink/header on card",                INK_HEADER, CARD_CREAM, AA_TEXT, None),
    ("paper on bg/neutral (sign out)",    PAPER,     NEUTRAL_500, AA_TEXT,
     "Grey sign-out fill is the design's own value (#858585). Flagged to Greg: "
     "on iOS a grey button reads as DISABLED, and destructive actions are "
     "conventionally red. Implemented as drawn pending his answer."),
    ("accent/default as text on paper",   TEAL_FILL, PAPER,       AA_TEXT, None),

    # Kid accent.
    ("ink/onPhoto-dark on accent/kid",   INK_900,   SAFFRON,      AA_TEXT, None),
    ("ink/primary on accent/kid-tint",   INK_900,   SAFFRON_TINT, AA_TEXT, None),
    ("paper on accent/kid (monogram)",   PAPER,     SAFFRON,      AA_TEXT,
     "Decorative monogram only — the kid's name is always rendered adjacent, "
     "so the letter is never the sole carrier of its information."),

    # Voice surface.
    ("ink/onPhoto-light on bg/voice",    PAPER,     VOICE,        AA_TEXT, None),

    # Disabled control.
    ("ink/secondary on bg/disabled",     INK_700,   DISABLED,     AA_TEXT, None),
]


def check_contrast() -> list[str]:
    failures: list[str] = []
    print("── contrast ──")
    for label, fg, bg, floor, note in PAIRS:
        ratio = contrast(fg, bg)
        ok = ratio >= floor
        if ok:
            print(f"  PASS  {ratio:5.2f}:1  (>= {floor})  {label}")
        elif note:
            print(f"  WAIVED {ratio:5.2f}:1  (< {floor})  {label}")
            print(f"         {note}")
        else:
            print(f"  FAIL  {ratio:5.2f}:1  (< {floor})  {label}")
            failures.append(f"contrast: {label} is {ratio:.2f}:1, needs {floor}:1")
    return failures


def check_drift() -> list[str]:
    """The hexes in Theme.swift must be exactly those documented."""
    failures: list[str] = []
    print("\n── spec/code drift ──")
    if not THEME_SWIFT.exists() or not TOKENS_DOC.exists():
        print("  SKIP  Theme.swift or DESIGN.tokens.md not found")
        return failures

    theme_src = THEME_SWIFT.read_text()
    # Only the primitives block declares raw hex.
    block = theme_src.split("enum HearthPrimitives")[-1]
    in_code = {h.upper() for h in HEX_RE.findall(block)}
    in_doc = {h.upper() for h in HEX_RE.findall(TOKENS_DOC.read_text())}

    undocumented = in_code - in_doc
    unused = in_doc - in_code

    for h in sorted(undocumented):
        print(f"  FAIL  {h} is in Theme.swift but not in DESIGN.tokens.md")
        failures.append(f"drift: {h} undocumented")
    for h in sorted(unused):
        # The doc also documents shadow rgba bases and prose examples; only
        # flag these as informational.
        print(f"  INFO  {h} is documented but not used by Theme.swift")
    if not undocumented:
        print(f"  PASS  all {len(in_code)} primitives in Theme.swift are documented")
    return failures


def check_no_inline_hex() -> list[str]:
    """Hearth rule #1: raw hex lives in Theme.swift and nowhere else."""
    failures: list[str] = []
    print("\n── inline hex ──")
    offenders = 0
    for path in sorted(SWIFT_ROOT.rglob("*.swift")):
        if path.name == "Theme.swift":
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("///"):
                continue
            for hex_value in HEX_RE.findall(line):
                rel = path.relative_to(REPO)
                print(f"  FAIL  {rel}:{lineno} declares raw hex {hex_value}")
                failures.append(f"inline-hex: {rel}:{lineno} {hex_value}")
                offenders += 1
    if offenders == 0:
        print("  PASS  no Swift file outside Theme.swift declares a raw hex")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Hearth design-token linter")
    parser.add_argument("--contrast", action="store_true",
                        help="run only the contrast check")
    args = parser.parse_args()

    failures: list[str] = []
    failures += check_contrast()
    if not args.contrast:
        failures += check_drift()
        failures += check_no_inline_hex()

    print()
    if failures:
        print(f"✘ {len(failures)} violation(s)")
        for f in failures:
            print(f"   - {f}")
        return 1
    print("✓ tokens clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
