import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.raw_event import RawEvent
from app.repositories.base import BaseRepository


class RawEventRepository(BaseRepository[RawEvent]):
    model = RawEvent

    async def create_if_new(self, values: dict[str, object]) -> bool:
        insert_values = dict(values)
        insert_values["metadata"] = insert_values.pop("event_metadata", {})

        statement = insert(RawEvent.__table__).values(**insert_values)
        statement = statement.on_conflict_do_nothing(index_elements=["idempotency_key"]).returning(
            RawEvent.__table__.c.id
        )
        result = await self.session.execute(statement)
        created_id = result.scalar_one_or_none()
        return isinstance(created_id, uuid.UUID)

    async def exists_by_idempotency_key(self, idempotency_key: str) -> bool:
        result = await self.session.execute(
            select(RawEvent.id).where(RawEvent.idempotency_key == idempotency_key).limit(1)
        )
        return result.scalar_one_or_none() is not None
