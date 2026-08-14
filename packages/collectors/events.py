import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NormalizedEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str
    published_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("url", "title", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("published_at")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @property
    def idempotency_key(self) -> str:
        raw = "|".join(
            [
                self.source,
                self.url,
                self.title,
                self.published_at.isoformat(),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @property
    def event_hash(self) -> str:
        payload = {
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "published_at": self.published_at.isoformat(),
            "metadata": self.metadata,
        }
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def stream_payload(self, trace_id: str) -> dict[str, str]:
        payload = self.model_dump(mode="json")
        payload["idempotency_key"] = self.idempotency_key
        payload["event_hash"] = self.event_hash
        payload["trace_id"] = trace_id
        return {"event": json.dumps(payload, sort_keys=True, separators=(",", ":"))}
