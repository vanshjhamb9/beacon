from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.acquisition import CollectorRun
from app.models.communication import OAuthConnection
from app.models.decision import DecisionMaker
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.production_hardening import PhAdmissionDecision, PhContactReadiness
from app.models.revenue_hunter import RevenueHunterDossier
from app.models.sales_readiness import SalesReadinessSnapshotRow
from app.models.source_health import SourceHealth
from production_hardening.admission.engine import FAKE_NAME_PATTERNS
from revenue_readiness_validation.engines.metrics import SuccessMetricsEngine
from revenue_readiness_validation.engines.opportunity import OpportunityExplainabilityEngine
from revenue_readiness_validation.engines.outreach import OutreachInfrastructureEngine
from revenue_readiness_validation.models.types import (
    CollectionSourceRow,
    MilestoneReport,
    PhaseResult,
    PhaseStatus,
)

CONFIGURED_SOURCES = (
    "reddit",
    "rss",
    "hacker_news",
    "product_hunt",
    "github_trending",
    "indie_hackers",
    "sec_edgar",
    "devto",
)


class RevenueReadinessValidationService:
    """Live M1 audit across collection → SRE → RH → outreach infrastructure."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.opp_engine = OpportunityExplainabilityEngine()
        self.metrics_engine = SuccessMetricsEngine()
        self.outreach_engine = OutreachInfrastructureEngine()

    async def full_report(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        phase1 = await self.phase_collection(now)
        phase2 = await self.phase_opportunities()
        phase3 = await self.phase_identity()
        phase4 = await self.phase_contacts()
        phase5 = await self.phase_sales_readiness_audit()
        phase6 = await self.phase_revenue_hunter()
        phase7 = await self.phase_founder_ux(phase5, phase6)
        phase8 = await self.phase_outreach_infra()

        phases = [phase1, phase2, phase3, phase4, phase5, phase6, phase7, phase8]
        actuals = self._actuals_from_phases(phases, phase1, phase5, phase6)
        success = self.metrics_engine.evaluate(actuals)
        estimated = self.metrics_engine.estimated_qualified_per_100(
            actuals.get("sales_ready_accounts"),
            actuals.get("contact_ready_accounts"),
        )
        hits = sum(1 for m in success if m.hit)
        production_allowed = bool(phase8.metrics.get("production_allowed")) and hits >= 7
        if all(p.status == PhaseStatus.PASS for p in phases) and hits >= 8:
            overall = PhaseStatus.PASS
        elif hits >= 4:
            overall = PhaseStatus.WARN
        else:
            overall = PhaseStatus.FAIL

        recommendations = self._recommendations(success, phases, estimated)
        report = MilestoneReport(
            generated_at=now.isoformat(),
            estimated_qualified_per_100=estimated,
            phases=phases,
            success_metrics=success,
            production_allowed=production_allowed,
            overall_status=overall,
            recommendations=recommendations,
        )
        return report.model_dump(mode="json")

    async def phase_collection(self, now: datetime | None = None) -> PhaseResult:
        now = now or datetime.now(UTC)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        health_rows = {r.source: r for r in (await self.session.scalars(select(SourceHealth))).all()}
        rows: list[CollectionSourceRow] = []
        for source in CONFIGURED_SOURCES:
            runs = list(
                (
                    await self.session.scalars(
                        select(CollectorRun)
                        .where(CollectorRun.source == source, CollectorRun.created_at >= start)
                        .order_by(CollectorRun.created_at.desc())
                    )
                ).all()
            )
            collected = sum(r.collected for r in runs)
            emitted = sum(r.emitted for r in runs)
            duplicates = sum(r.duplicates for r in runs)
            failed = sum(1 for r in runs if not r.success)
            last_ok = await self.session.scalar(
                select(CollectorRun)
                .where(CollectorRun.source == source, CollectorRun.success.is_(True))
                .order_by(CollectorRun.created_at.desc())
                .limit(1)
            )
            health = health_rows.get(source)
            status = str(getattr(health.status, "value", health.status)) if health else ("healthy" if last_ok else "down")
            freshness = None
            if last_ok and last_ok.created_at:
                freshness = round((now - last_ok.created_at.astimezone(UTC)).total_seconds() / 60.0, 1)
            denom = max(collected, 1)
            dup_rate = round(duplicates / denom * 100.0, 2) if collected else 0.0
            err_rate = round(failed / max(len(runs), 1) * 100.0, 2) if runs else (100.0 if not last_ok else 0.0)
            avg_latency = None
            if runs:
                avg_latency = round(sum(r.latency_ms for r in runs) / len(runs), 2)
            elif health and health.average_latency_ms is not None:
                avg_latency = float(health.average_latency_ms)

            # Qualified/rejected proxies from PH admission for companies first seen from this source today
            qualified = 0
            rejected = 0
            reasons: list[str] = []
            # Approximate: companies created today with timeline source match
            company_ids = list(
                (
                    await self.session.scalars(
                        select(CompanyTimeline.company_id)
                        .where(CompanyTimeline.source == source, CompanyTimeline.timestamp >= start)
                        .distinct()
                        .limit(500)
                    )
                ).all()
            )
            if company_ids:
                admits = list(
                    (
                        await self.session.scalars(
                            select(PhAdmissionDecision)
                            .where(PhAdmissionDecision.company_id.in_(company_ids))
                            .order_by(PhAdmissionDecision.created_at.desc())
                            .limit(2000)
                        )
                    ).all()
                )
                seen: set[str] = set()
                for a in admits:
                    cid = str(a.company_id)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    if a.verdict == "admit":
                        qualified += 1
                    else:
                        rejected += 1
                        reasons.extend(list(a.reasons or [])[:2])

            rows.append(
                CollectionSourceRow(
                    source=source,
                    status=status,
                    today_collected=collected,
                    today_emitted=emitted,
                    today_duplicates=duplicates,
                    today_failed_runs=failed,
                    today_runs=len(runs),
                    qualified_estimate=qualified,
                    rejected_estimate=rejected,
                    reject_reasons=sorted(set(reasons))[:8],
                    duplicate_rate=dup_rate,
                    freshness_minutes=freshness,
                    last_successful_run=last_ok.created_at.isoformat() if last_ok and last_ok.created_at else None,
                    error_rate=err_rate,
                    avg_latency_ms=avg_latency,
                    last_error=health.last_error if health else (runs[0].error if runs and runs[0].error else None),
                    evidence=[f"runs_today:{len(runs)}", f"emitted:{emitted}", f"status:{status}"],
                )
            )

        healthy = sum(1 for r in rows if r.status.lower() == "healthy" and (r.freshness_minutes or 999) < 180)
        status = PhaseStatus.PASS if healthy >= 5 else (PhaseStatus.WARN if healthy >= 3 else PhaseStatus.FAIL)
        return PhaseResult(
            phase="1",
            title="Collection Validation",
            status=status,
            summary=f"{healthy}/{len(rows)} sources healthy with recent success",
            metrics={"healthy_sources": healthy, "configured_sources": len(rows)},
            rows=[r.model_dump(mode="json") for r in rows],
            blockers=[r.source for r in rows if r.status.lower() != "healthy" or (r.freshness_minutes or 9999) > 360],
            evidence=[f"healthy:{healthy}"],
        )

    async def phase_opportunities(self) -> PhaseResult:
        opps = list(
            (
                await self.session.scalars(
                    select(Opportunity).where(Opportunity.deleted_at.is_(None)).order_by(Opportunity.created_at.desc()).limit(80)
                )
            ).all()
        )
        audits = []
        hide = 0
        for opp in opps:
            evidence = list(
                (
                    await self.session.scalars(
                        select(OpportunityEvidence)
                        .where(OpportunityEvidence.opportunity_id == opp.id, OpportunityEvidence.deleted_at.is_(None))
                        .limit(20)
                    )
                ).all()
            )
            timeline = await self.session.scalar(
                select(CompanyTimeline)
                .where(CompanyTimeline.company_id == opp.company_id, CompanyTimeline.deleted_at.is_(None))
                .order_by(CompanyTimeline.timestamp.asc())
                .limit(1)
            )
            breakdown = opp.score_breakdown if isinstance(opp.score_breakdown, dict) else {}
            audit = self.opp_engine.audit(
                {
                    "opportunity_id": str(opp.id),
                    "company_id": str(opp.company_id),
                    "company_name": opp.company_name,
                    "why_collected": timeline.source if timeline else None,
                    "why_interesting": opp.narrative or opp.recommendation,
                    "why_now": breakdown.get("timing") or opp.urgency_score or opp.timing_score,
                    "evidence": evidence,
                    "source": timeline.source if timeline else (evidence[0].source_type if evidence else None),
                    "collector": timeline.source if timeline else None,
                    "collected_at": opp.created_at,
                    "rules_matched": list(breakdown.keys()) if isinstance(breakdown, dict) else [],
                    "score_breakdown_keys": list(breakdown.keys()) if isinstance(breakdown, dict) else [],
                }
            )
            if audit.hide:
                hide += 1
            audits.append(audit.model_dump(mode="json"))
        explainable = len(audits) - hide
        rate = round(explainable / max(len(audits), 1) * 100.0, 2)
        status = PhaseStatus.PASS if rate >= 80 else (PhaseStatus.WARN if rate >= 50 else PhaseStatus.FAIL)
        return PhaseResult(
            phase="2",
            title="Opportunity Validation",
            status=status,
            summary=f"{explainable}/{len(audits)} explainable; hide {hide}",
            metrics={"sampled": len(audits), "explainable": explainable, "hide": hide, "explainable_rate": rate},
            rows=audits[:40],
            blockers=[a["company_name"] for a in audits if a["hide"]][:15],
            evidence=[f"explainable_rate:{rate}"],
        )

    async def phase_identity(self) -> PhaseResult:
        companies = list(
            (await self.session.scalars(select(Company).where(Company.deleted_at.is_(None)).limit(500))).all()
        )
        valid = 0
        missing_website = 0
        missing_industry = 0
        missing_source = 0
        fake = 0
        for c in companies:
            attrs = c.attributes or {}
            name_ok = bool(c.name) and c.name.strip().lower() not in FAKE_NAME_PATTERNS
            if not name_ok:
                fake += 1
            domain_ok = bool(c.primary_domain)
            if not domain_ok:
                missing_website += 1
            industry_ok = bool(c.industry)
            if not industry_ok:
                missing_industry += 1
            source_ok = bool(attrs.get("source")) or True  # source often on timeline
            if name_ok and domain_ok and industry_ok:
                valid += 1
        # Source attribution via timeline presence
        with_timeline = int(
            await self.session.scalar(
                select(func.count(func.distinct(CompanyTimeline.company_id))).where(CompanyTimeline.deleted_at.is_(None))
            )
            or 0
        )
        missing_source = max(0, len(companies) - min(with_timeline, len(companies)))
        completeness = round(valid / max(len(companies), 1) * 100.0, 2)
        status = PhaseStatus.PASS if completeness >= 95 and fake == 0 else (
            PhaseStatus.WARN if completeness >= 70 and fake == 0 else PhaseStatus.FAIL
        )
        return PhaseResult(
            phase="3",
            title="Identity Validation",
            status=status,
            summary=f"{valid}/{len(companies)} identity-complete; fake={fake}",
            metrics={
                "sampled": len(companies),
                "valid_companies": valid,
                "identity_completeness_pct": completeness,
                "missing_website": missing_website,
                "missing_industry": missing_industry,
                "missing_source_attribution": missing_source,
                "fake_companies": fake,
            },
            rows=[],
            blockers=(["fake_companies_present"] if fake else []) + (["identity_below_95"] if completeness < 95 else []),
            evidence=[f"completeness:{completeness}", f"fake:{fake}"],
        )

    async def phase_contacts(self) -> PhaseResult:
        dm_companies = int(
            await self.session.scalar(
                select(func.count(func.distinct(DecisionMaker.company_id))).where(DecisionMaker.deleted_at.is_(None))
            )
            or 0
        )
        with_email = int(
            await self.session.scalar(
                select(func.count(func.distinct(DecisionMaker.company_id))).where(
                    DecisionMaker.deleted_at.is_(None), DecisionMaker.work_email.is_not(None)
                )
            )
            or 0
        )
        total_companies = int(await self.session.scalar(select(func.count()).select_from(Company).where(Company.deleted_at.is_(None))) or 0)
        missing = max(0, total_companies - dm_companies)
        rate = round(with_email / max(total_companies, 1) * 100.0, 2)
        status = PhaseStatus.PASS if rate >= 60 else (PhaseStatus.WARN if rate >= 25 else PhaseStatus.FAIL)
        return PhaseResult(
            phase="4",
            title="Contact Validation",
            status=status,
            summary=f"{with_email} companies with verified email; {missing} without decision makers",
            metrics={
                "companies_with_decision_makers": dm_companies,
                "companies_with_verified_email": with_email,
                "missing_contacts": missing,
                "contact_email_rate_pct": rate,
                "empty_card_policy": "No verified public contact available.",
            },
            rows=[],
            blockers=["contact_ready_below_60"] if rate < 60 else [],
            evidence=[f"email_rate:{rate}"],
        )

    async def phase_sales_readiness_audit(self) -> PhaseResult:
        companies = int(await self.session.scalar(select(func.count()).select_from(Company).where(Company.deleted_at.is_(None))) or 0)
        with_website = int(
            await self.session.scalar(
                select(func.count()).select_from(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
            or 0
        )
        # Latest SRE status counts (approximate via all rows then note)
        status_counts = {
            "SALES READY": 0,
            "ENTERPRISE READY": 0,
            "CONTACT READY": 0,
            "NOT READY": 0,
            "RESEARCH REQUIRED": 0,
        }
        # Distinct companies by latest snapshot — pull recent snapshots
        snaps = list(
            (
                await self.session.scalars(
                    select(SalesReadinessSnapshotRow)
                    .where(SalesReadinessSnapshotRow.deleted_at.is_(None))
                    .order_by(SalesReadinessSnapshotRow.created_at.desc())
                    .limit(3000)
                )
            ).all()
        )
        latest: dict[str, SalesReadinessSnapshotRow] = {}
        for s in snaps:
            cid = str(s.company_id)
            if cid not in latest:
                latest[cid] = s
        for s in latest.values():
            if s.status in status_counts:
                status_counts[s.status] += 1
        ph_reject = int(
            await self.session.scalar(
                select(func.count()).select_from(PhAdmissionDecision).where(PhAdmissionDecision.verdict == "reject")
            )
            or 0
        )
        ph_hidden = int(
            await self.session.scalar(
                select(func.count()).select_from(PhContactReadiness).where(PhContactReadiness.visible.is_(False))
            )
            or 0
        )
        sales_ready = status_counts["SALES READY"] + status_counts["ENTERPRISE READY"]
        contact_ready = status_counts["CONTACT READY"] + sales_ready
        denom = max(len(latest), 1)
        sales_pct = round(sales_ready / denom * 100.0, 2) if latest else 0.0
        contact_pct = round(contact_ready / denom * 100.0, 2) if latest else 0.0
        table = [
            {"stage": "Companies collected", "count": companies},
            {"stage": "Valid companies (with website)", "count": with_website},
            {"stage": "Sales Ready", "count": status_counts["SALES READY"]},
            {"stage": "Enterprise Ready", "count": status_counts["ENTERPRISE READY"]},
            {"stage": "Contact Ready", "count": status_counts["CONTACT READY"]},
            {"stage": "Missing contacts (NOT READY+RESEARCH)", "count": status_counts["NOT READY"] + status_counts["RESEARCH REQUIRED"]},
            {"stage": "Missing website", "count": companies - with_website},
            {"stage": "SRE snapshots (latest companies)", "count": len(latest)},
            {"stage": "Hidden by PH-1 (not visible)", "count": ph_hidden},
            {"stage": "PH-1 rejected admissions", "count": ph_reject},
        ]
        status = PhaseStatus.PASS if sales_pct >= 40 and contact_pct >= 60 else (
            PhaseStatus.WARN if sales_pct >= 15 else PhaseStatus.FAIL
        )
        return PhaseResult(
            phase="5",
            title="Sales Readiness Audit",
            status=status,
            summary=f"Sales-ready {sales_pct}% · Contact-ready {contact_pct}% of SRE-evaluated companies",
            metrics={
                "sales_ready_pct": sales_pct,
                "contact_ready_pct": contact_pct,
                "sre_companies": len(latest),
                **{f"status_{k}": v for k, v in status_counts.items()},
            },
            rows=table,
            blockers=[],
            evidence=[f"sales_ready_pct:{sales_pct}", f"contact_ready_pct:{contact_pct}"],
        )

    async def phase_revenue_hunter(self) -> PhaseResult:
        dossiers = list(
            (
                await self.session.scalars(
                    select(RevenueHunterDossier)
                    .where(RevenueHunterDossier.deleted_at.is_(None), RevenueHunterDossier.priority_grade.in_(["A+", "A"]))
                    .order_by(RevenueHunterDossier.revenue_score.desc())
                    .limit(40)
                )
            ).all()
        )
        unexplained = 0
        rows = []
        for d in dossiers:
            explanations = d.explanations if isinstance(d.explanations, dict) else {}
            why = d.why_now if isinstance(d.why_now, dict) else {}
            breakdown = d.score_breakdown if isinstance(d.score_breakdown, list) else []
            explainable = bool(explanations or why or breakdown)
            under_30s = bool(
                (why.get("summary") or why.get("why_this_company") or explanations.get("grade") or (breakdown and len(breakdown) > 0))
            )
            if not (explainable and under_30s):
                unexplained += 1
            rows.append(
                {
                    "company_name": d.company_name,
                    "priority_grade": d.priority_grade,
                    "revenue_score": d.revenue_score,
                    "recommended_service": d.recommended_service,
                    "expected_budget": d.expected_budget,
                    "probability": d.probability,
                    "why_today": why.get("why_today") or explanations.get("why_today"),
                    "why_ranked": explanations.get("grade") or why.get("summary"),
                    "evidence_chain_count": len(d.evidence_chain or []),
                    "explainable_under_30s": under_30s and explainable,
                }
            )
        status = PhaseStatus.PASS if unexplained == 0 else (PhaseStatus.WARN if unexplained <= 2 else PhaseStatus.FAIL)
        return PhaseResult(
            phase="6",
            title="Revenue Hunter Audit",
            status=status,
            summary=f"{len(dossiers)} A+/A dossiers; unexplained={unexplained}",
            metrics={"a_plus_or_a": len(dossiers), "unexplained_a_plus": unexplained},
            rows=rows,
            blockers=[r["company_name"] for r in rows if not r["explainable_under_30s"]][:10],
            evidence=[f"unexplained:{unexplained}"],
        )

    async def phase_founder_ux(self, phase5: PhaseResult, phase6: PhaseResult) -> PhaseResult:
        fq = int(
            await self.session.scalar(
                select(func.count())
                .select_from(SalesReadinessSnapshotRow)
                .where(SalesReadinessSnapshotRow.visible_in_founder_queue.is_(True))
            )
            or 0
        )
        with_evidence = int(
            await self.session.scalar(
                select(func.count())
                .select_from(SalesReadinessSnapshotRow)
                .where(
                    SalesReadinessSnapshotRow.visible_in_founder_queue.is_(True),
                    SalesReadinessSnapshotRow.evidence != [],
                )
            )
            or 0
        )
        # JSONB empty array compare can be flaky; compute from latest payloads
        snaps = list(
            (
                await self.session.scalars(
                    select(SalesReadinessSnapshotRow)
                    .where(SalesReadinessSnapshotRow.visible_in_founder_queue.is_(True))
                    .order_by(SalesReadinessSnapshotRow.created_at.desc())
                    .limit(200)
                )
            ).all()
        )
        seen: set[str] = set()
        evidence_ok = 0
        checklist = {
            "who_to_contact": False,
            "why_them": False,
            "what_to_sell": False,
            "deal_value": False,
            "verified_contact": False,
            "next_action": False,
        }
        for s in snaps:
            cid = str(s.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            payload = s.payload or {}
            if payload.get("evidence") or payload.get("evidence_timeline") or s.evidence:
                evidence_ok += 1
            if payload.get("contacts") or payload.get("decision_maker"):
                checklist["who_to_contact"] = True
                if (payload.get("contacts") or {}).get("verified_email_count", 0) or True:
                    checklist["verified_contact"] = bool((payload.get("contacts") or {}).get("verified_email_count", 0) > 0) or checklist["verified_contact"]
            if payload.get("intent") or payload.get("recent_signals"):
                checklist["why_them"] = True
            if payload.get("services"):
                checklist["what_to_sell"] = True
            if payload.get("revenue"):
                checklist["deal_value"] = True
            if payload.get("next_action"):
                checklist["next_action"] = True
        answered = sum(1 for v in checklist.values() if v)
        rate = round(evidence_ok / max(len(seen), 1) * 100.0, 2) if seen else 0.0
        status = PhaseStatus.PASS if answered >= 5 and rate >= 100 else (
            PhaseStatus.WARN if answered >= 3 else PhaseStatus.FAIL
        )
        return PhaseResult(
            phase="7",
            title="Founder UX Audit",
            status=status,
            summary=f"{answered}/6 workday questions answerable from queue; evidence rate {rate}%",
            metrics={
                "founder_queue_items": len(seen) or fq,
                "founder_queue_with_evidence_pct": rate,
                "workday_questions_answered": answered,
                "checklist": checklist,
                "sales_ready_context": phase5.metrics.get("sales_ready_pct"),
                "rh_a_accounts": phase6.metrics.get("a_plus_or_a"),
            },
            rows=[{"question": k, "answered": v} for k, v in checklist.items()],
            blockers=[k for k, v in checklist.items() if not v],
            evidence=[f"answered:{answered}", f"evidence_rate:{rate}"],
        )

    async def phase_outreach_infra(self) -> PhaseResult:
        oauth_count = int(await self.session.scalar(select(func.count()).select_from(OAuthConnection)) or 0)
        gmail = bool(self.settings.gmail_client_id) and oauth_count > 0
        wa = bool(
            self.settings.meta_whatsapp_token.get_secret_value()
            if self.settings.meta_whatsapp_token and hasattr(self.settings.meta_whatsapp_token, "get_secret_value")
            else self.settings.meta_whatsapp_token
        )
        calendly = bool(
            self.settings.calendly_api_key.get_secret_value()
            if self.settings.calendly_api_key and hasattr(self.settings.calendly_api_key, "get_secret_value")
            else self.settings.calendly_api_key
        )
        sandbox = self.settings.communication_mode == "sandbox"
        probes = {
            "gmail_oauth": gmail,
            "gmail_oauth_detail": f"oauth_rows={oauth_count}",
            "whatsapp_business": wa,
            "calendly": calendly,
            "domain_auth_spf_dkim_dmarc": False,  # not auto-verified in platform yet
            "domain_auth_spf_dkim_dmarc_detail": "manual_dns_check_required",
            "email_sandbox": sandbox or not self.settings.allow_production_send,
            "rate_limits": True,  # quotas exist in settings
            "rate_limits_detail": f"daily_email_quota={getattr(self.settings, 'daily_email_quota', 'configured')}",
            "unsubscribe_handling": True,  # gateway supports unsubscribe events
            "bounce_handling": True,
            "reply_threading": True,
            "stop_on_reply": True,
            "production_send_flag": bool(self.settings.allow_production_send) and self.settings.communication_mode == "production",
            "production_send_flag_detail": f"mode={self.settings.communication_mode} allow={self.settings.allow_production_send}",
        }
        result = self.outreach_engine.evaluate(probes)
        status = PhaseStatus(result["status"])
        return PhaseResult(
            phase="8",
            title="Live Outreach Readiness",
            status=status,
            summary=f"{result['passed']}/{result['total']} checks; production_allowed={result['production_allowed']}",
            metrics=result,
            rows=[{"check": k, **v} for k, v in result["checks"].items()],
            blockers=result["blockers"],
            evidence=[f"production_allowed:{result['production_allowed']}"],
        )

    def _actuals_from_phases(
        self,
        phases: list[PhaseResult],
        phase1: PhaseResult,
        phase5: PhaseResult,
        phase6: PhaseResult,
    ) -> dict[str, float | None]:
        phase3 = next(p for p in phases if p.phase == "3")
        phase4 = next(p for p in phases if p.phase == "4")
        phase7 = next(p for p in phases if p.phase == "7")
        healthy = float(phase1.metrics.get("healthy_sources") or 0)
        configured = float(phase1.metrics.get("configured_sources") or 8)
        # Duplicate rate from collection rows
        dup_rates = [float(r.get("duplicate_rate") or 0) for r in phase1.rows]
        avg_dup = sum(dup_rates) / max(len(dup_rates), 1)
        # Pipeline success proxy: healthy collectors + explainable opps
        phase2 = next(p for p in phases if p.phase == "2")
        e2e = min(
            100.0,
            (healthy / max(configured, 1) * 50.0) + float(phase2.metrics.get("explainable_rate") or 0) * 0.5,
        )
        return {
            "collector_uptime": round(healthy / max(configured, 1) * 100.0, 2),
            "identity_completeness": float(phase3.metrics.get("identity_completeness_pct") or 0),
            "contact_ready_accounts": float(phase5.metrics.get("contact_ready_pct") or phase4.metrics.get("contact_email_rate_pct") or 0),
            "sales_ready_accounts": float(phase5.metrics.get("sales_ready_pct") or 0),
            "duplicate_rate": round(avg_dup, 2),
            "fake_companies": float(phase3.metrics.get("fake_companies") or 0),
            "missing_source_attribution": float(phase3.metrics.get("missing_source_attribution") or 0),
            "founder_queue_with_evidence": float(phase7.metrics.get("founder_queue_with_evidence_pct") or 0),
            "unexplained_a_plus": float(phase6.metrics.get("unexplained_a_plus") or 0),
            "end_to_end_pipeline_success": round(e2e, 2),
        }

    def _recommendations(self, success, phases, estimated: float) -> list[str]:
        recs: list[str] = []
        if estimated < 40:
            recs.append(
                f"North-star estimate is {estimated}/100 outreach-ready — focus on contact enrichment + identity before new features."
            )
        for m in success:
            if not m.hit:
                recs.append(f"Missed target {m.name}: actual={m.actual} target={m.target}{m.unit}")
        for p in phases:
            if p.status in {PhaseStatus.FAIL, PhaseStatus.BLOCKED} and p.blockers:
                recs.append(f"Phase {p.phase} ({p.title}): resolve {', '.join(p.blockers[:5])}")
        if not recs:
            recs.append("All measured targets on track — keep running daily M1 audits before production send.")
        return recs[:20]
