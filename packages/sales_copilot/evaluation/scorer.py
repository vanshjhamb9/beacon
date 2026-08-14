from __future__ import annotations

import re

from sales_copilot.models.types import INSUFFICIENT, QualityScores, SalesIntelligencePackage


CTA_PATTERNS = (
    r"\bopen to\b",
    r"\bwould you\b",
    r"\bnext week\b",
    r"\b15-minute\b",
    r"\b20-minute\b",
    r"\bconversation\b",
    r"\bdiscuss\b",
)


class QualityScorer:
    def score(self, package: SalesIntelligencePackage) -> QualityScores:
        section_map = {section.key: section.content for section in package.sections}
        grounded_sections = sum(1 for section in package.sections if section.content != INSUFFICIENT)
        coverage = (grounded_sections / max(1, len(package.sections))) * 100.0

        personalization = 40.0
        if package.company_name and package.company_name in " ".join(section_map.values()):
            personalization += 20.0
        if any(section_map.get(key) not in (None, INSUFFICIENT) for key in ("pain_points", "decision_makers", "technology_stack")):
            personalization += 20.0
        if package.evidence_chain:
            personalization += min(20.0, len(package.evidence_chain) * 2.0)
        personalization = min(100.0, personalization)

        email_bodies = [
            draft.body
            for variant in package.style_variants
            for draft in variant.drafts
            if draft.kind.value == "email"
        ]
        sample = email_bodies[0] if email_bodies else next(iter(section_map.values()), "")
        words = len(re.findall(r"\w+", sample))
        readability = 85.0 if 40 <= words <= 220 else 60.0 if words else 40.0
        professional_tone = 88.0 if not re.search(r"\b(asap|!!!|buy now)\b", sample, flags=re.IGNORECASE) else 55.0
        length_score = 90.0 if 40 <= words <= 220 else 65.0
        cta_score = 90.0 if any(re.search(pattern, sample, flags=re.IGNORECASE) for pattern in CTA_PATTERNS) else 45.0
        confidence = min(
            100.0,
            (coverage * 0.45)
            + (personalization * 0.25)
            + (min(100.0, len(package.evidence_chain) * 5.0) * 0.30),
        )
        overall = (
            personalization * 0.18
            + coverage * 0.22
            + readability * 0.12
            + professional_tone * 0.12
            + length_score * 0.10
            + cta_score * 0.12
            + confidence * 0.14
        )
        return QualityScores(
            personalization=round(personalization, 2),
            evidence_coverage=round(coverage, 2),
            readability=round(readability, 2),
            professional_tone=round(professional_tone, 2),
            length=round(length_score, 2),
            call_to_action=round(cta_score, 2),
            confidence=round(confidence, 2),
            overall=round(overall, 2),
        )
