# Next Level local concept

Working name; no brand clearance. Synthetic, scripted browser prototype, separate from the live MVP product. This does not implement a model, sign-in, persistence, reminders, diagnosis, sharing connector, or scientific personalization. Please use fictional examples only.

From the worktree root:

```sh
python3 -m http.server 8937 --bind 127.0.0.1 --directory experiments/next-level
```

Open http://127.0.0.1:8937 . Refresh clears conversation/notes. Forget & restart clears conversation and restores the clearly labeled synthetic understanding examples. There is no localStorage, IndexedDB, cookie or fetch call. Content Security Policy blocks connections. The HTTP server still logs local asset requests; no conversation content is sent to it.

```sh
node --test experiments/next-level/model.test.mjs
node --check experiments/next-level/app.mjs
```

`browser-check.cjs` uses an existing host playwright-core installation by absolute path, temporary headless Chrome, and localhost port 8937. Its tests and screenshots are reproducible on this host; for another machine install playwright-core and adjust the require path. It never reuses a signed-in browser profile.

Views: conversation → reviewed observation → small experiment → check-in; Understanding (strengths, parent-attributed child perspective, uncertain context); Share preview (default minimal selection, blocks sensitive/unreviewed notes, JSON download only). Editing an observation clears the old plan/outcomes and revokes its remembered status. Editing an understanding note removes it from the share selection until review.

Known limits: one scripted morning scenario; fixed synthetic IDs and dates; no adaptive coaching; no validated developmental assessment; scripted health/safety language; no authentication/tenant isolation/deletion infrastructure; no true persistence; no connectors. The reminder is a displayed return flow, not a scheduled delivery. Security tests verify local UI/model rules only, not production boundaries.

The share filter enforces record tags, not semantic redaction. Pasted health/identifier text can appear in any edited free-text field. Do not use real data. Before a real export, classify sensitivity, minimize identifiers, review exact text and validate recipient/purpose policy; no “automatic safe sharing” claim is supported by this prototype.
