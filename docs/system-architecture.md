# MVP — System Architecture

A parenting app with four AI agents (parent coach, kid companion, **chief-of-staff**,
and a **deep-research** background agent), a content library, and ElevenLabs voice.
Backend is FastAPI + LangGraph + DuckDB; clients are a SwiftUI iOS app and React web apps.

> **Legend:** 🟢 = activity-planning / chief-of-staff capability (newest, branch
> `feat/activity-planning-chief-of-staff`). Everything else is shipped.

---

## 1. System context

```mermaid
flowchart TB
    subgraph Clients
        iOS["📱 iOS app (SwiftUI)<br/>Home · Library · Coach · Circle<br/>🟢 Plan (pending)"]
        CMS["🖥️ CMS web (Vite/React)<br/>admin — X-Admin-Token"]
        DASH["🟢 Parent dashboard (planned)<br/>same login as the app"]
    end

    subgraph Backend["FastAPI backend — app/server.py @ :8904"]
        API["HTTP / SSE API"]
        WORKER["🟢 Research worker<br/>(daemon thread)"]
    end

    subgraph Data["Storage"]
        DUCK[("DuckDB<br/>app/duckdb_storage.py")]
        PARQ[("Parquet snapshots<br/>(volume-durable)")]
    end

    subgraph External["External services"]
        OAI["OpenAI<br/>gpt-5.x"]
        TAV["Tavily<br/>web search"]
        EL["ElevenLabs<br/>ConvAI v2 voice"]
        SLACK["Slack<br/>alerts"]
        GOOG["🟢 Google OAuth<br/>Gmail + Calendar (Phase 3)"]
    end

    iOS -->|"Bearer token"| API
    CMS -->|"X-Admin-Token"| API
    DASH -.->|"Bearer token"| API

    API <--> DUCK
    DUCK <-->|"bootstrap / export"| PARQ
    WORKER --> DUCK

    API --> OAI
    API --> TAV
    API --> EL
    API --> SLACK
    WORKER --> OAI
    WORKER --> TAV
    API -.-> GOOG

    iOS <-->|"WebSocket (voice)"| EL
```

---

## 2. Backend internals — agents, services, storage

```mermaid
flowchart LR
    subgraph Edge["Edge"]
        AUTH["auth.py<br/>opaque bearer tokens"]
        RL["rate_limit.py<br/>token buckets:<br/>chat · config · auth · 🟢research"]
    end

    subgraph Agents["Agents (LangGraph create_agent / deepagents)"]
        COACH["Parent coach<br/>agent.py<br/>/chat · /onboarding-chat"]
        KID["Kid companion<br/>kid_agent.py + prompt_synthesis.py<br/>/kid-chat"]
        MOD["moderation.py<br/>crisis regex → OpenAI mod →<br/>age classifier → output gate"]
        COS["🟢 Chief-of-staff<br/>cos/agent.py + cos/tools.py<br/>/cos/chat"]
        RESEARCH["🟢 Deep research (deepagents)<br/>research/graph.py<br/>record-tool → candidates"]
    end

    subgraph Services["Domain services"]
        PROF["profiling.py<br/>parent + child profiles"]
        CONTENT["content.py<br/>library + community"]
        SUMM["summary.py<br/>daily digests"]
        PLAN["🟢 cos/planning.py (pure)<br/>cost · conflicts · eligibility · gaps"]
        VOICE["convai endpoints<br/>signed ElevenLabs tokens"]
        TEL["telemetry.py → Slack"]
    end

    STORE[("duckdb_storage.py<br/>thread-safe DuckDB + parquet")]

    AUTH --> Agents
    RL --> Agents
    KID --> MOD
    COACH --> PROF
    KID --> PROF
    COS --> PLAN
    COS --> PROF
    RESEARCH -->|"writes candidates"| STORE
    COS --> STORE
    COACH --> STORE
    KID --> STORE
    MOD --> STORE
    CONTENT --> STORE
    SUMM --> STORE
    PROF --> STORE
    TEL -.-> MOD
```

**Agent isolation:** the coach, kid, and chief-of-staff agents each have their **own**
`ChatOpenAI`, checkpointer, and per-user cache — no shared state, so a regression in one
can't affect the others. The research agent is `deepagents` (planning + sub-agents +
filesystem harness) with an explicit OpenAI model (deepagents defaults to Anthropic).

---

## 3. 🟢 Activity-planning capability (the new flow)

Two cooperating pieces: a **background research agent** that discovers activities, and an
interactive **chief-of-staff** agent that turns discoveries into a coordinated plan.

### 3a. Discovery — research run lifecycle (async, poll-based)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant API as /research router
    participant DB as research_runs
    participant W as Research worker (thread)
    participant DA as deepagents + Tavily + OpenAI

    C->>API: POST /research/runs {location?, params?}
    API->>DB: insert run (status=queued)<br/>location+kids from profile
    API->>W: notify()
    API-->>C: {run_id, status:"queued"}  (instant)

    W->>DB: claim_next_queued_run() → running
    W->>DA: discover_activities(location, kids)
    loop plan → search → record
        DA->>DA: write_todos · Tavily search
        DA->>DA: record_activity_candidate(...)  (structured)
    end
    DA-->>W: [candidates]
    W->>DB: insert_activity_candidates (delete-then-insert = idempotent)
    W->>DB: status=done, candidate_count=N

    C->>API: GET /research/runs/{id}  (poll)
    API-->>C: {status, progress, candidate_count}
    C->>API: GET /research/runs/{id}/candidates
    API-->>C: ranked candidates (fit_score)
