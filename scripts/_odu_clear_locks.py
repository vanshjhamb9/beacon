import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "packages"), str(ROOT)]


async def main() -> None:
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as s:
        rows = (
            await s.execute(
                text(
                    """
                    SELECT pid, state, wait_event_type, wait_event, left(query, 100) AS q
                    FROM pg_stat_activity
                    WHERE datname = current_database() AND pid <> pg_backend_pid()
                    """
                )
            )
        ).fetchall()
        print("sessions", len(rows))
        for r in rows:
            print(dict(r._mapping))
        killed = (
            await s.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                      AND pid <> pg_backend_pid()
                      AND (
                        state = 'idle in transaction'
                        OR wait_event_type = 'Lock'
                      )
                    """
                )
            )
        ).fetchall()
        await s.commit()
        print("terminated", len(killed))


if __name__ == "__main__":
    asyncio.run(main())
