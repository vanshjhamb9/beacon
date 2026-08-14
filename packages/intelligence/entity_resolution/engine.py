import re
from collections.abc import Iterable

from intelligence.entity_resolution.normalization import (
    fuzzy_similarity,
    normalize_company_name,
    normalize_domain,
)
from intelligence.entity_resolution.platform_domains import is_platform_domain, is_platform_label
from intelligence.types import EntityResolutionResult, RawSignal, ResolvedEntity

TECHNOLOGY_TERMS = {
    "aws",
    "azure",
    "databricks",
    "gcp",
    "hubspot",
    "kubernetes",
    "postgres",
    "salesforce",
    "snowflake",
    "zendesk",
}

PRODUCT_PATTERNS = (
    re.compile(r"\b(?:launches|released|introduces|announces)\s+([A-Z][A-Za-z0-9\- ]{2,60})"),
)

PERSON_PATTERN = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")
DOMAIN_PATTERN = re.compile(r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?\b")
COMPANY_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,3})"
    r"\s+(?:is|has|announces|announced|launches|launched|raises|raised|opens|opened|hiring|partners)\b"
)
SHOW_HN_PATTERN = re.compile(r"\bShow HN:\s*([A-Za-z0-9][A-Za-z0-9.&+\- ]{1,60})", re.IGNORECASE)
GITHUB_OWNER_PATTERN = re.compile(r"github\.com/([^/]+)/", re.IGNORECASE)


