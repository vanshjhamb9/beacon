"""Decision Maker Engine — Discovers decision makers with evidence.

Priority: Founder > CEO > Co-founder > Head of Ecommerce > ...

Never return: support@, info@, hello@, sales@
Never fabricate phone numbers or email addresses.
If data cannot be verified, mark it UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.comai_intelligence.evidence_tracker import EvidenceTracker, VerificationMethod


@dataclass
class DecisionMakerInfo:
    """Single decision maker record."""

    name: str
    role: str
    email: str
    phone: str
    linkedin_url: str
    confidence: float  # 0-1
    source: str
    evidence_url: str
    verification_status: str  # "verified", "unverified", "unknown"
    is_generic: bool = False  # True for support@, info@, etc.

    @property
    def is_reachable(self) -> bool:
        """Is this a reachable, specific contact?"""
        return bool(self.email or self.phone) and not self.is_generic

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "evidence_url": self.evidence_url,
            "verification_status": self.verification_status,
            "is_generic": self.is_generic,
        }


# Priority order for decision maker roles
ROLE_PRIORITY: dict[str, int] = {
    "founder": 1,
    "ceo": 2,
    "co-founder": 3,
    "cofounder": 3,
    "chief executive officer": 2,
    "managing director": 2,
    "head of ecommerce": 4,
    "ecommerce head": 4,
    "head of growth": 5,
    "growth head": 5,
    "marketing head": 6,
    "cmo": 6,
    "chief marketing officer": 6,
    "cx head": 7,
    "customer experience head": 7,
    "customer success head": 8,
    "crm head": 9,
    "crm manager": 9,
    "retention head": 10,
    "retention manager": 10,
    "digital head": 11,
    "digital marketing head": 11,
    "operations head": 12,
    "coo": 12,
    "head of operations": 12,
    "vp engineering": 13,
    "cto": 14,
    "chief technology officer": 14,
}

# Generic email prefixes that should be rejected
GENERIC_PREFIXES = {
    "support", "info", "hello", "sales", "care", "contact",
    "help", "feedback", "noreply", "no-reply", "admin",
    "office", "team", "marketing", "hr", "billing",
}


class DecisionMakerEngine:
    """Discovers decision makers with evidence-based confidence.

    Priority order:
    1. Founder/CEO/Co-founder
    2. Head of Ecommerce
    3. Head of Growth
    4. Marketing Head
    5. CX Head
    6. Customer Success Head
    7. Operations Head

    Never returns generic emails unless no better contact exists.
    """

    PRIORITY_ROLES = [
        "founder", "ceo", "co-founder",
        "head of ecommerce", "head of growth",
        "marketing head", "cx head",
        "customer success head", "operations head",
    ]

    def __init__(self, evidence_tracker: EvidenceTracker | None = None) -> None:
        self._evidence = evidence_tracker

    async def discover(self, company: dict[str, Any]) -> list[DecisionMakerInfo]:
        """Discover decision makers from multiple sources.

        Args:
            company: Company data with website, domain, social profiles, etc.

        Returns:
            List of DecisionMakerInfo, sorted by role priority.
        """
        contacts: list[DecisionMakerInfo] = []

        # Source 1: Website scrape data (pre-collected)
        website_contacts = self._extract_from_website(company)
        contacts.extend(website_contacts)

        # Source 2: LinkedIn data (if available)
        linkedin_contacts = self._extract_from_linkedin(company)
        contacts.extend(linkedin_contacts)

        # Source 3: About/Team page data
        team_contacts = self._extract_from_team_page(company)
        contacts.extend(team_contacts)

        # Source 4: Google search results
        search_contacts = self._extract_from_search(company)
        contacts.extend(search_contacts)

        # Deduplicate and rank
        deduped = self._deduplicate(contacts)
        ranked = self._rank_by_priority(deduped)

        # Record evidence for each contact
        if self._evidence:
            for contact in ranked:
                if contact.email:
                    self._evidence.record(
                        domain=company.get("domain", ""),
                        company_name=company.get("company_name", ""),
                        field_name=f"decision_maker_email_{contact.role}",
                        field_value=contact.email,
                        confidence=contact.confidence,
                        source=contact.source,
                        proof_url=contact.evidence_url,
                        verification_method=VerificationMethod.WEBSITE_SCRAPE
                        if "website" in contact.source.lower()
                        else VerificationMethod.LINKEDIN_PROFILE,
                    )

        return ranked

    def _extract_from_website(self, company: dict[str, Any]) -> list[DecisionMakerInfo]:
        """Extract contacts from website scraping data."""
        contacts: list[DecisionMakerInfo] = []
        website = company.get("website", "")
        scraped_data = company.get("scraped_contacts", {})

        # Founder/CEO from about page
        founder_name = scraped_data.get("founder_name") or company.get("founder_name", "")
        founder_email = scraped_data.get("founder_email") or company.get("founder_email", "")
        if founder_name:
            contacts.append(DecisionMakerInfo(
                name=founder_name,
                role="founder",
                email=founder_email,
                phone=scraped_data.get("founder_phone", ""),
                linkedin_url=scraped_data.get("founder_linkedin", ""),
                confidence=0.8 if founder_email else 0.5,
                source="website_about_page",
                evidence_url=f"{website}/about",
                verification_status="unverified",
            ))

        # Team page contacts
        team_members = scraped_data.get("team_members", [])
        for member in team_members:
            name = member.get("name", "")
            role = member.get("role", "")
            if name and role:
                is_generic = self._is_generic_email(member.get("email", ""))
                contacts.append(DecisionMakerInfo(
                    name=name,
                    role=role.lower(),
                    email=member.get("email", ""),
                    phone=member.get("phone", ""),
                    linkedin_url=member.get("linkedin", ""),
                    confidence=0.7 if member.get("email") else 0.4,
                    source="website_team_page",
                    evidence_url=f"{website}/team",
                    verification_status="unverified",
                    is_generic=is_generic,
                ))

        # Contact page emails
        contact_emails = scraped_data.get("contact_emails", [])
        for email in contact_emails:
            if not self._is_generic_email(email):
                contacts.append(DecisionMakerInfo(
                    name="",
                    role="contact",
                    email=email,
                    phone="",
                    linkedin_url="",
                    confidence=0.4,
                    source="website_contact_page",
                    evidence_url=f"{website}/contact",
                    verification_status="unverified",
                ))

        return contacts

    def _extract_from_linkedin(self, company: dict[str, Any]) -> list[DecisionMakerInfo]:
        """Extract contacts from LinkedIn data."""
        contacts: list[DecisionMakerInfo] = []
        linkedin_data = company.get("linkedin_contacts", [])

        for person in linkedin_data:
            name = person.get("name", "")
            title = person.get("title", "")
            if name and title:
                contacts.append(DecisionMakerInfo(
                    name=name,
                    role=title.lower(),
                    email=person.get("email", ""),
                    phone="",
                    linkedin_url=person.get("linkedin_url", ""),
                    confidence=0.75,
                    source="linkedin_company_page",
                    evidence_url=person.get("linkedin_url", ""),
                    verification_status="unverified",
                ))

        return contacts

    def _extract_from_team_page(self, company: dict[str, Any]) -> list[DecisionMakerInfo]:
        """Extract from pre-scraped team page data."""
        contacts: list[DecisionMakerInfo] = []
        team_data = company.get("team_page_data", [])

        for member in team_data:
            name = member.get("name", "")
            role = member.get("role", "")
            if name and role:
                is_generic = self._is_generic_email(member.get("email", ""))
                contacts.append(DecisionMakerInfo(
                    name=name,
                    role=role.lower(),
                    email=member.get("email", ""),
                    phone=member.get("phone", ""),
                    linkedin_url=member.get("linkedin", ""),
                    confidence=0.65,
                    source="team_page_scrape",
                    evidence_url=company.get("website", ""),
                    verification_status="unverified",
                    is_generic=is_generic,
                ))

        return contacts

    def _extract_from_search(self, company: dict[str, Any]) -> list[DecisionMakerInfo]:
        """Extract from Google search results."""
        contacts: list[DecisionMakerInfo] = []
        search_results = company.get("search_contacts", [])

        for result in search_results:
            name = result.get("name", "")
            role = result.get("role", "")
            if name and role:
                contacts.append(DecisionMakerInfo(
                    name=name,
                    role=role.lower(),
                    email=result.get("email", ""),
                    phone="",
                    linkedin_url=result.get("linkedin", ""),
                    confidence=0.5,
                    source="google_search",
                    evidence_url=result.get("url", ""),
                    verification_status="unverified",
                ))

        return contacts

    def _deduplicate(self, contacts: list[DecisionMakerInfo]) -> list[DecisionMakerInfo]:
        """Deduplicate contacts by name+email or email alone."""
        seen_emails: set[str] = set()
        seen_names: set[str] = set()
        deduped: list[DecisionMakerInfo] = []

        for contact in contacts:
            email_key = contact.email.lower().strip() if contact.email else ""
            name_key = f"{contact.name.lower().strip()}_{contact.role.lower().strip()}"

            if email_key and email_key in seen_emails:
                continue
            if name_key in seen_names:
                continue

            if email_key:
                seen_emails.add(email_key)
            seen_names.add(name_key)
            deduped.append(contact)

        return deduped

    def _rank_by_priority(self, contacts: list[DecisionMakerInfo]) -> list[DecisionMakerInfo]:
        """Rank contacts by role priority."""
        def get_priority(contact: DecisionMakerInfo) -> int:
            role_lower = contact.role.lower()
            # Check exact match
            if role_lower in ROLE_PRIORITY:
                return ROLE_PRIORITY[role_lower]
            # Check partial match
            for key, priority in ROLE_PRIORITY.items():
                if key in role_lower or role_lower in key:
                    return priority
            return 99

        # Sort by priority, then by confidence, then by is_generic (non-generic first)
        contacts.sort(key=lambda c: (get_priority(c), -c.confidence, c.is_generic))
        return contacts

    def _is_generic_email(self, email: str) -> bool:
        """Check if email is generic (support@, info@, etc.)."""
        if not email:
            return False
        prefix = email.split("@")[0].lower().strip()
        return prefix in GENERIC_PREFIXES

    def get_best_contact(self, contacts: list[DecisionMakerInfo]) -> DecisionMakerInfo | None:
        """Get the single best contact (non-generic, highest confidence)."""
        non_generic = [c for c in contacts if not c.is_generic and c.is_reachable]
        if non_generic:
            return non_generic[0]
        return contacts[0] if contacts else None

    def has_verified_contact(self, contacts: list[DecisionMakerInfo]) -> bool:
        """Check if any contact has been verified."""
        return any(c.verification_status == "verified" for c in contacts)

    def contact_quality_score(self, contacts: list[DecisionMakerInfo]) -> float:
        """Score overall contact quality 0-1."""
        if not contacts:
            return 0.0

        non_generic = [c for c in contacts if not c.is_generic]
        with_email = [c for c in non_generic if c.email]
        with_linkedin = [c for c in non_generic if c.linkedin_url]
        verified = [c for c in contacts if c.verification_status == "verified"]

        score = 0.0
        if non_generic:
            score += 0.3 * min(len(non_generic) / 3, 1.0)
        if with_email:
            score += 0.3 * min(len(with_email) / 2, 1.0)
        if with_linkedin:
            score += 0.2 * min(len(with_linkedin) / 2, 1.0)
        if verified:
            score += 0.2

        return min(score, 1.0)
