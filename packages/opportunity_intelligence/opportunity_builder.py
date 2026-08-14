"""Opportunity builder orchestration."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from uuid import uuid4

from opportunity_intelligence.buying_window_engine import BuyingWindowEngine
from opportunity_intelligence.confidence_engine import ConfidenceEngine
from opportunity_intelligence.constants import DEFAULT_ICP_SCORE, DEDUPLICATION_KEY_LIMIT
from opportunity_intelligence.evidence_engine import EvidenceEngine
from opportunity_intelligence.freshness_engine import FreshnessEngine
from opportunity_intelligence.models import Opportunity, OpportunityEvidence, OpportunityScoreRecord
from opportunity_intelligence.opportunity_scoring import OpportunityScoring
from opportunity_intelligence.schemas import CompanyInput, EvidenceInput, SignalInput
from opportunity_intelligence.signal_registry import SignalRegistry

logger = logging.getLogger(__name__)


class OpportunityBuilder:
    def __init__(
        self,
        *,
        evidence_engine: EvidenceEngine | None = None,
        freshness_engine: FreshnessEngine | None = None,
        buying_window_engine: BuyingWindowEngine | None = None,
        scoring: OpportunityScoring | None = None,
        confidence_engine: ConfidenceEngine | None = None,
        signal_registry: SignalRegistry | None = None,
    ) -> None:
        self.evidence_engine = evidence_engine or EvidenceEngine()
        self.freshness_engine = freshness_engine or FreshnessEngine()
        self.buying_window_engine = buying_window_engine or BuyingWindowEngine()
        self.scoring = scoring or OpportunityScoring()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.signal_registry = signal_registry or SignalRegistry()

    def build(
        self,
        *,
        signal: SignalInput,
        company: CompanyInput,
        evidence: list[EvidenceInput],
        now: datetime | None = None,
    ) -> Opportunity:
        signal_category = self.signal_registry.get(signal.category).name
        signal_config = self.signal_registry.get(signal_category)
        unique_evidence = self.evidence_engine.validate(
            evidence,
            minimum=signal_config.minimum_evidence,
        )
        freshness = self.freshness_engine.calculate(signal.timestamp, now=now)
        buying_window = self.buying_window_engine.calculate(freshness.age_days)
        evidence_score = self.evidence_engine.score(unique_evidence)
        trust = self.evidence_engine.trust(unique_evidence)
        confidence = self.confidence_engine.calculate(unique_evidence)
        score = self.scoring.calculate(
            signal_category=signal_category,
            freshness_score=freshness.score,
            evidence_score=evidence_score,
            icp_score=company.icp_score if company.icp_score is not None else DEFAULT_ICP_SCORE,
            buying_window=buying_window,
        )

        opportunity_id = uuid4()
        evidence_records = tuple(
            OpportunityEvidence(
                opportunity_id=opportunity_id,
                provider=item.provider.strip(),
                source_type=item.source_type.strip(),
                url=str(item.url) if item.url else None,
                title=item.title.strip(),
                description=item.description.strip(),
                captured_at=item.captured_at,
                trust=item.trust,
                confidence=item.confidence,
            )
            for item in unique_evidence
        )
        breakdown = score.breakdown
        score_record = OpportunityScoreRecord(
            opportunity_id=opportunity_id,
            intent=breakdown["intent"],
            budget=breakdown["budget"],
            growth=breakdown["growth"],
            timing=breakdown["timing"],
            pain=breakdown["pain"],
            freshness=breakdown["freshness"],
            evidence=breakdown["evidence"],
            icp=breakdown["icp"],
            final_score=score.score,
        )
        current = now or datetime.now(UTC)
        opportunity = Opportunity(
            id=opportunity_id,
            company_id=company.id,
            company_name=company.name.strip(),
            website=company.website,
            industry=company.industry,
            country=company.country,
            signal_type=signal.type.strip(),
            signal_source=signal.source.strip(),
            signal_category=signal_category,
            signal_title=signal.title.strip(),
            signal_summary=signal.summary.strip(),
            signal_url=str(signal.url) if signal.url else None,
            signal_timestamp=signal.timestamp,
            signal_age_days=freshness.age_days,
            buying_window=buying_window,
            intent_score=breakdown["intent"],
            pain_score=breakdown["pain"],
            budget_score=breakdown["budget"],
            growth_score=breakdown["growth"],
            timing_score=breakdown["timing"],
            freshness_score=breakdown["freshness"],
            evidence_score=breakdown["evidence"],
            icp_score=breakdown["icp"],
            opportunity_score=score.score,
            confidence=confidence,
            trust=trust,
            created_at=current,
            updated_at=current,
            evidence=evidence_records,
            score_record=score_record,
            reasons=tuple(score.reasons),
            dedupe_key=self.dedupe_key(company=company, signal=signal, evidence=unique_evidence),
        )
        logger.info(
            "Opportunity created",
            extra={
                "opportunity_id": str(opportunity.id),
                "company": opportunity.company_name,
                "signal": opportunity.signal_category,
                "buying_window": opportunity.buying_window,
                "evidence_count": len(opportunity.evidence),
                "score": opportunity.opportunity_score,
                "confidence": opportunity.confidence,
            },
        )
        return opportunity

    def dedupe_key(
        self,
        *,
        company: CompanyInput,
        signal: SignalInput,
        evidence: tuple[EvidenceInput, ...],
    ) -> str:
        evidence_urls = ",".join(sorted(str(item.url or item.title).lower() for item in evidence))
        raw = "|".join(
            [
                str(company.id),
                self.signal_registry.get(signal.category).name.value,
                signal.title.strip().lower(),
                signal.source.strip().lower(),
                signal.timestamp.date().isoformat(),
                evidence_urls,
            ]
        )
        if len(raw) <= DEDUPLICATION_KEY_LIMIT:
            return raw
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:DEDUPLICATION_KEY_LIMIT]
