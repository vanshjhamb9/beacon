"""RDAP pipeline — classify → discover website → expand → contacts → DMs → dossier."""

from __future__ import annotations

from typing import Any

from revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine
from revenue_data_acquisition.dm_recovery.engine import DecisionMakerRecoveryEngine
from revenue_data_acquisition.dossier.engine import CompanyDossierEngine
from revenue_data_acquisition.identity_expansion.engine import CompanyIdentityExpansionEngine
from revenue_data_acquisition.models.types import RdapSnapshot, SourceClass
from revenue_data_acquisition.recovery.engine import RdapRecoveryEngine
from revenue_data_acquisition.source_roles.engine import SourceClassificationEngine
from revenue_data_acquisition.website_discovery.engine import OfficialWebsiteDiscoveryPipeline


class RevenueDataAcquisitionPipeline:
    def __init__(self) -> None:
        self.roles = SourceClassificationEngine()
        self.websites = OfficialWebsiteDiscoveryPipeline()
        self.identity = CompanyIdentityExpansionEngine()
        self.contacts = ContactRecoveryEngine()
        self.dms = DecisionMakerRecoveryEngine()
        self.dossier = CompanyDossierEngine()
        self.recovery = RdapRecoveryEngine()

    def evaluate(
        self,
        payload: dict[str, Any],
        *,
        fetch_github: bool = False,
        recover_contacts: bool = False,
        recover_dms: bool = False,
        crawl_website: bool = False,
        company_id: str | None = None,
    ) -> RdapSnapshot:
        signal_id = str(payload.get("signal_id") or payload.get("id") or "unknown")
        source = str(payload.get("source") or "unknown").lower()
        roles = self.roles.roles(source)
        can_id = self.roles.can_create_identity(source)

        website, domain, trail = self.websites.discover(payload, fetch_github=fetch_github)
        identity = self.identity.expand(
            {**payload, "official_website": website, "website": website},
            crawl_website=crawl_website,
        )
        emails = []
        dms = []
        if recover_contacts and website:
            emails = self.contacts.recover(website, collector=source)
        if recover_dms and website:
            dms = self.dms.recover(website, collector=source)

        conf = 30.0
        if website:
            conf += 35.0
        if emails:
            conf += 20.0
        if dms:
            conf += 15.0
        if not can_id:
            conf = min(conf, 55.0)

        dossier = None
        if website and domain:
            dossier = self.dossier.build(
                company_id=company_id,
                identity=identity,
                website=website,
                domain=domain,
                emails=emails,
                decision_makers=dms,
                payload=payload,
                collector=source,
            )

        recovery = self.recovery.from_payload(payload, website=website, emails=emails, dms=dms)
        if SourceClass.IDENTITY not in roles and website:
            # community may attach intent later — never identity create
            pass

        return RdapSnapshot(
            signal_id=signal_id,
            source=source,
            roles=roles,
            can_create_identity=can_id,
            website=website,
            domain=domain,
            emails=emails,
            decision_makers=dms,
            dossier=dossier,
            recovery=recovery,
            confidence=min(99.0, conf),
            payload={
                "trail": trail,
                "identity": identity,
                "igf_enrichment": {
                    "official_website": website,
                    "homepage": website,
                    "official_domain": domain,
                    "domain": domain,
                    "business_email": emails[0].value if emails else None,
                    "decision_maker": (
                        f"{dms[0]['name']} ({dms[0].get('role')})" if dms else None
                    ),
                    "description": identity.get("description"),
                    "linkedin_company": identity.get("linkedin"),
                },
            },
        )

    def evaluate_many(self, payloads: list[dict[str, Any]], **kwargs: Any) -> list[RdapSnapshot]:
        return [self.evaluate(p, **kwargs) for p in payloads]
