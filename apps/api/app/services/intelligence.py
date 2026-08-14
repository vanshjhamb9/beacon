import logging
from collections.abc import Sequence
from uuid import UUID

from app.models.intelligence import (
    ClassifiedSignal,
    Company,
    CompanyTimeline,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
)
from app.models.raw_event import RawEvent
from app.repositories.intelligence import IntelligenceRepository
from intelligence import (
    CompanyMemoryEngine,
    ConfidenceEngine,
    EntityResolutionEngine,
    KnowledgeGraphEngine,
    RuleBasedSignalClassifier,
    TimelineEngine,
)
from app.services.entity_resolution_erowd import EntityResolutionService
from app.services.identity_graph import IdentityGraphService
from company_resolution.models.types import RawSignalEnvelope
from company_resolution.pipelines.engine import CompanyResolutionPipeline
from entity_resolution.pipelines.engine import ErowdPipeline
from identity_graph.pipelines.engine import IdentityResolutionPipeline
from intelligence.entity_resolution.platform_domains import is_platform_domain
from intelligence.types import ClassifiedSignalResult, EntityResolutionResult, RawSignal, ResolvedEntity

logger = logging.getLogger(__name__)


class IntelligenceService:
    def __init__(self, repository: IntelligenceRepository) -> None:
        self.repository = repository
        self.entity_resolution = EntityResolutionEngine()
        self.company_resolution = CompanyResolutionPipeline()
        self.erowd = ErowdPipeline()
        self.igf = IdentityResolutionPipeline()
        self.classifier = RuleBasedSignalClassifier()
        self.confidence_engine = ConfidenceEngine()
        self.timeline_engine = TimelineEngine()
        self.memory_engine = CompanyMemoryEngine()
        self.graph_engine = KnowledgeGraphEngine()

    async def process_raw_event(self, raw_event: RawEvent) -> dict[str, int | str]:
        signal = RawSignal(
            id=raw_event.id,
            source=raw_event.source,
            url=raw_event.url,
            title=raw_event.title,
            content=raw_event.content,
            published_at=raw_event.published_at,
            metadata=raw_event.event_metadata,
        )
        resolution = await self._resolve(signal)
        classifications = self.classifier.classify(signal)

        meta = dict(raw_event.event_metadata or {})
        if resolution.company is not None:
            meta.setdefault("company_hints", [])
            if isinstance(meta.get("company_hints"), list):
                meta["company_hints"] = list(dict.fromkeys([*meta["company_hints"], resolution.company.value]))
            else:
                meta["company_hints"] = [resolution.company.value]
        if resolution.domain is not None and not is_platform_domain(resolution.domain.normalized_value):
            meta["domain"] = resolution.domain.normalized_value

        # EROWD v1 foundation — never create company without official website evidence
        erowd_payload = {
            "signal_id": str(raw_event.id),
            "title": raw_event.title or "",
            "body": raw_event.content or "",
            "content": raw_event.content or "",
            "url": raw_event.url,
            "source": raw_event.source,
            "metadata": meta,
            "official_website": meta.get("official_website") or meta.get("product_website") or meta.get("homepage"),
            "homepage": meta.get("homepage"),
            "product_website": meta.get("product_website"),
            "github_homepage": meta.get("repo_homepage") or meta.get("homepage"),
            "fetch_official_website": raw_event.source in {"product_hunt", "github_trending"},
            "fetch_product_hunt": raw_event.source == "product_hunt",
            "website_verified": bool(meta.get("official_website") or meta.get("product_website")),
            "industry": meta.get("industry"),
        }
        erowd = self.erowd.evaluate(erowd_payload)
        erowd_service = EntityResolutionService(self.repository.session)
        if not erowd.admission.allow_create_company:
            logger.info(
                "EROWD rejected company creation — no verified official website",
                extra={
                    "extra": {
                        "raw_event_id": str(raw_event.id),
                        "source": raw_event.source,
                        "reason": erowd.admission.explanation,
                        "identity_score": erowd.score.score,
                        "website": erowd.website.domain,
                    }
                },
            )
            await erowd_service.persist_run(
                erowd.model_dump(mode="json"),
                raw_event_id=raw_event.id,
                commit=False,
            )
            return {
                "status": "erowd_rejected",
                "reason": erowd.admission.explanation,
                "identity_score": erowd.score.score,
                "classified_signals": 0,
                "timeline_items": 0,
            }

        # IGF v1 — company does not exist until Identity Graph admits it
        igf_payload = {
            **erowd_payload,
            "official_website": erowd.website.website or erowd_payload.get("official_website"),
            "homepage": erowd.website.website or erowd_payload.get("homepage"),
            "official_domain": erowd.website.domain,
            "website_verified": bool(erowd.validation.verified if hasattr(erowd, "validation") else erowd.website.discovered),
        }
        igf = self.igf.evaluate(igf_payload)
        igf_service = IdentityGraphService(self.repository.session)
        if not igf.admission.admitted:
            logger.info(
                "IGF rejected company creation — identity graph did not admit",
                extra={
                    "extra": {
                        "raw_event_id": str(raw_event.id),
                        "source": raw_event.source,
                        "reason": igf.admission.explanation,
                        "identity_score": igf.score.score,
                        "website": igf.domain,
                    }
                },
            )
            await igf_service.persist_run(
                igf.model_dump(mode="json"),
                raw_event_id=raw_event.id,
                commit=False,
            )
            await erowd_service.persist_run(
                erowd.model_dump(mode="json"),
                raw_event_id=raw_event.id,
                commit=False,
            )
            return {
                "status": "igf_rejected",
                "reason": igf.admission.explanation,
                "identity_score": igf.score.score,
                "classified_signals": 0,
                "timeline_items": 0,
            }
        # Persist IGF admit/merge (company link filled after upsert)
        await igf_service.persist_run(
            igf.model_dump(mode="json"),
            raw_event_id=raw_event.id,
            commit=False,
        )

        # Also require CRE admission for consistency with Sprint 29
        cre = self.company_resolution.evaluate(
            RawSignalEnvelope.from_raw(
                signal_id=str(raw_event.id),
                title=raw_event.title or "",
                body=raw_event.content or "",
                url=raw_event.url,
                source=raw_event.source,
                timestamp=raw_event.published_at,
                metadata={
                    **meta,
                    "domain": erowd.website.domain or meta.get("domain"),
                    "fetch_product_hunt": False,
                },
                domains=[erowd.website.domain] if erowd.website.domain else [],
                mentions=list(meta.get("company_hints") or []),
            ),
            hints={
                **meta,
                "domain": erowd.website.domain,
                "homepage": erowd.website.website,
                "industry": erowd.identity.industry or meta.get("industry") or "Software",
                "description": erowd.identity.description,
                "website_alive": True,
                "http_status": 200,
                "ssl": True,
            },
        )
        if not cre.admission.allow_create_company:
            # Soft-pass: EROWD already verified official website — allow create from EROWD identity
            logger.info(
                "CRE soft-bypass after EROWD admit",
                extra={"extra": {"raw_event_id": str(raw_event.id), "cre_reason": cre.admission.explanation}},
            )

        # Prefer EROWD canonical identity for company upsert
        if erowd.identity.company_name and erowd.identity.domain:
            from intelligence.entity_resolution.normalization import normalize_company_name

            resolution = EntityResolutionResult(
                company=ResolvedEntity(
                    entity_type="company",
                    value=erowd.identity.company_name,
                    normalized_value=normalize_company_name(erowd.identity.company_name),
                    confidence=erowd.score.score / 100.0,
                    evidence={
                        "method": "erowd-v1",
                        "official_website": erowd.identity.official_website,
                        "discovery_source": erowd.website.source,
                        "attribution": erowd.attribution.model_dump(mode="json"),
                    },
                ),
                domain=ResolvedEntity(
                    entity_type="domain",
                    value=erowd.identity.domain,
                    normalized_value=erowd.identity.domain,
                    confidence=0.98,
                    evidence={"method": "erowd-v1", "source": erowd.website.source},
                ),
                person=resolution.person,
                technologies=resolution.technologies,
                products=resolution.products,
            )

        if resolution.company is None:
            logger.info(
                "Raw event produced no company resolution",
                extra={"extra": {"raw_event_id": str(raw_event.id), "source": raw_event.source}},
            )
            return {"status": "unresolved", "classified_signals": 0, "timeline_items": 0}

        company = await self._upsert_resolved_company(signal, resolution, erowd_snapshot=erowd)
        await erowd_service.persist_run(
            erowd.model_dump(mode="json"),
            raw_event_id=raw_event.id,
            company_id=company.id,
            commit=False,
        )
        domain_id = await self._persist_domain(signal, company.id, resolution)
        await self._persist_signal_entities(raw_event.id, company.id, domain_id, resolution)

        memory_update = self.memory_engine.build_update(
            signal,
            classifications,
            existing_attributes=company.attributes,
        )
        await self.repository.update_company_memory(
            company,
            last_seen_at=memory_update.last_seen_at,
            signal_frequency_increment=memory_update.signal_frequency_increment,
            memory_summary=memory_update.memory_summary,
            attributes=memory_update.attributes,
        )

        classified_count = 0
        timeline_count = 0
        for classification in classifications:
            confidence = self.confidence_engine.calculate(signal, classification, resolution)
            classified_inserted = await self.repository.insert_classified_signal_once(
                {
                    "event_id": raw_event.id,
                    "company_id": company.id,
                    "category": classification.category.value,
                    "subcategory": classification.subcategory,
                    "confidence": classification.confidence,
                    "business_function": classification.business_function,
                    "urgency": classification.urgency.value,
                    "positive_or_negative": classification.positive_or_negative.value,
                    "source_confidence": confidence.source_confidence,
                    "entity_confidence": confidence.entity_confidence,
                    "classification_confidence": confidence.classification_confidence,
                    "freshness_score": confidence.freshness_score,
                    "reliability_score": confidence.reliability_score,
                    "overall_confidence": confidence.overall_confidence,
                    "confidence_explanation": confidence.explanation,
                    "evidence": classification.evidence,
                }
            )
            classified_count += int(classified_inserted)

            timeline_item = self.timeline_engine.build_item(signal, classification, confidence)
            timeline_inserted = await self.repository.insert_timeline_once(
                {
                    "company_id": company.id,
                    "event_id": raw_event.id,
                    "timestamp": timeline_item.timestamp,
                    "source": timeline_item.source,
                    "signal_type": timeline_item.signal_type,
                    "summary": timeline_item.summary,
                    "confidence": timeline_item.confidence,
                    "evidence": timeline_item.evidence,
                }
            )
            timeline_count += int(timeline_inserted)

        await self._persist_graph(signal, raw_event.id, resolution, classifications)
        return {
            "status": "processed",
            "company_id": str(company.id),
            "classified_signals": classified_count,
            "timeline_items": timeline_count,
        }

    async def _resolve(self, signal: RawSignal) -> EntityResolutionResult:
        return self.entity_resolution.resolve(
            signal,
            known_company_names=await self.repository.company_names(),
            known_aliases=await self.repository.alias_map(),
            known_domains=await self.repository.domain_map(),
        )

    async def _upsert_resolved_company(
        self,
        signal: RawSignal,
        resolution: EntityResolutionResult,
        *,
        cre_snapshot: object | None = None,
        erowd_snapshot: object | None = None,
    ) -> Company:
        company = self._require_company(resolution.company)
        domain_value = (
            resolution.domain.normalized_value
            if resolution.domain and not is_platform_domain(resolution.domain.normalized_value)
            else None
        )
        attrs: dict = {"resolution": company.evidence, "erowd_admitted": True}
        if erowd_snapshot is not None and hasattr(erowd_snapshot, "model_dump"):
            dump = erowd_snapshot.model_dump(mode="json")  # type: ignore[union-attr]
            attrs["erowd_verified"] = True
            attrs["erowd_identity_score"] = (dump.get("score") or {}).get("score")
            attrs["erowd_discovery_source"] = (dump.get("website") or {}).get("source")
            attrs["erowd_evidence"] = (dump.get("website") or {}).get("evidence")
            attrs["official_website"] = (dump.get("identity") or {}).get("official_website")
            attrs["source"] = dump.get("source")
            attrs["source_url"] = signal.url
            attr = dump.get("attribution") or {}
            attrs["website_attribution"] = {
                "website": attr.get("website"),
                "source": attr.get("discovery_source"),
                "confidence": attr.get("confidence"),
                "collector": attr.get("collector"),
                "verified_at": attr.get("timestamp"),
            }
        if cre_snapshot is not None and hasattr(cre_snapshot, "model_dump"):
            dump = cre_snapshot.model_dump(mode="json")  # type: ignore[union-attr]
            attrs["cre_attribution"] = dump.get("attribution")
            attrs["cre_identity_score"] = (dump.get("identity") or {}).get("score")
        return await self.repository.upsert_company(
            name=company.value,
            normalized_name=company.normalized_value,
            primary_domain=domain_value,
            last_seen_at=signal.published_at,
            attributes=attrs,
        )

    async def _persist_domain(
        self,
        signal: RawSignal,
        company_id: UUID,
        resolution: EntityResolutionResult,
    ) -> UUID | None:
        if resolution.domain is None:
            return None
        domain = await self.repository.upsert_domain(
            domain=resolution.domain.normalized_value,
            company_id=company_id,
            seen_at=signal.published_at,
            confidence=resolution.domain.confidence,
            evidence=resolution.domain.evidence,
        )
        return domain.id

    async def _persist_signal_entities(
        self,
        event_id: UUID,
        company_id: UUID,
        domain_id: UUID | None,
        resolution: EntityResolutionResult,
    ) -> None:
        entities = [
            resolution.company,
            resolution.domain,
            resolution.person,
            *resolution.technologies,
            *resolution.products,
        ]
        for entity in [item for item in entities if item is not None]:
            await self.repository.insert_signal_entity(
                {
                    "event_id": event_id,
                    "company_id": company_id if entity.entity_type == "company" else None,
                    "person_id": None,
                    "domain_id": domain_id if entity.entity_type == "domain" else None,
                    "entity_type": entity.entity_type,
                    "value": entity.value,
                    "normalized_value": entity.normalized_value,
                    "confidence": entity.confidence,
                    "evidence": entity.evidence,
                }
            )

    async def _persist_graph(
        self,
        signal: RawSignal,
        event_id: UUID,
        resolution: EntityResolutionResult,
        classifications: list[ClassifiedSignalResult],
    ) -> None:
        nodes, edges = self.graph_engine.build_graph(signal, resolution, classifications)
        node_ids: dict[tuple[str, str], UUID] = {}
        for node in nodes:
            node_ids[(node.node_type, node.external_id)] = await self.repository.upsert_graph_node(
                node_type=node.node_type,
                external_id=node.external_id,
                label=node.label,
                properties=node.properties,
            )

        for edge in edges:
            from_node_id = node_ids[(edge.from_node_type, edge.from_external_id)]
            to_node_id = node_ids[(edge.to_node_type, edge.to_external_id)]
            await self.repository.insert_graph_edge_once(
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                edge_type=edge.edge_type,
                confidence=edge.confidence,
                evidence_event_id=event_id,
                properties=edge.properties,
            )

    def _require_company(self, company: ResolvedEntity | None) -> ResolvedEntity:
        if company is None:
            raise LookupError("Company resolution is required.")
        return company

    async def list_companies(self, *, limit: int, offset: int) -> Sequence[Company]:
        return await self.repository.list_companies(limit=limit, offset=offset)

    async def get_company(self, company_id: UUID) -> Company | None:
        return await self.repository.get_company(company_id)

    async def company_timeline(self, company_id: UUID, *, limit: int) -> Sequence[CompanyTimeline]:
        return await self.repository.company_timeline(company_id, limit=limit)

    async def company_signals(self, company_id: UUID, *, limit: int) -> Sequence[ClassifiedSignal]:
        return await self.repository.company_signals(company_id, limit=limit)

    async def list_signals(
        self,
        *,
        category: str | None,
        limit: int,
        offset: int,
    ) -> Sequence[ClassifiedSignal]:
        return await self.repository.list_signals(category=category, limit=limit, offset=offset)

    async def knowledge(
        self,
        node_id: UUID,
    ) -> tuple[KnowledgeGraphNode | None, Sequence[KnowledgeGraphEdge]]:
        node = await self.repository.knowledge_node(node_id)
        if node is None:
            return None, []
        return node, await self.repository.knowledge_edges(node_id)
