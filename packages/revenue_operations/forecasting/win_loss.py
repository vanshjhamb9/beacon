from __future__ import annotations

from revenue_operations.models.types import RevenueOperationsInput, WinLossRecord


class WinLossAnalyticsEngine:
    def analyze(self, item: RevenueOperationsInput) -> list[WinLossRecord]:
        out: list[WinLossRecord] = []
        for opp in item.opportunities:
            if not (opp.won or opp.lost):
                continue
            out.append(
                WinLossRecord(
                    outcome="won" if opp.won else "lost",
                    why=(opp.why_won if opp.won else opp.why_lost) or ("Closed won" if opp.won else "Closed lost"),
                    industry=opp.industry,
                    budget=opp.budget,
                    timeline=opp.timeline,
                    service_sold=opp.service,
                    competitor=opp.competitor,
                    decision_maker=(opp.decision_makers[0] if opp.decision_makers else None),
                    reply_speed_hours=float(opp.reply_speed_hours),
                    meeting_count=int(opp.meeting_count),
                    proposal_count=int(opp.proposal_count),
                    sales_cycle_days=int(opp.sales_cycle_days or opp.days_in_stage),
                    objections=list(opp.objections)[:8],
                    close_probability=float(opp.probability),
                    company_name=opp.company_name,
                    evidence=[f"outcome:{'won' if opp.won else 'lost'}", f"service:{opp.service or 'n/a'}"],
                )
            )
        out.sort(key=lambda r: (r.outcome != "won", r.company_name))
        return out

    def visualize(self, records: list[WinLossRecord]) -> dict[str, object]:
        won = [r for r in records if r.outcome == "won"]
        lost = [r for r in records if r.outcome == "lost"]
        return {
            "won": len(won),
            "lost": len(lost),
            "win_rate": round((len(won) / len(records)) * 100.0, 2) if records else 0.0,
            "avg_sales_cycle_won": round(sum(r.sales_cycle_days for r in won) / len(won), 2) if won else 0.0,
            "avg_sales_cycle_lost": round(sum(r.sales_cycle_days for r in lost) / len(lost), 2) if lost else 0.0,
            "top_win_services": self._top([r.service_sold for r in won]),
            "top_loss_reasons": self._top([r.why for r in lost]),
            "top_competitors": self._top([r.competitor for r in lost if r.competitor]),
        }

    def _top(self, values: list[str | None]) -> list[str]:
        counts: dict[str, int] = {}
        for v in values:
            if not v:
                continue
            counts[v] = counts.get(v, 0) + 1
        return [k for k, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))][:5]
