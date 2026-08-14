"""ARIE: Intent Intelligence Engine.

Detects buying intent from public evidence. Intent signals decay with time -
recent signals matter more.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class IntentSignal:
    """A detected intent signal for a company."""
    signal_type: str  # technology_migration, hiring, website_redesign, etc.
    signal_category: str  # strong, moderate, weak
    signal_value: Any
    evidence: list = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    decay_rate: float = 0.1  # How much this signal decays per day
    impact_score: float = 0.0


@dataclass
class IntentAnalysis:
    """Complete intent analysis for a company."""
    domain: str
    intent_score: float  # 0-100
    intent_level: str  # hot, warm, cold, none
    signals: list = field(default_factory=list)
    intent_factors: dict = field(default_factory=dict)
    buying_timeframe: str = "unknown"  # immediate, 30_days, 90_days, unknown
    confidence: float = 0.0
    recommendations: list = field(default_factory=list)


class ARIEIntentEngine:
    """Intent Intelligence Engine - detects buying intent from public signals."""
    
    # Intent signal types and their base scores
    INTENT_SIGNALS = {
        # Strong intent signals (score 80-100)
        "technology_migration": {"base_score": 90, "decay_rate": 0.05, "category": "strong"},
        "platform_migration": {"base_score": 85, "decay_rate": 0.05, "category": "strong"},
        "ai_adoption": {"base_score": 88, "decay_rate": 0.06, "category": "strong"},
        "automation_initiative": {"base_score": 85, "decay_rate": 0.06, "category": "strong"},
        "vendor_evaluation": {"base_score": 80, "decay_rate": 0.08, "category": "strong"},
        
        # Moderate intent signals (score 50-79)
        "hiring_ai_roles": {"base_score": 75, "decay_rate": 0.07, "category": "moderate"},
        "hiring_marketing": {"base_score": 60, "decay_rate": 0.10, "category": "moderate"},
        "website_redesign": {"base_score": 70, "decay_rate": 0.08, "category": "moderate"},
        "marketing_change": {"base_score": 55, "decay_rate": 0.12, "category": "moderate"},
        "support_hiring": {"base_score": 65, "decay_rate": 0.09, "category": "moderate"},
        "new_campaign_launch": {"base_score": 50, "decay_rate": 0.15, "category": "moderate"},
        
        # Weak intent signals (score 20-49)
        "blog_content_ai": {"base_score": 40, "decay_rate": 0.15, "category": "weak"},
        "social_media_ai": {"base_score": 35, "decay_rate": 0.18, "category": "weak"},
        "conference_attendance": {"base_score": 45, "decay_rate": 0.12, "category": "weak"},
        "job_description_ai": {"base_score": 50, "decay_rate": 0.10, "category": "weak"},
        
        # Negative intent signals (reduce score)
        "recently_purchased_competitor": {"base_score": -30, "decay_rate": 0.02, "category": "negative"},
        "long_contract_with_competitor": {"base_score": -20, "decay_rate": 0.01, "category": "negative"},
        "no_recent_activity": {"base_score": -15, "decay_rate": 0.05, "category": "negative"},
    }
    
    def analyze_intent(self, company_data: dict[str, Any]) -> IntentAnalysis:
        """Perform comprehensive intent analysis for a company.
        
        Args:
            company_data: Company information including signals
            
        Returns:
            IntentAnalysis with score, signals, and recommendations
        """
        domain = company_data.get("domain", "")
        
        analysis = IntentAnalysis(
            domain=domain,
            intent_score=0.0,
            intent_level="none",
        )
        
        signals = []
        factor_scores = {}
        
        # 1. Technology signals
        tech_score, tech_signals = self._analyze_technology_signals(company_data)
        signals.extend(tech_signals)
        factor_scores["technology"] = tech_score
        
        # 2. Hiring signals
        hiring_score, hiring_signals = self._analyze_hiring_signals(company_data)
        signals.extend(hiring_signals)
        factor_scores["hiring"] = hiring_score
        
        # 3. Website signals
        website_score, website_signals = self._analyze_website_signals(company_data)
        signals.extend(website_signals)
        factor_scores["website"] = website_score
        
        # 4. Marketing signals
        marketing_score, marketing_signals = self._analyze_marketing_signals(company_data)
        signals.extend(marketing_signals)
        factor_scores["marketing"] = marketing_score
        
        # 5. Support signals
        support_score, support_signals = self._analyze_support_signals(company_data)
        signals.extend(support_signals)
        factor_scores["support"] = support_score
        
        # 6. Content signals
        content_score, content_signals = self._analyze_content_signals(company_data)
        signals.extend(content_signals)
        factor_scores["content"] = content_score
        
        # Apply time decay to all signals
        signals = self._apply_time_decay(signals)
        
        # Calculate weighted intent score
        weights = {
            "technology": 0.25,
            "hiring": 0.20,
            "website": 0.15,
            "marketing": 0.15,
            "support": 0.10,
            "content": 0.15,
        }
        
        total_weight = 0
        weighted_sum = 0
        for factor, score in factor_scores.items():
            weight = weights.get(factor, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            analysis.intent_score = weighted_sum / total_weight
        else:
            analysis.intent_score = 30.0  # Default low intent
        
        # Determine intent level
        if analysis.intent_score >= 75:
            analysis.intent_level = "hot"
        elif analysis.intent_score >= 50:
            analysis.intent_level = "warm"
        elif analysis.intent_score >= 25:
            analysis.intent_level = "cold"
        else:
            analysis.intent_level = "none"
        
        # Determine buying timeframe
        analysis.buying_timeframe = self._determine_timeframe(analysis.intent_score, signals)
        
        # Store signals and factors
        analysis.signals = signals
        analysis.intent_factors = factor_scores
        
        # Calculate confidence
        analysis.confidence = self._calculate_intent_confidence(company_data, signals)
        
        # Generate recommendations
        analysis.recommendations = self._generate_intent_recommendations(analysis)
        
        return analysis
    
    def _analyze_technology_signals(self, company: dict) -> tuple[float, list]:
        """Analyze technology-related intent signals."""
        signals = []
        score = 30.0  # Default low
        
        # Technology changes
        tech_changes = company.get("recent_tech_changes", [])
        for change in tech_changes:
            change_type = change.get("type", "").lower()
            
            if "migration" in change_type or "switch" in change_type:
                signal = IntentSignal(
                    signal_type="technology_migration",
                    signal_category="strong",
                    signal_value=f"Migrating from {change.get('from', 'unknown')} to {change.get('to', 'unknown')}",
                    evidence=[change.get("url", "")],
                    confidence=0.8,
                    source="technology_monitoring",
                    impact_score=90,
                    decay_rate=0.05,
                )
                signals.append(signal)
                score = max(score, 90)
            
            elif "add" in change_type or "implement" in change_type:
                signal = IntentSignal(
                    signal_type="ai_adoption",
                    signal_category="strong",
                    signal_value=f"Adding {change.get('tool', 'new technology')}",
                    evidence=[change.get("url", "")],
                    confidence=0.7,
                    source="technology_monitoring",
                    impact_score=80,
                    decay_rate=0.06,
                )
                signals.append(signal)
                score = max(score, 80)
        
        # Current tech stack gaps
        tech_stack = company.get("technology_stack", {})
        has_chatbot = tech_stack.get("chatbot", False)
        has_ai = tech_stack.get("ai", False)
        has_crm = tech_stack.get("crm", False)
        
        if not has_chatbot and not has_ai:
            signal = IntentSignal(
                signal_type="technology_gap",
                signal_category="moderate",
                signal_value="No AI/chatbot detected",
                evidence=[],
                confidence=0.6,
                source="technology_analysis",
                impact_score=60,
                decay_rate=0.10,
            )
            signals.append(signal)
            score = max(score, 60)
        
        return score, signals
    
    def _analyze_hiring_signals(self, company: dict) -> tuple[float, list]:
        """Analyze hiring-related intent signals."""
        signals = []
        score = 30.0
        
        hiring_data = company.get("hiring_signals", [])
        
        for hire in hiring_data:
            role = hire.get("role", "").lower()
            description = hire.get("description", "").lower()
            
            # AI/ML roles
            if any(kw in role for kw in ["ai", "ml", "machine learning", "data scientist"]):
                signal = IntentSignal(
                    signal_type="hiring_ai_roles",
                    signal_category="strong",
                    signal_value=f"Hiring for AI role: {role}",
                    evidence=[hire.get("url", "")],
                    confidence=0.85,
                    source="job_postings",
                    impact_score=75,
                    decay_rate=0.07,
                )
                signals.append(signal)
                score = max(score, 75)
            
            # Marketing roles
            elif any(kw in role for kw in ["marketing", "growth", "digital"]):
                signal = IntentSignal(
                    signal_type="hiring_marketing",
                    signal_category="moderate",
                    signal_value=f"Hiring for marketing role: {role}",
                    evidence=[hire.get("url", "")],
                    confidence=0.7,
                    source="job_postings",
                    impact_score=60,
                    decay_rate=0.10,
                )
                signals.append(signal)
                score = max(score, 60)
            
            # Support roles
            elif any(kw in role for kw in ["support", "customer success", "cx"]):
                signal = IntentSignal(
                    signal_type="support_hiring",
                    signal_category="moderate",
                    signal_value=f"Hiring for support role: {role}",
                    evidence=[hire.get("url", "")],
                    confidence=0.7,
                    source="job_postings",
                    impact_score=65,
                    decay_rate=0.09,
                )
                signals.append(signal)
                score = max(score, 65)
        
        return score, signals
    
    def _analyze_website_signals(self, company: dict) -> tuple[float, list]:
        """Analyze website-related intent signals."""
        signals = []
        score = 30.0
        
        website_changes = company.get("website_changes", [])
        
        for change in website_changes:
            change_type = change.get("type", "").lower()
            
            if "redesign" in change_type or "relaunch" in change_type:
                signal = IntentSignal(
                    signal_type="website_redesign",
                    signal_category="strong",
                    signal_value="Website redesign detected",
                    evidence=[change.get("url", "")],
                    confidence=0.7,
                    source="website_monitoring",
                    impact_score=70,
                    decay_rate=0.08,
                )
                signals.append(signal)
                score = max(score, 70)
            
            elif "new_feature" in change_type or "integration" in change_type:
                signal = IntentSignal(
                    signal_type="website_update",
                    signal_category="moderate",
                    signal_value="New website feature detected",
                    evidence=[change.get("url", "")],
                    confidence=0.6,
                    source="website_monitoring",
                    impact_score=50,
                    decay_rate=0.12,
                )
                signals.append(signal)
                score = max(score, 50)
        
        return score, signals
    
    def _analyze_marketing_signals(self, company: dict) -> tuple[float, list]:
        """Analyze marketing-related intent signals."""
        signals = []
        score = 30.0
        
        marketing_changes = company.get("marketing_changes", [])
        
        for change in marketing_changes:
            change_type = change.get("type", "").lower()
            
            if "campaign" in change_type or "launch" in change_type:
                signal = IntentSignal(
                    signal_type="new_campaign_launch",
                    signal_category="moderate",
                    signal_value=f"New campaign: {change.get('name', 'unknown')}",
                    evidence=[change.get("url", "")],
                    confidence=0.6,
                    source="marketing_monitoring",
                    impact_score=50,
                    decay_rate=0.15,
                )
                signals.append(signal)
                score = max(score, 50)
        
        return score, signals
    
    def _analyze_support_signals(self, company: dict) -> tuple[float, list]:
        """Analyze support-related intent signals."""
        signals = []
        score = 30.0
        
        support_data = company.get("support_signals", [])
        
        for signal_data in support_data:
            signal_type = signal_data.get("type", "").lower()
            
            if "complaint" in signal_type or "issue" in signal_type:
                signal = IntentSignal(
                    signal_type="support_issues",
                    signal_category="moderate",
                    signal_value=signal_data.get("description", "Support issue detected"),
                    evidence=[signal_data.get("url", "")],
                    confidence=0.7,
                    source="support_monitoring",
                    impact_score=55,
                    decay_rate=0.10,
                )
                signals.append(signal)
                score = max(score, 55)
        
        return score, signals
    
    def _analyze_content_signals(self, company: dict) -> tuple[float, list]:
        """Analyze content-related intent signals."""
        signals = []
        score = 30.0
        
        content = company.get("content_signals", [])
        
        for item in content:
            title = item.get("title", "").lower()
            description = item.get("description", "").lower()
            
            ai_keywords = ["ai", "artificial intelligence", "machine learning", "automation", "chatbot"]
            
            if any(kw in title or kw in description for kw in ai_keywords):
                signal = IntentSignal(
                    signal_type="blog_content_ai",
                    signal_category="weak",
                    signal_value=f"AI-related content: {item.get('title', '')}",
                    evidence=[item.get("url", "")],
                    confidence=0.5,
                    source="content_analysis",
                    impact_score=40,
                    decay_rate=0.15,
                )
                signals.append(signal)
                score = max(score, 40)
        
        return score, signals
    
    def _apply_time_decay(self, signals: list[IntentSignal]) -> list[IntentSignal]:
        """Apply time decay to signals - recent signals matter more."""
        now = datetime.utcnow()
        
        for signal in signals:
            days_old = (now - signal.detected_at).days
            decay_factor = max(0.1, 1.0 - (signal.decay_rate * days_old))
            signal.impact_score *= decay_factor
        
        return signals
    
    def _determine_timeframe(self, intent_score: float, signals: list) -> str:
        """Determine buying timeframe from intent score and signals."""
        strong_signals = sum(1 for s in signals if s.signal_category == "strong")
        
        if intent_score >= 80 and strong_signals >= 2:
            return "immediate"
        elif intent_score >= 60 and strong_signals >= 1:
            return "30_days"
        elif intent_score >= 40:
            return "90_days"
        else:
            return "unknown"
    
    def _calculate_intent_confidence(self, company: dict, signals: list) -> float:
        """Calculate confidence in intent analysis."""
        data_points = [
            bool(company.get("recent_tech_changes")),
            bool(company.get("hiring_signals")),
            bool(company.get("website_changes")),
            bool(company.get("marketing_changes")),
            bool(company.get("support_signals")),
            bool(company.get("content_signals")),
            len(signals) > 0,
        ]
        
        available = sum(1 for p in data_points if p)
        return (available / len(data_points)) * 100
    
    def _generate_intent_recommendations(self, analysis: IntentAnalysis) -> list:
        """Generate recommendations based on intent analysis."""
        recommendations = []
        
        if analysis.intent_level == "hot":
            recommendations.append({
                "priority": "critical",
                "action": "Immediate outreach - high buying intent detected",
                "reason": f"Intent score {analysis.intent_score:.0f} with {analysis.buying_timeframe} timeframe",
            })
        elif analysis.intent_level == "warm":
            recommendations.append({
                "priority": "high",
                "action": "Schedule outreach within 1 week",
                "reason": f"Intent score {analysis.intent_score:.0f} indicates active evaluation",
            })
        elif analysis.intent_level == "cold":
            recommendations.append({
                "priority": "medium",
                "action": "Add to nurture sequence",
                "reason": f"Intent score {analysis.intent_score:.0f} - monitor for changes",
            })
        
        # Specific recommendations based on signals
        for signal in analysis.signals:
            if signal.signal_type == "technology_migration":
                recommendations.append({
                    "priority": "high",
                    "action": f"Position COMAI as migration alternative",
                    "reason": f"Company migrating from {signal.signal_value}",
                })
            elif signal.signal_type == "hiring_ai_roles":
                recommendations.append({
                    "priority": "high",
                    "action": "Highlight AI capabilities in outreach",
                    "reason": "Company investing in AI talent",
                })
        
        return recommendations
