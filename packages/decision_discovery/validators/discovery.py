from __future__ import annotations

from decision_discovery.models.types import ContactChannel, DecisionMakerCandidate, DecisionMakerReport


class DiscoveryValidator:
    NO_CONTACT_MESSAGE = "No verified public business contact available."

    def validate_report(self, report: DecisionMakerReport) -> DecisionMakerReport:
        makers = [item for item in report.decision_makers if item.name and item.role]
        channels = [item for item in report.contact_channels if item.value and item.is_verified_public]
        public_emails = sorted({item.value.lower() for item in channels if "@" in item.value})
        public_phones = sorted({item.value for item in channels if item.kind.value == "business_phone"})

        no_contact = None
        if not public_emails and not public_phones and not any(
            item.kind.value.endswith("_company") or item.kind.value in {"contact_form", "careers_page", "press_page"}
            for item in channels
        ):
            no_contact = self.NO_CONTACT_MESSAGE

        return report.model_copy(
            update={
                "decision_makers": makers,
                "contact_channels": channels,
                "public_emails": public_emails,
                "public_phones": public_phones,
                "no_public_contact_message": no_contact,
            }
        )

    def reject_invented_contacts(
        self,
        makers: list[DecisionMakerCandidate],
        channels: list[ContactChannel],
    ) -> tuple[list[DecisionMakerCandidate], list[ContactChannel]]:
        clean_makers = [
            maker.model_copy(
                update={
                    "work_email": maker.work_email if maker.work_email and "@" in maker.work_email else None,
                    "business_phone": maker.business_phone
                    if maker.business_phone and sum(ch.isdigit() for ch in maker.business_phone) >= 7
                    else None,
                }
            )
            for maker in makers
        ]
        clean_channels = [
            channel
            for channel in channels
            if channel.value
            and (
                bool(channel.source_url)
                or "@" in channel.value
                or channel.value.startswith("http")
                or sum(ch.isdigit() for ch in channel.value) >= 7
            )
        ]
        return clean_makers, clean_channels
