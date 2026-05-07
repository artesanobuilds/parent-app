import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.agent import get_agent
from app.onboarding_agent import get_onboarding_agent
from app.memory import MemoryRepository
from app.profiling import profiling_service
from app.duckdb_storage import DuckDBStorage
from app import content as content_service

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Quiet third-party debug logs unless explicitly enabled
verbose_external_logs = os.getenv("DEBUG_ALL_LOGS", "0").lower() in ("1", "true", "yes")
if not verbose_external_logs:
    for noisy in ("httpx", "httpcore", "openai", "urllib3", "langchain", "langgraph"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

storage_backend = DuckDBStorage()
content_service.init(storage_backend)
chat_memory = MemoryRepository()
onboarding_memory = MemoryRepository()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_persisted_state()
    yield
    persist_state()
    storage_backend.close()


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


class FeedbackRequest(BaseModel):
    message_id: str
    thread_id: str
    user_id: str
    feedback: str  # "thumbs_up", "thumbs_down", or "none"


class OnboardingSeedRequest(BaseModel):
    user_id: str
    parent_name: str
    kids: List[Dict[str, str]] = []      # [{"name", "age", "temperament", "pronouns", "grade_band"}]
    household: str = ""
    support_system: str = ""
    energy_pattern: str = ""
    dreaded_moment: str = ""
    challenges: List[str] = []
    goals: List[str] = []
    # Demographic additions
    postal_code: str = ""
    country: str = ""
    primary_language: str = ""
    parent_age_range: str = ""
    adults_in_household: Optional[int] = None
    cultural_background: str = ""
    employment: str = ""
    pronouns: str = ""


# ── CMS Pydantic models ──────────────────────────────────────────────

class ArticleCreateRequest(BaseModel):
    id: str
    category: str
    title: str
    subtitle: str = ""
    emoji: str = ""
    author: str = "MVP Editorial"
    read_time: str = ""
    summary: str = ""
    tags: List[str] = []
    content: str = ""


class ArticleUpdateRequest(BaseModel):
    category: str | None = None
    title: str | None = None
    subtitle: str | None = None
    emoji: str | None = None
    author: str | None = None
    read_time: str | None = None
    summary: str | None = None
    tags: List[str] | None = None
    content: str | None = None


class CommunityPostCreateRequest(BaseModel):
    id: str
    category: str
    initials: str = ""
    name: str = ""
    title: str = ""
    preview: str = ""
    user_id: str | None = None


class CommunityPostUpdateRequest(BaseModel):
    category: str | None = None
    initials: str | None = None
    name: str | None = None
    title: str | None = None
    preview: str | None = None
    user_id: str | None = None


class CategoryCreateRequest(BaseModel):
    id: str
    name: str
    emoji: str = ""
    description: str = ""


class CategoryUpdateRequest(BaseModel):
    name: str | None = None
    emoji: str | None = None
    description: str | None = None


class UserPostCreateRequest(BaseModel):
    category: str
    title: str
    preview: str
    user_id: str
    author_name: str


class ReplyCreateRequest(BaseModel):
    user_id: str
    author_name: str
    body: str


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


def persist_state(user_id: str | None = None):
    """Persist state. If user_id is given, only save that user. Otherwise save all."""
    if user_id:
        user_ids = {user_id}
    else:
        user_ids = set(chat_memory.user_ids()) | set(onboarding_memory.user_ids())
        # Include profile-only users
        user_ids |= set(profiling_service.export_snapshot().keys())

    for uid in user_ids:
        storage_backend.save_user_data(uid, "chat_threads", chat_memory.snapshot_user(uid))
        storage_backend.save_user_data(uid, "onboarding_threads", onboarding_memory.snapshot_user(uid))

    # Persist profiles for targeted users
    all_profiles = profiling_service.export_snapshot()
    for uid in user_ids:
        if uid in all_profiles:
            storage_backend.save_user_data(uid, "profiles", all_profiles[uid])

    storage_backend.export_parquet()
    logger.debug(f"[storage] persisted state for users: {list(user_ids)}")


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
        persist_state(user_id)

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
        persist_state(user_id)

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


@app.post("/content/community/new")
def create_user_community_post(req: UserPostCreateRequest):
    """Create a community post from the mobile app."""
    import uuid
    words = req.author_name.strip().split()
    initials = "".join(w[0].upper() for w in words[:2]) if words else "?"
    post_id = f"cp-{uuid.uuid4().hex[:12]}"
    data = {
        "id": post_id,
        "category": req.category,
        "title": req.title,
        "preview": req.preview,
        "user_id": req.user_id,
        "name": req.author_name,
        "initials": initials,
    }
    return content_service.create_community_post(data)


@app.get("/content/community/{post_id}")
def get_community_post_detail(post_id: str):
    """Get a single community post with its replies."""
    post = content_service.get_community_post(post_id)
    if post is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    replies = content_service.get_replies_for_post(post_id)
    post["replies"] = replies
    post["reply_count"] = len(replies)
    return post


@app.get("/content/community/{post_id}/replies")
def get_post_replies(post_id: str, limit: int = 100):
    """Get replies for a community post."""
    return content_service.get_replies_for_post(post_id, limit=limit)


@app.post("/content/community/{post_id}/replies")
def create_post_reply(post_id: str, req: ReplyCreateRequest):
    """Create a reply on a community post."""
    post = content_service.get_community_post(post_id)
    if post is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    import uuid
    words = req.author_name.strip().split()
    initials = "".join(w[0].upper() for w in words[:2]) if words else "?"
    data = {
        "id": str(uuid.uuid4()),
        "post_id": post_id,
        "user_id": req.user_id,
        "author_name": req.author_name,
        "initials": initials,
        "body": req.body,
    }
    return content_service.create_reply(data)


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


@app.post("/profile/seed")
def seed_profile(request: OnboardingSeedRequest):
    """
    Receive structured onboarding data from the mobile app and seed
    the parent + child profiles so the coaching agent has context.
    """
    # Seed parent profile
    parent_updates: Dict[str, Any] = {"name": request.parent_name}
    if request.challenges:
        parent_updates["stressors"] = request.challenges
    if request.goals:
        parent_updates["goals"] = request.goals
    if request.household:
        parent_updates["household_structure"] = request.household
    if request.support_system:
        parent_updates["support_system"] = request.support_system
    if request.energy_pattern:
        parent_updates["energy_pattern"] = request.energy_pattern
    if request.dreaded_moment:
        parent_updates["dreaded_moment"] = request.dreaded_moment
    if request.postal_code:
        parent_updates["postal_code"] = request.postal_code
    if request.country:
        parent_updates["country"] = request.country
    if request.primary_language:
        parent_updates["primary_language"] = request.primary_language
    if request.parent_age_range:
        parent_updates["parent_age_range"] = request.parent_age_range
    if request.adults_in_household is not None:
        parent_updates["adults_in_household"] = request.adults_in_household
    if request.cultural_background:
        parent_updates["cultural_background"] = request.cultural_background
    if request.employment:
        parent_updates["employment"] = request.employment
    if request.pronouns:
        parent_updates["pronouns"] = request.pronouns

    profiling_service.update_parent_profile(request.user_id, parent_updates)

    # Seed child profiles
    for kid in request.kids:
        child_name = kid.get("name", "").strip()
        if not child_name:
            continue
        child_updates: Dict[str, Any] = {"name": child_name}
        age_str = kid.get("age", "").strip()
        if age_str:
            try:
                child_updates["age"] = float(age_str)
            except ValueError:
                pass
        temperament = kid.get("temperament", "").strip()
        if temperament:
            child_updates["temperament"] = temperament
        pronouns = kid.get("pronouns", "").strip()
        if pronouns:
            child_updates["pronouns"] = pronouns
        grade_band = kid.get("grade_band", "").strip()
        if grade_band:
            child_updates["grade_band"] = grade_band
        profiling_service.update_child_profile(request.user_id, child_name, child_updates)

    # Persist immediately so nothing is lost if server restarts
    persist_state(request.user_id)

    logger.info(f"[profile/seed] seeded profile for user_id={request.user_id}")
    return profiling_service.get_family_profile(request.user_id)


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """
    Store thumbs-up/down feedback for an assistant message.
    Persisted inside the user's chat_threads data keyed by message_id.
    """
    # Load existing feedback store (or create one)
    feedback_data = storage_backend.load_user_data(req.user_id, "feedback") or {}
    if req.feedback == "none":
        feedback_data.pop(req.message_id, None)
    else:
        feedback_data[req.message_id] = {
            "thread_id": req.thread_id,
            "feedback": req.feedback,
        }
    storage_backend.save_user_data(req.user_id, "feedback", feedback_data)
    logger.info(f"[feedback] user={req.user_id} message={req.message_id} feedback={req.feedback}")
    return {"ok": True}


# ── CMS CRUD Endpoints ────────────────────────────────────────────────

@app.post("/cms/articles")
def cms_create_article(req: ArticleCreateRequest):
    return content_service.create_article(req.model_dump())


@app.put("/cms/articles/{article_id}")
def cms_update_article(article_id: str, req: ArticleUpdateRequest):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = content_service.update_article(article_id, data)
    if result is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return result


@app.delete("/cms/articles/{article_id}")
def cms_delete_article(article_id: str):
    if not content_service.delete_article(article_id):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return {"deleted": True}


@app.get("/cms/community-posts/{post_id}")
def cms_get_community_post(post_id: str):
    post = content_service.get_community_post(post_id)
    if post is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return post


@app.post("/cms/community-posts")
def cms_create_community_post(req: CommunityPostCreateRequest):
    return content_service.create_community_post(req.model_dump())


@app.put("/cms/community-posts/{post_id}")
def cms_update_community_post(post_id: str, req: CommunityPostUpdateRequest):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = content_service.update_community_post(post_id, data)
    if result is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return result


@app.delete("/cms/community-posts/{post_id}")
def cms_delete_community_post(post_id: str):
    if not content_service.delete_community_post(post_id):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return {"deleted": True}


@app.post("/cms/categories")
def cms_create_category(req: CategoryCreateRequest):
    return content_service.create_category(req.model_dump())


@app.put("/cms/categories/{category_id}")
def cms_update_category(category_id: str, req: CategoryUpdateRequest):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = content_service.update_category(category_id, data)
    if result is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Category not found"})
    return result


@app.delete("/cms/categories/{category_id}")
def cms_delete_category(category_id: str):
    if not content_service.delete_category(category_id):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Category not found"})
    return {"deleted": True}


@app.get("/cms/stats")
def cms_stats():
    return content_service.get_content_stats()


@app.post("/cms/export-parquet")
def cms_export_parquet():
    content_service.export_content_parquet()
    return {"exported": True}


@app.get("/data/export")
def data_export():
    """Trigger parquet export and return checksums for sync detection."""
    import hashlib
    content_service.export_content_parquet()
    persist_state()
    data_dir = Path(__file__).resolve().parent.parent / "data"
    checksums = {}
    for pq in sorted(data_dir.glob("*.parquet")):
        checksums[pq.name] = hashlib.md5(pq.read_bytes()).hexdigest()
    return {"checksums": checksums}


@app.get("/data/download/{filename}")
def data_download(filename: str):
    """Download a parquet file from the data directory."""
    if not filename.endswith(".parquet"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": "Only .parquet files"})
    data_dir = Path(__file__).resolve().parent.parent / "data"
    file_path = data_dir / filename
    if not file_path.is_file():
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ── Serve built CMS static files ─────────────────────────────────────

_cms_dist = Path(__file__).resolve().parent.parent / "cms" / "dist"
if _cms_dist.is_dir():
    # Catch-all for SPA routing: serve index.html for any /cms/* path not matched above
    @app.get("/cms/{full_path:path}")
    def cms_spa_fallback(full_path: str):
        # Try to serve the static file first
        file_path = _cms_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA client-side routing
        return FileResponse(_cms_dist / "index.html")

    @app.get("/cms")
    def cms_root():
        return FileResponse(_cms_dist / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8904)

