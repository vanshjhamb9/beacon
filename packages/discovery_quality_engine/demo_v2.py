"""DQE v2 Standalone Demo — runs the full quality gate pipeline with scoring and grading."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

sys.path.insert(0, "packages")
sys.path.insert(0, "apps/api")
sys.path.insert(0, ".")

from discovery_quality_engine.activity_engine import ActivityEvidence
from discovery_quality_engine.dqe_orchestrator_v2 import DQEOrchestratorV2
from discovery_quality_engine.v2_schemas import QualityGrade


def run_demo():
    orch = DQEOrchestratorV2()
    now = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)

    companies = [
        {
            "company_id": uuid4(),
            "company_name": "TechFlow AI Solutions",
            "website": "https://techflow.io",
            "industry": "Technology",
            "country": "US",
            "signal_type": "Hiring",
            "signal_source": "LinkedIn",
            "signal_title": "VP of Engineering hired",
            "signal_timestamp": now - timedelta(days=5),
            "signal_types": ["Hiring"],
            "domain": "techflow.io",
            "has_https": True,
            "content_length": 8000,
            "company_age_days": 1800,
            "activity_evidence": [
                ActivityEvidence(
                    activity_type="Hiring",
                    timestamp=now - timedelta(days=3),
                    source="LinkedIn",
                    title="Hired VP Engineering",
                ),
                ActivityEvidence(
                    activity_type="Expansion",
                    timestamp=now - timedelta(days=10),
                    source="Crunchbase",
                    title="Series B funding",
                ),
            ],
        },
        {
            "company_id": uuid4(),
            "company_name": "CloudFirst Systems",
            "website": "https://cloudfirst.com",
            "industry": "Technology",
            "country": "US",
            "signal_type": "Cloud Migration",
            "signal_source": "LinkedIn",
            "signal_title": "Migrating to AWS cloud",
            "signal_timestamp": now - timedelta(days=45),
            "signal_types": ["Cloud Migration", "Infrastructure Upgrade"],
            "domain": "cloudfirst.com",
            "has_https": True,
            "content_length": 12000,
            "company_age_days": 5000,
            "activity_evidence": [
                ActivityEvidence(
                    activity_type="Cloud Migration",
                    timestamp=now - timedelta(days=15),
                    source="LinkedIn",
                    title="Cloud migration announcement",
                ),
            ],
        },
        {
            "company_id": uuid4(),
            "company_name": "StaleSignals Corp",
            "website": "https://stalesignals.com",
            "industry": "Marketing",
            "country": "US",
            "signal_type": "Blog posts",
            "signal_source": "Twitter",
            "signal_title": "Marketing blog post",
            "signal_timestamp": now - timedelta(days=200),
            "signal_types": ["Blog posts"],
            "domain": "stalesignals.com",
            "has_https": True,
            "content_length": 3000,
            "company_age_days": 500,
            "activity_evidence": [
                ActivityEvidence(
                    activity_type="Blog posts",
                    timestamp=now - timedelta(days=200),
                    source="Twitter",
                    title="Blog post",
                ),
            ],
        },
        {
            "company_id": uuid4(),
            "company_name": "GrowthEdge Consulting",
            "website": "https://growthedge.com",
            "industry": "Consulting",
            "country": "CA",
            "signal_type": "Partnership",
            "signal_source": "Crunchbase",
            "signal_title": "New partnership announced",
            "signal_timestamp": now - timedelta(days=120),
            "signal_types": ["Partnership"],
            "domain": "growthedge.com",
            "has_https": True,
            "content_length": 6000,
            "company_age_days": 2500,
            "activity_evidence": [
                ActivityEvidence(
                    activity_type="Partnership",
                    timestamp=now - timedelta(days=10),
                    source="Crunchbase",
                    title="Partnership announcement",
                ),
            ],
        },
        {
            "company_id": uuid4(),
            "company_name": "InnovateTech Labs",
            "website": "https://innovatetech.io",
            "industry": "Technology",
            "country": "US",
            "signal_type": "Funding",
            "signal_source": "Crunchbase",
            "signal_title": "Series A funding",
            "signal_timestamp": now - timedelta(days=15),
            "signal_types": ["Funding"],
            "domain": "innovatetech.io",
            "has_https": True,
            "content_length": 10000,
            "company_age_days": 3000,
            "activity_evidence": [
                ActivityEvidence(
                    activity_type="Funding",
                    timestamp=now - timedelta(days=10),
                    source="Crunchbase",
                    title="Series A",
                ),
            ],
        },
    ]

    results = []

    for company in companies:
        result = orch.evaluate(
            company_id=company["company_id"],
            company_name=company["company_name"],
            website=company.get("website"),
            industry=company.get("industry"),
            country=company.get("country"),
            signal_type=company.get("signal_type", ""),
            signal_source=company.get("signal_source", ""),
            signal_title=company.get("signal_title", ""),
            signal_timestamp=company.get("signal_timestamp"),
            signal_types=company.get("signal_types"),
            domain=company.get("domain"),
            has_https=company.get("has_https"),
            content_length=company.get("content_length"),
            company_age_days=company.get("company_age_days"),
            activity_evidence=company.get("activity_evidence"),
            now=now,
        )
        results.append((company["company_name"], result))

    print("=" * 70)
    print("  DQE v2 — Discovery Quality Engine Demo")
    print("  Deterministic Quality Gate with Scoring & Grading")
    print("=" * 70)
    print()

    for name, result in results:
        grade = result.grade.value
        decision = result.decision
        score = result.report.quality_score.total_score if result.report.quality_score else "N/A"

        if decision == "ACCEPT":
            status = "  ACCEPT"
        elif decision == "HOLD":
            status = "   HOLD "
        else:
            status = " REJECT "

        print(f"  [{status}] {name}")
        print(f"           Grade: {grade}  |  Score: {score}/100  |  Decision: {decision}")
        if result.rejection_reasons:
            print(f"           Reasons: {', '.join(result.rejection_reasons[:3])}")
        if result.report.quality_score and result.report.quality_score.components:
            top = sorted(
                result.report.quality_score.components,
                key=lambda c: c.weighted_score,
                reverse=True,
            )[:3]
            print(
                f"           Top components: "
                + ", ".join(f"{c.name}={c.weighted_score:.1f}" for c in top)
            )
        print()

    accepted = sum(1 for _, r in results if r.decision == "ACCEPT")
    held = sum(1 for _, r in results if r.decision == "HOLD")
    rejected = sum(1 for _, r in results if r.decision == "REJECT")

    print("-" * 70)
    print("  Summary")
    print("-" * 70)
    print(f"  Total evaluated : {len(results)}")
    print(f"  ACCEPT          : {accepted}")
    print(f"  HOLD            : {held}")
    print(f"  REJECT          : {rejected}")
    print()

    print("  Grade Distribution:")
    grade_counts: dict[str, int] = {}
    for _, r in results:
        g = r.grade.value
        grade_counts[g] = grade_counts.get(g, 0) + 1
    for g in ["A+", "A", "B", "C", "Reject"]:
        count = grade_counts.get(g, 0)
        bar = "#" * (count * 8)
        print(f"    {g:>6}: {bar} ({count})")
    print()

    print("  Score Breakdown (per company):")
    for name, result in results:
        if result.report.quality_score:
            score = result.report.quality_score.total_score
            bar = "#" * score
            print(f"    {name:>25}: {bar} {score}/100")
    print()

    snap = orch.dashboard.snapshot(now=now)
    print("  Dashboard Snapshot:")
    print(f"    Signals collected : {snap.signals_collected}")
    print(f"    Signals accepted  : {snap.signals_accepted}")
    print(f"    Signals rejected  : {snap.signals_rejected}")
    print(f"    Acceptance rate   : {snap.acceptance_rate:.1f}%")
    print()

    print("  Audit Trail (last company):")
    last_name, last_result = results[-1]
    print(f"    Company: {last_name}")
    for entry in last_result.report.audit_trail:
        print(f"      [{entry.decision:>4}] {entry.gate}")
    print()
    print("=" * 70)
    print("  DQE v2 Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
