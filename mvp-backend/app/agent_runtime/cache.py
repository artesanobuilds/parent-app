"""Bounded process-local graph caches; durable history lives in checkpoints."""
from collections import OrderedDict
from collections.abc import MutableMapping
import os
from threading import RLock


class AgentCache(MutableMapping):
    """Small LRU preserving existing cache shapes and invalidation APIs.

    Eviction discards only a compiled graph, never checkpoints or profile state.
    Factories still rebuild prompts from each tenant's current context. This is
    deliberately not a shared graph containing mutable per-family prompt data.
    """
    def __init__(self, maxsize=None):
        self.maxsize = maxsize if maxsize is not None else int(os.getenv('MVP_AGENT_CACHE_SIZE', '256'))
        if not isinstance(self.maxsize, int) or self.maxsize < 1:
            raise ValueError('MVP_AGENT_CACHE_SIZE must be a positive integer')
        self._items = OrderedDict()
        self._lock = RLock()

    def __getitem__(self, key):
        with self._lock:
            value = self._items[key]
            self._items.move_to_end(key)
            return value

    def __setitem__(self, key, value):
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            while len(self._items) > self.maxsize:
                self._items.popitem(last=False)

    def __delitem__(self, key):
        with self._lock:
            del self._items[key]

    def __iter__(self):
        with self._lock:
            return iter(tuple(self._items))

    def __len__(self):
        with self._lock:
            return len(self._items)

    def clear(self):
        with self._lock:
            self._items.clear()

    def pop(self, key, *default):
        with self._lock:
            return self._items.pop(key, *default)

    def items(self):
        with self._lock:
            return tuple(self._items.items())
