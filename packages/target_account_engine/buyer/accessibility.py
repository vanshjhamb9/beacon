from __future__ import annotations

from target_account_engine.models.types import EngineScore, TargetAccountInput


class AccessibilityEngine:
    """Can we reach them? Channels + decision makers + verification."""

    def score(self, item: TargetAccountInput) -> EngineScore:
        score = 0.0
        evidence: list[str] = []
        channels = {c.strip().lower() for c in item.channels}
        contact_types = set()
        for contact in item.contacts:
            for key in ("email", "linkedin", "whatsapp", "phone", "type", "channel"):
                value = contact.get(key)
                if isinstance(value, str) and value:
                    contact_types.add(value.lower())
                    channels.add(value.lower())

        checks = [
            ("email", 18.0, "Verified email path"),
            ("linkedin", 14.0, "LinkedIn reachability"),
            ("whatsapp", 12.0, "WhatsApp channel"),
            ("phone", 10.0, "Phone contact"),
            ("website", 8.0, "Website present"),
            ("contact_form", 8.0, "Contact form available"),
        ]
        for key, points, label in checks:
            if key in channels or any(key in ct for ct in contact_types):
                score += points
                evidence.append(label)

        if item.domain or item.website:
            if "website" not in {e.lower() for e in evidence}:
                score += 8.0
                evidence.append("Website/domain available")

        dm_count = len(item.decision_makers)
        if dm_count:
            score += min(20.0, 8.0 * dm_count)
            evidence.append(f"{dm_count} decision maker(s) identified")
        else:
            evidence.append("No decision maker identified yet")

        score += min(15.0, item.verification_score * 0.15)
        if item.verification_score >= 70:
            evidence.append(f"Verification score {item.verification_score:.0f}")

        score = min(100.0, score)
        return EngineScore(
            score=round(score, 2),
            explanation=f"Accessibility {score:.1f}/100 based on channels and decision makers.",
            evidence=evidence,
            details={"channels": sorted(channels), "decision_makers": dm_count},
        )
