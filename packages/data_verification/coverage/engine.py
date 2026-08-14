from __future__ import annotations

from typing import Any

from data_verification.models.types import CompletenessScores, CoverageBreakdown, LeadReadinessChecklist


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _ratio(present: int, expected: int) -> float:
    if expected <= 0:
        return 0.0
    return round((present / expected) * 100.0, 2)


class CoverageEngine:
    def evaluate(
        self,
        lead_profile: dict[str, Any],
        *,
        timeline_event_count: int,
    ) -> tuple[CompletenessScores, list[CoverageBreakdown], LeadReadinessChecklist, list[str]]:
        profile = lead_profile.get("company_profile") or {}
        contacts = list(lead_profile.get("public_contact_information") or [])
        people = list(lead_profile.get("decision_makers") or [])
        technologies = list(lead_profile.get("technology_stack") or [])
        social = list(lead_profile.get("social_profiles") or [])
        jobs = list(lead_profile.get("open_jobs") or [])
        team = lead_profile.get("team_insights") or {}
        evidence = list(lead_profile.get("evidence_chain") or [])

        company_fields = {
            "website": profile.get("website"),
            "domain": profile.get("domain"),
            "industry": profile.get("industry"),
            "description": profile.get("description"),
            "location": profile.get("location"),
            "country": profile.get("country"),
            "founded_year": profile.get("founded_year"),
            "employee_count_estimate": profile.get("employee_count_estimate"),
            "company_size_range": profile.get("company_size_range"),
        }
        company_present = sum(1 for value in company_fields.values() if _present(value))
        company_missing = [name for name, value in company_fields.items() if not _present(value)]

        has_email = any(
            str(item.get("kind") or "") in {"company_email", "role_based_email"} and _present(item.get("value"))
            for item in contacts
        )
        has_phone = any(str(item.get("kind") or "") == "business_phone" and _present(item.get("value")) for item in contacts)
        has_role_email = any(str(item.get("kind") or "") == "role_based_email" for item in contacts)
        contact_checks = [has_email, has_phone, has_role_email, bool(contacts)]
        contact_present = sum(1 for item in contact_checks if item)
        contact_missing = [
            name
            for name, ok in (
                ("public_business_email", has_email),
                ("public_phone", has_phone),
                ("role_based_email", has_role_email),
                ("any_contact", bool(contacts)),
            )
            if not ok
        ]

        leadership_roles = {str(person.get("role") or "").lower() for person in people}
        has_executive = any(
            role in leadership_roles or any(token in role for token in ("ceo", "cto", "coo", "founder", "head"))
            for role in leadership_roles
        )
        has_linkedin = any(_present(person.get("linkedin_url")) for person in people)
        leadership_checks = [bool(people), has_executive, has_linkedin, len(people) >= 1]
        leadership_present = sum(1 for item in leadership_checks if item)
        leadership_missing = [
            name
            for name, ok in (
                ("decision_makers", bool(people)),
                ("executive_role", has_executive),
                ("leadership_linkedin", has_linkedin),
            )
            if not ok
        ]

        tech_categories = {str(item.get("category") or "") for item in technologies}
        technology_checks = [
            bool(technologies),
            len(technologies) >= 2,
            len(tech_categories) >= 2,
            any(float(item.get("confidence") or 0) >= 70 for item in technologies),
        ]
        technology_present = sum(1 for item in technology_checks if item)
        technology_missing = ["technology_stack"] if not technologies else []

        revenue_fields = {
            "recommended_service": lead_profile.get("recommended_service"),
            "business_pain": lead_profile.get("business_pain"),
            "buyer_persona": lead_profile.get("buyer_persona"),
            "estimated_budget": lead_profile.get("estimated_budget"),
            "priority": lead_profile.get("priority"),
            "best_outreach_angle": lead_profile.get("best_outreach_angle"),
            "revenue_estimate": profile.get("revenue_estimate"),
        }
        revenue_present = sum(1 for value in revenue_fields.values() if _present(value))
        revenue_missing = [name for name, value in revenue_fields.items() if not _present(value)]

        hiring_checks = [
            bool(jobs) or bool(team.get("open_positions")),
            bool(team.get("recent_hires")),
            _present(team.get("hiring_trends")),
            _present(team.get("engineering_team_estimate")) or _present(team.get("leadership_team_size")),
        ]
        hiring_present = sum(1 for item in hiring_checks if item)
        hiring_missing = [
            name
            for name, ok in (
                ("open_positions", bool(jobs) or bool(team.get("open_positions"))),
                ("recent_hires", bool(team.get("recent_hires"))),
                ("hiring_trends", _present(team.get("hiring_trends"))),
            )
            if not ok
        ]

        social_platforms = {str(item.get("platform") or "").lower() for item in social}
        social_checks = [
            bool(social),
            "linkedin" in social_platforms,
            "website" in social_platforms or _present(profile.get("website")),
            len(social_platforms) >= 2,
        ]
        social_present = sum(1 for item in social_checks if item)
        social_missing = ["social_profiles"] if not social else ([] if "linkedin" in social_platforms else ["linkedin"])

        evidence_checks = [
            bool(evidence),
            len(evidence) >= 2,
            any(_present(item.get("source")) for item in evidence),
            any(float(item.get("confidence") or 0) >= 60 for item in evidence),
        ]
        evidence_present = sum(1 for item in evidence_checks if item)
        evidence_missing = ["evidence_chain"] if not evidence else []

        timeline_score = 100.0 if timeline_event_count >= 5 else _ratio(timeline_event_count, 5)
        timeline_missing = ["timeline_events"] if timeline_event_count < 1 else []

        company_score = _ratio(company_present, len(company_fields))
        contact_score = _ratio(contact_present, len(contact_checks))
        leadership_score = _ratio(leadership_present, len(leadership_checks))
        technology_score = _ratio(technology_present, len(technology_checks))
        revenue_score = _ratio(revenue_present, len(revenue_fields))
        hiring_score = _ratio(hiring_present, len(hiring_checks))
        social_score = _ratio(social_present, len(social_checks))
        evidence_score = _ratio(evidence_present, len(evidence_checks))

        overall = round(
            company_score * 0.18
            + contact_score * 0.16
            + leadership_score * 0.14
            + technology_score * 0.12
            + revenue_score * 0.12
            + hiring_score * 0.08
            + social_score * 0.08
            + evidence_score * 0.07
            + timeline_score * 0.05,
            2,
        )

        completeness = CompletenessScores(
            overall_completeness=overall,
            company_profile_completeness=company_score,
            contact_completeness=contact_score,
            leadership_completeness=leadership_score,
            technology_completeness=technology_score,
            revenue_completeness=revenue_score,
            hiring_completeness=hiring_score,
            social_profile_completeness=social_score,
            evidence_completeness=evidence_score,
            timeline_completeness=timeline_score,
        )

        coverage = [
            CoverageBreakdown(
                category="company_profile",
                present_fields=company_present,
                expected_fields=len(company_fields),
                score=company_score,
                missing_fields=company_missing,
            ),
            CoverageBreakdown(
                category="contacts",
                present_fields=contact_present,
                expected_fields=len(contact_checks),
                score=contact_score,
                missing_fields=contact_missing,
            ),
            CoverageBreakdown(
                category="leadership",
                present_fields=leadership_present,
                expected_fields=len(leadership_checks),
                score=leadership_score,
                missing_fields=leadership_missing,
            ),
            CoverageBreakdown(
                category="technology",
                present_fields=technology_present,
                expected_fields=len(technology_checks),
                score=technology_score,
                missing_fields=technology_missing,
            ),
            CoverageBreakdown(
                category="revenue",
                present_fields=revenue_present,
                expected_fields=len(revenue_fields),
                score=revenue_score,
                missing_fields=revenue_missing,
            ),
            CoverageBreakdown(
                category="hiring",
                present_fields=hiring_present,
                expected_fields=len(hiring_checks),
                score=hiring_score,
                missing_fields=hiring_missing,
            ),
            CoverageBreakdown(
                category="social",
                present_fields=social_present,
                expected_fields=len(social_checks),
                score=social_score,
                missing_fields=social_missing,
            ),
            CoverageBreakdown(
                category="evidence",
                present_fields=evidence_present,
                expected_fields=len(evidence_checks),
                score=evidence_score,
                missing_fields=evidence_missing,
            ),
            CoverageBreakdown(
                category="timeline",
                present_fields=min(timeline_event_count, 5),
                expected_fields=5,
                score=timeline_score,
                missing_fields=timeline_missing,
            ),
        ]

        funding_present = _present(profile.get("revenue_estimate")) or any(
            "fund" in str(item.get("summary") or "").lower() or "fund" in str(item.get("category") or "").lower()
            for item in evidence
        )

        checklist = LeadReadinessChecklist(
            company_profile=company_score >= 60.0,
            technology=technology_score >= 50.0,
            leadership=leadership_score >= 50.0,
            public_business_email=has_email,
            public_phone=has_phone,
            hiring=hiring_score >= 40.0,
            funding=funding_present,
            timeline=timeline_event_count >= 1,
        )

        missing = sorted({field for item in coverage for field in item.missing_fields})
        return completeness, coverage, checklist, missing
