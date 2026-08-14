from __future__ import annotations

from target_account_engine.models.types import BudgetBand, EngineScore, TargetAccountInput


_COUNTRY_MULTIPLIER = {
    "united states": 1.15,
    "usa": 1.15,
    "us": 1.15,
    "united kingdom": 1.1,
    "uk": 1.1,
    "germany": 1.08,
    "singapore": 1.12,
    "uae": 1.1,
    "india": 0.85,
    "pakistan": 0.8,
}


class BudgetEngine:
    def score(self, item: TargetAccountInput) -> EngineScore:
        employees = item.employee_count or 0
        funding = item.funding_amount or 0.0
        band = self._band(employees=employees, funding=funding, revenue_band=item.revenue_band)
        base = {
            BudgetBand.SMALL: 35.0,
            BudgetBand.MEDIUM: 55.0,
            BudgetBand.LARGE: 75.0,
            BudgetBand.ENTERPRISE: 90.0,
        }[band]
        country_mult = _COUNTRY_MULTIPLIER.get((item.country or "").strip().lower(), 1.0)
        funding_boost = 12.0 if funding >= 1_000_000 else 6.0 if funding > 0 else 0.0
        revenue_boost = 8.0 if item.revenue_band in {"series_a", "series_b", "growth", "enterprise"} else 0.0
        value = min(100.0, (base + funding_boost + revenue_boost) * country_mult)
        evidence = [
            f"Budget band {band.value}",
            f"Employees {employees or 'unknown'}",
        ]
        if funding:
            evidence.append(f"Funding amount signal {funding:,.0f}")
        if item.country:
            evidence.append(f"Market {item.country} multiplier {country_mult}")
        return EngineScore(
            score=round(value, 2),
            band=band.value,
            explanation=f"Budget capacity estimated as {band.value} ({value:.1f}/100).",
            evidence=evidence,
            details={"band": band.value, "country_multiplier": country_mult},
        )

    def _band(self, *, employees: int, funding: float, revenue_band: str | None) -> BudgetBand:
        rb = (revenue_band or "").lower()
        if employees >= 2000 or funding >= 50_000_000 or rb in {"enterprise", "public"}:
            return BudgetBand.ENTERPRISE
        if employees >= 500 or funding >= 10_000_000 or rb in {"series_b", "series_c", "growth"}:
            return BudgetBand.LARGE
        if employees >= 100 or funding >= 1_000_000 or rb in {"series_a", "seed+", "medium"}:
            return BudgetBand.MEDIUM
        return BudgetBand.SMALL
