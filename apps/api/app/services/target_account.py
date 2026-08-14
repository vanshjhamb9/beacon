from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.repositories.target_account import TargetAccountRepository
from target_account_engine import TargetAccountEngineService, TargetAccountPipeline
from target_account_engine.models.types import ICPProfile


class TargetAccountPlatformService:
    def __init__(self, repository: TargetAccountRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        self._engine: TargetAccountEngineService | None = None

    async def _service(self) -> TargetAccountEngineService:
        if self._engine is None:
            profiles = await self.repository.domain_icps()
            pipeline = TargetAccountPipeline(
                profiles=profiles,
                top_tier_threshold=self.settings.target_account_top_tier_threshold,
                hunter_threshold=self.settings.target_account_hunter_threshold,
                mid_tier_threshold=self.settings.target_account_mid_tier_threshold,
            )
            self._engine = TargetAccountEngineService(
                profiles=profiles,
                pipeline=pipeline,
                top_tier_threshold=self.settings.target_account_top_tier_threshold,
                hunter_threshold=self.settings.target_account_hunter_threshold,
            )
        return self._engine

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        await self.repository.ensure_default_icps()
        engine = await self._service()
        engine.profiles = await self.repository.domain_icps()
        engine.pipeline.profiles = engine.profiles
        processed = 0
        hunter = 0
        top = 0
        for item in await self.repository.pending_inputs(limit=limit):
            decision = engine.evaluate(item)
            row = await self.repository.store_decision(decision)
            processed += 1
            if decision.tier.value == "top":
                top += 1
            if decision.hunter_triggered:
                job = engine.start_hunter(item, revenue_score=decision.revenue_opportunity_score)
                if job is not None:
                    await self.repository.create_hunter_job(job, target_account_id=row.id)
                    hunter += 1
        return {"processed": processed, "top_tier": top, "hunter_jobs": hunter}

    async def list_targets(
        self, *, tier: str | None, icp_key: str | None, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        rows = await self.repository.list_targets(tier=tier, icp_key=icp_key, limit=limit, offset=offset)
        return [self._target_dict(row) for row in rows]

    async def get_target(self, target_id: UUID) -> dict[str, Any] | None:
        row = await self.repository.get_target(target_id)
        if row is None:
            return None
        return self._target_dict(row)

    async def list_icps(self) -> list[dict[str, Any]]:
        await self.repository.ensure_default_icps()
        rows = await self.repository.list_icps(active_only=True)
        return [self._icp_dict(row) for row in rows]

    @staticmethod
    def _pack_lead_engine_meta(body: dict[str, Any]) -> dict[str, Any]:
        """Fold Lead Engine COMPANY filters into metadata (DB-safe without migration)."""
        meta = dict(body.get("metadata") or body.get("metadata_json") or {})
        for key in (
            "headquarters_cities",
            "specialties",
            "company_types",
            "year_founded_min",
            "year_founded_max",
            "linkedin_url_required",
            "company_name_contains",
            "domains",
            "lists",
        ):
            if key in body and body[key] is not None:
                meta[key] = body[key]
        return meta

    @classmethod
    def _profile_from_body(cls, body: dict[str, Any], *, key: str | None = None) -> ICPProfile:
        meta = cls._pack_lead_engine_meta(body)
        return ICPProfile(
            key=key or body["key"],
            name=body["name"],
            service_match=body["service_match"],
            priority=int(body.get("priority") or 100),
            company_size_min=body.get("company_size_min"),
            company_size_max=body.get("company_size_max"),
            employee_count_min=body.get("employee_count_min"),
            employee_count_max=body.get("employee_count_max"),
            industries=list(body.get("industries") or []),
            revenue_bands=list(body.get("revenue_bands") or []),
            countries=list(body.get("countries") or []),
            funding_stages=list(body.get("funding_stages") or []),
            hiring_signals=list(body.get("hiring_signals") or []),
            technology_stack=list(body.get("technology_stack") or []),
            business_models=list(body.get("business_models") or []),
            growth_signals=list(body.get("growth_signals") or []),
            decision_makers=list(body.get("decision_makers") or []),
            pain_points=list(body.get("pain_points") or []),
            buying_signals=list(body.get("buying_signals") or []),
            negative_signals=list(body.get("negative_signals") or []),
            headquarters_cities=list(body.get("headquarters_cities") or meta.get("headquarters_cities") or []),
            specialties=list(body.get("specialties") or meta.get("specialties") or []),
            company_types=list(body.get("company_types") or meta.get("company_types") or []),
            year_founded_min=body.get("year_founded_min", meta.get("year_founded_min")),
            year_founded_max=body.get("year_founded_max", meta.get("year_founded_max")),
            linkedin_url_required=bool(body.get("linkedin_url_required", meta.get("linkedin_url_required", False))),
            company_name_contains=list(body.get("company_name_contains") or meta.get("company_name_contains") or []),
            domains=list(body.get("domains") or meta.get("domains") or []),
            lists=list(body.get("lists") or meta.get("lists") or []),
            metadata=meta,
        )

    async def create_icp(self, body: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_body(body)
        row = await self.repository.upsert_icp(profile)
        self._engine = None
        return self._icp_dict(row)

    async def update_icp(self, icp_id: UUID, body: dict[str, Any]) -> dict[str, Any] | None:
        existing = await self.repository.get_icp(icp_id)
        if existing is None:
            return None
        payload = self._icp_dict(existing)
        payload.update({k: v for k, v in body.items() if v is not None and k != "id"})
        payload["key"] = existing.key
        profile = self._profile_from_body(payload, key=existing.key)
        row = await self.repository.upsert_icp(profile)
        self._engine = None
        return self._icp_dict(row)

    async def delete_icp(self, icp_id: UUID) -> bool:
        ok = await self.repository.delete_icp(icp_id)
        if ok:
            self._engine = None
        return ok

    async def start_hunter(self, *, company_id: UUID) -> dict[str, Any]:
        engine = await self._service()
        item = await self.repository.build_input(company_id)
        if item is None:
            return {"started": False, "reason": "company_not_found"}
        target = await self.repository.latest_for_company(company_id)
        score = target.revenue_opportunity_score if target else 0.0
        if score <= 0:
            decision = engine.evaluate(item)
            target = await self.repository.store_decision(decision)
            score = decision.revenue_opportunity_score
        job = engine.start_hunter(item, revenue_score=max(score, self.settings.target_account_hunter_threshold + 0.1))
        if job is None:
            return {"started": False, "reason": "below_threshold", "score": score}
        row = await self.repository.create_hunter_job(job, target_account_id=target.id if target else None)
        return {
            "started": True,
            "job_id": str(row.id),
            "status": row.status,
            "tasks": row.tasks,
            "completed_tasks": row.completed_tasks,
            "result": row.result,
        }

    async def hunter_status(self, *, company_id: UUID | None = None) -> dict[str, Any]:
        row = await self.repository.latest_hunter(company_id)
        if row is None:
            return {"status": "idle", "jobs": 0}
        return {
            "status": row.status,
            "job_id": str(row.id),
            "company_id": str(row.company_id),
            "tasks": row.tasks,
            "completed_tasks": row.completed_tasks,
            "result": row.result,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }

    async def dashboard(self) -> dict[str, Any]:
        rows = await self.repository.list_targets(limit=500, offset=0)
        engine = await self._service()
        # Build lightweight decision-like summaries for analytics
        from target_account_engine.models.types import (
            AccountTier,
            EngineScore,
            TargetAccountDecision,
        )

        decisions = [
            TargetAccountDecision(
                company_id=row.company_id,
                company_name=row.company_name,
                opportunity_id=row.opportunity_id,
                matched_icp_key=row.matched_icp_key,
                matched_icp_name=row.matched_icp_name,
                service_match=row.service_match,
                fit=EngineScore(score=row.fit_score, explanation="persisted"),
                intent=EngineScore(score=row.intent_score, explanation="persisted"),
                budget=EngineScore(score=row.budget_score, band=row.budget_band, explanation="persisted"),
                urgency=EngineScore(score=row.urgency_score, explanation="persisted"),
                accessibility=EngineScore(score=row.accessibility_score, explanation="persisted"),
                competition=EngineScore(score=row.competition_score, explanation="persisted"),
                revenue_opportunity_score=row.revenue_opportunity_score,
                tier=AccountTier(row.tier),
                why_now=row.why_now,
                buying_signals=list(row.buying_signals or []),
                hunter_triggered=row.hunter_triggered,
                proceed_to_copilot=row.proceed_to_copilot,
                explanations=dict(row.explanations or {}),
            )
            for row in rows
        ]
        summary = engine.summarize(decisions)
        summary["countries"] = {}
        for row in rows:
            country = row.country or "unknown"
            summary["countries"][country] = summary["countries"].get(country, 0) + 1
        industries: dict[str, int] = {}
        for row in rows:
            industry = row.industry or "unknown"
            industries[industry] = industries.get(industry, 0) + 1
        summary["industries"] = industries
        return summary

    def _target_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "company_id": str(row.company_id),
            "opportunity_id": str(row.opportunity_id) if row.opportunity_id else None,
            "company_name": row.company_name,
            "industry": row.industry,
            "country": row.country,
            "matched_icp_key": row.matched_icp_key,
            "matched_icp_name": row.matched_icp_name,
            "service_match": row.service_match,
            "fit_score": row.fit_score,
            "intent_score": row.intent_score,
            "budget_score": row.budget_score,
            "budget_band": row.budget_band,
            "urgency_score": row.urgency_score,
            "accessibility_score": row.accessibility_score,
            "competition_score": row.competition_score,
            "revenue_opportunity_score": row.revenue_opportunity_score,
            "tier": row.tier,
            "why_now": row.why_now,
            "buying_signals": list(row.buying_signals or []),
            "negative_signals": list(row.negative_signals or []),
            "score_breakdown": list(row.score_breakdown or []),
            "evidence_chain": list(row.evidence_chain or []),
            "explanations": dict(row.explanations or {}),
            "hunter_triggered": row.hunter_triggered,
            "hunter_tasks": list(row.hunter_tasks or []),
            "proceed_to_copilot": row.proceed_to_copilot,
            "scoring_version": row.scoring_version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def _icp_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "key": row.key,
            "name": row.name,
            "service_match": row.service_match,
            "priority": row.priority,
            "company_size_min": row.company_size_min,
            "company_size_max": row.company_size_max,
            "employee_count_min": row.employee_count_min,
            "employee_count_max": row.employee_count_max,
            "industries": list(row.industries or []),
            "revenue_bands": list(row.revenue_bands or []),
            "countries": list(row.countries or []),
            "funding_stages": list(row.funding_stages or []),
            "hiring_signals": list(row.hiring_signals or []),
            "technology_stack": list(row.technology_stack or []),
            "business_models": list(row.business_models or []),
            "growth_signals": list(row.growth_signals or []),
            "decision_makers": list(row.decision_makers or []),
            "pain_points": list(row.pain_points or []),
            "buying_signals": list(row.buying_signals or []),
            "negative_signals": list(row.negative_signals or []),
            "is_active": row.is_active,
            "metadata_json": dict(row.metadata_json or {}),
            "headquarters_cities": list((row.metadata_json or {}).get("headquarters_cities") or []),
            "specialties": list((row.metadata_json or {}).get("specialties") or []),
            "company_types": list((row.metadata_json or {}).get("company_types") or []),
            "year_founded_min": (row.metadata_json or {}).get("year_founded_min"),
            "year_founded_max": (row.metadata_json or {}).get("year_founded_max"),
            "linkedin_url_required": bool((row.metadata_json or {}).get("linkedin_url_required") or False),
            "company_name_contains": list((row.metadata_json or {}).get("company_name_contains") or []),
            "domains": list((row.metadata_json or {}).get("domains") or []),
            "lists": list((row.metadata_json or {}).get("lists") or []),
        }
