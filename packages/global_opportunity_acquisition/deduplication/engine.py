from __future__ import annotations

from global_opportunity_acquisition.models.types import NormalizedCompanySignal


class DeduplicationEngine:
    """Cross-source deduplication — merge evidence, never duplicate companies."""

    def merge(self, normalized: list[dict]) -> tuple[list[NormalizedCompanySignal], int]:
        buckets: dict[str, dict] = {}
        duplicates = 0
        for row in normalized:
            key = row["canonical_key"]
            if key not in buckets:
                buckets[key] = {
                    "canonical_key": key,
                    "company_name": row["company_name"],
                    "company_domain": row.get("company_domain"),
                    "source_connector_ids": [row["connector_id"]],
                    "titles": [row["title"]] if row.get("title") else [],
                    "bodies": [row["body"]] if row.get("body") else [],
                    "urls": [row["url"]] if row.get("url") else [],
                    "evidence": [f"source:{row['connector_id']}"],
                }
            else:
                duplicates += 1
                b = buckets[key]
                if row["connector_id"] not in b["source_connector_ids"]:
                    b["source_connector_ids"].append(row["connector_id"])
                if row.get("title"):
                    b["titles"].append(row["title"])
                if row.get("body"):
                    b["bodies"].append(row["body"])
                if row.get("url"):
                    b["urls"].append(row["url"])
                b["evidence"].append(f"merged:{row['connector_id']}")
        return [NormalizedCompanySignal.model_validate(v) for v in buckets.values()], duplicates
