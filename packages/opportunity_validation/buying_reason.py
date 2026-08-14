"""Buying reason engine — explains why company should be contacted now.

Answer: Why now? Why this company?
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


class BuyingReasonEngine:
    """Determines why a company is a valid buying opportunity now."""

    STRONG_SIGNALS = {
        "Hiring": "Actively hiring — needs team/tools",
        "Expansion": "Expanding operations — scaling up",
        "Migration": "Migrating systems — actively changing",
        "Funding": "Just raised funding — has budget",
        "Compliance": "Facing compliance deadline — urgent need",
        "Digital Transformation": "Digital transformation — modernizing",
        "Infrastructure Upgrade": "Upgrading infrastructure — investing",
        "Cloud Migration": "Moving to cloud — changing stack",
        "Automation": "Implementing automation — optimizing",
        "New Office": "Opening new office — growing",
        "ERP Migration": "Replacing ERP — major investment",
        "CRM Migration": "Replacing CRM — actively shopping",
        "Technology Replacement": "Replacing technology — decision made",
        "Executive Hiring": "Hiring executives — building team",
        "Partnership": "Forming partnerships — scaling",
        "API Launch": "Launching API — expanding platform",
        "Marketplace Launch": "Launching marketplace — growing ecosystem",
    }

    WEAK_SIGNALS = {
        "Blog posts": "Content marketing — no buying intent",
        "Marketing articles": "Educational content — researching",
        "Random tweets": "Social activity — no intent",
        "Motivational posts": "Inspirational content — no action",
        "Old Product Hunt launches": "Old launch — no current activity",
    }

    def determine_reason(
        self,
        signal_type: str,
        signal_age_days: int,
        company_industry: str,
        company_country: str,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine why this company should be contacted now."""
        reason_parts = []
        confidence = 0.0

        # Check if strong signal
        if signal_type in self.STRONG_SIGNALS:
            reason_parts.append(self.STRONG_SIGNALS[signal_type])
            confidence = 0.9
        elif signal_type in self.WEAK_SIGNALS:
            reason_parts.append(self.WEAK_SIGNALS[signal_type])
            confidence = 0.3
        else:
            reason_parts.append(f"Signal type: {signal_type}")
            confidence = 0.5

        # Check signal freshness
        if signal_age_days <= 7:
            reason_parts.append("Very fresh signal (≤7 days)")
            confidence = min(confidence + 0.1, 1.0)
        elif signal_age_days <= 30:
            reason_parts.append("Fresh signal (≤30 days)")
            confidence = min(confidence + 0.05, 1.0)
        elif signal_age_days <= 90:
            reason_parts.append("Aging signal (≤90 days)")
            confidence = max(confidence - 0.1, 0.0)
        else:
            reason_parts.append(f"Stale signal ({signal_age_days} days)")
            confidence = max(confidence - 0.3, 0.0)

        # Check industry relevance
        if company_industry in ("Technology", "SaaS", "Software"):
            reason_parts.append("Tech industry — high intent")
            confidence = min(confidence + 0.05, 1.0)
        elif company_industry in ("Finance", "Healthcare", "Retail"):
            reason_parts.append("Digital industry — moderate intent")
            confidence = min(confidence + 0.02, 1.0)

        # Build why_now explanation
        why_now = "; ".join(reason_parts) if reason_parts else "Unknown"

        return {
            "why_now": why_now,
            "confidence": round(confidence, 3),
            "signal_type": signal_type,
            "signal_age_days": signal_age_days,
            "strong_signal": signal_type in self.STRONG_SIGNALS,
            "reason_parts": reason_parts,
        }

    def would_sdr_contact(
        self,
        signal_type: str,
        signal_age_days: int,
        quality_score: int,
        confidence: float,
        icp_match: bool,
    ) -> dict[str, Any]:
        """Would a human SDR actually contact this company?"""
        score = 0
        reasons = []

        # Signal strength
        if signal_type in self.STRONG_SIGNALS:
            score += 40
            reasons.append("Strong buying signal")
        elif signal_type in self.WEAK_SIGNALS:
            score += 10
            reasons.append("Weak buying signal")
        else:
            score += 20
            reasons.append("Unknown signal strength")

        # Signal freshness
        if signal_age_days <= 30:
            score += 25
            reasons.append("Very fresh signal")
        elif signal_age_days <= 90:
            score += 15
            reasons.append("Fresh signal")
        else:
            score += 5
            reasons.append("Stale signal")

        # Quality score
        if quality_score >= 90:
            score += 20
            reasons.append("High quality")
        elif quality_score >= 75:
            score += 10
            reasons.append("Medium quality")
        else:
            score += 0
            reasons.append("Low quality")

        # ICP match
        if icp_match:
            score += 15
            reasons.append("ICP match")

        # Decision
        would_contact = score >= 60
        verdict = "YES" if would_contact else "NO"

        return {
            "verdict": verdict,
            "score": score,
            "reasons": reasons,
            "would_contact": would_contact,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get buying reason statistics."""
        return {
            "strong_signals": list(self.STRONG_SIGNALS.keys()),
            "weak_signals": list(self.WEAK_SIGNALS.keys()),
            "total_strong_signals": len(self.STRONG_SIGNALS),
            "total_weak_signals": len(self.WEAK_SIGNALS),
        }
