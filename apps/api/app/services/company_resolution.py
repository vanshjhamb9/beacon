from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_resolution import CreAdmissionDecisionRow, CreRebuildReportRow, CreSnapshotRow
from app.models.intelligence import Company
from app.models.raw_event import RawEvent
from company_resolution.models.types import RawSignalEnvelope
from company_resolution.pipelines.engine import CompanyResolutionPipeline
from company_resolution.rebuild.engine import CreRebuildEngine


class CompanyResolutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = CompanyResolutionPipeline()
        self.rebuild_engine = CreRebuildEngine()

    def evaluate_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        snap = self.pipeline.evaluate(payload)
        return snap.model_dump(mode="json")

    async def persist_snapshot(
        self,
        snap_data: dict[str, Any],
        *,
        raw_event_id: UUID | None = None,
        company_id: UUID | None = None,
    ) -> None:
        admitted = bool(snap_data.get("admission", {}).get("admitted"))
        self.session.add(
            CreSnapshotRow(
                id=uuid.uuid4(),
                signal_id=str(snap_data.get("signal_id") or ""),
                raw_event_id=raw_event_id,
                source=str(snap_data.get("source") or ""),
                verdict=str(snap_data.get("verdict") or "REJECTED"),
                company_name=snap_data.get("company_name"),
                company_domain=snap_data.get("company_domain"),
                identity_score=float((snap_data.get("identity") or {}).get("score") or 0),
                website_valid=bool((snap_data.get("website") or {}).get("valid")),
                admitted=admitted,
                rejection_explanation=(snap_data.get("admission") or {}).get("explanation"),
                attribution_url=(snap_data.get("attribution") or {}).get("source_url"),
                payload=snap_data,
                evidence=list(snap_data.get("evidence") or []),
                scoring_version="cre-v1",
            )
        )
        self.session.add(
            CreAdmissionDecisionRow(
                id=uuid.uuid4(),
                signal_id=str(snap_data.get("signal_id") or ""),
                raw_event_id=raw_event_id,
                source=str(snap_data.get("source") or ""),
                admitted=admitted,
                reasons=[r for r in ((snap_data.get("admission") or {}).get("reasons") or [])],
                explanation=str((snap_data.get("admission") or {}).get("explanation") or ""),
                company_id=company_id,
                payload=snap_data,
                scoring_version="cre-v1",
            )
        )
        await self.session.commit()

    async def dashboard(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count()).select_from(CreSnapshotRow).where(CreSnapshotRow.deleted_at.is_(None)))
        admitted = await self.session.scalar(
            select(func.count()).select_from(CreSnapshotRow).where(CreSnapshotRow.deleted_at.is_(None), CreSnapshotRow.admitted.is_(True))
        )
        return {
            "snapshots": int(total or 0),
            "admitted": int(admitted or 0),
            "rejected": int(total or 0) - int(admitted or 0),
            "scoring_version": "cre-v1",
        }

    async def latest_rebuild_report(self) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(CreRebuildReportRow)
            .where(CreRebuildReportRow.deleted_at.is_(None))
            .order_by(CreRebuildReportRow.created_at.desc())
            .limit(1)
        )
        if not row:
            return None
        return {
            "total_raw_signals": row.total_raw_signals,
            "resolved_companies": row.resolved_companies,
            "verified_companies": row.verified_companies,
            "sales_ready": row.sales_ready,
            "companies_created": row.companies_created,
            "companies_rejected": row.companies_rejected,
            "resolution_success_rate": row.resolution_success_rate,
            "rejection_reasons": row.rejection_reasons,
            "identity_confidence_distribution": row.identity_confidence_distribution,
            "source_precision": row.source_precision,
            "top_verified": row.top_verified,
            "rejected_examples": row.rejected_examples,
            "scoring_version": row.scoring_version,
            "generated_at": row.generated_at.isoformat() if row.generated_at else None,
        }

    async def rebuild_from_raw_events(self, *, limit: int = 1000, soft_delete_companies: bool = True) -> dict[str, Any]:
        """Phase 9 — do not trust existing identities; re-resolve from raw signals."""
        if soft_delete_companies:
            companies = list((await self.session.scalars(select(Company).where(Company.deleted_at.is_(None)))).all())
            for c in companies:
                attrs = dict(c.attributes or {})
                attrs["cre_rebuild_soft_deleted"] = True
                attrs["cre_rebuild_at"] = datetime.now(UTC).isoformat()
                c.attributes = attrs
                c.soft_delete()
            await self.session.commit()

        events = list(
            (
                await self.session.scalars(
                    select(RawEvent).order_by(RawEvent.created_at.desc()).limit(limit)
                )
            ).all()
        )
        snaps = []
        created = 0
        for event in events:
            meta = dict(event.event_metadata or {})
            envelope = RawSignalEnvelope.from_raw(
                signal_id=str(event.id),
                title=event.title or "",
                body=event.content or "",
                url=event.url,
                source=event.source,
                timestamp=event.published_at or event.created_at,
                metadata=meta,
                domains=[meta["domain"]] if meta.get("domain") else [],
                mentions=list(meta.get("company_hints") or []),
            )
            snap = self.pipeline.evaluate(envelope, hints=meta)
            snaps.append(snap)
            data = snap.model_dump(mode="json")
            company_id = None
            if snap.admission.allow_create_company and snap.company_name and snap.company_domain:
                from intelligence.entity_resolution.normalization import normalize_company_name

                company = await self.session.scalar(
                    select(Company).where(
                        Company.normalized_name == normalize_company_name(snap.company_name),
                    )
                )
                attrs = {
                    "cre_attribution": data.get("attribution"),
                    "cre_identity_score": snap.identity.score,
                    "cre_source_signal_id": str(event.id),
                    "cre_admitted": True,
                    "source": event.source,
                    "source_url": event.url,
                }
                if company and company.deleted_at is not None:
                    company.deleted_at = None
                    company.primary_domain = snap.company_domain
                    company.attributes = {**(company.attributes or {}), **attrs}
                    company_id = company.id
                    created += 1
                elif company is None:
                    company = Company(
                        id=uuid.uuid4(),
                        name=snap.company_name,
                        normalized_name=normalize_company_name(snap.company_name),
                        primary_domain=snap.company_domain,
                        last_seen_at=event.published_at or event.created_at,
                        attributes=attrs,
                    )
                    self.session.add(company)
                    company_id = company.id
                    created += 1
                else:
                    # existing active — attach attribution, do not duplicate
                    company.attributes = {**(company.attributes or {}), **attrs}
                    if not company.primary_domain:
                        company.primary_domain = snap.company_domain
                    company_id = company.id
            await self.persist_snapshot(data, raw_event_id=event.id, company_id=company_id)

        report = self.rebuild_engine.build(snaps)
        self.session.add(
            CreRebuildReportRow(
                id=uuid.uuid4(),
                total_raw_signals=report.total_raw_signals,
                resolved_companies=report.resolved_companies,
                verified_companies=report.verified_companies,
                sales_ready=report.sales_ready,
                companies_created=created,
                companies_rejected=report.companies_rejected,
                resolution_success_rate=report.resolution_success_rate,
                rejection_reasons=report.rejection_reasons,
                identity_confidence_distribution=report.identity_confidence_distribution,
                source_precision=report.source_precision,
                top_verified=report.top_verified,
                rejected_examples=report.rejected_examples,
                payload=report.model_dump(mode="json"),
                scoring_version="cre-v1",
                generated_at=datetime.now(UTC),
            )
        )
        await self.session.commit()
        out = report.model_dump(mode="json")
        out["companies_created"] = created
        return out
