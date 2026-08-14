from typing import Generic, TypeVar
from uuid import UUID

from app.models.base import BaseModel
from app.repositories.base import BaseRepository

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseService(Generic[ModelT]):
    def __init__(self, repository: BaseRepository[ModelT]) -> None:
        self.repository = repository

    async def get_required(self, entity_id: UUID) -> ModelT:
        entity = await self.repository.get(entity_id)
        if entity is None:
            raise LookupError(f"{self.repository.model.__name__} was not found.")
        return entity
