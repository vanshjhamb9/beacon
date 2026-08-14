from abc import ABC, abstractmethod
from collections.abc import Sequence

import httpx

from collectors.events import NormalizedEvent


class BaseCollector(ABC):
    source: str

    def __init__(self, http_client: httpx.AsyncClient, *, max_items: int) -> None:
        self.http_client = http_client
        self.max_items = max_items

    @abstractmethod
    async def collect(self) -> Sequence[NormalizedEvent]:
        raise NotImplementedError
