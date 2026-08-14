"""Revenue Readiness Perfection (rrp-v1) — quality-only. No new collectors."""

from revenue_readiness_perfection.pipelines.engine import RevenueReadinessPerfectionPipeline

SCORING_VERSION = "rrp-v1"

__all__ = ["SCORING_VERSION", "RevenueReadinessPerfectionPipeline"]
