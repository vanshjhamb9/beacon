from __future__ import annotations

from sales_intelligence.models.types import ObjectionType, PredictedObjection, SalesIntelligenceInput


OBJECTION_PLAYBOOK: dict[ObjectionType, dict[str, object]] = {
    ObjectionType.BUDGET: {
        "patterns": ["budget", "cost", "expensive", "price"],
        "response": "Anchor on ROI and phased MVP scope to reduce upfront commitment.",
        "base": 45.0,
    },
    ObjectionType.TIMELINE: {
        "patterns": ["timeline", "later", "next quarter", "busy"],
        "response": "Offer a 2-week discovery workshop with clear milestones.",
        "base": 40.0,
    },
    ObjectionType.SECURITY: {
        "patterns": ["security", "soc2", "encryption", "data privacy"],
        "response": "Share security checklist, data handling policy, and prior audit posture.",
        "base": 35.0,
    },
    ObjectionType.COMPLIANCE: {
        "patterns": ["compliance", "hipaa", "gdpr", "regulated"],
        "response": "Map compliance requirements into the delivery plan with evidence from similar industries.",
        "base": 35.0,
    },
    ObjectionType.EXISTING_VENDOR: {
        "patterns": ["vendor", "already use", "incumbent", "zendesk", "salesforce"],
        "response": "Position as complementary layer that improves the current stack, not a rip-and-replace.",
        "base": 42.0,
    },
    ObjectionType.INTERNAL_TEAM: {
        "patterns": ["internal team", "in-house", "we have engineers"],
        "response": "Frame as acceleration + specialist delivery that frees internal team for core product.",
        "base": 48.0,
    },
    ObjectionType.ROI: {
        "patterns": ["roi", "payback", "value", "prove"],
        "response": "Quantify status-quo cost and show 90-day measurable outcome targets.",
        "base": 50.0,
    },
    ObjectionType.TRUST: {
        "patterns": ["trust", "reference", "case study", "unknown"],
        "response": "Lead with relevant case study, portfolio, and founder-led discovery call.",
        "base": 38.0,
    },
    ObjectionType.TECHNICAL_COMPLEXITY: {
        "patterns": ["complex", "integration", "legacy", "hard"],
        "response": "Propose architecture spike + phased integration with rollback plan.",
        "base": 44.0,
    },
}


class ObjectionPredictionEngine:
    def predict(self, item: SalesIntelligenceInput, *, limit: int = 6) -> list[PredictedObjection]:
        blob = " ".join(
            item.pains + item.signals + item.objections_seen + item.notes + [str(r.get("body", "")) for r in item.replies]
        ).lower()
        results: list[PredictedObjection] = []
        for obj, cfg in OBJECTION_PLAYBOOK.items():
            patterns = [str(p) for p in cfg["patterns"]]  # type: ignore[index]
            hits = [p for p in patterns if p in blob]
            likelihood = float(cfg["base"])
            evidence = [f"base:{cfg['base']}"]
            if hits:
                likelihood += min(30.0, len(hits) * 10.0)
                evidence.extend([f"pattern:{h}" for h in hits])
            if obj == ObjectionType.EXISTING_VENDOR and item.vendors:
                likelihood += 15.0
                evidence.append(f"vendors:{len(item.vendors)}")
            if obj == ObjectionType.INTERNAL_TEAM and item.hiring_count >= 3:
                likelihood += 10.0
                evidence.append(f"hiring_count:{item.hiring_count}")
            if obj == ObjectionType.COMPLIANCE and (item.industry or "").lower() in {"healthcare", "fintech", "legal"}:
                likelihood += 12.0
                evidence.append(f"industry:{item.industry}")
            likelihood = min(95.0, likelihood)
            confidence = min(92.0, 50.0 + len(hits) * 12.0 + (8.0 if evidence else 0.0))
            results.append(
                PredictedObjection(
                    objection=obj,
                    likelihood=round(likelihood, 4),
                    confidence=round(confidence, 4),
                    suggested_response=str(cfg["response"]),
                    evidence=evidence,
                )
            )
        results.sort(key=lambda r: (-r.likelihood, r.objection.value))
        return results[:limit]
