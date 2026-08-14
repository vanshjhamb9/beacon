"""Contact classification — never mix categories."""

from __future__ import annotations

import re

from revenue_readiness_perfection.models.types import ClassifiedContact, ContactCategory

PRIVACY = ("privacy@", "dpo@")
SUPPORT = ("support@", "help@", "care@")
SALES = ("sales@", "revenue@", "deals@")
PRESS = ("press@", "media@", "pr@", "media.inquiries@")
LEGAL = ("legal@", "counsel@", "compliance@")
BUSINESS = ("info@", "hello@", "contact@", "team@", "hi@", "office@", "marketing@")
DM_LOCAL = ("founder@", "ceo@", "cofounder@", "co-founder@")


class ContactClassificationEngine:
    def classify(self, email: str, *, dm_name: str | None = None) -> ClassifiedContact:
        low = (email or "").lower().strip()
        local = low.split("@")[0] if "@" in low else ""
        if any(low.startswith(p) for p in PRIVACY):
            return ClassifiedContact(email=low, category=ContactCategory.PRIVACY, confidence=95)
        if any(low.startswith(p) for p in LEGAL):
            return ClassifiedContact(email=low, category=ContactCategory.LEGAL, confidence=95)
        if any(low.startswith(p) for p in PRESS):
            return ClassifiedContact(email=low, category=ContactCategory.PRESS, confidence=95)
        if any(low.startswith(p) for p in SUPPORT):
            return ClassifiedContact(email=low, category=ContactCategory.SUPPORT, confidence=92)
        if any(low.startswith(p) for p in SALES):
            return ClassifiedContact(email=low, category=ContactCategory.SALES, confidence=93)
        # Decision Maker Email only with name match or explicit founder/ceo mailbox — never invent.
        if any(low.startswith(p) for p in DM_LOCAL) or (dm_name and self._matches_person(local, dm_name)):
            return ClassifiedContact(email=low, category=ContactCategory.DECISION_MAKER_EMAIL, confidence=96)
        if any(low.startswith(p) for p in BUSINESS):
            return ClassifiedContact(email=low, category=ContactCategory.BUSINESS_EMAIL, confidence=90)
        # Personal-looking locals without name evidence stay Business Email (unknown > incorrect).
        return ClassifiedContact(email=low, category=ContactCategory.BUSINESS_EMAIL, confidence=80)

    def _matches_person(self, local: str, dm_name: str) -> bool:
        parts = [p for p in re.split(r"[^a-z]+", dm_name.lower()) if len(p) > 1]
        if len(parts) < 2:
            return False
        first, last = parts[0], parts[-1]
        return local in {f"{first}.{last}", f"{first}{last}", f"{first[0]}{last}", f"{first}_{last}"}
