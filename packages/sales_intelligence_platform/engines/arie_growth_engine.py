"""ARIE: Growth Intelligence Engine.

Continuously detects company growth signals: hiring, funding, expansion,
traffic growth, review growth, new products, and more.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GrowthSignal:
    """A detected growth signal for a company."""
    signal_type: str  # hiring, funding, expansion, traffic, reviews, products, etc.
    signal_category: str  # positive, neutral, negative
    signal_value: Any  # The actual value
    evidence: list = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    impact_score: float = 0.0  # 0-100 impact on growth score


@dataclass
class GrowthAnalysis:
    """Complete growth analysis for a company."""
    domain: str
    growth_score: float  # 0-100
    growth_rate: float  # Monthly %
    growth_trend: str  # accelerating, stable, decelerating, declining
    signals: list = field(default_factory=list)
    growth_factors: dict = field(default_factory=dict)
    expansion_stage: str = "unknown"  # startup, growth, scale, mature
    confidence: float = 0.0
    recommendations: list = field(default_factory=list)


class ARIEGrowthEngine:
    """Growth Intelligence Engine - detects and scores company growth."""
    
    # Growth signal weights
    SIGNAL_WEIGHTS = {
        "hiring": 15.0,
        "funding": 20.0,
        "traffic_growth": 12.0,
        "review_growth": 10.0,
        "new_products": 8.0,
        "new_collections": 6.0,
        "price_increase": 5.0,
        "international_expansion": 10.0,
        "app_launch": 8.0,
        "warehouse_expansion": 6.0,
    }
    
    # Hiring role importance
    HIRING_ROLES = {
        "marketing": {"weight": 1.2, "signals": ["growth_focus", "customer_acquisition"]},
        "engineering": {"weight": 1.0, "signals": ["tech_investment", "product_development"]},
        "sales": {"weight": 1.3, "signals": ["revenue_growth", "customer_expansion"]},
        "support": {"weight": 0.8, "signals": ["customer_growth", "scaling_support"]},
        "operations": {"weight": 0.9, "signals": ["operational_scale", "logistics_growth"]},
        "data": {"weight": 1.1, "signals": ["data_driven", "analytics_focus"]},
        "ai": {"weight": 1.5, "signals": ["ai_adoption", "automation_focus"]},
        "product": {"weight": 1.0, "signals": ["product_expansion", "innovation"]},
    }
    
    # Funding stages
    FUNDING_STAGES = {
        "pre_seed": {"amount_range": (100000, 1000000), "score": 30},
        "seed": {"amount_range": (500000, 5000000), "score": 50},
        "series_a": {"amount_range": (5000000, 30000000), "score": 70},
        "series_b": {"amount_range": (20000000, 100000000), "score": 85},
        "series_c": {"amount_range": (50000000, 300000000), "score": 95},
        "ipo": {"amount_range": (100000000, 1000000000), "score": 100},
    }
    
    def analyze_growth(self, company_data: dict[str, Any]) -> GrowthAnalysis:
        """Perform comprehensive growth analysis for a company.
        
        Args:
            company_data: Company information including signals
            
        Returns:
            GrowthAnalysis with score, signals, and recommendations
        """
        domain = company_data.get("domain", "")
        
        analysis = GrowthAnalysis(
            domain=domain,
            growth_score=0.0,
            growth_rate=0.0,
            growth_trend="unknown",
        )
        
        signals = []
        factor_scores = {}
        
        # 1. Hiring signals
        hiring_score, hiring_signals = self._analyze_hiring(company_data)
        signals.extend(hiring_signals)
        factor_scores["hiring"] = hiring_score
        
        # 2. Funding signals
        funding_score, funding_signals = self._analyze_funding(company_data)
        signals.extend(funding_signals)
        factor_scores["funding"] = funding_score
        
        # 3. Traffic growth
        traffic_score, traffic_signals = self._analyze_traffic_growth(company_data)
        signals.extend(traffic_signals)
        factor_scores["traffic_growth"] = traffic_score
        
        # 4. Review growth
        review_score, review_signals = self._analyze_review_growth(company_data)
        signals.extend(review_signals)
        factor_scores["review_growth"] = review_score
        
        # 5. Product expansion
        product_score, product_signals = self._analyze_product_expansion(company_data)
        signals.extend(product_signals)
        factor_scores["new_products"] = product_score
        
        # 6. Geographic expansion
        geo_score, geo_signals = self._analyze_geographic_expansion(company_data)
        signals.extend(geo_signals)
        factor_scores["international_expansion"] = geo_score
        
        # 7. Technology investment
        tech_score, tech_signals = self._analyze_technology_investment(company_data)
        signals.extend(tech_signals)
        factor_scores["technology_investment"] = tech_score
        
        # Calculate weighted growth score
        total_weight = 0
        weighted_sum = 0
        for factor, score in factor_scores.items():
            weight = self.SIGNAL_WEIGHTS.get(factor, 10.0)
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            analysis.growth_score = weighted_sum / total_weight
        else:
            analysis.growth_score = 50.0  # Default neutral
        
        # Determine growth rate
        traffic_growth = company_data.get("traffic_growth_rate", 0)
        review_growth = company_data.get("review_growth_rate", 0)
        analysis.growth_rate = (traffic_growth + review_growth) / 2 if (traffic_growth or review_growth) else 0
        
        # Determine trend
        analysis.growth_trend = self._determine_trend(analysis.growth_rate, signals)
        
        # Determine expansion stage
        analysis.expansion_stage = self._determine_expansion_stage(company_data, analysis)
        
        # Store signals and factors
        analysis.signals = signals
        analysis.growth_factors = factor_scores
        
        # Calculate confidence
        analysis.confidence = self._calculate_growth_confidence(company_data, signals)
        
        # Generate recommendations
        analysis.recommendations = self._generate_growth_recommendations(analysis)
        
        return analysis
    
    def _analyze_hiring(self, company: dict) -> tuple[float, list]:
        """Analyze hiring signals."""
        signals = []
        score = 0.0
        
        hiring_data = company.get("hiring_signals", [])
        if not hiring_data:
            return 50.0, signals  # Neutral if no data
        
        for hire in hiring_data:
            role = hire.get("role", "").lower()
            department = hire.get("department", "").lower()
            
            for key, config in self.HIRING_ROLES.items():
                if key in role or key in department:
                    signal = GrowthSignal(
                        signal_type="hiring",
                        signal_category="positive",
                        signal_value=f"Hiring {role}",
                        evidence=[hire.get("url", "")],
                        confidence=0.8,
                        source="job_postings",
                        impact_score=config["weight"] * 20,
                    )
                    signals.append(signal)
                    score += config["weight"] * 15
        
        return min(100.0, score), signals
    
    def _analyze_funding(self, company: dict) -> tuple[float, list]:
        """Analyze funding signals."""
        signals = []
        score = 0.0
        
        funding_data = company.get("funding_signals", [])
        if not funding_data:
            return 50.0, signals
        
        for funding in funding_data:
            stage = funding.get("stage", "").lower()
            amount = funding.get("amount", 0)
            
            stage_config = self.FUNDING_STAGES.get(stage, {})
            if stage_config:
                signal = GrowthSignal(
                    signal_type="funding",
                    signal_category="positive",
                    signal_value=f"{stage.upper()} - ${amount:,.0f}",
                    evidence=[funding.get("source", "")],
                    confidence=0.9,
                    source="funding_announcement",
                    impact_score=stage_config["score"],
                )
                signals.append(signal)
                score = stage_config["score"]
        
        return min(100.0, score), signals
    
    def _analyze_traffic_growth(self, company: dict) -> tuple[float, list]:
        """Analyze traffic growth signals."""
        signals = []
        score = 50.0
        
        traffic_growth = company.get("traffic_growth_rate", 0)
        traffic_trend = company.get("traffic_trend", "")
        
        if traffic_growth > 20:
            signal = GrowthSignal(
                signal_type="traffic_growth",
                signal_category="positive",
                signal_value=f"+{traffic_growth}% monthly",
                evidence=[],
                confidence=0.7,
                source="traffic_analysis",
                impact_score=min(100, traffic_growth * 2),
            )
            signals.append(signal)
            score = min(100, 50 + traffic_growth)
        elif traffic_growth < -10:
            signal = GrowthSignal(
                signal_type="traffic_growth",
                signal_category="negative",
                signal_value=f"{traffic_growth}% monthly",
                evidence=[],
                confidence=0.7,
                source="traffic_analysis",
                impact_score=max(0, 50 + traffic_growth),
            )
            signals.append(signal)
            score = max(0, 50 + traffic_growth)
        
        return score, signals
    
    def _analyze_review_growth(self, company: dict) -> tuple[float, list]:
        """Analyze review growth signals."""
        signals = []
        score = 50.0
        
        review_growth = company.get("review_growth_rate", 0)
        review_count = company.get("review_count", 0)
        avg_rating = company.get("avg_rating", 0)
        
        if review_growth > 10:
            signal = GrowthSignal(
                signal_type="review_growth",
                signal_category="positive",
                signal_value=f"+{review_growth}% monthly reviews",
                evidence=[],
                confidence=0.8,
                source="review_analysis",
                impact_score=min(100, review_growth * 3),
            )
            signals.append(signal)
            score = min(100, 50 + review_growth * 2)
        
        if avg_rating >= 4.5 and review_count > 100:
            score = min(100, score + 20)
        
        return score, signals
    
    def _analyze_product_expansion(self, company: dict) -> tuple[float, list]:
        """Analyze product expansion signals."""
        signals = []
        score = 50.0
        
        product_count = company.get("product_count", 0)
        collection_count = company.get("collection_count", 0)
        new_products = company.get("new_products", [])
        
        if new_products:
            signal = GrowthSignal(
                signal_type="new_products",
                signal_category="positive",
                signal_value=f"{len(new_products)} new products",
                evidence=[p.get("url", "") for p in new_products[:3]],
                confidence=0.7,
                source="product_monitoring",
                impact_score=min(100, len(new_products) * 10),
            )
            signals.append(signal)
            score = min(100, 50 + len(new_products) * 10)
        
        if product_count > 500:
            score = min(100, score + 15)
        
        return score, signals
    
    def _analyze_geographic_expansion(self, company: dict) -> tuple[float, list]:
        """Analyze geographic expansion signals."""
        signals = []
        score = 50.0
        
        countries = company.get("countries", [])
        international = company.get("international_presence", False)
        new_markets = company.get("new_markets", [])
        
        if international and len(countries) > 1:
            signal = GrowthSignal(
                signal_type="international_expansion",
                signal_category="positive",
                signal_value=f"Operating in {len(countries)} countries",
                evidence=[],
                confidence=0.8,
                source="market_analysis",
                impact_score=min(100, len(countries) * 20),
            )
            signals.append(signal)
            score = min(100, 50 + len(countries) * 15)
        
        if new_markets:
            signal = GrowthSignal(
                signal_type="new_markets",
                signal_category="positive",
                signal_value=f"Expanding to {len(new_markets)} new markets",
                evidence=[],
                confidence=0.6,
                source="expansion_news",
                impact_score=min(100, len(new_markets) * 25),
            )
            signals.append(signal)
            score = min(100, score + len(new_markets) * 20)
        
        return score, signals
    
    def _analyze_technology_investment(self, company: dict) -> tuple[float, list]:
        """Analyze technology investment signals."""
        signals = []
        score = 50.0
        
        tech_stack = company.get("technology_stack", {})
        recent_tech_changes = company.get("recent_tech_changes", [])
        
        if recent_tech_changes:
            signal = GrowthSignal(
                signal_type="technology_investment",
                signal_category="positive",
                signal_value=f"{len(recent_tech_changes)} recent tech changes",
                evidence=[],
                confidence=0.7,
                source="technology_monitoring",
                impact_score=min(100, len(recent_tech_changes) * 15),
            )
            signals.append(signal)
            score = min(100, 50 + len(recent_tech_changes) * 15)
        
        return score, signals
    
    def _determine_trend(self, growth_rate: float, signals: list) -> str:
        """Determine growth trend from rate and signals."""
        positive_signals = sum(1 for s in signals if s.signal_category == "positive")
        negative_signals = sum(1 for s in signals if s.signal_category == "negative")
        
        if growth_rate > 15 and positive_signals > negative_signals:
            return "accelerating"
        elif growth_rate > 5:
            return "stable"
        elif growth_rate > -5:
            return "decelerating"
        else:
            return "declining"
    
    def _determine_expansion_stage(self, company: dict, analysis: GrowthAnalysis) -> str:
        """Determine company expansion stage."""
        revenue = company.get("revenue_estimate", 0)
        employees = company.get("employee_estimate", 0)
        traffic = company.get("monthly_traffic", 0)
        
        if revenue > 10000000 or employees > 500 or traffic > 500000:
            return "mature"
        elif revenue > 1000000 or employees > 100 or traffic > 100000:
            return "scale"
        elif revenue > 100000 or employees > 20 or traffic > 20000:
            return "growth"
        else:
            return "startup"
    
    def _calculate_growth_confidence(self, company: dict, signals: list) -> float:
        """Calculate confidence in growth analysis."""
        data_points = [
            bool(company.get("traffic_growth_rate")),
            bool(company.get("review_growth_rate")),
            bool(company.get("hiring_signals")),
            bool(company.get("funding_signals")),
            bool(company.get("new_products")),
            len(signals) > 0,
        ]
        
        available = sum(1 for p in data_points if p)
        return (available / len(data_points)) * 100
    
    def _generate_growth_recommendations(self, analysis: GrowthAnalysis) -> list:
        """Generate recommendations based on growth analysis."""
        recommendations = []
        
        if analysis.growth_trend == "accelerating":
            recommendations.append({
                "priority": "high",
                "action": "Reach out immediately - company is in growth mode",
                "reason": "Accelerating growth indicates budget availability and scaling needs",
            })
        
        if analysis.growth_score > 70:
            recommendations.append({
                "priority": "high",
                "action": "Focus on automation and AI solutions",
                "reason": "High growth companies need efficient scaling solutions",
            })
        
        if analysis.expansion_stage == "growth":
            recommendations.append({
                "priority": "medium",
                "action": "Position COMAI as growth enabler",
                "reason": "Growth-stage companies are most receptive to efficiency tools",
            })
        
        return recommendations
