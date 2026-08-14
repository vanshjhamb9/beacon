from __future__ import annotations

from global_opportunity_acquisition.models.types import FundingEvent

ROUND_PATTERNS: list[tuple[str, tuple[str, ...], float]] = [
    ("seed", ("seed round", "pre-seed", "seed funding"), 80.0),
    ("series_a", ("series a", "series-a"), 85.0),
    ("series_b", ("series b", "series-b"), 85.0),
    ("series_c", ("series c", "series-c"), 85.0),
    ("acquisition", ("acquired", "acquisition", "acquires"), 88.0),
    ("ipo", ("ipo", "goes public", "s-1 filing"), 90.0),
    ("new_office", ("new office", "opened office"), 75.0),
    ("global_expansion", ("global expansion", "international expansion"), 78.0),
]


class FundingIntelligenceEngine:
    def detect(self, texts: list[str]) -> list[FundingEvent]:
        blob = " ".join(texts).lower()
        out: list[FundingEvent] = []
        for round_name, patterns, conf in ROUND_PATTERNS:
            hits = [p for p in patterns if p in blob]
            if hits:
                out.append(
                    FundingEvent(
                        round=round_name,
                        amount_hint=None,
                        confidence=min(95.0, conf + len(hits) * 2.0),
                        evidence=[f"hits:{','.join(hits[:3])}"],
                    )
                )
        return out
