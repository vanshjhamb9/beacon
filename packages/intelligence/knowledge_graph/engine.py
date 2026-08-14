from intelligence.types import (
    ClassifiedSignalResult,
    EntityResolutionResult,
    GraphEdgeDraft,
    GraphNodeDraft,
    RawSignal,
)


class KnowledgeGraphEngine:
    def build_graph(
        self,
        signal: RawSignal,
        resolution: EntityResolutionResult,
        classifications: list[ClassifiedSignalResult],
    ) -> tuple[list[GraphNodeDraft], list[GraphEdgeDraft]]:
        nodes: list[GraphNodeDraft] = []
        edges: list[GraphEdgeDraft] = []
        signal_external_id = str(signal.id or f"{signal.source}:{signal.url}")

        nodes.append(
            GraphNodeDraft(
                node_type="signal",
                external_id=signal_external_id,
                label=signal.title,
                properties={"source": signal.source, "url": signal.url},
            )
        )

        if resolution.company:
            company_id = resolution.company.normalized_value
            nodes.append(
                GraphNodeDraft(
                    node_type="company",
                    external_id=company_id,
                    label=resolution.company.value,
                    properties=resolution.company.evidence,
                )
            )
            edges.append(
                GraphEdgeDraft(
                    from_node_type="company",
                    from_external_id=company_id,
                    to_node_type="signal",
                    to_external_id=signal_external_id,
                    edge_type="has_signal",
                    confidence=resolution.company.confidence,
                )
            )

        related_entities = [
            resolution.domain,
            resolution.person,
            *resolution.technologies,
            *resolution.products,
        ]
        for entity in [item for item in related_entities if item is not None]:
            nodes.append(
                GraphNodeDraft(
                    node_type=entity.entity_type,
                    external_id=entity.normalized_value,
                    label=entity.value,
                    properties=entity.evidence,
                )
            )
            edges.append(
                GraphEdgeDraft(
                    from_node_type=entity.entity_type,
                    from_external_id=entity.normalized_value,
                    to_node_type="signal",
                    to_external_id=signal_external_id,
                    edge_type="mentioned_in",
                    confidence=entity.confidence,
                )
            )

        for classification in classifications:
            category_id = classification.category.value
            nodes.append(
                GraphNodeDraft(
                    node_type="signal_category",
                    external_id=category_id,
                    label=category_id.replace("_", " ").title(),
                    properties={"business_function": classification.business_function},
                )
            )
            edges.append(
                GraphEdgeDraft(
                    from_node_type="signal",
                    from_external_id=signal_external_id,
                    to_node_type="signal_category",
                    to_external_id=category_id,
                    edge_type="classified_as",
                    confidence=classification.confidence,
                )
            )

        return nodes, edges