class EntityResolutionEngine:
    def resolve(
        self,
        signal: RawSignal,
        *,
        known_company_names: Iterable[str] = (),
        known_aliases: dict[str, str] | None = None,
        known_domains: dict[str, str] | None = None,
    ) -> EntityResolutionResult:
        aliases = known_aliases or {}
        domains = known_domains or {}
        text = f"{signal.title}\n{signal.content}"
        domain_entity = self._resolve_domain(signal, domains)
        company_entity = self._resolve_company(
            signal,
            text,
            domain_entity,
            known_company_names,
            aliases,
            domains,
        )
        person_entity = self._resolve_person(text)
        technologies = self._resolve_technologies(text)
        products = self._resolve_products(text)

        return EntityResolutionResult(
            company=company_entity,
            domain=domain_entity,
            person=person_entity,
            technologies=technologies,
            products=products,
        )

    def _resolve_domain(
        self,
        signal: RawSignal,
        known_domains: dict[str, str],
    ) -> ResolvedEntity | None:
        candidates = [signal.url, *DOMAIN_PATTERN.findall(signal.searchable_text)]
        metadata_domain = signal.metadata.get("domain")
        if isinstance(metadata_domain, str):
            candidates.insert(0, metadata_domain)

        ranked: list[ResolvedEntity] = []
        for candidate in candidates:
            domain = normalize_domain(candidate)
            if domain is None or is_platform_domain(domain):
                continue
            confidence = 0.96 if domain in known_domains else 0.82
            ranked.append(
                ResolvedEntity(
                    entity_type="domain",
                    value=domain,
                    normalized_value=domain,
                    confidence=confidence,
                    evidence={"method": "domain_match", "candidate": candidate},
                )
            )
        if ranked:
            return ranked[0]

        # Keep platform domain only as weak evidence (never company identity).
        for candidate in candidates:
            domain = normalize_domain(candidate)
            if domain is None:
                continue
            return ResolvedEntity(
                entity_type="domain",
                value=domain,
                normalized_value=domain,
                confidence=0.35,
                evidence={"method": "platform_domain", "candidate": candidate},
            )
        return None

    def _resolve_company(
        self,
        signal: RawSignal,
        text: str,
        domain: ResolvedEntity | None,
        known_company_names: Iterable[str],
        aliases: dict[str, str],
        known_domains: dict[str, str],
    ) -> ResolvedEntity | None:
        if (
            domain
            and domain.normalized_value in known_domains
            and not is_platform_domain(domain.normalized_value)
        ):
            company = known_domains[domain.normalized_value]
            return ResolvedEntity(
                entity_type="company",
                value=company,
                normalized_value=normalize_company_name(company),
                confidence=min(0.99, domain.confidence + 0.03),
                evidence={"method": "known_domain", "domain": domain.normalized_value},
            )

        for candidate in self._candidate_names(signal, text):
            if is_platform_label(candidate):
                continue
            normalized = normalize_company_name(candidate)
            if not normalized or is_platform_label(normalized):
                continue

            if normalized in aliases:
                canonical = aliases[normalized]
                return ResolvedEntity(
                    entity_type="company",
                    value=canonical,
                    normalized_value=normalize_company_name(canonical),
                    confidence=0.94,
                    evidence={"method": "alias_match", "alias": candidate},
                )

            best_match, best_score = self._best_fuzzy_match(candidate, known_company_names)
            if best_match and best_score >= 0.88:
                return ResolvedEntity(
                    entity_type="company",
                    value=best_match,
                    normalized_value=normalize_company_name(best_match),
                    confidence=round(0.72 + (best_score * 0.2), 4),
                    evidence={"method": "fuzzy_company_match", "candidate": candidate, "score": best_score},
                )

            return ResolvedEntity(
                entity_type="company",
                value=candidate,
                normalized_value=normalized,
                confidence=0.68,
                evidence={"method": "pattern_extraction", "candidate": candidate},
            )

        if domain and not is_platform_domain(domain.normalized_value):
            domain_name = domain.normalized_value.split(".")[0]
            if domain_name and not is_platform_label(domain_name):
                return ResolvedEntity(
                    entity_type="company",
                    value=domain_name.title(),
                    normalized_value=normalize_company_name(domain_name),
                    confidence=0.58,
                    evidence={"method": "domain_inference", "domain": domain.normalized_value},
                )
        return None

    def _candidate_names(self, signal: RawSignal, text: str) -> list[str]:
        candidates: list[str] = []

        owner = signal.metadata.get("owner")
        if isinstance(owner, str) and owner.strip():
            candidates.append(owner.strip())

        github_match = GITHUB_OWNER_PATTERN.search(signal.url)
        if github_match:
            candidates.append(github_match.group(1))

        show_hn = SHOW_HN_PATTERN.search(signal.title)
        if show_hn:
            candidates.append(show_hn.group(1).strip())

        hints = signal.metadata.get("company_hints")
        if isinstance(hints, list):
            for hint in hints:
                if isinstance(hint, str) and hint.strip():
                    candidates.append(hint.strip())

        candidates.extend(match.group(1).strip() for match in COMPANY_PATTERN.finditer(text))

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = normalize_company_name(candidate)
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)
        return deduped

    def _resolve_person(self, text: str) -> ResolvedEntity | None:
        for match in PERSON_PATTERN.finditer(text):
            value = match.group(1)
            lowered = value.lower()
            if lowered in {"customer support", "product launch", "hiring freeze"}:
                continue
            return ResolvedEntity(
                entity_type="person",
                value=value,
                normalized_value=lowered,
                confidence=0.55,
                evidence={"method": "name_pattern"},
            )
        return None

    def _resolve_technologies(self, text: str) -> list[ResolvedEntity]:
        lowered = text.lower()
        return [
            ResolvedEntity(
                entity_type="technology",
                value=technology,
                normalized_value=technology,
                confidence=0.86,
                evidence={"method": "technology_dictionary"},
            )
            for technology in sorted(TECHNOLOGY_TERMS)
            if re.search(rf"\b{re.escape(technology)}\b", lowered)
        ]

    def _resolve_products(self, text: str) -> list[ResolvedEntity]:
        products: list[ResolvedEntity] = []
        for pattern in PRODUCT_PATTERNS:
            for match in pattern.finditer(text):
                product = match.group(1).strip()
                products.append(
                    ResolvedEntity(
                        entity_type="product",
                        value=product,
                        normalized_value=product.lower(),
                        confidence=0.72,
                        evidence={"method": "product_launch_pattern"},
                    )
                )
        return products

    def _best_fuzzy_match(
        self,
        candidate: str,
        known_company_names: Iterable[str],
    ) -> tuple[str | None, float]:
        best_match: str | None = None
        best_score = 0.0
        for known_name in known_company_names:
            score = fuzzy_similarity(candidate, known_name)
            if score > best_score:
                best_match = known_name
                best_score = score
        return best_match, best_score
