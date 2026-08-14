from __future__ import annotations

from target_account_engine.models.types import ICPProfile, TargetAccountInput


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _contains_any(haystack: list[str], needles: list[str]) -> list[str]:
    text = " ".join(_norm(item) for item in haystack)
    hits: list[str] = []
    for needle in needles:
        n = _norm(needle)
        if n and n in text:
            hits.append(needle)
    return hits


class ICPMatcher:
    """Match a company against configurable ICP profiles. Deterministic."""

    def match(self, item: TargetAccountInput, profiles: list[ICPProfile]) -> tuple[ICPProfile | None, float, list[str]]:
        if not profiles:
            return None, 0.0, []
        ranked = sorted(profiles, key=lambda row: row.priority)
        best: ICPProfile | None = None
        best_score = -1.0
        best_evidence: list[str] = []
        for profile in ranked:
            score, evidence = self._score_profile(item, profile)
            if score > best_score:
                best = profile
                best_score = score
                best_evidence = evidence
        if best is None or best_score < 20.0:
            return None, max(0.0, best_score), best_evidence
        return best, round(best_score, 2), best_evidence

    def _score_profile(self, item: TargetAccountInput, profile: ICPProfile) -> tuple[float, list[str]]:
        score = 0.0
        evidence: list[str] = []
        industry = _norm(item.industry)
        if profile.industries:
            if any(ind in industry or industry in _norm(ind) for ind in profile.industries):
                score += 18.0
                evidence.append(f"Industry matches {profile.name}")
            else:
                score -= 8.0
        else:
            score += 5.0

        employees = item.employee_count
        if employees is not None and (profile.employee_count_min or profile.employee_count_max):
            lo = profile.employee_count_min or 0
            hi = profile.employee_count_max or 10_000_000
            if lo <= employees <= hi:
                score += 16.0
                evidence.append(f"Employee count {employees} in ICP range {lo}-{hi}")
            else:
                score -= 10.0

        tech_hits = _contains_any(item.technologies, profile.technology_stack)
        if tech_hits:
            score += min(18.0, 6.0 * len(tech_hits))
            evidence.append(f"Technology stack hits: {', '.join(tech_hits[:5])}")

        hiring_hits = _contains_any(item.hiring_roles + item.signals, profile.hiring_signals)
        if hiring_hits:
            score += min(14.0, 4.0 * len(hiring_hits))
            evidence.append(f"Hiring signals: {', '.join(hiring_hits[:5])}")

        pain_hits = _contains_any(item.pains + item.signals, profile.pain_points)
        if pain_hits:
            score += min(16.0, 4.0 * len(pain_hits))
            evidence.append(f"Pain points: {', '.join(pain_hits[:5])}")

        buy_hits = _contains_any(
            item.signals + item.growth_signals + item.goals + item.pains,
            profile.buying_signals,
        )
        if buy_hits:
            score += min(14.0, 3.5 * len(buy_hits))
            evidence.append(f"Buying signals: {', '.join(buy_hits[:5])}")

        growth_hits = _contains_any(item.growth_signals + item.signals, profile.growth_signals)
        if growth_hits:
            score += min(10.0, 3.0 * len(growth_hits))
            evidence.append(f"Growth signals: {', '.join(growth_hits[:4])}")

        if item.business_model and profile.business_models:
            if any(_norm(item.business_model) in _norm(bm) or _norm(bm) in _norm(item.business_model) for bm in profile.business_models):
                score += 8.0
                evidence.append(f"Business model {_norm(item.business_model)} fits ICP")

        if item.country and profile.countries:
            if any(_norm(item.country) == _norm(c) for c in profile.countries):
                score += 6.0
                evidence.append(f"Country {item.country} in ICP")
            else:
                score -= 4.0

        negative = _contains_any(item.signals + item.pains + item.reviews, profile.negative_signals)
        if negative:
            score -= min(25.0, 8.0 * len(negative))
            evidence.append(f"Negative signals: {', '.join(negative[:3])}")

        website = item.website_metrics or {}
        if profile.key == "website_development":
            lighthouse = website.get("lighthouse") or website.get("lighthouse_score")
            if isinstance(lighthouse, (int, float)) and lighthouse < 60:
                score += 12.0
                evidence.append(f"Low Lighthouse score ({lighthouse})")
            if website.get("outdated") or website.get("mobile_unfriendly"):
                score += 10.0
                evidence.append("Website quality issues detected")
            traffic = website.get("traffic") or website.get("monthly_visits")
            if isinstance(traffic, (int, float)) and traffic >= 10_000:
                score += 8.0
                evidence.append(f"High traffic ({traffic})")

        if profile.key == "mobile_app_development":
            if any("launch" in _norm(s) or "mobile" in _norm(s) for s in item.signals + item.goals):
                score += 10.0
                evidence.append("Product/mobile launch signals present")
            if item.funding_stage:
                score += 6.0
                evidence.append(f"Funding stage {item.funding_stage}")

        return max(0.0, min(100.0, score)), evidence
