"""Single-process ownership. Replicas need durable leases before using this design."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary


@dataclass
class _Gate:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    users: int = 0


class ConversationGates:
    def __init__(self):
        self._loops = WeakKeyDictionary()

    @asynccontextmanager
    async def hold(self, thread_key: str, timeout: float = 30):
        # Locks belong to one event loop. Tests and app lifespans can create new loops.
        gates = self._loops.setdefault(asyncio.get_running_loop(), {})
        gate = gates.setdefault(thread_key, _Gate())
        gate.users += 1
        acquired = False
        try:
            await asyncio.wait_for(gate.lock.acquire(), timeout)
            acquired = True
            yield
        finally:
            if acquired:
                gate.lock.release()
            gate.users -= 1
            if not gate.users:
                gates.pop(thread_key, None)


def resolve_parent_thread(user_id, surface, thread_id, conversation_id=None):
    # Keep the existing key function as the durable compatibility authority.
    from app.agent import thread_key
    return thread_key(user_id, surface, thread_id, conversation_id=conversation_id)


conversation_gates = ConversationGates()
