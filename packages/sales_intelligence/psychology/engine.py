from __future__ import annotations

from sales_intelligence.models.types import CommunicationStyle, PsychologyProfile, SalesIntelligenceInput


class PsychologyEngine:
    def analyze(self, item: SalesIntelligenceInput) -> PsychologyProfile:
        blob = " ".join(item.pains + item.goals + item.signals + item.hiring_roles).lower()
        evidence: list[str] = []

        motivation = "growth"
        if any(x in blob for x in ("cost", "efficiency", "manual", "automation")):
            motivation = "efficiency"
            evidence.append("motivation:efficiency")
        elif any(x in blob for x in ("support", "customer", "conversion")):
            motivation = "customer_experience"
            evidence.append("motivation:cx")
        else:
            evidence.append("motivation:growth")

        risk = "moderate"
        if item.funding_stage and item.funding_stage.lower() in {"bootstrapped", "seed"}:
            risk = "conservative"
        elif (item.employee_count or 0) >= 250 or (item.funding_stage or "").lower() in {"series b", "series c", "public"}:
            risk = "managed"
        evidence.append(f"risk:{risk}")

        innovation = "high" if any(x in blob for x in ("ai", "llm", "automation", "agent")) else (
            "medium" if item.technologies else "low"
        )
        evidence.append(f"innovation:{innovation}")

        growth = "aggressive" if item.hiring_count >= 5 or "scaling" in blob else (
            "steady" if item.hiring_count > 0 else "stable"
        )
        evidence.append(f"growth:{growth}")

        cost = "high" if any(x in blob for x in ("cost", "budget", "roi", "cheap")) else (
            "medium" if (item.employee_count or 0) < 100 else "low"
        )
        evidence.append(f"cost_sensitivity:{cost}")

        auto = min(100.0, 30.0 + sum(8.0 for t in item.technologies if any(k in t.lower() for k in ("zapier", "automation", "rpa", "ai", "bot"))) + len(item.pains) * 4.0)
        pain = min(100.0, 20.0 + len(item.pains) * 12.0 + (10.0 if "manual" in blob else 0.0))

        style = CommunicationStyle.CONSULTATIVE
        if any(x in blob for x in ("cto", "engineer", "technical", "api")):
            style = CommunicationStyle.TECHNICAL
        elif any(x in blob for x in ("ceo", "founder", "board")):
            style = CommunicationStyle.EXECUTIVE
        elif motivation == "efficiency":
            style = CommunicationStyle.DIRECT
        evidence.append(f"style:{style.value}")

        return PsychologyProfile(
            buyer_motivation=motivation,
            risk_tolerance=risk,
            innovation_level=innovation,
            growth_focus=growth,
            cost_sensitivity=cost,
            automation_readiness=round(auto, 4),
            pain_intensity=round(pain, 4),
            preferred_communication_style=style,
            evidence=evidence,
        )
