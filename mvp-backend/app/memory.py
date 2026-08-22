from copy import deepcopy
from typing import Any, Dict, List


class MemoryRepository:
    """
    Repository wrapper over in-memory conversation threads.
    Structure: {user_id: {thread_id: [ {role, content}, ... ]}}
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    def append_message(self, user_id: str, thread_id: str, role: str, content: str) -> None:
        threads = self._store.setdefault(user_id, {})
        messages = threads.setdefault(thread_id, [])
        messages.append({"role": role, "content": content})

    def get_thread_messages(self, user_id: str, thread_id: str) -> List[Dict[str, Any]]:
        threads = self._store.setdefault(user_id, {})
        return threads.setdefault(thread_id, [])

    def snapshot_user(self, user_id: str) -> Dict[str, Any]:
        return deepcopy(self._store.get(user_id, {}))

    def snapshot_all(self) -> Dict[str, Any]:
        return deepcopy(self._store)

    def load_user_snapshot(self, user_id: str, data: Dict[str, Any]) -> None:
        # Replace the user snapshot entirely with loaded data
        self._store[user_id] = deepcopy(data)

    def remove_user(self, user_id: str) -> None:
        """Forget a user entirely. Account deletion MUST call this: as long as
        the id stays in the store, the next persist_state() writes the deleted
        conversations straight back into user_data — which is exactly what
        happened to two deleted accounts on 2026-08-10 (their coach chats
        resurrected on every export until this eviction existed)."""
        self._store.pop(user_id, None)

    def user_ids(self):
        return list(self._store.keys())

