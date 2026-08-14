"""Rule-based service intent classification."""

from __future__ import annotations


SERVICE_RULES: dict[str, tuple[str, ...]] = {
    "Recruitment Automation": ("Hiring Recruiters", "Hiring HR", "Need recruitment"),
    "Sales Automation": ("Hiring SDRs", "Hiring Sales", "Need CRM"),
    "AI Chatbot": ("Hiring Support", "Need customer support"),
    "Finance Automation": ("Hiring Finance", "finance"),
    "Cloud Automation": ("Hiring DevOps", "Moving cloud", "Migration", "Need IT"),
    "Marketing Automation": ("Hiring Marketing", "Marketing growth"),
    "HR Automation": ("Need HR", "Hiring HR", "Need onboarding"),
    "Operations Automation": ("Hiring Operations", "Operations change", "Need automation"),
    "Compliance Automation": ("Compliance program", "Procurement"),
    "Security Automation": ("Security program",),
}


class IntentClassifier:
    def classify(self, event_type: str, category: str, text: str = "") -> list[str]:
        haystack = f"{event_type} {category} {text}".lower()
        matches = [
            service
            for service, triggers in SERVICE_RULES.items()
            if any(trigger.lower() in haystack for trigger in triggers)
        ]
        if matches:
            return matches
        if category == "EXPANSION":
            return ["Operations Automation", "HR Automation", "Sales Automation"]
        if category == "TECHNOLOGY CHANGE":
            return ["Cloud Automation"]
        return []
