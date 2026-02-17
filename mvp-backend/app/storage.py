import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Strategy interface for persisting user-scoped JSON blobs."""

    @abstractmethod
    def save_user_data(self, user_id: str, name: str, data: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def load_user_data(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def list_users(self) -> Iterable[str]:
        ...


class LocalFileStorage(StorageBackend):
    """
    File-system implementation of StorageBackend.
    Persists under base_dir/<user_id>/<name>.json
    """

    def __init__(self, base_dir: Path | str = None) -> None:
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent / "local-storage"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, user_id: str) -> Path:
        return self.base_dir / user_id

    def save_user_data(self, user_id: str, name: str, data: Dict[str, Any]) -> None:
        try:
            user_dir = self._user_dir(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)
            path = user_dir / f"{name}.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            logger.debug(f"[storage] saved {name} for user {user_id} to {path}")
        except Exception as exc:
            logger.error(f"[storage] failed to save {name} for user {user_id}: {exc}")

    def load_user_data(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        path = self._user_dir(user_id) / f"{name}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception as exc:
            logger.error(f"[storage] failed to load {name} for user {user_id}: {exc}")
            return None

    def list_users(self) -> Iterable[str]:
        if not self.base_dir.exists():
            return []
        return [
            p.name
            for p in self.base_dir.iterdir()
            if p.is_dir()
        ]

