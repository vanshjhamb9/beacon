from datetime import UTC, datetime, timedelta
from uuid import uuid4

from data_verification import VerificationPipeline
from data_verification.models.types import AutomaticAction, FreshnessStatus, VerificationInput


def make_input(**overrides: object) -> VerificationInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "opportunity_id": uuid4(),
        "enrichment_report_id": uuid4(),
        "company_name": "Acme Logistics",
        "enriched_at": datetime.now(UTC) - timedelta(days=2),
        "timeline_event_count": 6,
        "enrichment_latency_ms": 12.5,
        "source_rows": [
            {
                "source": "company_website",
                "fields": ["company_profile.website", "contact.company_email"],
                "confidence": 84.0,
            }
        ],
        "lead_profile": {
            "company_name": "Acme Logistics",
            "recommended_service": "AI Automation",
            "business_pain": "manual ops workflows",
            "buyer_persona": "COO",
            "estimated_budget": "medium",
            "priority": "high",
            "best_outreach_angle": "Lead with cycle-time reduction",
            "why_now": "Scaling ops",
            "company_profile": {
                "company_name": "Acme Logistics",
                "website": "https://acme.example",
                "domain": "acme.example",
                "industry": "logistics",
                "description": "Ops automation",
                "location": "Austin, TX",
                "country": "USA",
                "founded_year": 2016,
                "employee_count_estimate": 120,
                "company_size_range": "51-200",
                "revenue_estimate": "medium",
                "attributions": [
                    {
                        "field_name": "website",
                        "value": "https://acme.example",
                        "source": "company_website",
                        "confidence": 90.0,
                    },
                    {
                        "field_name": "website",
                        "value": "https://acme.example",
                        "source": "beacon_intelligence",
                        "confidence": 80.0,
                    },
                ],
            },
            "public_contact_information": [
                {"kind": "company_email", "value": "hello@acme.example", "confidence": 90.0, "source": "company_website"},
                {"kind": "business_phone", "value": "+15125550100", "confidence": 80.0, "source": "company_website"},
                {"kind": "role_based_email", "value": "sales@acme.example", "confidence": 85.0, "source": "company_website"},
            ],
            "decision_makers": [
                {
                    "name": "Jane Founder",
                    "role": "CEO",
                    "linkedin_url": "https://www.linkedin.com/in/jane",
                    "confidence": 88.0,
                    "source": "company_website",
                }
            ],
            "technology_stack": [
                {"name": "Stripe", "category": "payment_gateways", "confidence": 80.0, "source": "public_js"},
                {"name": "AWS", "category": "hosting", "confidence": 75.0, "source": "beacon_context"},
            ],
            "social_profiles": [
                {"platform": "linkedin", "url": "https://www.linkedin.com/company/acme", "confidence": 70.0, "source": "linkedin"},
                {"platform": "website", "url": "https://acme.example", "confidence": 90.0, "source": "company_website"},
            ],
            "open_jobs": [{"title": "Software Engineer", "confidence": 70.0, "source": "company_website"}],
            "team_insights": {
                "leadership_team_size": 3,
                "engineering_team_estimate": 1,
                "recent_hires": ["Engineering expansion"],
                "open_positions": ["Software Engineer"],
                "hiring_trends": "Active hiring",
            },
            "evidence_chain": [
                {"category": "opportunity", "summary": "Qualified opportunity", "source": "beacon_opportunity", "confidence": 80.0},
                {"category": "revenue", "summary": "AI Automation", "source": "beacon_revenue", "confidence": 75.0},
            ],
            "enrichment_confidence": {"overall_enrichment_confidence": 82.0},
        },
    }
    payload.update(overrides)
    return VerificationInput(**payload)  # type: ignore[arg-type]


def test_verification_pipeline_scores_sales_ready_profile() -> None:
    result = VerificationPipeline().process(make_input())

    assert 0 <= result.overall_readiness <= 100
    assert 0 <= result.completeness.overall_completeness <= 100
    assert result.completeness.company_profile_completeness > 0
    assert result.completeness.contact_completeness > 0
    assert result.freshness_status in {
        FreshnessStatus.FRESH,
        FreshnessStatus.AGEING,
        FreshnessStatus.STALE,
        FreshnessStatus.EXPIRED,
    }
    assert result.readiness_checklist.company_profile
    assert result.readiness_checklist.public_business_email
    assert result.field_verifications
    assert any(field.is_canonical for field in result.field_verifications)
    assert result.connector_statistics
    assert result.processing_latency_ms >= 0.0


def test_verification_pipeline_flags_expired_freshness() -> None:
    result = VerificationPipeline().process(
        make_input(enriched_at=datetime.now(UTC) - timedelta(days=120))
    )
    assert result.freshness_status == FreshnessStatus.EXPIRED
    assert AutomaticAction.QUEUE_REENRICHMENT in result.automatic_actions


def test_conflict_keeps_all_values_and_marks_canonical() -> None:
    lead_profile = make_input().lead_profile
    company_profile = dict(lead_profile["company_profile"])  # type: ignore[index]
    company_profile["attributions"] = [
        {
            "field_name": "industry",
            "value": "logistics",
            "source": "company_website",
            "confidence": 90.0,
        },
        {
            "field_name": "industry",
            "value": "freight",
            "source": "crunchbase",
            "confidence": 70.0,
        },
    ]
    lead_profile = {**lead_profile, "company_profile": company_profile}
    result = VerificationPipeline().process(make_input(lead_profile=lead_profile))
    industry_fields = [field for field in result.field_verifications if field.field_name.endswith("industry")]
    assert len(industry_fields) >= 2
    assert sum(1 for field in industry_fields if field.is_canonical) == 1
    assert any(field.conflicting_sources for field in industry_fields)
