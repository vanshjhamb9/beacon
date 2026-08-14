from __future__ import annotations

from datetime import datetime
from typing import Any

from runtime_ops.models.types import HealthTone, PipelineStageStatus


STAGE_SPECS: tuple[tuple[str, str], ...] = (
    ("collection", "collectors.collect_source"),
    ("enrichment", "enrichment.process_opportunities"),
    ("verification", "verification.process_enrichments"),
    ("decision_discovery", "decision.process_companies"),
    ("account_intelligence", "account.refresh_profiles"),
    ("revenue_hunter", "revenue_hunter.process_accounts"),
    ("sales_intelligence", "sales_intelligence.refresh_from_replies"),
    ("campaign", "campaigns.process_pending"),
    ("communication", "communication.process_queue"),
    ("founder_queue", "founder_os.refresh_brief"),
    ("revenue_optimization", "optimization.collect_metrics"),
)


class PipelineStageAuditor:
    """Compose pipeline stage health from counts (no engine redesign)."""

    def audit(self, counts: dict[str, Any], *, last_runs: dict[str, datetime | None] | None = None) -> list[PipelineStageStatus]:
        last_runs = last_runs or {}
        stages: list[PipelineStageStatus] = []

        mapping = {
            "collection": ("companies", "raw_events"),
            "enrichment": ("opportunities", "enrichment_reports"),
            "verification": ("enrichment_reports", "verification_reports"),
            "decision_discovery": ("verification_reports", "decision_reports"),
            "account_intelligence": ("companies", "aip_profiles"),
            "revenue_hunter": ("target_accounts", "hunter_dossiers"),
            "sales_intelligence": ("hunter_dossiers", "sales_intelligence_snapshots"),
            "campaign": ("sales_intelligence_snapshots", "campaigns"),
            "communication": ("campaigns", "communication_messages"),
            "founder_queue": ("communication_messages", "founder_tasks"),
            "revenue_optimization": ("campaigns", "roip_metrics"),
        }

        worker_by_stage = {name: task for name, task in STAGE_SPECS}

        for stage, (inp_key, out_key) in mapping.items():
            entering = int(counts.get(inp_key, 0) or 0)
            leaving = int(counts.get(out_key, 0) or 0)
            dropped = max(0, entering - leaving)
            success = 0.0 if entering <= 0 else round(min(100.0, (leaving / entering) * 100.0), 2)
            status = HealthTone.PASS
            if entering > 0 and success < 10:
                status = HealthTone.FAIL
            elif entering > 0 and success < 50:
                status = HealthTone.WARNING
            elif entering == 0 and leaving == 0:
                status = HealthTone.UNKNOWN

            stages.append(
                PipelineStageStatus(
                    stage=stage,
                    input_count=entering,
                    output_count=leaving,
                    dropped_count=dropped,
                    success_percent=success,
                    average_time_ms=None,
                    last_run_at=last_runs.get(stage),
                    worker_task=worker_by_stage.get(stage),
                    failures=int(counts.get(f"{stage}_failures", 0) or 0),
                    retry_count=int(counts.get(f"{stage}_retries", 0) or 0),
                    status=status,
                    evidence=[f"input:{entering}", f"output:{leaving}", f"success_pct:{success}"],
                )
            )
        return stages
