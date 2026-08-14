"""Run async worker coroutines safely under Celery's sync task model.

Each Celery task uses ``asyncio.run``, which creates and closes an event loop.
SQLAlchemy's async engine must dispose connections before that loop closes.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import TypeVar

from app.db.session import engine

T = TypeVar("T")


def run_async(coro: Coroutine[object, object, T]) -> T:
    async def _runner() -> T:
        try:
            return await coro
        finally:
            await engine.dispose()

    return asyncio.run(_runner())
