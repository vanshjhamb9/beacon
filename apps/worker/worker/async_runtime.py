"""Run async worker coroutines safely under Celery's sync task model.

Uses a single persistent event loop per worker process so that
SQLAlchemy's async engine connections stay attached to the correct loop.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")

_loop: asyncio.AbstractEventLoop | None = None
_lock = threading.Lock()


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        with _lock:
            if _loop is None or _loop.is_closed():
                _loop = asyncio.new_event_loop()
                asyncio.set_event_loop(_loop)
    return _loop


def run_async(coro: Coroutine[object, object, T]) -> T:
    loop = _get_loop()
    return loop.run_until_complete(coro)
