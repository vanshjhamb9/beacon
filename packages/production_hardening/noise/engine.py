from __future__ import annotations

from typing import Any, Hashable


class NoiseCollapser:
    """Collapse repeated evidence / tech / signals / pains / recommendations."""

    def collapse(self, items: list[Any], *, key_fn=None) -> list[Any]:
        seen: set[Hashable] = set()
        out: list[Any] = []
        for item in items:
            key: Hashable
            if key_fn is not None:
                key = key_fn(item)
            elif isinstance(item, dict):
                key = tuple(sorted((k, str(v)) for k, v in item.items() if k in {"summary", "category", "source_type", "name", "url", "value"}))
            else:
                key = str(item).strip().lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out
