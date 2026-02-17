import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Any

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.agent import get_agent
from app.onboarding_agent import get_onboarding_agent
from app.memory import MemoryRepository
from app.profiling import profiling_service
from app.storage import LocalFileStorage
from app import content as content_service

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Quiet third-party debug logs unless explicitly enabled
verbose_external_logs = os.getenv("DEBUG_ALL_LOGS", "0").lower() in ("1", "true", "yes")
if not verbose_external_logs:
    for noisy in ("httpx", "httpcore", "openai", "urllib3", "langchain", "langgraph"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

storage_backend = LocalFileStorage()
chat_memory = MemoryRepository()
onboarding_memory = MemoryRepository()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_persisted_state()
    yield
    persist_state()


app = FastAPI(title="MVP Backend", version="1.0.0", lifespan=lifespan)

# Enable CORS for all origins (dev mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"
    user_id: str = "0"


def load_persisted_state():
    users = set(storage_backend.list_users())
    profile_snapshot: Dict[str, Any] = {}

    for user_id in users:
        chat_data = storage_backend.load_user_data(user_id, "chat_threads")
        if chat_data:
            chat_memory.load_user_snapshot(user_id, chat_data)

        onboarding_data = storage_backend.load_user_data(user_id, "onboarding_threads")
        if onboarding_data:
            onboarding_memory.load_user_snapshot(user_id, onboarding_data)

        profile_data = storage_backend.load_user_data(user_id, "profiles")
        if profile_data:
            profile_snapshot[user_id] = profile_data

    if profile_snapshot:
        profiling_service.load_snapshot(profile_snapshot)
        logger.debug(f"[storage] loaded profiles for users: {list(profile_snapshot.keys())}")

    logger.debug(f"[storage] loaded chat memory users: {chat_memory.user_ids()}")
    logger.debug(f"[storage] loaded onboarding memory users: {onboarding_memory.user_ids()}")


def persist_state():
    # Persist conversations
    user_ids = set(chat_memory.user_ids()) | set(onboarding_memory.user_ids())
    for user_id in user_ids:
        storage_backend.save_user_data(user_id, "chat_threads", chat_memory.snapshot_user(user_id))
        storage_backend.save_user_data(user_id, "onboarding_threads", onboarding_memory.snapshot_user(user_id))

    # Persist profiles
    profiles = profiling_service.export_snapshot()
    for user_id, profile_data in profiles.items():
        storage_backend.save_user_data(user_id, "profiles", profile_data)

    logger.debug(f"[storage] persisted state for users: {list(user_ids | set(profiles.keys()))}")


async def generate_stream(message: str, thread_id: str, user_id: str) -> AsyncGenerator[str, None]:
    """
    Streams events from the LangGraph agent.
    Format: SSE (Server-Sent Events)
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[chat] start user_id={user_id} thread_id={thread_id} message={message[:200]}")
    agent = get_agent(user_id)
    # Memory is scoped per user + thread to isolate conversations by user
    memory_key = f"{user_id}:{thread_id}"
    config = {"configurable": {"thread_id": memory_key}}

    thread_messages = chat_memory.get_thread_messages(user_id, thread_id)
    thread_messages.append({"role": "user", "content": message})
    assistant_buffer = ""
    
    try:
        # Stream events from the graph
        # "values" mode streams the full state at each step
        # "updates" mode streams only the changes
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v1"
        ):
            # We are interested in chat model stream events to stream tokens back to client
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # Format as SSE data
                    assistant_buffer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            
            elif kind == "on_tool_start":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[chat] tool_start name={event.get('name')} input={event.get('data', {}).get('input')}")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
                 
            elif kind == "on_tool_end":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[chat] tool_end name={event.get('name')} output={event.get('data', {}).get('output')}")
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield "data: [DONE]\n\n"
        if assistant_buffer:
            thread_messages.append({"role": "assistant", "content": assistant_buffer})
        
    except Exception as e:
        logger.error(f"Error in stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


async def generate_onboarding_stream(message: str, thread_id: str, user_id: str) -> AsyncGenerator[str, None]:
    """
    Streams events from the onboarding agent.
    Format: SSE (Server-Sent Events)
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[onboarding] start user_id={user_id} thread_id={thread_id} message={message[:200]}")
    agent = get_onboarding_agent(user_id)
    memory_key = f"onboarding:{user_id}:{thread_id}"
    config = {"configurable": {"thread_id": memory_key}}

    thread_messages = onboarding_memory.get_thread_messages(user_id, thread_id)
    thread_messages.append({"role": "user", "content": message})
    assistant_buffer = ""

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v1"
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    assistant_buffer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            elif kind == "on_tool_start":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[onboarding] tool_start name={event.get('name')} input={event.get('data', {}).get('input')}")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
            elif kind == "on_tool_end":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[onboarding] tool_end name={event.get('name')} output={event.get('data', {}).get('output')}")
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield "data: [DONE]\n\n"
        if assistant_buffer:
            thread_messages.append({"role": "assistant", "content": assistant_buffer})

    except Exception as e:
        logger.error(f"Error in onboarding stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        generate_stream(request.message, request.thread_id, request.user_id),
        media_type="text/event-stream"
    )


@app.post("/onboarding-chat")
async def onboarding_chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        generate_onboarding_stream(request.message, request.thread_id, request.user_id),
        media_type="text/event-stream"
    )


@app.get("/memory/{user_id}")
def dump_memory(user_id: str):
    """
    Returns all conversation threads for a given user_id from in-memory storage.
    Includes both coaching (/chat) and onboarding (/onboarding-chat) memories.
    """
    return {
        "user_id": user_id,
        "chat_threads": chat_memory.snapshot_user(user_id),
        "onboarding_threads": onboarding_memory.snapshot_user(user_id),
        "profile": profiling_service.get_family_profile(user_id),
    }

@app.get("/content/categories")
def list_categories():
    """Return all content categories."""
    return content_service.get_categories()


@app.get("/content/articles")
def list_articles(category: str | None = None, limit: int = 50):
    """Return library articles, optionally filtered by category."""
    return content_service.get_articles(category=category, limit=limit)


@app.get("/content/articles/{article_id}")
def get_article(article_id: str):
    """Return a single article with full content."""
    article = content_service.get_article(article_id)
    if article is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return article


@app.get("/content/community")
def list_community_posts(category: str | None = None, limit: int = 50):
    """Return community posts, optionally filtered by category."""
    return content_service.get_community_posts(category=category, limit=limit)


@app.get("/content/search")
def search_content(q: str, limit: int = 10):
    """Search articles and community posts by keyword."""
    return content_service.search_content(q, limit=limit)


@app.get("/content/relevant")
def relevant_content(topic: str, limit: int = 5):
    """Return content relevant to a topic (for contextual recommendations)."""
    return content_service.get_relevant_content(topic, limit=limit)


@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

