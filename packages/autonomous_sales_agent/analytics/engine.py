from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentDecision, NextActionKind


class AsaAnalyticsEngine:
    """Lightweight deterministic analytics over ASA decisions."""

    def summarize(self, decisions: list[AutonomousSalesAgentDecision]) -> dict[str, object]:
        by_stage: dict[str, int] = {}
        by_action: dict[str, int] = {}
        founder_items = 0
        follow_ups_due = 0
        for d in decisions:
            by_stage[d.stage.value] = by_stage.get(d.stage.value, 0) + 1
            by_action[d.next_best_action.action.value] = by_action.get(d.next_best_action.action.value, 0) + 1
            founder_items += len(d.work_queue)
            if d.follow_up.due:
                follow_ups_due += 1
        wait_count = by_action.get(NextActionKind.WAIT.value, 0)
        return {
            "total": len(decisions),
            "by_stage": by_stage,
            "by_action": by_action,
            "founder_work_items": founder_items,
            "follow_ups_due": follow_ups_due,
            "automation_ratio": round((wait_count / len(decisions)) if decisions else 0.0, 4),
            "scoring_version": decisions[0].scoring_version if decisions else "asa-v1",
        }
