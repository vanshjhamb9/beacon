from __future__ import annotations

from target_account_engine.models.types import EngineScore, ICPProfile, TargetAccountInput


class WhyNowEngine:
    def generate(
        self,
        item: TargetAccountInput,
        *,
        profile: ICPProfile | None,
        fit: EngineScore,
        intent: EngineScore,
        urgency: EngineScore,
        service_match: str | None,
    ) -> str:
        lines: list[str] = []
        if item.funding_days_ago is not None and item.funding_days_ago <= 90:
            stage = item.funding_stage or "funding"
            lines.append(f"Company raised {stage} funding {item.funding_days_ago} days ago.")
        if item.hiring_count > 0:
            roles = ", ".join(item.hiring_roles[:4]) or "key roles"
            lines.append(f"Hiring {item.hiring_count} roles including {roles}.")
        for signal in urgency.evidence[:4]:
            if signal.startswith("funding_within_"):
                continue
            lines.append(f"Trigger: {signal.replace('_', ' ')}.")
        for signal in intent.evidence[:3]:
            if signal not in " ".join(lines).lower():
                lines.append(f"Intent signal: {signal}.")
        for ev in fit.evidence[:2]:
            lines.append(ev if ev.endswith(".") else f"{ev}.")
        service = service_match or (profile.service_match if profile else "Beacon services")
        lines.append(f"Ideal time to pitch {service}.")
        if not any("evidence" in line.lower() or "signal" in line.lower() or "hiring" in line.lower() or "funding" in line.lower() for line in lines[:-1]):
            lines.insert(0, f"{item.company_name} matches ICP signals with scoreable buying pressure.")
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for line in lines:
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(line)
        return " ".join(unique[:8])
