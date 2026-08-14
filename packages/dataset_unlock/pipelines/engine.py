"""ODU pipeline — collect identity sources → verify website → enrich payload for IGF/RDAP.

Phase 0: only event sources (Product Hunt with real createdAt) open lead events.
YC / App Store remain available as enrichment-only collectors.
"""

from __future__ import annotations

import os
from typing import Any

from collectors.events import NormalizedEvent
from collectors.freshness import FRESH_HOURS, filter_fresh_events, parse_datetime
from dataset_unlock.app_store.collector import AppStoreDeveloperCollector
from dataset_unlock.directories.contracts import provider_status
from dataset_unlock.github.enterprise import GitHubEnterpriseDiscovery
from dataset_unlock.google_play.collector import GooglePlayDeveloperCollector
from dataset_unlock.models.types import ConnectorHealthStatus, ConnectorMetric, OduAudit
from dataset_unlock.product_hunt.client import ProductHuntGraphQLClient
from dataset_unlock.website_verify.engine import WebsiteVerificationEngine
from dataset_unlock.yc.collector import YCCompanyCollector


class DatasetUnlockPipeline:
    def __init__(self) -> None:
        self.ph = ProductHuntGraphQLClient()
        self.github = GitHubEnterpriseDiscovery()
        # Directory collectors: enrichment only (lead_eligible=False)
        self.yc = YCCompanyCollector(max_items=120, lead_eligible=False)
        self.app_store = AppStoreDeveloperCollector(max_items=40, lead_eligible=False)
        self.play = GooglePlayDeveloperCollector(max_items=20, lead_eligible=False)
        self.verify = WebsiteVerificationEngine()

    def collect_identity_events(self) -> list[NormalizedEvent]:
        """Lead-path events only — last 48h event sources. Directories excluded."""
        events: list[NormalizedEvent] = []
        if self.ph.has_token:
            for post in self.ph.fetch_posts(first=50):
                norm = self.ph.normalize_post(post)
                if not norm:
                    continue
                created = parse_datetime(
                    norm.get("published_at") or (norm.get("metadata") or {}).get("launch_date")
                )
                if created is None:
                    continue
                events.append(
                    NormalizedEvent(
                        source="product_hunt",
                        url=norm["url"],
                        title=norm["title"],
                        content=norm["content"],
                        published_at=created,
                        metadata={
                            **norm["metadata"],
                            "source_kind": "event",
                            "lead_eligible": True,
                            "content_occurred_at": created.isoformat(),
                        },
                    )
                )
        return filter_fresh_events(events, max_age_hours=FRESH_HOURS)

    def collect_enrichment_profiles(self) -> list[NormalizedEvent]:
        """Directory rows for website/founder enrichment — never outbound leads."""
        events: list[NormalizedEvent] = []
        events.extend(self.yc.collect())
        events.extend(self.app_store.collect())
        return events

    def enrich_github_payload(self, payload: dict[str, Any], *, fetch_live: bool = True) -> dict[str, Any]:
        disc = self.github.discover(payload, fetch_live=fetch_live)
        meta = dict(payload.get("metadata") or {})
        if disc.get("website"):
            meta["official_website"] = disc["website"]
            meta["homepage"] = disc["website"]
            meta["official_domain"] = disc.get("domain")
            meta["domain"] = disc.get("domain")
            meta["github_enterprise"] = disc
        return {
            **payload,
            "metadata": meta,
            "official_website": disc.get("website") or payload.get("official_website"),
        }

    def verify_website(self, website: str, *, company_name: str | None = None) -> dict[str, Any]:
        return self.verify.verify(website, company_name=company_name)

    def connector_health(self) -> list[dict[str, Any]]:
        ph_status = (
            ConnectorHealthStatus.HEALTHY
            if self.ph.has_token
            else ConnectorHealthStatus.MISSING_TOKEN
        )
        if not self.ph.has_token:
            ph_note = "PRODUCT_HUNT_DEVELOPER_TOKEN missing — Cloudflare blocks HTML"
        else:
            ph_note = f"GraphQL ready · lead path ≤{FRESH_HOURS}h"
        gh_token = bool(os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"))
        return [
            {
                "connector": "product_hunt",
                "health": ph_status.value,
                "note": ph_note,
                "requires": ["PRODUCT_HUNT_DEVELOPER_TOKEN"],
            },
            {
                "connector": "github_trending",
                "health": (
                    ConnectorHealthStatus.HEALTHY if gh_token else ConnectorHealthStatus.RATE_LIMITED
                ).value,
                "note": "GITHUB_TOKEN optional; unauthenticated rate limited",
                "requires": ["GITHUB_TOKEN"],
            },
            {
                "connector": "yc",
                "health": ConnectorHealthStatus.HEALTHY.value,
                "note": "YC directory — enrichment only (not lead source)",
                "requires": [],
            },
            {
                "connector": "app_store",
                "health": ConnectorHealthStatus.HEALTHY.value,
                "note": "iTunes Search — enrichment only (not lead source)",
                "requires": [],
            },
            {
                "connector": "google_play",
                "health": ConnectorHealthStatus.HEALTHY.value,
                "note": "Play Store — enrichment only (deferred)",
                "requires": [],
            },
            *[
                {
                    "connector": p["name"],
                    "health": ConnectorHealthStatus.DISABLED.value
                    if not p["enabled"]
                    else ConnectorHealthStatus.HEALTHY.value,
                    "note": p["status"],
                    "requires": [p["requires"]] if p["requires"] else [],
                }
                for p in provider_status()
            ],
        ]

    def build_audit(
        self,
        *,
        before: dict[str, Any],
        after: dict[str, Any],
        connector_rows: list[dict[str, Any]],
        top_companies: list[dict[str, Any]],
        failures: dict[str, int],
        websites_recovered: int,
        emails_recovered: int,
        dms_recovered: int,
    ) -> OduAudit:
        metrics: list[ConnectorMetric] = []
        for row in connector_rows:
            signals = int(row.get("signals") or 0) or 1
            rr = int(row.get("revenue_ready") or 0)
            metrics.append(
                ConnectorMetric(
                    connector=str(row.get("connector")),
                    signals=int(row.get("signals") or 0),
                    websites=int(row.get("websites") or 0),
                    companies=int(row.get("companies") or 0),
                    emails=int(row.get("emails") or 0),
                    decision_makers=int(row.get("decision_makers") or 0),
                    sales_ready=int(row.get("sales_ready") or 0),
                    revenue_ready=rr,
                    yield_pct=round(rr / signals * 100.0, 2),
                    duplicates=int(row.get("duplicates") or 0),
                    health=(
                        ConnectorHealthStatus(row["health"])
                        if row.get("health") in {s.value for s in ConnectorHealthStatus}
                        else ConnectorHealthStatus.HEALTHY
                    ),
                    note=str(row.get("note") or ""),
                )
            )
        metrics = sorted(metrics, key=lambda m: (m.revenue_ready, m.companies, m.emails), reverse=True)
        highest = metrics[0].connector if metrics else "unknown"
        disable = [
            m.connector
            for m in metrics
            if m.health in {ConnectorHealthStatus.DISABLED, ConnectorHealthStatus.CLOUDFLARE}
            or (m.signals > 50 and m.companies == 0)
        ]
        sales = int(after.get("sales_ready") or 0)
        rr = int(after.get("revenue_ready") or 0)
        outreach = int(after.get("outreach_ready") or 0)
        answer = (
            "YES"
            if outreach >= 10 or (sales >= 10 and int(after.get("business_emails") or 0) >= 10)
            else "NO"
        )
        return OduAudit(
            before=before,
            after=after,
            connectors=metrics,
            top_failures=failures,
            top_companies=top_companies[:20],
            websites_recovered=websites_recovered,
            emails_recovered=emails_recovered,
            dms_recovered=dms_recovered,
            sales_ready_delta=sales - int(before.get("sales_ready") or 0),
            revenue_ready_delta=rr - int(before.get("revenue_ready") or 0),
            highest_yield_connector=highest,
            disable_connectors=disable,
            vansh_ready_answer=answer,
        )
