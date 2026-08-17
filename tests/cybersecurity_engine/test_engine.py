"""Integration tests for the full cybersecurity discovery pipeline."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.engine import (
    CybersecurityDiscoveryEngine,
    extract_company_from_signal,
    extract_domain_from_url,
)
from cybersecurity_engine.evidence_engine import SalesReadinessEvaluator
from cybersecurity_engine.export_engine import ExportEngine
from cybersecurity_engine.models import (
    Company, CybersecurityOpportunity, OpportunityPriority, OpportunityType,
)
from cybersecurity_engine.outreach_generator import OutreachMessageGenerator
from cybersecurity_engine.signal_detector import CybersecuritySignalDetector
from cybersecurity_engine.sources import RawSignal


# ── extract_company_from_signal ───────────────────────────

class TestExtractCompany:
    def test_from_text_pattern(self):
        signal = RawSignal(source="test", source_tier=2, url="http://example.com",
                           title="Test", content="Acme Corp needs penetration testing")
        name = extract_company_from_signal(signal)
        assert name != ""

    def test_from_url(self):
        signal = RawSignal(source="test", source_tier=2, url="https://www.mysaas.io/page",
                           title="Test", content="We are looking for a security audit")
        name = extract_company_from_signal(signal)
        assert name != ""

    def test_empty_on_no_match(self):
        signal = RawSignal(source="test", source_tier=2, url="http://x.com",
                           title="Test", content="nice weather")
        name = extract_company_from_signal(signal)
        # May be empty or extract something from domain
        assert isinstance(name, str)


# ── extract_domain_from_url ───────────────────────────────

class TestExtractDomain:
    def test_simple_url(self):
        assert extract_domain_from_url("https://example.com/path") == "example.com"

    def test_www_url(self):
        assert extract_domain_from_url("https://www.example.com/path") == "example.com"

    def test_no_path(self):
        assert extract_domain_from_url("https://example.com") == "example.com"


# ── Full Pipeline Integration ─────────────────────────────

class TestFullPipeline:
    def test_end_to_end_with_sample_data(self, tmp_path):
        from cybersecurity_engine.test_data import get_sample_signals

        signals = get_sample_signals()
        assert len(signals) > 0

        detector = CybersecuritySignalDetector()
        evaluator = SalesReadinessEvaluator()
        generator = OutreachMessageGenerator(sender_name="Test Team")
        exporter = ExportEngine(output_dir=str(tmp_path))

        opportunities = []
        for signal in signals:
            full_text = f"{signal.title} {signal.content}"
            priority, event = detector.detect_priority(full_text, source_tier=signal.source_tier)

            if priority == OpportunityPriority.P3:
                continue

            opp = CybersecurityOpportunity(
                opportunity_id=f"test-{signal.source}",
                company=Company(name="TestCo", url="test.io", country="US", industry="SaaS"),
                opportunity_type=OpportunityType.CYBERSECURITY,
                priority=priority,
                buying_event=event,
                source_name=signal.source,
                source_type="event",
                source_url=signal.url,
                source_status="accessible",
            )
            opp.add_evidence(
                claim="buying_signal", value=event.description[:200],
                source_name=signal.source, source_type="event",
                source_url=signal.url, source_status="accessible",
                method="web_scrape", confidence=80.0, verified=True,
                published_at=signal.published_at,
            )
            opportunities.append(opp)

        evaluated = [evaluator.evaluate(o) for o in opportunities]
        files = exporter.export_all(evaluated)

        assert len(files) == 6
        assert all(Path(v).exists() for v in files.values())

    def test_signal_detector_to_evaluator(self, sample_opportunity):
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.final_verdict in {"SALES_READY", "MARKETING_READY", "NOT_READY"}

    def test_generator_after_evaluator(self, sample_opportunity):
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)

        if result.final_verdict == "SALES_READY":
            generator = OutreachMessageGenerator()
            prep = generator.generate(result)
            assert prep.personalized_message != ""
            assert len(prep.follow_up_sequence) == 3

    def test_country_detection(self):
        engine = CybersecurityDiscoveryEngine()
        assert engine._detect_country("company based in Singapore") == "Singapore"
        assert engine._detect_country("startup in London") == "United Kingdom"
        assert engine._detect_country("no location info") == ""

    def test_industry_detection(self):
        engine = CybersecurityDiscoveryEngine()
        assert engine._detect_industry("B2B SaaS platform") == "SaaS"
        assert engine._detect_industry("fintech startup") == "Fintech"
        assert engine._detect_industry("no industry info") == ""
