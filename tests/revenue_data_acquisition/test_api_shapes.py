"""RDAP API / dashboard contract shapes (offline)."""

from __future__ import annotations

from revenue_data_acquisition import RevenueDataAcquisitionPipeline, RdapRebuildEngine


def test_snapshot_json_contract():
    snap = RevenueDataAcquisitionPipeline().evaluate(
        {
            "signal_id": "api-1",
            "source": "product_hunt",
            "title": "API Co",
            "official_website": "https://api.co",
            "metadata": {"official_domain": "api.co"},
        },
        recover_contacts=False,
        recover_dms=False,
    )
    data = snap.model_dump(mode="json")
    for key in (
        "signal_id",
        "source",
        "roles",
        "can_create_identity",
        "website",
        "domain",
        "emails",
        "decision_makers",
        "dossier",
        "recovery",
        "confidence",
        "scoring_version",
        "payload",
    ):
        assert key in data
    assert data["scoring_version"] == "rdap-v1"
    assert "igf_enrichment" in data["payload"]


def test_audit_dashboard_fields():
    snaps = [
        RevenueDataAcquisitionPipeline().evaluate(
            {
                "signal_id": f"d{i}",
                "source": "github_trending",
                "title": f"GitHub: org/d{i}",
                "official_website": f"https://d{i}.io",
                "metadata": {"official_domain": f"d{i}.io", "repo_homepage": f"https://d{i}.io"},
            },
            recover_contacts=False,
            recover_dms=False,
        )
        for i in range(12)
    ]
    audit = RdapRebuildEngine().audit(
        before={"verified_companies": 44, "business_emails": 15, "decision_makers": 3, "sales_ready": 0, "revenue_ready": 0},
        after={"verified_companies": 50, "business_emails": 20, "decision_makers": 8, "sales_ready": 5, "revenue_ready": 2},
        snaps=snaps,
        collector_rows=[
            {
                "connector": "github_trending",
                "candidate": True,
                "company": True,
                "website": True,
                "business_email": True,
                "decision_maker": True,
                "sales_ready": True,
                "revenue_ready": False,
                "confidence": 80,
            }
            for _ in range(12)
        ],
        top_rr=[{"name": f"D{i}", "domain": f"d{i}.io"} for i in range(5)],
    )
    data = audit.model_dump(mode="json")
    assert "funnel" in data
    assert "connectors" in data
    assert "yields" in data
    assert "top_rejections" in data
    assert "top_revenue_ready" in data
    assert data["vansh_ready_answer"] in {"YES", "NO"}
    assert data["vansh_ready_answer"] == "YES"


def test_non_identity_enrichment_still_safe():
    snap = RevenueDataAcquisitionPipeline().evaluate(
        {
            "signal_id": "safe-1",
            "source": "hacker_news",
            "title": "Show HN: tool",
            "official_website": "https://tool.dev",
            "metadata": {"official_domain": "tool.dev"},
        },
        recover_contacts=False,
        recover_dms=False,
    )
    assert not snap.can_create_identity
    # May discover website for enrichment, but identity create remains false
    assert snap.roles
