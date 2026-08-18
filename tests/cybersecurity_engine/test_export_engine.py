"""Tests for cybersecurity_engine.export_engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.export_engine import ExportEngine
from cybersecurity_engine.models import (
    Company, CybersecurityOpportunity, OpportunityPriority, OpportunityType,
)


@pytest.fixture
def tmp_export(tmp_path):
    return ExportEngine(output_dir=str(tmp_path))


@pytest.fixture
def sales_ready_opp(sample_opportunity):
    sample_opportunity.final_verdict = "SALES_READY"
    return sample_opportunity


@pytest.fixture
def not_ready_opp():
    opp = CybersecurityOpportunity(
        opportunity_id="opp-rejected",
        company=Company(name="RejectedCo", url="x.io", country="US", industry="SaaS"),
        opportunity_type=OpportunityType.CYBERSECURITY,
        priority=OpportunityPriority.P3,
    )
    opp.final_verdict = "NOT_READY"
    return opp


class TestExportEngine:
    def test_export_all_creates_files(self, tmp_export, sales_ready_opp, not_ready_opp):
        files = tmp_export.export_all([sales_ready_opp, not_ready_opp])
        assert "cybersecurity_sales_ready.json" in files
        assert "cybersecurity_sales_ready.xlsx" in files
        assert "cybersecurity_outreach_queue.json" in files
        assert "cybersecurity_report.txt" in files
        assert "cybersecurity_rejected.json" in files
        assert "cybersecurity_evidence_audit.json" in files

    def test_sales_ready_json_content(self, tmp_export, sales_ready_opp):
        files = tmp_export.export_all([sales_ready_opp])
        content = json.loads(Path(files["cybersecurity_sales_ready.json"]).read_text())
        assert len(content) == 1
        assert content[0]["company"]["name"] == "TestCo"

    def test_rejected_json_content(self, tmp_export, not_ready_opp):
        files = tmp_export.export_all([not_ready_opp])
        content = json.loads(Path(files["cybersecurity_rejected.json"]).read_text())
        assert len(content) == 1
        assert content[0]["company"]["name"] == "RejectedCo"

    def test_report_contains_summary(self, tmp_export, sales_ready_opp):
        files = tmp_export.export_all([sales_ready_opp])
        report = Path(files["cybersecurity_report.txt"]).read_text()
        assert "SALES_READY" in report
        assert "TestCo" in report
        assert "FINAL CTO TEST" in report

    def test_evidence_audit(self, tmp_export, sales_ready_opp):
        files = tmp_export.export_all([sales_ready_opp])
        audit = json.loads(Path(files["cybersecurity_evidence_audit.json"]).read_text())
        assert len(audit) == 1
        assert audit[0]["evidence_count"] >= 3

    def test_empty_opportunities(self, tmp_export):
        files = tmp_export.export_all([])
        content = json.loads(Path(files["cybersecurity_sales_ready.json"]).read_text())
        assert content == []

    def test_outreach_queue_includes_marketing(self, tmp_export, sales_ready_opp):
        sales_ready_opp.final_verdict = "MARKETING_READY"
        files = tmp_export.export_all([sales_ready_opp])
        queue = json.loads(Path(files["cybersecurity_outreach_queue.json"]).read_text())
        assert len(queue) == 1
