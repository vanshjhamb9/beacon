from context_engine.models.types import BusinessContextInput, EvidenceChain
from context_engine.rules.definitions import ContextRule


class EvidenceBuilder:
    def build(
        self,
        item: BusinessContextInput,
        *,
        rules: list[ContextRule],
        confidence_breakdown: dict[str, float],
        explanation: str,
    ) -> EvidenceChain:
        return EvidenceChain(
            source_events=[item.raw_event_id],
            timeline_references=[item.timeline_item_id] if item.timeline_item_id else [],
            knowledge_graph_references=item.knowledge_node_ids,
            rule_references=[rule.key for rule in rules],
            quality_references=[item.quality_report_id],
            confidence_breakdown=confidence_breakdown,
            explanation=explanation,
        )
