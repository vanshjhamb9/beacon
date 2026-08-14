from __future__ import annotations

import re

from decision_discovery.models.types import DecisionMakerCandidate, DecisionRole

# Deterministic service → preferred decision roles (ordered).
_SERVICE_ROLE_MAP: tuple[tuple[str, tuple[DecisionRole, ...]], ...] = (
    (r"\bcomai\b|customer support|support automation|helpdesk", (DecisionRole.HEAD_OF_CUSTOMER_SUPPORT, DecisionRole.SUPPORT_MANAGER, DecisionRole.COO, DecisionRole.CEO)),
    (r"\bai automation\b|automation|rpa|workflow", (DecisionRole.CTO, DecisionRole.HEAD_OF_OPERATIONS, DecisionRole.COO, DecisionRole.AI_LEAD)),
    (r"\bmobile app\b|ios|android|react native", (DecisionRole.FOUNDER, DecisionRole.CTO, DecisionRole.PRODUCT_MANAGER, DecisionRole.CEO)),
    (r"\berp\b|operations platform|supply chain", (DecisionRole.COO, DecisionRole.HEAD_OF_OPERATIONS, DecisionRole.CEO, DecisionRole.FOUNDER)),
    (r"\bwebsite\b|web design|web development|landing page", (DecisionRole.MARKETING_HEAD, DecisionRole.FOUNDER, DecisionRole.CEO, DecisionRole.PRODUCT_MANAGER)),
    (r"\bai\b|machine learning|genai|llm", (DecisionRole.AI_LEAD, DecisionRole.CTO, DecisionRole.INNOVATION_LEAD, DecisionRole.CEO)),
    (r"\bsales\b|crm|revenue", (DecisionRole.SALES_HEAD, DecisionRole.CEO, DecisionRole.FOUNDER)),
    (r"\bproduct\b", (DecisionRole.PRODUCT_MANAGER, DecisionRole.CTO, DecisionRole.FOUNDER)),
)


class BuyerMatcher:
    def preferred_roles(self, recommended_service: str, buyer_persona: str | None) -> list[DecisionRole]:
        roles: list[DecisionRole] = []
        service = recommended_service or ""
        for pattern, mapped in _SERVICE_ROLE_MAP:
            if re.search(pattern, service, flags=re.I):
                roles.extend(mapped)
                break
        if buyer_persona:
            normalized = self._persona_role(buyer_persona)
            if normalized is not None and normalized not in roles:
                roles.insert(0, normalized)
        if not roles:
            roles = [DecisionRole.FOUNDER, DecisionRole.CEO, DecisionRole.CTO, DecisionRole.COO]
        # stable unique
        seen: set[DecisionRole] = set()
        ordered: list[DecisionRole] = []
        for role in roles:
            if role in seen:
                continue
            seen.add(role)
            ordered.append(role)
        return ordered

    def score_candidate(self, candidate: DecisionMakerCandidate, preferred: list[DecisionRole]) -> float:
        if candidate.normalized_role in preferred:
            index = preferred.index(candidate.normalized_role)
            return max(40.0, 100.0 - index * 12.0)
        if candidate.seniority_rank >= 90:
            return 45.0
        return 25.0

    def select_primary_secondary(
        self,
        candidates: list[DecisionMakerCandidate],
        preferred: list[DecisionRole],
    ) -> tuple[DecisionMakerCandidate | None, DecisionMakerCandidate | None, list[DecisionMakerCandidate]]:
        scored: list[DecisionMakerCandidate] = []
        for candidate in candidates:
            match_score = self.score_candidate(candidate, preferred)
            scored.append(
                candidate.model_copy(
                    update={
                        "buyer_match_score": match_score,
                    }
                )
            )
        scored.sort(
            key=lambda item: (item.buyer_match_score, item.seniority_rank, item.confidence),
            reverse=True,
        )
        primary = scored[0] if scored else None
        secondary = scored[1] if len(scored) > 1 else None
        finalized: list[DecisionMakerCandidate] = []
        for index, item in enumerate(scored):
            finalized.append(
                item.model_copy(
                    update={
                        "is_primary": index == 0,
                        "is_secondary": index == 1,
                    }
                )
            )
        return primary, secondary, finalized

    def _persona_role(self, persona: str) -> DecisionRole | None:
        from decision_discovery.extractors.roles import normalize_role

        normalized = normalize_role(persona)
        return normalized[0] if normalized else None
