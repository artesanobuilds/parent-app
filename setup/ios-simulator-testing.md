# Automated iOS Simulator Testing with Claude Code

**TL;DR:** With three tools installed, Claude Code can autonomously build an iOS app, launch it in the Simulator, tap buttons, fill forms, navigate multi-screen flows, and verify results — no hand-testing, no XCUITest targets, no test scripts to maintain. The key mechanism is the **iOS accessibility tree**: Claude reads the screen as structured JSON and taps elements by their accessibility label, not pixel coordinates, so interactions survive UI redesigns.

## How it works

The iOS Simulator exposes every on-screen element (type, label, identifier, frame, value) through Apple's accessibility APIs. Tools built on Meta's idb frameworks can dump this tree and synthesize HID events (taps, swipes, keystrokes). Claude's loop is:

1. **Read** — dump the accessibility tree (`axe describe-ui`) → JSON list of elements. Far cheaper token-wise than interpreting a screenshot, and machine-precise.
2. **Act** — tap by label/ID (`axe tap --label "Continue"`), type into the focused field, swipe, press hardware keys.
3. **Verify** — re-read the tree to confirm the expected screen/state appeared; take a screenshot (which Claude reads as an image) for visual checks.

Because SwiftUI auto-derives accessibility labels from visible text, this works on most apps **without adding accessibility identifiers first** — even custom controls (we verified against a fully custom tab bar). The fallback chain is: accessibility ID → label → raw coordinates from the tree's `frame`. Adding `.accessibilityIdentifier()` to icon-only/custom controls improves reliability but is not a prerequisite.

## What to install (macOS, Apple Silicon or Intel)

**Prerequisite:** current Xcode Command Line Tools. If brew errors with "Command Line Tools are too outdated": `sudo rm -rf /Library/Developer/CommandLineTools && sudo xcode-select --install` (or `sudo softwareupdate --install "Command Line Tools for Xcode <ver>"`).

**1. AXe** — single-binary CLI for tap/type/swipe/describe-ui/screenshot (github.com/cameroncooke/AXe, actively maintained):

```bash
brew install cameroncooke/axe/axe
# (brew may require: brew trust cameroncooke/axe)
# Fallback if brew is blocked: download the universal tarball from GitHub Releases,
# keep the binary next to its Frameworks/ dir, symlink onto PATH
```

**2. iOS Simulator Skill for Claude Code** (github.com/conorluddy/ios-simulator-skill) — 27 scripts that make the loop token-efficient (a full screen summarized in ~4 lines, build results as one line with drill-down on demand), plus WCAG audits, visual screenshot diffing, push-notification simulation, permission grant/revoke, log monitoring:

```
claude plugin marketplace add conorluddy/ios-simulator-skill
claude plugin install ios-simulator-skill@conorluddy
```

(restart Claude Code to load it)

**3. idb** — Meta's iOS Development Bridge; the skill's interaction scripts call it:

```bash
brew tap facebook/fb && brew trust facebook/fb && brew install idb-companion
pip3 install fb-idb   # the client CLI; if Homebrew Python is broken, use: /usr/bin/python3 -m pip install --user fb-idb
```

`xcodebuild` and `xcrun simctl` (build/boot/install/launch/screenshot) come with Xcode — no install needed.

## Claude Code configuration

Add a permission allowlist so the loop runs unattended, keeping destructive ops gated (in `~/.claude/settings.json` or the project's `.claude/settings.json`):

```json
"permissions": {
  "allow": ["Bash(axe *)", "Bash(xcrun simctl *)", "Bash(xcodebuild *)"],
  "ask": ["Bash(xcrun simctl erase*)", "Bash(xcrun simctl delete*)"]
}
```

Optionally, add a short section to the project's CLAUDE.md describing the app's scheme name, bundle ID, and the expected verify loop, so any session knows how to drive the app.

## Gotchas we hit

- **idb text input mangles special characters** (known bug: `@` can arrive as `_`). Use `axe type` for emails/form text — we verified `@` survives.
- **The built `.app` name can differ from the scheme name** — resolve it from the build products dir rather than assuming.
- **Accessibility trees are empty on the home screen and some system dialogs** — screenshots are the fallback there.
- **`axe type` targets the *focused* field** — tap the field first; iOS autocapitalization mutates the first letter.
- **Simulator-only.** All element-level automation (idb/AXe and every MCP variant) fails on physical devices due to iOS restrictions. Real-device coverage stays with TestFlight/humans.

## Alternatives considered

If your team prefers an MCP server over CLI tools: **XcodeBuildMCP** (github.com/getsentry/XcodeBuildMCP, Sentry-maintained, ~82 tools) covers build + simulator + UI automation in one server — it bundles the same AXe engine. One-liner: `claude mcp add XcodeBuildMCP -- npx -y xcodebuildmcp@latest mcp`. We chose the skill+CLI route to avoid always-on MCP tool context; functionally they're equivalent. (If evaluating `ios-simulator-mcp` instead, pin ≥1.3.3 — earlier versions had a command-injection CVE.)

## What it looks like in practice

Verified end-to-end on our app: Claude built with xcodebuild, booted an iPhone 17 Pro sim, installed and launched the app, read the accessibility tree, tapped a tab by label, confirmed the destination screen from the new tree + a screenshot, typed into a chat field, read the value back, and cleared it — zero manual steps. From there, "build the app and test the signup flow" is a single request; Claude finds real bugs (missing confirmations, keyboard covering fields) and reports them with screenshots.
