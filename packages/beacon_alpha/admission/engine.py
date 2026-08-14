from __future__ import annotations

from typing import Any

from production_hardening.admission.engine import FAKE_NAME_PATTERNS
from beacon_alpha.models.types import AdmissionResult, UNKNOWN

REJECT_HINTS = (
    "github.com/",
    "reddit.com/",
    "medium.com/",
    "dev.to/",
    "personal portfolio",
    "open source",
    "documentation",
    "tutorial",
    "awesome-",
)


class ColdEmailAdmissionEngine:
    """Rule 1 — Would Vansh personally spend his next cold email on this company?"""

    def evaluate(self, payload: dict[str, Any]) -> AdmissionResult:
        name = str(payload.get("company_name") or payload.get("legal_name") or "").strip()
        website = str(payload.get("website") or payload.get("domain") or "").strip()
        evidence = payload.get("evidence") or payload.get("timeline") or []
        narrative = str(payload.get("narrative") or payload.get("description") or payload.get("business_description") or "")
        industry = str(payload.get("industry") or "")
        entity = str(payload.get("entity_type") or "").lower()
        reasons: list[str] = []
        proof: list[str] = []

        if not name:
            reasons.append("no_identity")
        elif name.lower() in FAKE_NAME_PATTERNS:
            reasons.append("fake_or_noise_name")
        else:
            proof.append(f"name:{name}")

        if not website:
            reasons.append("no_website")
        else:
            proof.append(f"website:{website}")

        if not evidence:
            reasons.append("no_evidence")
        else:
            proof.append(f"evidence:{len(evidence) if hasattr(evidence, '__len__') else 1}")

        if len(narrative.strip()) < 20 and not payload.get("business_description"):
            reasons.append("no_business_description")
        else:
            proof.append("has_description")

        if not industry:
            reasons.append("no_industry")

        blob = " ".join([name, website, narrative, str(payload.get("url") or ""), entity]).lower()
        if any(h in blob for h in REJECT_HINTS) or entity in {
            "repository",
            "blog",
            "individual",
            "community",
            "documentation",
            "library",
        }:
            reasons.append("not_a_real_business_target")

        # Soft signal: opportunity / intent must exist for email worthiness
        if not (payload.get("signals") or payload.get("opportunity") or payload.get("buying_intent") or payload.get("recommended_service")):
            reasons.append("no_opportunity_signal")

        admit = len(reasons) == 0
        return AdmissionResult(
            admit=admit,
            reason="worth_cold_email" if admit else ";".join(reasons) or "rejected",
            evidence=proof if admit else [f"reject:{r}" for r in reasons],
        )
