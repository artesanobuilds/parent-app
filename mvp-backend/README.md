# MVP Backend (FastAPI + LangGraph)

This backend hosts a LangGraph ReAct-style agent behind a FastAPI server. It streams responses with Server-Sent Events (SSE) and exposes endpoints for chat, content, CMS, and health checking.

## What's inside
- `app/server.py`: FastAPI app with SSE streaming, content API, CMS CRUD, and user profiling.
- `app/agent.py`: LangGraph agent with ChatOpenAI and Tavily search.
- `app/duckdb_storage.py`: DuckDB + Parquet storage backend. Bootstraps from parquet files on first run.
- `app/content.py`: Content service for articles, community posts, and categories.
- `cms/`: React + Vite CMS frontend (served at `/cms`).
- `data/`: Parquet snapshots used for seeding and persistence.
- `tools/`: Utility scripts (sync, etc).

## Prerequisites
- Python 3.13+ (matches the current `.venv`).
- An OpenAI API key and a Tavily API key.
- Docker (for deployment).

## Local setup
1. Create and activate a virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```bash
   cp env.example .env
   # set OPENAI_API_KEY, TAVILY_API_KEY, OPENAI_MODEL_NAME
   ```

## Running locally
```bash
uvicorn app.server:app --reload --host 0.0.0.0 --port 8904
```

CMS (if built):
```bash
cd cms && npm install && npm run build
```
Then visit http://localhost:8904/cms

## Deployment (Railway)

The backend is deployed to Railway using a multi-stage Dockerfile.

**Production URL:** https://mvp-backend-production-8678.up.railway.app
**CMS:** https://mvp-backend-production-8678.up.railway.app/cms

### How it works
- `Dockerfile`: Stage 1 builds the CMS frontend (Node), Stage 2 runs the Python backend.
- `railway.toml`: Railway config (Dockerfile builder, healthcheck).
- `entrypoint.sh`: Seeds the persistent volume with parquet data on first deploy, clears stale DuckDB files so the app bootstraps fresh from parquet each time.
- A Railway **volume** is mounted at `/app/data/` so data persists across deploys.

### Deploy commands
```bash
cd mvp-backend

# First time setup (already done)
railway login
railway init
railway service mvp-backend
railway variables set OPENAI_API_KEY=xxx OPENAI_MODEL_NAME=gpt-5.1 TAVILY_API_KEY=xxx
railway volume add --mount-path /app/data

# Deploy
railway up

# Check status
railway service status --all

# View logs
railway logs

# Get public URL
railway domain
```

### Environment variables (set via `railway variables set`)
| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL_NAME` | Model name (e.g. `gpt-5.1`) |
| `TAVILY_API_KEY` | Tavily search API key |

### Data persistence
- Railway volume at `/app/data/` persists DuckDB and parquet files across deploys.
- On each deploy, `entrypoint.sh` seeds any missing parquet files from `/app/seed-data/` (baked into the image) and removes stale `.duckdb` files so the app bootstraps cleanly.
- On shutdown, the app exports all data to parquet via `persist_state()`.

## Syncing production data locally

A sync script pulls parquet files from production to keep your local data in sync.

```bash
# One-shot sync
./tools/sync-data.sh

# Watch mode — syncs every 30 minutes
./tools/sync-data.sh --watch
```

The script calls `/data/export` to trigger a fresh parquet export, compares MD5 checksums, and only downloads files that changed. Checksums are cached in `data/.remote-checksums.json`.

You can override the remote URL:
```bash
MVP_REMOTE_URL=https://your-url.railway.app ./tools/sync-data.sh
```

## API usage
- **Health check:** `GET /health`
- **Chat (SSE stream):** `POST /chat` with `{"message": "...", "thread_id": "...", "user_id": "..."}`
- **Onboarding chat:** `POST /onboarding-chat` (same body as chat)
- **Content:** `GET /content/categories`, `GET /content/articles`, `GET /content/community`
- **Article detail:** `GET /content/articles/{id}`
- **Search:** `GET /content/search?q=keyword`
- **User memory dump:** `GET /memory/{user_id}`
- **CMS CRUD:** `POST/PUT/DELETE /cms/articles`, `/cms/community-posts`, `/cms/categories`
- **Data sync:** `GET /data/export` (checksums), `GET /data/download/{filename}`

## Interactive docs
- Swagger UI: http://localhost:8904/docs
- ReDoc: http://localhost:8904/redoc
