from __future__ import annotations

from sales_intelligence.intent.engine import BuyingIntentEngine
from sales_intelligence.meeting.engine import MeetingCoachEngine
from sales_intelligence.memory.engine import SalesMemoryEngine
from sales_intelligence.models.types import (
    SCORING_VERSION,
    ReplyIntelligenceResult,
    SalesIntelligenceDecision,
    SalesIntelligenceInput,
)
from sales_intelligence.objections.engine import ObjectionPredictionEngine
from sales_intelligence.offers.engine import OfferRecommendationEngine
from sales_intelligence.proposal.engine import ProposalIntelligenceEngine
from sales_intelligence.psychology.engine import PsychologyEngine
from sales_intelligence.reply.engine import ReplyIntelligenceEngine
from sales_intelligence.score.engine import SalesScoreEngine
from sales_intelligence.trust.engine import TrustBuilderEngine


class SalesIntelligencePipeline:
    """Compose Beacon signals into a full Sales Intelligence decision pack."""

    def __init__(self) -> None:
        self.intent = BuyingIntentEngine()
        self.psychology = PsychologyEngine()
        self.objections = ObjectionPredictionEngine()
        self.offers = OfferRecommendationEngine()
        self.trust = TrustBuilderEngine()
        self.proposal = ProposalIntelligenceEngine()
        self.meeting = MeetingCoachEngine()
        self.reply = ReplyIntelligenceEngine()
        self.memory = SalesMemoryEngine()
        self.score = SalesScoreEngine()

    def process(self, item: SalesIntelligenceInput) -> SalesIntelligenceDecision:
        intent = self.intent.analyze(item)
        psychology = self.psychology.analyze(item)
        objections = self.objections.predict(item)
        offer = self.offers.recommend(item)
        trust = self.trust.build(item, primary_offer=offer.primary_offer)
        proposal = self.proposal.generate(
            item,
            primary_offer=offer.primary_offer,
            expected_value=offer.expected_value,
        )
        meeting = self.meeting.coach(item, intent=intent, psychology=psychology, objections=objections)
        replies: list[ReplyIntelligenceResult] = []
        for idx, reply in enumerate(item.replies):
            classified = self.reply.classify(
                str(reply.get("body") or reply.get("snippet") or ""),
                subject=str(reply.get("subject") or ""),
            )
            replies.append(classified.model_copy(update={"reply_ref": str(reply.get("id") or idx)}))
        memory = self.memory.build(item)
        score = self.score.score(
            item,
            intent=intent,
            psychology=psychology,
            objections=objections,
            offer=offer,
        )
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"intent:{intent.buying_intent_score}",
            f"stage:{intent.buying_stage.value}",
            f"primary_offer:{offer.primary_offer.value}",
            f"deal_probability:{score.deal_probability}",
            *intent.evidence_chain[:8],
        ]
        return SalesIntelligenceDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            opportunity_id=item.opportunity_id,
            buying_intent=intent,
            psychology=psychology,
            objections=objections,
            offer=offer,
            trust=trust,
            proposal=proposal,
            meeting_coach=meeting,
            reply_intelligence=replies,
            memory=memory,
            score=score,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
        )
