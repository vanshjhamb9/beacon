from __future__ import annotations

from global_opportunity_acquisition.models.types import ProcurementSignal


class ProcurementIntelligenceEngine:
    def detect(self, texts: list[str]) -> list[ProcurementSignal]:
        blob = " ".join(texts).lower()
        out: list[ProcurementSignal] = []
        patterns = [
            ("rfp", ("rfp", "request for proposal"), "Public RFP signal"),
            ("tender", ("tender", "government tender"), "Government tender signal"),
            ("procurement", ("procurement", "vendor selection"), "Procurement signal"),
        ]
        for kind, keys, summary in patterns:
            hits = [k for k in keys if k in blob]
            if hits:
                out.append(
                    ProcurementSignal(
                        tender_type=kind,
                        summary=summary,
                        confidence=min(95.0, 70.0 + len(hits) * 8.0),
                        evidence=[f"hits:{','.join(hits)}"],
                    )
                )
        return out
