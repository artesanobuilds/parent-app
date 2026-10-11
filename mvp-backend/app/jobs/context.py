from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class JobStopped(RuntimeError):
    """The attempt was canceled, superseded, or exhausted its budget."""


@dataclass
class JobContext:
    storage: Any
    kind: str
    run_id: str
    token: str
    deadline: float
    stop: threading.Event = field(default_factory=threading.Event)

    @classmethod
    def from_run(cls, storage, kind, run, stop=None):
        expires = datetime.fromisoformat(run['_deadline_at'])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        remaining = (expires - datetime.now(timezone.utc)).total_seconds()
        return cls(storage, kind, run['id'], run['_attempt_token'],
                   time.monotonic() + max(0, remaining), stop or threading.Event())

    def check(self):
        if self.stop.is_set() or time.monotonic() >= self.deadline:
            raise JobStopped('job canceled or deadline exceeded')
        if not self.storage.job_attempt_active(self.kind, self.run_id, self.token):
            raise JobStopped('job attempt no longer active')

    def remaining(self, ceiling=None):
        self.check()
        seconds = max(0.001, self.deadline - time.monotonic())
        return min(seconds, ceiling) if ceiling is not None else seconds

    async def wait(self, awaitable):
        """Cancel and join supported async work; never pretend threads are killed."""
        task = asyncio.ensure_future(awaitable)
        try:
            while True:
                self.check()
                done, _ = await asyncio.wait({task}, timeout=min(.2, self.remaining()))
                if done:
                    value = task.result()
                    self.check()
                    return value
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)


class StepStorage:
    """Only public storage calls cross the step fence, including late writes.

    The transaction spans validation, the call, and a final deadline check.
    Nested domain transactions join it. Timed-out step contexts are
    separate copies, so a late return also cannot corrupt the next step's state.
    """
    def __init__(self, storage, context, deadline, canceled):
        self._storage = storage
        self._context = context
        self._deadline = deadline
        self._canceled = canceled

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        method = getattr(self._storage, name)
        if not callable(method):
            raise AttributeError(name)
        def guarded(*args, **kwargs):
            with self._storage.job_write_guard(self._context):
                with self._storage._con.transaction():
                    if self._canceled.is_set() or time.monotonic() >= self._deadline:
                        raise JobStopped('warmup step expired')
                    result = method(*args, **kwargs)
                    self._context.check()
                    if self._canceled.is_set() or time.monotonic() >= self._deadline:
                        raise JobStopped('warmup step expired before commit')
                    return result
        return guarded
