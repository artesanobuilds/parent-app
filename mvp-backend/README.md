# MVP Backend (FastAPI + LangGraph)

This backend hosts a LangGraph ReAct-style agent behind a FastAPI server. It streams responses with Server-Sent Events (SSE) and exposes a small set of endpoints for chat and health checking.

## What’s inside
- `app/server.py`: FastAPI app with:
  - `POST /chat`: streams agent responses as SSE tokens.
  - `GET /health`: simple liveness check.
  - CORS open for development.
- `app/agent.py`: builds the LangGraph agent via `create_agent`, wiring:
  - `ChatOpenAI` model (configurable via `OPENAI_MODEL_NAME`, default `gpt-4o`).
  - Tavily search tool from `langchain-tavily` (`TavilySearch`) for web search.
  - In-memory checkpointing (`MemorySaver`) to maintain conversation state by `thread_id`.
- `requirements.txt`: Python dependencies.
- `env.example`: sample environment variables.

## Prerequisites
- Python 3.14 (matches the current `.venv`) or compatible 3.11+.
- An OpenAI API key and a Tavily API key.

## Setup
1) Create and activate a virtualenv (skip if you already use `.venv`):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2) Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   - If you see interpreter mismatches, install key packages with the project
     interpreter explicitly (helps when 3.13 and 3.14 are both present):
     ```bash
     ./.venv/bin/python -m pip install langchain-community langchain-agents-pip langchain-tavily
     ```
3) Configure environment variables (copy and edit):
   ```bash
   cp env.example .env
   # then set OPENAI_API_KEY, TAVILY_API_KEY, OPENAI_MODEL_NAME
   ```

## Running the server
From `mvp-backend/` (with the virtualenv active):
```bash
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

## API usage
- Health check:
  ```bash
  curl http://localhost:8000/health
  ```
- Chat (streams SSE tokens):
  ```bash
  curl -N -H "Content-Type: application/json" \
    -d '{"message":"Hello","thread_id":"demo","user_id":"alice"}' \
    http://localhost:8000/chat
  ```
  Response is an SSE stream (`data: ...`), ending with `data: [DONE]`.
  - `thread_id`: conversation thread identifier.
  - `user_id`: optional user identifier; defaults to `"0"` if omitted.
  - Memory is scoped to `user_id:thread_id` using an in-memory checkpointer (not persisted).
- Dump user memory (all threads for a user):
  ```bash
  curl http://localhost:8000/memory/alice
  ```

## Interactive docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Notes and gotchas
- Tavily now comes from `langchain-tavily` (`from langchain_tavily import TavilySearch`); the older `langchain_community` Tavily tool is deprecated.
- Warnings about Pydantic on Python 3.14 are upstream deprecations; they are non-blocking but may go away after upstream updates or pinning Python to 3.11/3.12.

