# Iteration 2: how the parent shows up

Synthetic, scripted local reflection. No model, account, persistence, clinical scale, alliance score, microphone/camera, child session, reminder or connector. Prior prototype remains at `../next-level/`.

From the worktree root:

```sh
python3 -m http.server 8938 --bind 127.0.0.1 --directory experiments/next-level-iteration-2
```

Open http://127.0.0.1:8938 . Refresh or Forget & restart clears the in-tab episode and sharing choice. CSP blocks connections; no fetch, localStorage, IndexedDB, cookies or telemetry. Local HTTP logs contain asset requests, not reflection content. Use only fictional information.

Three scripted examples: school-morning transition, shared joy in a cardboard world, and repair after an adult raises their voice. Review observable event → choose/skip adult capacity → consider one parent adjustment → rehearse privately without recording → try later → reflect. A child staying upset, disagreeing, declining or going quiet does not establish parental failure or connection. No child is asked to regulate an adult or forgive them.

The reflection view separates observation, parent interpretation, possibilities, absent/parent-reported child perspective, private adult context and chosen action. These are dimensions of reflection, not measured relationship constructs or a score. Parent-private context, child words and hypotheses are omitted from the initial manual brief.

```sh
node --test experiments/next-level-iteration-2/model.test.mjs
node --check experiments/next-level-iteration-2/app.mjs
node experiments/next-level-iteration-2/browser-check.cjs
```

The browser check uses host Chrome and an existing playwright-core installation; set `NEXT_LEVEL_PLAYWRIGHT` to its module path elsewhere. It opens a temporary headless profile and saves synthetic captures to `docs/next-level/iteration-2/screenshots/`.

Limits: correcting an observation clears prior context/interpretations and yields an unknown/reflection-only path; the app does not analyze corrected text and disables its export. There is no adaptive safety or clinical assessment. Sensitive text in a reviewed free-text observation is not automatically detected/redacted. Flags and UI filtering do not establish safe real-data export. No claim of validated Dr. Becky content, effectiveness, parent-child measurement, or superiority to competitors is supported by this implementation.
