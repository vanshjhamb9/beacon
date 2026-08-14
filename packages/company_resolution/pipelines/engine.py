"""CRE pipeline — Signal → Evidence → Identity → Verification → Company admission."""

from __future__ import annotations

from typing import Any

from company_resolution.admission.engine import CreAdmissionEngine
from company_resolution.identity_confidence.engine import IdentityConfidenceEngine
from company_resolution.models.types import CreSnapshot, CreVerdict, RawSignalEnvelope
from company_resolution.organization_resolver.engine import OrganizationResolverEngine
from company_resolution.source_attribution.engine import SourceAttributionEngine
from company_resolution.website_validator.engine import WebsiteValidatorEngine


class CompanyResolutionPipeline:
    """Replace Signal→Company with Signal→Evidence→Identity→Verification→Company."""

    def __init__(self) -> None:
        self.org = OrganizationResolverEngine()
        self.identity = IdentityConfidenceEngine()
        self.website = WebsiteValidatorEngine()
        self.attribution = SourceAttributionEngine()
        self.admission = CreAdmissionEngine()

    def evaluate(
        self,
        signal: RawSignalEnvelope | dict[str, Any],
        *,
        hints: dict[str, Any] | None = None,
        website_payload: dict[str, Any] | None = None,
    ) -> CreSnapshot:
        env = signal if isinstance(signal, RawSignalEnvelope) else self._to_envelope(signal)
        hints = {**(hints or {}), **dict(env.metadata or {})}

        # Product Hunt: recover real product homepage when domain missing/platform.
        # Live HTTP fetch only when hints/website_payload set fetch_product_hunt=True
        # (intelligence + rebuild). Unit tests pass domain via metadata and never fetch.
        if env.source == "product_hunt":
            from intelligence.entity_resolution.platform_domains import is_platform_domain

            meta_domain = hints.get("domain")
            needs_homepage = not meta_domain or is_platform_domain(str(meta_domain))
            fetch = bool(
                (website_payload or {}).get("fetch_product_hunt")
                or hints.get("fetch_product_hunt")
                or hints.get("product_hunt_html")
            )
            if needs_homepage and fetch:
                from company_resolution.product_hunt_enrichment.engine import ProductHuntHomepageEngine

                ph = ProductHuntHomepageEngine().extract(
                    product_url=env.url,
                    html=hints.get("product_hunt_html") or (website_payload or {}).get("product_hunt_html"),
                )
                if ph.get("domain"):
                    hints["domain"] = ph["domain"]
                    hints["homepage"] = ph.get("homepage")
                    env = RawSignalEnvelope.from_raw(
                        signal_id=env.signal_id,
                        title=env.title,
                        body=env.body,
                        url=env.url,
                        source=env.source,
                        author=env.author,
                        timestamp=env.timestamp,
                        metadata={**env.metadata, "domain": ph["domain"], "homepage": ph.get("homepage")},
                        extracted_entities=list(env.extracted_entities),
                        outbound_links=list(env.outbound_links),
                        domains=[ph["domain"]],
                        mentions=list(env.mentions),
                    )

        org = self.org.resolve(env, hints=hints)
        website = self.website.validate(org, payload=website_payload or hints)
        identity = self.identity.score(
            env,
            org,
            industry=hints.get("industry"),
            description=hints.get("description") or env.body[:400],
            country=hints.get("country"),
            website_valid=website.valid,
            extras=hints,
        )
        # Re-score boost: if website valid, identity may cross 90
        if website.valid and not identity.passed:
            identity = self.identity.score(
                env,
                org,
                industry=hints.get("industry") or ("Software" if env.source == "product_hunt" else None),
                description=hints.get("description") or env.body[:400] or env.title,
                country=hints.get("country"),
                website_valid=True,
                extras=hints,
            )
        attribution = self.attribution.attribute(env)
        admission = self.admission.evaluate(
            env,
            org=org,
            identity=identity,
            website=website,
            attribution=attribution,
        )

        return CreSnapshot(
            signal_id=env.signal_id,
            source=env.source,
            verdict=admission.verdict,
            signal=env,
            organization=org,
            identity=identity,
            website=website,
            attribution=attribution,
            admission=admission,
            company_name=org.legal_name if admission.admitted else None,
            company_domain=org.official_domain if admission.admitted else None,
            evidence=[
                f"verdict:{admission.verdict.value}",
                f"identity:{identity.score}",
                f"website:{website.valid}",
                f"org_found:{org.found}",
            ],
            false_positive_example=not admission.admitted and bool(org.legal_name),
        )

    def evaluate_many(self, signals: list[RawSignalEnvelope | dict[str, Any]]) -> list[CreSnapshot]:
        return [self.evaluate(s) for s in signals]

    def _to_envelope(self, payload: dict[str, Any]) -> RawSignalEnvelope:
        return RawSignalEnvelope.from_raw(
            signal_id=str(payload.get("signal_id") or payload.get("id") or payload.get("raw_event_id") or "unknown"),
            title=str(payload.get("title") or ""),
            body=str(payload.get("body") or payload.get("content") or ""),
            url=payload.get("url"),
            source=str(payload.get("source") or "unknown"),
            author=payload.get("author"),
            timestamp=payload.get("timestamp") or payload.get("published_at") or payload.get("collected_at"),
            metadata=dict(payload.get("metadata") or payload.get("event_metadata") or {}),
            extracted_entities=list(payload.get("extracted_entities") or []),
            outbound_links=list(payload.get("outbound_links") or []),
            domains=list(payload.get("domains") or []),
            mentions=list(payload.get("mentions") or payload.get("company_hints") or []),
        )
