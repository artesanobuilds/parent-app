# Voice v2 — ElevenLabs Conversational AI Setup

Real-time voice for kid companions via ElevenLabs Conversational AI (WebRTC, sub-150ms).
Our backend stays the brain (LangGraph agent + 5-layer moderation + crisis locks) as a
**Custom LLM**; ElevenLabs handles STT, turn-taking, TTS, and transport.

> Scope: kid companion **and** the parent coaching agent (opt-in "call" mode).
> The parent path adds **client tools** so the voiced coach can surface article /
> community cards on screen — see "Parent voice agent" below.

---

## Two agents at a glance — exact console config (recreation reference)

There are **two** ElevenLabs Conversational AI agents. This table is the canonical
spec to recreate either one from scratch. (Per-agent step-by-step is below.)

| Setting | `kid-companion-v2` | `parent-coach-v2` |
|---|---|---|
| Purpose | kid companion voice | parent coach opt-in "call" mode |
| LLM type | **Custom LLM** | **Custom LLM** |
| **Server URL field** | `https://mvp-backend-production-8678.up.railway.app/v1` | `https://mvp-backend-production-8678.up.railway.app/v1/parent` |
| Resolves to (EL appends `/chat/completions`) | `…/v1/chat/completions` | `…/v1/parent/chat/completions` |
| Backend handler | `app/convai_endpoint.py` (`@router.post("/v1/chat/completions")`) | `app/parent_convai_endpoint.py` (`@router.post("/v1/parent/chat/completions")`) |
| API-key secret (sent as `Authorization: Bearer`) | `ELEVENLABS_CONVAI_SECRET` | **same value** (`ELEVENLABS_CONVAI_SECRET`) |
| Model ID field | anything (e.g. `kid`) — ignored; routes on `elevenlabs_extra_body` | anything (e.g. `parent`) — ignored |
| Security → overrides to enable | System prompt, First message, Language, Voice ID (TTS), **Custom LLM extra body** | System prompt, Language, **Custom LLM extra body** (first-message **not** needed) |
| Client tools | none | `show_article` + `show_community_post`, type **Client**, one param `id` (string, required) |
| System tools | **`end_call`** (crisis hang-up) | none |
| Moderation / crisis / PIN | yes — 5-layer moderation + crisis lock + `kid_pin` | **none** (adult) |
| Turn detection (server VAD silence) | ~1.5 s | ~1.5 s |
| Max conversation duration | ~15 min | ~15 min |
| Voice / first-message / prompt fields | leave **empty** (overridden per connection) | leave **empty** (prompt set per connection) |
| iOS token endpoint | `GET /voice/convai-token` (parent token + `X-Kid-Pin`) | `GET /voice/parent-convai-token` (parent token only) |
| Agent-ID env var | `ELEVENLABS_AGENT_ID` | `ELEVENLABS_PARENT_AGENT_ID` |

**Shared by both agents** (set in local `.env` **and** Railway):
- `ELEVENLABS_API_KEY` — mints the WebRTC conversation token; must have the **`convai_write`** permission.
- `ELEVENLABS_CONVAI_SECRET` — Custom-LLM auth; the console "API key" secret value must **exactly equal** this.

> ⚠️ **#1 footgun — the Server-URL append.** ElevenLabs appends `/chat/completions`
> to whatever you type in the Server URL field. So the kid field ends in **`/v1`** and
> the parent field ends in **`/v1/parent`**. Pitfalls seen in practice:
> - Typing the full `…/chat/completions` path doubles it → `…/chat/completions/chat/completions` → 404.
> - Pointing the **parent** agent at the kid base (`…/v1`) routes it to the kid endpoint, and every turn 400s with `missing user_id or kid_name` (the parent path sends no `kid_name`). This exact misconfig is what made parent voice "connect but never respond."

---

## Parent voice agent (`parent-coach-v2`) — 2026-06-17

A SECOND ElevenLabs agent powers the parent coach's opt-in voice call. It reuses
the same shared audio stack on iOS (`KidVoiceSessionManager`) and the same secret,
but a **separate** Custom-LLM endpoint and token endpoint.

