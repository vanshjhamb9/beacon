"""LIX v1 package unit tests — deterministic explainability helpers."""

from __future__ import annotations

from lead_intelligence.explorer_service import assemble_company_explorer
from lead_intelligence.provider_history import merge_provider_history
from lead_intelligence.score_breakdown import explain_score
from lead_intelligence.stage_history import failure_explanation


def test_score_breakdown_attributes_existing_total() -> None:
    result = explain_score(
        total_score=99,
        facts={
            "has_signal": True,
            "has_founder": True,
            "domain": "example.com",
            "business_email": "hello@example.com",
            "has_hiring": True,
            "yc": True,
            "industry": "saas",
        },
    )
    assert result["total"] == 99
    assert result["explained_total"] == 99
    assert len(result["components"]) == 7
    assert sum(c["points"] for c in result["components"]) == 99


def test_provider_history_reserves_future_slots() -> None:
    cards = merge_provider_history(
        [{"provider": "hunter", "status": "success", "success": True, "fields_added": ["email"]}]
    )
    names = {c["provider"] for c in cards}
    assert "hunter" in names
    assert "apollo" in names
    assert "linkedin" in names
    assert "people_data_labs" in names
    hunter = next(c for c in cards if c["provider"] == "hunter")
    assert hunter["success"] is True
    assert "email" in hunter["fields_added"]


def test_failure_explanation_lists_reasons() -> None:
    failure = failure_explanation(
        facts={
            "rejected": True,
            "generic_email_only": True,
            "has_founder": False,
            "has_website": False,
            "has_hiring": False,
        }
    )
    assert failure is not None
    assert failure["status"] == "rejected"
    assert "Generic email only" in failure["reasons"]


def test_assemble_company_explorer_payload() -> None:
    payload = assemble_company_explorer(
        {
            "facts": {
                "company": "Heroic Labs",
                "domain": "heroiclabs.com",
                "confidence": 99,
                "trust": 99,
                "revenue_ready": True,
                "has_signal": True,
                "has_website": True,
                "has_email": True,
                "has_founder": True,
                "founder": "Chris",
                "business_email": "sales@heroiclabs.com",
                "current_stage": "revenue_ready",
                "source": "yc",
            },
            "events": [
                {
                    "id": "1",
                    "event_type": "signal_collected",
                    "headline": "Signal",
                    "occurred_at": "2026-07-28T08:31:00+00:00",
                    "stage": "signal",
                    "connector": "yc",
                },
                {
                    "id": "2",
                    "event_type": "revenue_ready",
                    "headline": "Revenue Ready",
                    "occurred_at": "2026-07-28T08:43:00+00:00",
                    "stage": "revenue_ready",
                },
            ],
            "providers": [
                {
                    "provider": "hunter",
                    "status": "success",
                    "success": True,
                    "fields_added": ["email"],
                    "occurred_at": "2026-07-28T08:40:00+00:00",
                }
            ],
            "evidence": [{"kind": "yc_page", "label": "YC Page"}],
            "fields": [
                {
                    "field_name": "email",
                    "field_value": "sales@heroiclabs.com",
                    "provider": "hunter",
                    "confidence": 98,
                    "occurred_at": "2026-07-28T08:40:00+00:00",
                }
            ],
            "stages": [],
            "score_components": [],
        }
    )
    assert payload["summary"]["company"] == "Heroic Labs"
    assert payload["summary"]["revenue_ready"] is True
    assert len(payload["timeline"]) == 2
    assert payload["score"]["total"] == 99
    assert payload["replay"]
    assert payload["latest_fields"]["email"]["provider"] == "hunter"
