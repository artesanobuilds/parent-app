"""Real routes and disposable storage; no application lifespan or vendor calls."""
import os
import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "contracts.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "offline-contracts")
os.environ.setdefault("TAVILY_API_KEY", "offline-contracts")


class ScriptedAgent:
    def __init__(self, script=None):
        self.script = script if script is not None else ["Hello", " parent"]
        self.configs = []

    async def aget_state(self, config):
        return SimpleNamespace(values={"messages": []})

    async def astream_events(self, inputs, config=None, version=None):
        self.configs.append(config)
        for item in self.script:
            if isinstance(item, BaseException):
                raise item
            if isinstance(item, dict):
                yield item
            else:
                yield {"event": "on_chat_model_stream", "data": {"chunk": SimpleNamespace(content=item)}}


@pytest.fixture
def harness(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app import server
    from app import profiling
    from app.auth import mint_access_token
    from app.coach_threads import CoachThreadStore
    from app.cos import router as cos
    from app.duckdb_storage import DuckDBStorage
    from app.memory import MemoryRepository

    def no_network(*args, **kwargs):
        raise AssertionError("Contract tests must not call a vendor")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setenv("AUTH_JWT_SECRET", "offline-contract-signing-key-long-enough")
    storage = DuckDBStorage(tmp_path / "contracts.duckdb")
    monkeypatch.setattr(server, "storage_backend", storage)
    monkeypatch.setattr(server, "chat_memory", MemoryRepository())
    monkeypatch.setattr(server, "onboarding_memory", MemoryRepository())
    monkeypatch.setattr(profiling.profiling_service, "_profiles", {})
    monkeypatch.setattr(server, "coach_threads", CoachThreadStore(storage, server.chat_memory))
    monkeypatch.setattr(server, "rate_limit_enforce", lambda *args: None)
    monkeypatch.setattr(cos, "rate_limit_enforce", lambda *args: None)
    agent = ScriptedAgent()
    monkeypatch.setattr(server, "get_agent", lambda *args: agent)
    monkeypatch.setattr(server, "get_onboarding_agent", lambda *args: agent)
    monkeypatch.setattr(cos, "get_cos_agent", lambda *args: agent)
    client = TestClient(server.app)  # no context: do not start production workers
    user = "contract-parent"
    token, _ = mint_access_token(user)
    yield SimpleNamespace(
        server=server, cos=cos, storage=storage, agent=agent, client=client,
        user=user, headers={"Authorization": "Bearer " + token},
    )
    client.close()
    storage.close()