**Backend (deployed):**
- Custom LLM: `POST /v1/parent/chat/completions` (`app/parent_convai_endpoint.py`) — runs the parent agent (`app.agent`), **no moderation/crisis/PIN**. It strips `[Title](mvp://library|community/{id})` links from the spoken text and emits `show_article` / `show_community_post` **client-tool** deltas (`arguments={"id":…}`, `finish_reason:null` so the turn continues). The token endpoint also appends a VOICE-MODE directive to the system prompt (no markdown spoken; keep emitting the links).
- Token: `GET /voice/parent-convai-token` (auth'd parent; no PIN/crisis). Uses env `ELEVENLABS_PARENT_AGENT_ID`.

**Dashboard setup for `parent-coach-v2`:**
1. Create a new agent. LLM → **Custom LLM**. **Server URL field** = `https://mvp-backend-production-8678.up.railway.app/v1/parent` (ElevenLabs appends `/chat/completions` → `…/v1/parent/chat/completions`; do **not** type the full path or it doubles). API-key secret = `ELEVENLABS_CONVAI_SECRET` (same value as the kid agent).
2. **Security tab** → enable overrides: **System prompt**, **Language**, **Custom LLM extra body** (first-message not needed). Same toggles as the kid agent.
3. **Client tools** (the new part) — add two, type **Client**:
   - `show_article` — one parameter `id` (string, required).
   - `show_community_post` — one parameter `id` (string, required).
   - Description e.g. "Display the referenced article/post card on the parent's screen." (Display-only; the app acks, the agent keeps talking.)
4. Pick a warm adult voice; turn detection ~1.5s. **Publish**, copy the **Agent ID**.

**Env vars:** add `ELEVENLABS_PARENT_AGENT_ID=<id>` to local `.env` **and** Railway. (Reuses `ELEVENLABS_API_KEY` + `ELEVENLABS_CONVAI_SECRET`.) Until set, `/voice/parent-convai-token` returns 503 "parent ConvAI not configured".

**iOS:** `AgentView` has a waveform/call button → `ParentVoiceView` (orb + mute + transcript + surfaced cards) → `ParentCompanionCoordinator` (observes `conversation.pendingToolCalls` → resolves ids via `ContentViewModel` → renders `LibraryItemCard`/`CommunityPostCard`, then `sendToolResult`).

**Status:** parent voice connects and responds on device (after the Server-URL fix above). Backend half verified via curl (clean speech + well-formed `show_article` delta). **Still to confirm on device:** that ElevenLabs forwards the **non-terminal** client-tool call (`finish_reason:null`) mid-turn so the surfaced article/community **cards actually render** in `ParentVoiceView`. If EL instead requires `finish_reason:"tool_calls"` + a tool round-trip, adjust `_show_content_tool_delta` accordingly.

---

## Client events — agent-level config, **not** overridable per connection

`client_events` is the list of non-audio events ElevenLabs pushes to the SDK. It is
configured **on the agent** (console → Advanced → Client events, or via the API recipe
below) and is **not** in the overridable set — putting a `conversation.client_events`
list in `conversation_config_override` at token-mint time does nothing. If the app needs
an event, the *agent* has to emit it.

As-built, **2026-07-23** (live values):

| Event | `kid-companion-v2` | `parent-coach-v2` | What breaks without it |
|---|---|---|---|
| `audio` | ✅ | ✅ | (enabled, but see "Text sync & alignment" — it doesn't actually arrive over WebRTC) |
| `interruption` | ✅ | ✅ | barge-in isn't signalled to the client |
| `user_transcript` | ✅ | ✅ | the kid/parent's own words never appear in the transcript |
| `agent_response` | ✅ | ✅ | no agent text at all — audio only |
| `agent_response_correction` | ✅ | ✅ | after a barge-in the transcript keeps the **unspoken** tail (see below) |
| `vad_score` | ❌ **missing** | ✅ | the listening orb doesn't animate — the SDK's `onVadScore` callback fires **only** if the agent emits this event |

> ⚠️ **Known follow-up:** `kid-companion-v2` is still missing `vad_score`, so the kid
> surface's orb can't react to the kid's voice the way the parent surface's does. Add it
> with the PATCH recipe below (the parent agent is the reference list).

---

## Text sync & alignment — why the transcript is revealed client-side

**Platform reality: there is no alignment data over WebRTC.** The `audio` client event is
enabled on both agents, but with the LiveKit/WebRTC transport ElevenLabs does **not**
send `audio` events to the client — the audio rides the media track directly, and the
per-chunk character **alignment** payload rides with those events. So the character-level
"which characters have been spoken so far" signal is, in practice, **unavailable to the
iOS app**. Treat alignment as **opportunistic**: wire it up, use it if it ever shows up
(`Conversation.$latestAudioEvent` → `event.alignment`), never depend on it.

**Why a naive `Text(message.content)` render is wrong.** The `agent_response` event
carries the **entire turn's text at once**, delivered alongside the *first* audio chunk,
and the SDK upserts it whole into `conversation.messages`. Render it directly and the
whole paragraph pops onto screen while the agent is still on its first syllable — the
reader finishes 10 seconds before the voice does, which reads as lag/desync and kills the
"it's talking to me" illusion.

**What the app does instead.** A client-side reveal engine — pacing in
`VoiceRevealEngine.swift`, rendering in `StreamingText.swift`, wired identically on both
surfaces (`ParentVoiceView` and `KidAgentView`) — types the turn out progressively:

- Gated on **`conversation.agentState == .speaking`** — text only advances while audio is
  actually playing, so it pauses through think-time and stops dead on a barge-in.
- **Adaptive characters-per-second**: the rate is derived from the turn's length against
  the observed speaking window rather than a fixed constant, so short and long turns both
  land roughly with the audio. A floor rate guarantees the text always completes.
- **Alignment, if present, wins**: when a real spoken-character count is available it
  drives the reveal directly (`spokenProgress()`), and the rate engine is just the
  fallback. Today that branch never fires on device — see above.
- Reveal is **monotonic** and keyed per message id, so only the in-progress turn animates
  and prior turns stay fully rendered.

**Barge-in is `agent_response_correction`.** When the user interrupts, ElevenLabs fires
`agent_response_correction` with the **truncated** text that actually got spoken, and the
SDK rewrites that message's content **in place**. The reveal must therefore tolerate the
text *shrinking* under it (clamp the revealed count down to the new length) — that
correction event is the only thing that keeps the transcript honest about what the parent
or kid actually heard. Drop the event from `client_events` and every interrupted turn
leaves unspoken words on screen.

---

## Architecture

```
iOS (ElevenLabs Swift SDK 3.2.0)
    ↕ WebRTC audio (automatic — no AVAudioEngine code)
    ↕ text callbacks (agent response, user transcript)
ElevenLabs Cloud (SFU + STT + TTS + turn detection)
    ↕ OpenAI-compatible streaming (Custom LLM)
Our Backend (Railway)
    - Pre-input moderation (crisis scan, OpenAI, age classifier)
    - LangGraph kid agent
    - Token-by-token StreamingModerator
    - Persist to kid_messages
    - Crisis lock → emits end_call tool to terminate the session
```

**One agent for all kids.** Per-kid voice, system prompt, and greeting are passed at
connection time via `conversation_config_override`. No per-kid agents.

### Relevant code
- `mvp-backend/app/convai_endpoint.py` — kid OpenAI-compatible `/v1/chat/completions` Custom LLM endpoint.
- `mvp-backend/app/parent_convai_endpoint.py` — parent `/v1/parent/chat/completions` Custom LLM endpoint (link-stripping + `show_article`/`show_community_post` client-tool deltas).
- `mvp-backend/app/server.py` — `GET /voice/convai-token` (kid; PIN + crisis-lock gated) and `GET /voice/parent-convai-token` (parent; auth only). Mint the WebRTC token + per-connection override + extra body.
- `mvp/MVP/KidVoiceSessionManager.swift` — process-singleton iOS SDK wrapper (owns session lifecycle, LiveKit engine resets, teardown, retry). Used by both the kid and parent coordinators.
- `mvp/MVP/KidCompanionCoordinator.swift` / `ParentCompanionCoordinator.swift` — per-surface phase machines.
- `mvp/MVP/KidAgentService.swift` — `voiceConvAIToken(kidName:)` (kid) and `voiceParentConvAIToken()` (parent) call the token endpoints.

> Note: `ElevenLabsVoiceSession.swift` / `VoiceController.swift` were the v1 wrappers and were **deleted** in the v2 redesign — don't look for them.

---

## Console setup (step by step)

### 1. Create the agent
1. elevenlabs.io → **Agents** → **Create agent** → **Blank template**.
2. Name it `kid-companion-v2`. Save.

### 2. Point it at the backend (Custom LLM)
1. Open the agent → config panel on the right.
2. **LLM** dropdown → scroll → **Custom LLM**.
3. **Server URL**: `https://mvp-backend-production-8678.up.railway.app/v1`
   (ElevenLabs appends `/chat/completions` → `/v1/chat/completions`. Do **not** type the
   full `…/chat/completions` path — it doubles. See the "#1 footgun" note above.)
4. **Model ID**: anything, e.g. `kid` — our endpoint ignores the model field; it routes on
   `elevenlabs_extra_body`.
5. **API key** → **Create new secret**:
   - Name: `CONVAI_SECRET`
   - Value: `openssl rand -hex 32` — **save this**, it becomes `ELEVENLABS_CONVAI_SECRET`.
   - Add secret.

> ⚠️ **Auth header mismatch.** The "API key" field is sent as `Authorization: Bearer <value>`.
> The backend accepts both `Authorization: Bearer` and the legacy `X-ElevenLabs-Secret` header
> (see `convai_endpoint.py`), so the API-key field works directly. (If you instead use a
> custom-header UI, set `X-ElevenLabs-Secret`.) The secret **value** in the console must exactly
> match `ELEVENLABS_CONVAI_SECRET` in Railway — a mismatch surfaces as
> `401 {"detail":"invalid secret"}` (wrapped by ElevenLabs as `External API error: ...`).

6. **⚠️ Enable "Custom LLM extra body"** — toggle in the LLM panel (below "Limit token usage").
   Must be **ON**, or ElevenLabs strips `custom_llm_extra_body` and every real session 400s with
   `missing user_id or kid_name`. The bare **Test connection** probe sends no extra body and is
   answered with a stub `200` stream (see "Connection probe" below), so the test can pass even
   before this toggle is on — but real kid sessions need it.

### Connection probe vs. real session
ElevenLabs' **Test connection** (and health checks) send a bare OpenAI request with **no**
`elevenlabs_extra_body`. The backend detects this (no extra body at all) and returns a minimal
valid SSE stream (`OK` + `[DONE]`) with **200**, without spinning up an agent or moderation.
A request that *has* an `elevenlabs_extra_body` but is missing `user_id`/`kid_name` is a genuine
misconfiguration and still returns **400** — so real breakage isn't masked.

### 3. Enable overrides — **easy to miss**
Per-kid voice/prompt/greeting are blocked by default. **Security** tab → enable:
- **System prompt** (`prompt`)
- **First message** (`first_message`)
- **Language**
- **Voice ID** (`voice_id`, under TTS)

Without these, every kid silently gets the agent's default voice and an empty prompt.

### 4. Enable crisis hang-up
**Tools / System tools** → enable the built-in **`end_call`** tool.
This lets the backend terminate the session when moderation fires a crisis
(`convai_endpoint.py` emits an `end_call` tool delta).

### 5. Turn detection & limits
- **Turn detection**: Server VAD, silence ~**1.5s** (kid-friendly pacing).
- **Max conversation duration**: ~**15 min** (cost guardrail).
- Leave **Voice**, **First message**, **System prompt** fields **empty** (overridden per-connection).

### 6. Language & TTS
- Base **Language**: English.
- Default **Voice**: any (overridden per kid).

### 7. Publish & grab the Agent ID
- **Publish** (top right).
- Copy the **Agent ID** → becomes `ELEVENLABS_AGENT_ID`.

### 8. Railway env vars
| Var | Value |
|-----|-------|
| `ELEVENLABS_AGENT_ID` | kid agent ID, from step 7 |
| `ELEVENLABS_PARENT_AGENT_ID` | parent agent ID (see "Parent voice agent" above) |
| `ELEVENLABS_CONVAI_SECRET` | the secret value from step 2 (shared by both agents) |
| `ELEVENLABS_API_KEY` | ElevenLabs API key, **`convai_write`** scope (mints the conversation token) |

(Set the same four in local `.env` too.)

### 9. Test before touching iOS
Agent page → **Test AI agent** call widget → speak. Railway logs should show
`/v1/chat/completions` hits and you should hear a reply. A **401** in logs = the auth
secret in step 2 doesn't match `ELEVENLABS_CONVAI_SECRET`.

---

## Editing agent config via API (safer than clicking through the console)

Everything in the console is readable/writable at
`https://api.elevenlabs.io/v1/convai/agents/{agent_id}` with an `xi-api-key` header
(same key as `ELEVENLABS_API_KEY`, needs **`convai_write`** to PATCH). Always run the
**GET-snapshot → PATCH → GET-diff** loop — a `PATCH` is a *partial* update, but nested
objects you *do* send replace what's there, so you want a before/after you can diff.

```bash
KEY="$ELEVENLABS_API_KEY"
AID="$ELEVENLABS_PARENT_AGENT_ID"          # or ELEVENLABS_AGENT_ID
BASE="https://api.elevenlabs.io/v1/convai/agents/$AID"

# 1. SNAPSHOT — keep it; this is your rollback and your key-name reference
curl -s "$BASE" -H "xi-api-key: $KEY" > /tmp/agent.before.json

# 2. PATCH — partial update, everything lives under conversation_config
curl -s -X PATCH "$BASE" \
  -H "xi-api-key: $KEY" -H "Content-Type: application/json" \
  -d '{
    "conversation_config": {
      "conversation": {
        "client_events": ["audio","interruption","user_transcript",
                          "agent_response","agent_response_correction","vad_score"]
      },
      "tts": { "model_id": "eleven_flash_v2", "optimize_streaming_latency": 3 }
    }
  }' > /tmp/agent.patch.json

# 3. DIFF — confirm you changed only what you meant to
curl -s "$BASE" -H "xi-api-key: $KEY" > /tmp/agent.after.json
diff <(jq -S . /tmp/agent.before.json) <(jq -S . /tmp/agent.after.json)
```

Notes:
- `client_events` is a **whole-list replace** — send the complete list, not a delta.
- For anything not shown here (`turn`, `asr`, `agent.prompt`, tools…), read the exact key
  names out of `/tmp/agent.before.json` rather than guessing; the schema is wider than
  the console UI.
- A PATCH takes effect on the **next connection** — no publish step needed.

> ⚠️ **Verified gotcha — English agents reject the `_v2_5` TTS models.** PATCHing
> `"model_id": "eleven_flash_v2_5"` (or `eleven_turbo_v2_5`) onto an English-language
> agent 400s with `English Agents must use turbo or flash v2`. The `_v2_5` models are the
> **multilingual** variants; an English agent must use **`eleven_flash_v2`** (or
> `eleven_turbo_v2`). The error text is confusing — it's telling you to *drop* the `_5`.

### TTS & turn-taking state — 2026-07-23

| | `kid-companion-v2` | `parent-coach-v2` |
|---|---|---|
| TTS model | `eleven_v3_conversational` (unchanged — **pending a listening check** before moving it) | **`eleven_flash_v2`** — moved here for latency (fastest first chunk, ~75–150 ms) |
| `optimize_streaming_latency` | `3` | `3` |
| Turn model | `turn_v3`, speculative turns **on** | `turn_v3`, speculative turns **on** |
| Soft-timeout filler | **off** (`timeout_seconds: -1`) | **on at `2.0`s**, 3 randomized coach lines |

Why the split: first-audio-chunk latency is what the parent perceives as "is this thing
broken?", so the coach took the fastest model. The kid voice trades some latency for
warmth, so it stays on `eleven_v3_conversational` until someone actually listens to both
back-to-back on a device and calls it.

### Soft-timeout fillers — the fix for silent tool turns

A prod baseline on 2026-07-23 (`tools/voice_bench.py --prod --endpoint parent`) measured a
**bimodal** time-to-first-spoken-text: ~1.0–1.7 s on most turns, but **~4.0–4.4 s whenever the
agent calls the Tavily search tool** — during which the parent hears *pure silence*, because
first-SSE-byte and first-content-delta are identical (we send nothing before the model's first
token). `soft_timeout_config` is ElevenLabs' native cover for exactly that gap: if the custom
LLM hasn't produced content within `timeout_seconds`, the agent speaks a filler line.

As-built on `parent-coach-v2`:

```jsonc
"turn": { "soft_timeout_config": {
  "timeout_seconds": 2.0,            // above the ~1.7s fast turns, below the ~4s tool turns
  "message": "Let me think about that for a second.",
  "additional_soft_timeout_messages": ["Mm — give me one sec.", "Okay, let me look at that."],
  "randomize_fillers": true,
  "use_llm_generated_message": false
}}
```

> ⚠️ **`max_soft_timeouts_per_generation` cannot be lowered to 1.** PATCHing it returns `200`
> but the value stays **`3`** — the API silently clamps it. So a genuinely slow generation can
> stack up to three fillers before the real answer. If that ever sounds broken on device, the
> lever is raising `timeout_seconds` (2.5–3.0), not the count.

This is belt-and-braces with the prompt-side directive (the parent `voice_directive` tells the
model to say something aloud *before* it searches): the directive depends on model compliance
every turn, the soft timeout fires deterministically.

---

## Data contract

**Token endpoint → iOS** (`GET /voice/convai-token?kid_name=X`, `Authorization: Bearer`, `X-Kid-Pin`):
```json
{
  "signed_url": "<WebRTC conversation token>",
  "conversation_config_override": {
    "agent":   { "prompt": {"prompt": "<system prompt>"}, "first_message": "...", "language": "en" },
    "tts":     { "voice_id": "<per-kid voice>" },
    "conversation": { "client_events": ["audio","agent_response","user_transcript","interruption","conversation_initiation_metadata"] }
  },
  "custom_llm_extra_body": { "user_id":"...", "kid_name":"...", "thread_id":"default", "kid_pin":"...", "agent_id":"..." }
}
```

> Note: the `conversation.client_events` list inside the override above is **inert** —
> client events are agent-level config and are not in the overridable set (see "Client
> events" above). It's harmless, but changing it changes nothing; PATCH the agent instead.

**ElevenLabs → Custom LLM** (`POST /v1/chat/completions`): standard OpenAI body plus
`elevenlabs_extra_body` carrying the `custom_llm_extra_body` above. Backend pulls
`user_id` / `kid_name` / `thread_id` from it to load the right agent + moderation context.

**Crisis flow**: backend streams the replacement message as content, then emits an
`end_call` tool delta with `finish_reason: "tool_calls"`. ElevenLabs speaks the message
and hangs up. The kid agent is locked in DB until the parent intervenes.

---

## Status (2026-06-12: v1 voice REMOVED, failure-mode redesign shipped)
- ✅ Backend: `convai_endpoint.py` + `/voice/convai-token` + `GET /kid-agent/status` live.
  The greeting (`first_message`) is persisted to `kid_messages` at token-mint time
  (anti-stacking guard via `get_last_kid_message`).
- ✅ **v1 voice deleted everywhere**: iOS `VoiceController`/fragments/mic-dictation,
  backend `/voice/synthesize*`, `app/voice/` module, fragment SSE plumbing,
  `SentenceBoundaryChunker`, TTS caps + `voice_synth` rate bucket. `/kid-chat`
  streams text only. Fallback is **text-only and silent** by design.
- ✅ iOS architecture: `KidVoiceSessionManager` (process singleton; only caller of
  startConversation/endConversation/`AudioManager.setEngineAvailability`; serialized
  teardown-before-connect; fresh-token retry on `microphoneToggleFailed`; 15s watchdog)
  → `KidCompanionCoordinator` (phase machine: connecting / voiceLive / textFallback /
  crisisLocked) → `KidAgentView` surfaces. The view observes the SDK `Conversation`
  directly (`$messages`, `$agentState`) — full transcript + typed input work natively.
- ⚠️ The app must link the **LiveKit** product (transitive via ElevenLabs but not
  re-exported) for `AudioManager` access — done in project.pbxproj (CC333333… entries).
- ⚠️ `setEngineAvailability(.default)` BLOCKS if mic permission is undetermined
  (LiveKit #815) — the manager resolves permission before any engine call.

---

## ⚠️ API key MUST have `convai_write`
`ELEVENLABS_API_KEY` mints the WebRTC conversation token via
`GET /v1/convai/conversation/token` — a **write** operation. A TTS-only key (what
voice-v1 used) fails with `401 {"status":"missing_permissions","message":"...missing
the permission convai_write..."}`, which surfaces to the app as the token endpoint
returning **503 "failed to get conversation token"**, and iOS then silently falls
back to text. In ElevenLabs → Developers → API Keys, the key's **Conversational AI**
permission must be **Read and write** (not "Read only"); keep Text-to-Speech enabled
so v1 TTS still works. Editing an existing key's permissions applies to every
environment using that same key string (local + prod) — no env-var change needed.
Quick check (expect a ~1KB JWT, not a 401):
`curl "https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=$AID" -H "xi-api-key: $KEY"`

## ⚠️ Voice mode does NOT work in the iOS Simulator

On `startConversation`, the SDK auto-publishes a microphone track over LiveKit
WebRTC. The **Simulator has no usable mic**, so the publish times out
(`LocalParticipant._publish … microphone … Code=101 "Timed out"` →
`microphoneToggleFailed("Timed out")`), the SDK treats it as fatal, `connect()`
fails, and the coordinator drops to the **text-only fallback** (v1 TTS no longer
exists — fallback is silent text by design). So on the sim you get text replies and
no agent audio, which looks like "voice is broken."

There is **no public SDK escape hatch**:
- `microphoneFailureHandling: .continueWithoutMicrophone` exists only on the
  internal `ConversationOptions`. Every public `startConversation` takes
  `ConversationConfig`, whose `toConversationOptions()` hard-defaults mic handling
  to `.throwError`.
- `ConversationOverrides.textOnly = true` skips the mic, but routes over a
  **WebSocket text path that skips the audio pipeline** (`setupAudioManager()`
  early-returns) → text replies, **no agent voice**.

**Therefore: test voice on a physical device.** There the mic publishes and the
real ConvAI agent responds with audio. Worth trying first on the sim:
Simulator menu → **I/O → Audio Input** → select a real input, and grant the
Simulator mic permission in macOS System Settings → Privacy → Microphone — this
*sometimes* lets the publish succeed, but a device is the reliable path.

**Typing while in voice mode:** `Conversation.sendMessage(_:)` works in voice mode
without the mic — the agent still replies with audio. The kid v2 surface wires its
text box straight to the SDK `Conversation` for exactly this.

## Security invariants (do not regress)
- `ELEVENLABS_API_KEY` lives **on the backend only**, never in the iOS app (App Store safety).
- `kid_pin` is required on `/voice/convai-token` — same gate as `/kid-chat`.
- Crisis-locked agents must not reconnect — the token endpoint returns 403 when locked.
- Voice fallback to text must be a deliberate path, not a silent fallthrough.

---

## Sources
- [Integrate your own model (Custom LLM)](https://elevenlabs.io/docs/agents-platform/customization/llm/custom-llm)
- [Overrides](https://elevenlabs.io/docs/eleven-agents/customization/personalization/overrides)
