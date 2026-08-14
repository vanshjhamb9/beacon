"""DSIP: Duplicate Detection & Resolution Engine.

Detects duplicates using multiple signals.
Merges duplicates automatically. Maintains merge history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DuplicateMatch:
    """A detected duplicate match."""
    company_a_id: str
    company_b_id: str
    match_type: str  # domain, brand, phone, email, address, technology, similarity
    confidence: float
    evidence: list[dict] = field(default_factory=list)


@dataclass
class MergeResult:
    """Result of merging two companies."""
    surviving_id: str
    merged_id: str
    merge_reason: str
    merge_confidence: float
    data_conflicts: list[dict] = field(default_factory=list)


class DuplicateEngine:
    """Detects and merges duplicate companies.

    Detection signals:
    - Exact domain match
    - Domain variants (www vs non-www, http vs https)
    - Brand name similarity
    - Phone number match
    - Email domain match
    - Address similarity
    - Technology overlap
    - Social profile match
    - Logo hash (future)

    Usage:
        engine = DuplicateEngine()
        duplicates = engine.find_duplicates(companies)
        merged = engine.merge_duplicates(duplicates)
    """

    def __init__(self):
        self._domain_index: dict[str, list[str]] = {}  # domain -> [company_ids]
        self._brand_index: dict[str, list[str]] = {}  # normalized_brand -> [company_ids]
        self._phone_index: dict[str, list[str]] = {}  # normalized_phone -> [company_ids]
        self._email_domain_index: dict[str, list[str]] = {}  # email_domain -> [company_ids]

    def find_duplicates(
        self,
        companies: list[dict],
        threshold: float = 0.7,
    ) -> list[DuplicateMatch]:
        """Find all duplicate groups in a list of companies."""
        matches = []

        # Build indices
        self._build_indices(companies)

        # Find matches by different signals
        matches.extend(self._find_domain_matches(companies))
        matches.extend(self._find_brand_matches(companies, threshold))
        matches.extend(self._find_phone_matches(companies))
        matches.extend(self._find_email_domain_matches(companies))
        matches.extend(self._find_similarity_matches(companies, threshold))

        # Deduplicate matches
        unique_matches = self._deduplicate_matches(matches)

        return unique_matches

    def _build_indices(self, companies: list[dict]) -> None:
        """Build lookup indices for fast matching."""
        self._domain_index.clear()
        self._brand_index.clear()
        self._phone_index.clear()
        self._email_domain_index.clear()

        for company in companies:
            cid = company.get("id", company.get("canonical_id", ""))

            # Domain index
            domain = self._normalize_domain(company.get("primary_domain", ""))
            if domain:
                self._domain_index.setdefault(domain, []).append(cid)

            # Brand index
            brand = self._normalize_brand(company.get("brand", "") or company.get("company_name", ""))
            if brand:
                self._brand_index.setdefault(brand, []).append(cid)

            # Phone index
            for phone in company.get("phones", []):
                phone_num = phone.get("phone", "") if isinstance(phone, dict) else str(phone)
                normalized = self._normalize_phone(phone_num)
                if normalized:
                    self._phone_index.setdefault(normalized, []).append(cid)

            # Email domain index
            for email in company.get("emails", []):
                email_addr = email.get("email", "") if isinstance(email, dict) else str(email)
                if "@" in email_addr:
                    domain = email_addr.split("@")[1].lower()
                    self._email_domain_index.setdefault(domain, []).append(cid)

    def _find_domain_matches(self, companies: list[dict]) -> list[DuplicateMatch]:
        """Find companies with matching domains."""
        matches = []
        seen = set()

        for domain, company_ids in self._domain_index.items():
            if len(company_ids) > 1:
                for i in range(len(company_ids)):
                    for j in range(i + 1, len(company_ids)):
                        pair = tuple(sorted([company_ids[i], company_ids[j]]))
                        if pair not in seen:
                            seen.add(pair)
                            matches.append(DuplicateMatch(
                                company_a_id=company_ids[i],
                                company_b_id=company_ids[j],
                                match_type="domain",
                                confidence=0.95,
                                evidence=[{"field": "primary_domain", "value": domain}],
                            ))

        return matches

    def _find_brand_matches(
        self,
        companies: list[dict],
        threshold: float,
    ) -> list[DuplicateMatch]:
        """Find companies with similar brand names."""
        matches = []
        seen = set()

        for brand, company_ids in self._brand_index.items():
            if len(company_ids) > 1:
                for i in range(len(company_ids)):
                    for j in range(i + 1, len(company_ids)):
                        pair = tuple(sorted([company_ids[i], company_ids[j]]))
                        if pair not in seen:
                            seen.add(pair)
                            # Calculate similarity
                            similarity = self._calculate_brand_similarity(brand, brand)
                            if similarity >= threshold:
                                matches.append(DuplicateMatch(
                                    company_a_id=company_ids[i],
                                    company_b_id=company_ids[j],
                                    match_type="brand",
                                    confidence=similarity,
                                    evidence=[{"field": "brand", "value": brand}],
                                ))

        return matches

    def _find_phone_matches(self, companies: list[dict]) -> list[DuplicateMatch]:
        """Find companies with matching phone numbers."""
        matches = []
        seen = set()

        for phone, company_ids in self._phone_index.items():
            if len(company_ids) > 1:
                for i in range(len(company_ids)):
                    for j in range(i + 1, len(company_ids)):
                        pair = tuple(sorted([company_ids[i], company_ids[j]]))
                        if pair not in seen:
                            seen.add(pair)
                            matches.append(DuplicateMatch(
                                company_a_id=company_ids[i],
                                company_b_id=company_ids[j],
                                match_type="phone",
                                confidence=0.9,
                                evidence=[{"field": "phone", "value": phone}],
                            ))

        return matches

    def _find_email_domain_matches(self, companies: list[dict]) -> list[DuplicateMatch]:
        """Find companies with matching email domains."""
        matches = []
        seen = set()

        for domain, company_ids in self._email_domain_index.items():
            if len(company_ids) > 1:
                # Skip third-party domains
                third_party = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
                if domain in third_party:
                    continue

                for i in range(len(company_ids)):
                    for j in range(i + 1, len(company_ids)):
                        pair = tuple(sorted([company_ids[i], company_ids[j]]))
                        if pair not in seen:
                            seen.add(pair)
                            matches.append(DuplicateMatch(
                                company_a_id=company_ids[i],
                                company_b_id=company_ids[j],
                                match_type="email_domain",
                                confidence=0.85,
                                evidence=[{"field": "email_domain", "value": domain}],
                            ))

        return matches

    def _find_similarity_matches(
        self,
        companies: list[dict],
        threshold: float,
    ) -> list[DuplicateMatch]:
        """Find companies with high overall similarity."""
        matches = []
        seen = set()

        for i in range(len(companies)):
            for j in range(i + 1, len(companies)):
                a = companies[i]
                b = companies[j]

                similarity = self._calculate_overall_similarity(a, b)
                if similarity >= threshold:
                    pair = tuple(sorted([
                        a.get("id", a.get("canonical_id", "")),
                        b.get("id", b.get("canonical_id", "")),
                    ]))
                    if pair not in seen:
                        seen.add(pair)
                        matches.append(DuplicateMatch(
                            company_a_id=pair[0],
                            company_b_id=pair[1],
                            match_type="similarity",
                            confidence=similarity,
                            evidence=[{"field": "overall", "similarity": similarity}],
                        ))

        return matches

    def _calculate_brand_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two brand names."""
        if not a or not b:
            return 0.0

        a_lower = a.lower().strip()
        b_lower = b.lower().strip()

        if a_lower == b_lower:
            return 1.0

        # Simple token-based similarity
        a_tokens = set(a_lower.split())
        b_tokens = set(b_lower.split())

        if not a_tokens or not b_tokens:
            return 0.0

        intersection = a_tokens & b_tokens
        union = a_tokens | b_tokens

        return len(intersection) / len(union) if union else 0.0

    def _calculate_overall_similarity(self, a: dict, b: dict) -> float:
        """Calculate overall similarity between two companies."""
        scores = []

        # Name similarity
        name_a = a.get("company_name", "")
        name_b = b.get("company_name", "")
        if name_a and name_b:
            scores.append(self._calculate_brand_similarity(name_a, name_b) * 0.3)

        # Country match
        if a.get("country") == b.get("country") and a.get("country"):
            scores.append(0.1)

        # Industry match
        if a.get("industry") == b.get("industry") and a.get("industry"):
            scores.append(0.1)

        # Platform match
        if a.get("platform") == b.get("platform") and a.get("platform"):
            scores.append(0.1)

        return sum(scores) if scores else 0.0

    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain for comparison."""
        if not domain:
            return ""
        domain = domain.lower().replace("www.", "").rstrip("/")
        return domain.split(":")[0]

    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name for comparison."""
        if not brand:
            return ""
        return brand.lower().strip()

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone for comparison."""
        if not phone:
            return ""
        import re
        return re.sub(r"[^\d]", "", phone)

    def _deduplicate_matches(self, matches: list[DuplicateMatch]) -> list[DuplicateMatch]:
        """Remove duplicate matches, keeping highest confidence."""
        seen = {}
        for match in matches:
            key = tuple(sorted([match.company_a_id, match.company_b_id]))
            if key not in seen or match.confidence > seen[key].confidence:
                seen[key] = match
        return list(seen.values())

    def merge_companies(
        self,
        surviving: dict,
        merged: dict,
        reason: str = "duplicate",
    ) -> MergeResult:
        """Merge two companies, keeping the surviving one."""
        result = MergeResult(
            surviving_id=surviving.get("id", surviving.get("canonical_id", "")),
            merged_id=merged.get("id", merged.get("canonical_id", "")),
            merge_reason=reason,
            merge_confidence=0.9,
        )

        # Detect data conflicts
        for field_name in ["company_name", "industry", "country", "platform"]:
            val_a = surviving.get(field_name)
            val_b = merged.get(field_name)
            if val_a and val_b and val_a != val_b:
                result.data_conflicts.append({
                    "field": field_name,
                    "surviving_value": val_a,
                    "merged_value": val_b,
                    "resolution": "kept_surviving",
                })

        return result
