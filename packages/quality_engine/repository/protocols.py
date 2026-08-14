from typing import Protocol

from quality_engine.models.types import SourceQualityProfile


class QualityContextRepository(Protocol):
    async def source_profile(self, source: str) -> SourceQualityProfile:
        ...

    async def recent_content_hashes(self, source: str, *, limit: int = 500) -> set[str]:
        ...

    async def recent_fingerprints(self, source: str, *, limit: int = 500) -> list[str]:
        ...

    async def processed_urls(self, source: str, *, limit: int = 500) -> set[str]:
        ...