```

Durability: the `research_runs` row **is** the job (the phone never holds it). On restart a
startup sweeper re-queues anything left `running`; re-runs are idempotent.

### 3b. Coordination — chief-of-staff

```mermaid
flowchart TB
    subgraph COSAgent["🟢 /cos/chat (SSE) — cos/agent.py"]
        LLM["isolated ChatOpenAI + MemorySaver"]
        TOOLS["12 tools (cos/tools.py)"]
    end

    subgraph Tools["Tools mutate the plan; GetPlanSnapshot reads it"]
        T1["TrackActivity (pending/confirmed)"]
        T2["AddToCalendar · AddRecurringAppointment"]
        T3["AddCaregiver · AssignLogistics (gap)"]
        T4["AddTodo · CompleteTodo"]
        T5["SearchActivities (candidates)"]
        T6["CheckEligibility · GetPlanSnapshot"]
        T7["DraftEmail (never sends — HITL)"]
    end

    PLAN["🟢 cos/planning.py (pure)<br/>build_plan_summary →<br/>cost · conflicts · eligibility · gaps · uncovered"]
    STORE[("tracked_activities · calendar_entries<br/>recurring_appointments · caregivers<br/>logistics_assignments · todo_items")]

    LLM --> TOOLS --> Tools
    Tools --> STORE
    Tools --> PLAN
    PLAN --> STORE
    STORE -->|"GET /cos/plan/summary"| PLAN
```

`GET /cos/plan/summary` returns the workbook's derived intelligence: running **cost** tally
(confirmed vs TBD), **time conflicts** (camp hours vs therapy), **age-eligibility** flags,
caregiver **coverage gaps**, and **uncovered weeks**.

### 3c. (Phase 3, planned) Multimodal ingestion → plan

```mermaid
flowchart LR
    PASTE["POST /ingest/text<br/>(email / iMessage paste)"]
    PHOTO["POST /ingest/image<br/>(flyer / form / screenshot)"]
    GMAIL["Gmail sync (OAuth)"]
    EXTRACT["extract.py (2-stage)<br/>text path | vision path<br/>→ ExtractedActivity"]
    SPAWN["tracked_activities (pending)<br/>+ todo_items + calendar_entries"]

    PASTE --> EXTRACT
    PHOTO --> EXTRACT
    GMAIL --> EXTRACT
    EXTRACT --> SPAWN
```

---

## 4. Data model (DuckDB)

All tables bootstrap from parquet snapshots on startup and export back on writes/shutdown.
User-state parquets are excluded from the Docker build context (prod keeps its own volume copy).

```mermaid
erDiagram
    user_data ||--o{ research_runs : "user_id"
    research_runs ||--o{ activity_candidates : "run_id"
    activity_candidates ||--o{ tracked_activities : "candidate_id (nullable)"
    tracked_activities ||--o{ calendar_entries : "activity_id (nullable)"
    tracked_activities ||--o{ todo_items : "activity_id (nullable)"
    calendar_entries ||--o{ logistics_assignments : "calendar_entry_id"
    caregivers ||--o{ logistics_assignments : "caregiver_id"
    ingest_artifacts ||--o{ todo_items : "source_artifact_id"
```

| Domain | Tables |
|---|---|
| Core / auth | `user_data`, `auth_tokens`, `consent_records`, `audit_events` |
| Content | `categories`, `articles`, `community_posts`, `post_replies` |
| Kid companion | `kid_agent_configs`, `kid_messages`, `kid_credentials`, `moderation_events`, `kid_agent_crisis_locks`, `daily_summaries` |
| 🟢 Discovery | `research_runs`, `activity_candidates` |
| 🟢 Coordination | `tracked_activities`, `calendar_entries`, `recurring_appointments`, `caregivers`, `logistics_assignments`, `todo_items`, `cos_messages` |
| 🟢 Ingestion (Phase 3) | `ingest_artifacts`, `google_oauth_tokens` |

---

## 5. Cross-cutting

- **Auth:** opaque bearer tokens (`/auth/issue-token`), hashed at rest; `authorize_user_match`
  blocks cross-user access on every write.
- **Rate limiting:** in-process token buckets per `(user, class)` — `chat`, `config`, `auth`,
  🟢`research` (runs are expensive → 20/hr).
- **Moderation (kid only):** deterministic crisis regex → OpenAI moderation → age classifier →
  streaming output gate; crisis trips a persistent lock until a parent revives it.
- **Streaming:** SSE everywhere a model streams (`/chat`, `/kid-chat`, 🟢`/cos/chat`) —
  `data: {"type":"token","content":...}` … `data: [DONE]`.
- **Voice:** ElevenLabs **ConvAI v2** only (v1 per-fragment TTS removed); backend issues signed
  WebSocket tokens, the client connects to ElevenLabs directly.
- **Concurrency:** one DuckDB connection behind an RLock (`_ThreadSafeConn`); the research
  worker and request threads serialize through it.

---

## 6. Stack

| Layer | Tech |
|---|---|
| iOS | SwiftUI, MarkdownUI, Hearth design system (Fraunces/Inter/JetBrains Mono) |
| Web | Vite 8 · React 19 · TS · Tailwind 4 (CMS today; 🟢 parent dashboard planned) |
| Backend | FastAPI · LangGraph 1.2 · LangChain 1.3 · 🟢 deepagents 0.6 · DuckDB |
| Models | OpenAI gpt-5.x (agents · moderation · synthesis · 🟢 research/extraction) |
| Search | Tavily (coach 2 results; 🟢 research 8, advanced depth) |
| Voice | ElevenLabs ConvAI v2 |
| Deploy | Railway (single instance, mounted volume for DuckDB + parquet) |
```
