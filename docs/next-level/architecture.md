# Proposed architecture and UX boundaries

Proposed new product, not the existing production system. The prototype implements only memory-in-tab UI, deterministic rules and filtered synthetic JSON export. See code-audit.md for existing mechanisms and profile-safety.md for a fuller proposed lifecycle.

```mermaid
flowchart LR
  P[Parent conversation] --> E[Ephemeral session]
  E --> D[Draft observation with provenance]
  D --> R[Parent confirms / edits / drops]
  R --> N[Reviewed notes: strengths, interests, perspective, context]
  N --> C[Minimal context builder]
  C --> A[Capped model adapter]
  A --> S[Optional small next step]
  S --> O[Parent outcome or skip]
  O --> R
  N --> V[Selected-note preview]
  V --> X[Manual portable brief]
  X -. No active connector .-> G[Existing general assistant]
  I[Identity auth] --> C
  U[Separate usage consent + provider eligibility] --> A
```

```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> Reviewed: Parent confirms
  Draft --> Dropped: Parent declines
  Reviewed --> SessionOnly: No memory consent
  Reviewed --> Remembered: Explicit memory consent
  Remembered --> ReReview: Correction / contradiction / expiry
  ReReview --> Reviewed
  Remembered --> SharePreview: Parent selects approved low-sensitivity notes
  SharePreview --> ManualExport: Exact text approved
  Remembered --> Deleted: Delete and invalidate dependent notes
  SessionOnly --> [*]: Session ends
```

```mermaid
flowchart TD
  A[What would you like to understand?] --> B[One concrete moment + what matters to child]
  B --> C[Strength / child perspective / situational context]
  C --> D[Visible draft notes]
  D --> E{Parent review}
  E -->|Correct| D
  E -->|Session only| F[Optional small action / observation]
  E -->|Remember| G[Reviewed notebook]
  G --> F
  F --> H[Easier / same / harder / skipped]
  H --> J[Reconsider with uncertainty]
  G --> K[Select minimal context]
  K --> L[See exact brief before manual export]
```

Real build boundaries: stable family/child/note IDs; server-side family authorization; separate draft/inference/confirmed records; versioned consent; source-based expiry and contradictions; encrypted store; no raw chat in analytics; tombstones to prevent deleted notes being re-extracted; deletion cascade plus cache/checkpoint/snapshot verification. Parent-only first. Direct child interaction requires separate adult-auth and session isolation, not merely hiding parent screens.

A data graph is justified only if it beats a short reviewed summary on task utility, safety and burden. Minimize first.
