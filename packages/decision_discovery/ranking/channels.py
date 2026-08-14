from __future__ import annotations

from decision_discovery.models.types import (
    ContactChannel,
    ContactChannelKind,
    DecisionMakerCandidate,
    DiscoverySourceType,
    OutreachStep,
)

_CHANNEL_PRIORITY: dict[ContactChannelKind, int] = {
    ContactChannelKind.FOUNDER_EMAIL: 1,
    ContactChannelKind.EXECUTIVE_EMAIL: 2,
    ContactChannelKind.CONTACT_FORM: 3,
    ContactChannelKind.BUSINESS_EMAIL: 4,
    ContactChannelKind.LINKEDIN_COMPANY: 5,
    ContactChannelKind.SUPPORT_EMAIL: 6,
    ContactChannelKind.SALES_EMAIL: 7,
    ContactChannelKind.BUSINESS_PHONE: 8,
    ContactChannelKind.ROLE_BASED_EMAIL: 9,
    ContactChannelKind.GITHUB_ORGANIZATION: 10,
    ContactChannelKind.CAREERS_PAGE: 11,
    ContactChannelKind.PRESS_PAGE: 12,
    ContactChannelKind.TWITTER_COMPANY: 13,
    ContactChannelKind.FACEBOOK_COMPANY: 14,
    ContactChannelKind.YOUTUBE_COMPANY: 15,
}


class ContactChannelRanker:
    def rank(
        self,
        channels: list[ContactChannel],
        primary: DecisionMakerCandidate | None,
        secondary: DecisionMakerCandidate | None,
    ) -> tuple[list[ContactChannel], list[OutreachStep]]:
        augmented = list(channels)

        for person, label_prefix in ((primary, "Primary"), (secondary, "Secondary")):
            if person is None:
                continue
            if person.work_email:
                kind = (
                    ContactChannelKind.FOUNDER_EMAIL
                    if person.normalized_role.value.lower() == "founder"
                    else ContactChannelKind.EXECUTIVE_EMAIL
                )
                augmented.append(
                    ContactChannel(
                        kind=kind,
                        value=person.work_email,
                        label=f"{label_prefix} {person.role} email",
                        confidence=person.confidence,
                        source=person.source,
                        source_url=person.source_url,
                        evidence=f"Public business email attributed to {person.name}",
                    )
                )
            if person.business_phone:
                augmented.append(
                    ContactChannel(
                        kind=ContactChannelKind.BUSINESS_PHONE,
                        value=person.business_phone,
                        label=f"{label_prefix} {person.role} phone",
                        confidence=person.confidence,
                        source=person.source,
                        source_url=person.source_url,
                        evidence=f"Public business phone attributed to {person.name}",
                    )
                )

        deduped: dict[str, ContactChannel] = {}
        for channel in augmented:
            key = f"{channel.kind.value}:{channel.value.lower()}"
            existing = deduped.get(key)
            if existing is None or channel.confidence > existing.confidence:
                deduped[key] = channel

        ranked_channels = sorted(
            deduped.values(),
            key=lambda item: (_CHANNEL_PRIORITY.get(item.kind, 99), -item.confidence, item.value),
        )
        numbered: list[ContactChannel] = []
        steps: list[OutreachStep] = []
        for index, channel in enumerate(ranked_channels, start=1):
            numbered.append(channel.model_copy(update={"rank": index}))
            steps.append(
                OutreachStep(
                    rank=index,
                    channel_kind=channel.kind,
                    value=channel.value,
                    rationale=self._rationale(channel, primary),
                    confidence=channel.confidence,
                    source=channel.source,
                    source_url=channel.source_url,
                )
            )
        return numbered, steps

    def _rationale(self, channel: ContactChannel, primary: DecisionMakerCandidate | None) -> str:
        if channel.kind == ContactChannelKind.FOUNDER_EMAIL:
            return "Highest-priority publicly listed founder business email"
        if channel.kind == ContactChannelKind.EXECUTIVE_EMAIL:
            role = primary.role if primary else "executive"
            return f"Publicly listed {role} business email"
        if channel.kind == ContactChannelKind.CONTACT_FORM:
            return "Official company contact form/page"
        if channel.kind == ContactChannelKind.LINKEDIN_COMPANY:
            return "Official LinkedIn company page for business outreach"
        if channel.kind == ContactChannelKind.SUPPORT_EMAIL:
            return "Public support mailbox"
        if channel.kind == ContactChannelKind.SALES_EMAIL:
            return "Public sales mailbox"
        if channel.kind == ContactChannelKind.BUSINESS_PHONE:
            return "Public business phone number"
        return channel.evidence or "Publicly attributed business channel"
