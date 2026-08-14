"""ICP Engine — Ideal Customer Profile matching for COMAI.

Deterministic, no GPT dependency. Every decision explainable.

Before searching even one company, Beacon must understand who should buy COMAI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.comai_intelligence.product_profile import COMAIProductCatalog


@dataclass
class ICPScore:
    """Result of ICP matching."""

    passed: bool
    score: float  # 0-100
    confidence: float  # 0-1
    reason: str
    breakdown: dict[str, float] = field(default_factory=dict)
    rejections: list[str] = field(default_factory=list)


class ICPEngine:
    """Ideal Customer Profile matching engine.

    Checks if a company matches COMAI's perfect customer profile.
    Returns a score and pass/fail for each dimension.
    """

    # --- Geography ---
    PRIMARY_GEOGRAPHY = {"India"}
    FUTURE_GEOGRAPHY = {"UAE", "Saudi Arabia", "Singapore", "Malaysia"}

    # --- Revenue (INR) ---
    REVENUE_MIN = 2_00_00_000   # ₹2 Cr
    REVENUE_MAX = 250_00_00_000  # ₹250 Cr

    # --- Employees ---
    EMPLOYEE_MIN = 10
    EMPLOYEE_MAX = 250

    # --- Traffic (monthly visitors) ---
    TRAFFIC_MIN = 10_000
    TRAFFIC_MAX = 500_000

    # --- Orders per day ---
    ORDERS_MIN = 50
    ORDERS_MAX = 1_000

    # --- Target industries ---
    TARGET_INDUSTRIES = {
        "beauty", "cosmetics", "skincare", "fashion", "apparel",
        "jewellery", "home_decor", "furniture", "baby_products",
        "pet_products", "organic_food", "luxury_d2c", "electronics_accessories",
        "health_wellness", "supplements",
    }

    # --- Target platforms ---
    PLATFORM_PRIORITY = {
        "shopify": 1.0,
        "shopify_plus": 1.0,
        "woocommerce": 0.85,
        "magento": 0.75,
        "bigcommerce": 0.6,
        "headless_shopify": 0.9,
    }

    # --- Reject list ---
    REJECT_KEYWORDS = {
        "government", "hospital", "bank", "insurance", "university",
        "agency", "consultancy", "consultant", "manufacturer", "wholesaler",
        "b2b supplier", "enterprise retailer", "marketplace",
        "amazon seller", "flipkart seller", "offline retail chain",
        "custom sap", "oracle erp", "salesforce enterprise",
    }

    REJECT_EMPLOYEE_THRESHOLD = 5_000

    def score(self, company: dict[str, Any]) -> ICPScore:
        """Score a company against COMAI's ICP.

        Args:
            company: Dict with keys like company_name, website, domain,
                     industry, platform, country, estimated_revenue,
                     estimated_employees, estimated_traffic, etc.

        Returns:
            ICPScore with pass/fail, score, confidence, and breakdown.
        """
        breakdown: dict[str, float] = {}
        rejections: list[str] = []

        # Gate 1: Negative qualification (hard reject)
        neg_score = self._score_negative(company, rejections)
        if neg_score < 0:
            return ICPScore(
                passed=False,
                score=0.0,
                confidence=1.0,
                reason=f"Rejected: {'; '.join(rejections)}",
                breakdown=breakdown,
                rejections=rejections,
            )

        # Gate 2: Geography
        geo_score = self._score_geography(company)
        breakdown["geography"] = geo_score

        # Gate 3: Industry
        ind_score = self._score_industry(company)
        breakdown["industry"] = ind_score

        # Gate 4: Platform
        plat_score = self._score_platform(company)
        breakdown["platform"] = plat_score

        # Gate 5: Revenue
        rev_score = self._score_revenue(company)
        breakdown["revenue"] = rev_score

        # Gate 6: Employees
        emp_score = self._score_employees(company)
        breakdown["employees"] = emp_score

        # Gate 7: Traffic
        traffic_score = self._score_traffic(company)
        breakdown["traffic"] = traffic_score

        # Gate 8: Orders
        orders_score = self._score_orders(company)
        breakdown["orders"] = orders_score

        # Gate 9: Business model (D2C check)
        d2c_score = self._score_d2c(company)
        breakdown["d2c_model"] = d2c_score

        # Calculate weighted total
        weights = {
            "geography": 0.10,
            "industry": 0.20,
            "platform": 0.15,
            "revenue": 0.15,
            "employees": 0.10,
            "traffic": 0.10,
            "orders": 0.10,
            "d2c_model": 0.10,
        }
        total_score = sum(breakdown[k] * weights[k] for k in weights)

        # Must pass minimum thresholds
        passed = (
            total_score >= 50.0
            and geo_score >= 50.0
            and ind_score >= 30.0
            and plat_score >= 40.0
            and rev_score >= 40.0
        )

        # Calculate confidence
        confidence = self._calculate_confidence(company, breakdown)

        reason = self._build_reason(passed, breakdown, rejections)

        return ICPScore(
            passed=passed,
            score=round(total_score, 2),
            confidence=confidence,
            reason=reason,
            breakdown=breakdown,
            rejections=rejections,
        )

    def _score_negative(self, company: dict[str, Any], rejections: list[str]) -> float:
        """Hard reject check. Returns -1 if rejected, 0 if passes."""
        name = (company.get("company_name") or "").lower()
        desc = (company.get("description") or "").lower()
        industry = (company.get("industry") or "").lower()
        text = f"{name} {desc} {industry}"

        for keyword in self.REJECT_KEYWORDS:
            if keyword in text:
                rejections.append(f"Contains reject keyword: {keyword}")
                return -1.0

        employees = company.get("estimated_employees") or 0
        if employees > self.REJECT_EMPLOYEE_THRESHOLD:
            rejections.append(f"Too many employees: {employees}")
            return -1.0

        return 0.0

    def _score_geography(self, company: dict[str, Any]) -> float:
        country = (company.get("country") or "").strip()
        if country in self.PRIMARY_GEOGRAPHY:
            return 100.0
        if country in self.FUTURE_GEOGRAPHY:
            return 60.0
        return 0.0

    def _score_industry(self, company: dict[str, Any]) -> float:
        industry = (company.get("industry") or "").lower().replace(" ", "_").replace("-", "_")
        if industry in self.TARGET_INDUSTRIES:
            multiplier = COMAIProductCatalog.get_industry_pain_multiplier(industry)
            return 100.0 * multiplier
        # Check category as fallback
        category = (company.get("category") or "").lower().replace(" ", "_").replace("-", "_")
        if category in self.TARGET_INDUSTRIES:
            multiplier = COMAIProductCatalog.get_industry_pain_multiplier(category)
            return 90.0 * multiplier
        return 10.0  # Unknown industry gets low score, not zero

    def _score_platform(self, company: dict[str, Any]) -> float:
        platform = (company.get("platform") or "").lower().replace(" ", "_")
        return self.PLATFORM_PRIORITY.get(platform, 20.0)

    def _score_revenue(self, company: dict[str, Any]) -> float:
        revenue = company.get("estimated_revenue") or 0
        if isinstance(revenue, str):
            revenue = self._parse_revenue(revenue)
        if revenue <= 0:
            return 30.0  # Unknown revenue
        if self.REVENUE_MIN <= revenue <= self.REVENUE_MAX:
            # Score based on where in range
            ratio = (revenue - self.REVENUE_MIN) / (self.REVENUE_MAX - self.REVENUE_MIN)
            return 60.0 + (ratio * 40.0)  # 60-100
        if revenue < self.REVENUE_MIN:
            return max(0.0, 30.0 * (revenue / self.REVENUE_MIN))
        # Above max — still usable but lower score
        return max(40.0, 100.0 - ((revenue - self.REVENUE_MAX) / self.REVENUE_MAX * 50.0))

    def _score_employees(self, company: dict[str, Any]) -> float:
        employees = company.get("estimated_employees") or 0
        if employees <= 0:
            return 30.0  # Unknown
        if self.EMPLOYEE_MIN <= employees <= self.EMPLOYEE_MAX:
            ratio = (employees - self.EMPLOYEE_MIN) / (self.EMPLOYEE_MAX - self.EMPLOYEE_MIN)
            return 60.0 + (ratio * 40.0)
        if employees < self.EMPLOYEE_MIN:
            return max(0.0, 40.0 * (employees / self.EMPLOYEE_MIN))
        return max(20.0, 80.0 - ((employees - self.EMPLOYEE_MAX) / self.EMPLOYEE_MAX * 60.0))

    def _score_traffic(self, company: dict[str, Any]) -> float:
        traffic = company.get("estimated_traffic") or 0
        if traffic <= 0:
            return 30.0  # Unknown
        if self.TRAFFIC_MIN <= traffic <= self.TRAFFIC_MAX:
            ratio = (traffic - self.TRAFFIC_MIN) / (self.TRAFFIC_MAX - self.TRAFFIC_MIN)
            return 60.0 + (ratio * 40.0)
        if traffic < self.TRAFFIC_MIN:
            return max(0.0, 40.0 * (traffic / self.TRAFFIC_MIN))
        return 80.0  # Above max is still good

    def _score_orders(self, company: dict[str, Any]) -> float:
        orders = company.get("estimated_orders_per_day") or 0
        if orders <= 0:
            return 30.0  # Unknown
        if self.ORDERS_MIN <= orders <= self.ORDERS_MAX:
            ratio = (orders - self.ORDERS_MIN) / (self.ORDERS_MAX - self.ORDERS_MIN)
            return 60.0 + (ratio * 40.0)
        if orders < self.ORDERS_MIN:
            return max(0.0, 40.0 * (orders / self.ORDERS_MIN))
        return 85.0

    def _score_d2c(self, company: dict[str, Any]) -> float:
        """Score D2C model indicators."""
        indicators = 0
        max_indicators = 6

        if company.get("has_own_website"):
            indicators += 1
        if company.get("has_own_products"):
            indicators += 1
        if company.get("has_ecommerce_checkout"):
            indicators += 1
        if company.get("runs_meta_ads") or company.get("runs_google_ads"):
            indicators += 1
        if company.get("has_instagram") or company.get("has_facebook"):
            indicators += 1
        if company.get("has_cod"):
            indicators += 1

        if indicators == 0:
            # Try to infer from description
            desc = (company.get("description") or "").lower()
            d2c_keywords = ["d2c", "direct to consumer", "own brand", "own website",
                           "shopify", "ecommerce", "online store"]
            for kw in d2c_keywords:
                if kw in desc:
                    indicators += 1
                    break

        return (indicators / max_indicators) * 100.0

    def _calculate_confidence(
        self, company: dict[str, Any], breakdown: dict[str, float]
    ) -> float:
        """Calculate confidence in the ICP score based on data completeness."""
        known_fields = 0
        total_fields = 8

        if company.get("country"):
            known_fields += 1
        if company.get("industry") or company.get("category"):
            known_fields += 1
        if company.get("platform"):
            known_fields += 1
        if company.get("estimated_revenue") and company["estimated_revenue"] > 0:
            known_fields += 1
        if company.get("estimated_employees") and company["estimated_employees"] > 0:
            known_fields += 1
        if company.get("estimated_traffic") and company["estimated_traffic"] > 0:
            known_fields += 1
        if company.get("estimated_orders_per_day") and company["estimated_orders_per_day"] > 0:
            known_fields += 1
        if company.get("has_own_website") or company.get("has_ecommerce_checkout"):
            known_fields += 1

        return known_fields / total_fields

    def _build_reason(
        self, passed: bool, breakdown: dict[str, float], rejections: list[str]
    ) -> str:
        if rejections:
            return f"REJECTED: {'; '.join(rejections)}"
        if passed:
            top_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
            factors = ", ".join(f"{k}={v:.0f}" for k, v in top_factors)
            return f"PASSED ICP ({factors})"
        weak = sorted(breakdown.items(), key=lambda x: x[1])[:2]
        weak_factors = ", ".join(f"{k}={v:.0f}" for k, v in weak)
        return f"FAILED ICP — weak: {weak_factors}"

    @staticmethod
    def _parse_revenue(revenue_str: str) -> int:
        """Parse revenue string like '₹8 Cr' or '8000000' to integer."""
        s = revenue_str.replace("₹", "").replace(",", "").replace(" ", "").lower()
        if "cr" in s:
            num = s.replace("cr", "")
            try:
                return int(float(num) * 1_00_00_000)
            except ValueError:
                return 0
        if "lakh" in s or "l" in s:
            num = s.replace("lakh", "").replace("l", "")
            try:
                return int(float(num) * 1_00_000)
            except ValueError:
                return 0
        if "m" in s:
            num = s.replace("m", "")
            try:
                return int(float(num) * 10_00_000)
            except ValueError:
                return 0
        try:
            return int(float(s))
        except ValueError:
            return 0
