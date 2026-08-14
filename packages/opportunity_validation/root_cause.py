"""Root cause engine — explains exactly why every company was rejected.

For every rejected company explain exactly why.

Examples:
    Rejected → No buying signal
    Rejected → Signal older than 120 days
    Rejected → AI company
    Rejected → Duplicate
    Rejected → Competitor
    Rejected → Parked domain
    Rejected → No website
    Rejected → Unknown company
    Rejected → Low trust source
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class RootCauseEngine:
    """Explains exactly why every company was rejected."""

    ROOT_CAUSES = {
        "no_buying_signal": {
            "category": "signal",
            "description": "No valid buying signal detected",
            "action": "Replace with high-intent signal source",
        },
        "stale_signal": {
            "category": "freshness",
            "description": "Signal older than freshness threshold",
            "action": "Update freshness thresholds or collect more frequently",
        },
        "ai_company": {
            "category": "company",
            "description": "Company is an AI/LLM provider",
            "action": "Add to AI exclusion list",
        },
        "duplicate": {
            "category": "deduplication",
            "description": "Company already exists in pipeline",
            "action": "Merge duplicate records",
        },
        "competitor": {
            "category": "company",
            "description": "Company is a known competitor",
            "action": "Add to competitor exclusion list",
        },
        "parked_domain": {
            "category": "website",
            "description": "Website domain is parked",
            "action": "Filter out parked domains",
        },
        "no_website": {
            "category": "website",
            "description": "No website available",
            "action": "Require website for validation",
        },
        "unknown_company": {
            "category": "company",
            "description": "Company cannot be verified",
            "action": "Improve company verification",
        },
        "low_trust_source": {
            "category": "source",
            "description": "Data source has low trust score",
            "action": "Filter out low-trust sources",
        },
        "no_icp_match": {
            "category": "targeting",
            "description": "Company does not match ICP",
            "action": "Refine ICP criteria",
        },
        "low_quality_score": {
            "category": "quality",
            "description": "Quality score below threshold",
            "action": "Improve data quality",
        },
        "no_website_quality": {
            "category": "website",
            "description": "Website quality check failed",
            "action": "Improve website validation",
        },
    }

    def determine_root_cause(
        self,
        validation_decision: str,
        reasons: list[str],
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine root cause of rejection."""
        if validation_decision == "approve":
            return {
                "root_cause": "passes_all_gates",
                "category": "success",
                "description": "Opportunity passed all validation gates",
                "action": "Continue pipeline",
                "confidence": 1.0,
            }

        # Map reasons to root causes
        root_causes = []
        for reason in reasons:
            root_cause = self._map_reason_to_root_cause(reason)
            if root_cause:
                root_causes.append(root_cause)

        if not root_causes:
            return {
                "root_cause": "unknown",
                "category": "unknown",
                "description": "Unable to determine root cause",
                "action": "Manual review required",
                "confidence": 0.0,
            }

        # Return primary root cause (first one)
        primary = root_causes[0]
        return {
            "root_cause": primary["root_cause"],
            "category": primary["category"],
            "description": primary["description"],
            "action": primary["action"],
            "confidence": primary["confidence"],
            "all_causes": root_causes,
        }

    def _map_reason_to_root_cause(self, reason: str) -> dict[str, Any] | None:
        """Map reason to root cause."""
        reason_lower = reason.lower()

        if "no buying signal" in reason_lower or "invalid buying signal" in reason_lower:
            return self._build_root_cause("no_buying_signal", 0.9)
        if "signal too old" in reason_lower or "stale" in reason_lower:
            return self._build_root_cause("stale_signal", 0.9)
        if "ai company" in reason_lower or "ai/llm" in reason_lower:
            return self._build_root_cause("ai_company", 0.95)
        if "duplicate" in reason_lower:
            return self._build_root_cause("duplicate", 0.9)
        if "competitor" in reason_lower:
            return self._build_root_cause("competitor", 0.95)
        if "parked" in reason_lower:
            return self._build_root_cause("parked_domain", 0.9)
        if "no website" in reason_lower or "website" in reason_lower:
            return self._build_root_cause("no_website", 0.8)
        if "unknown company" in reason_lower:
            return self._build_root_cause("unknown_company", 0.7)
        if "low trust" in reason_lower or "source" in reason_lower:
            return self._build_root_cause("low_trust_source", 0.8)
        if "no icp match" in reason_lower:
            return self._build_root_cause("no_icp_match", 0.85)
        if "quality score" in reason_lower:
            return self._build_root_cause("low_quality_score", 0.8)
        if "website quality" in reason_lower:
            return self._build_root_cause("no_website_quality", 0.8)

        return None

    def _build_root_cause(self, root_cause: str, confidence: float) -> dict[str, Any]:
        """Build root cause dict."""
        info = self.ROOT_CAUSES.get(root_cause, {})
        return {
            "root_cause": root_cause,
            "category": info.get("category", "unknown"),
            "description": info.get("description", "Unknown"),
            "action": info.get("action", "Unknown"),
            "confidence": confidence,
        }

    def get_all_root_causes(self) -> dict[str, dict[str, str]]:
        """Get all defined root causes."""
        return dict(self.ROOT_CAUSES)

    def get_root_causes_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get root causes by category."""
        return [
            {"root_cause": rc, **info}
            for rc, info in self.ROOT_CAUSES.items()
            if info.get("category") == category
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get root cause statistics."""
        categories = {}
        for info in self.ROOT_CAUSES.values():
            cat = info.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_root_causes": len(self.ROOT_CAUSES),
            "by_category": categories,
        }
