from __future__ import annotations

import re

from sales_copilot.models.types import INSUFFICIENT, SalesIntelligencePackage

# Phrases that often indicate fabricated specificity.
FABRICATION_PATTERNS = (
    r"\bwe found that they secretly\b",
    r"\bguaranteed roi\b",
    r"\b\$\d{2,}m ARR\b",
    r"\bdefinitely using\b",
)


class GroundingValidator:
    def validate(self, package: SalesIntelligencePackage) -> list[str]:
        issues: list[str] = []
        evidence_blob = " ".join(item.summary.lower() for item in package.evidence_chain)
        for section in package.sections:
            if section.content != INSUFFICIENT and not section.attribution.grounded and not section.attribution.evidence_summaries:
                issues.append(f"Section '{section.key}' lacks evidence attribution")
            for pattern in FABRICATION_PATTERNS:
                if re.search(pattern, section.content, flags=re.IGNORECASE):
                    issues.append(f"Section '{section.key}' matched fabrication pattern")
            if section.content != INSUFFICIENT:
                # Soft check: if content invents a proper noun not seen in evidence/company name
                for token in re.findall(r"\b[A-Z][a-z]+(?:Soft|Cloud|AI|Labs)\b", section.content):
                    if token.lower() not in evidence_blob and token.lower() not in package.company_name.lower():
                        # Only flag exotic product-like tokens
                        if token.lower() not in {"beacon"}:
                            issues.append(f"Section '{section.key}' may reference unverified term '{token}'")
        for variant in package.style_variants:
            for draft in variant.drafts:
                if draft.body and draft.body != INSUFFICIENT and not draft.attribution.evidence_summaries:
                    # Drafts may still be generic templates; only flag when they assert specific tech/hiring.
                    if re.search(r"\b(?:hired|using|revenue of)\b", draft.body, flags=re.IGNORECASE):
                        if not package.evidence_chain:
                            issues.append(f"Draft '{draft.kind}' asserts facts without evidence")
        return issues

    def is_safe(self, package: SalesIntelligencePackage) -> bool:
        return not self.validate(package)
