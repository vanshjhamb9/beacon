from __future__ import annotations

from account_journey.models.types import AccountJourneyInput, BuyingCommittee, CommitteeMember, CommitteeRole


TITLE_MAP: list[tuple[CommitteeRole, list[str]]] = [
    (CommitteeRole.ECONOMIC_BUYER, ["ceo", "founder", "owner", "cfo", "managing director", "president"]),
    (CommitteeRole.TECHNICAL_BUYER, ["cto", "vp engineering", "head of engineering", "architect", "it director"]),
    (CommitteeRole.CHAMPION, ["champion", "sponsor", "ops lead", "head of ops", "growth"]),
    (CommitteeRole.LEGAL, ["legal", "counsel", "compliance"]),
    (CommitteeRole.PROCUREMENT, ["procurement", "purchasing", "vendor"]),
    (CommitteeRole.OPERATIONS, ["coo", "operations", "delivery"]),
    (CommitteeRole.INFLUENCER, ["manager", "lead", "director", "vp"]),
]


class BuyingCommitteeEngine:
    def build(self, item: AccountJourneyInput) -> BuyingCommittee:
        members: list[CommitteeMember] = []
        used_roles: set[CommitteeRole] = set()
        for dm in item.decision_makers:
            name = str(dm.get("name") or "Unknown")
            title = str(dm.get("title") or dm.get("role") or "")
            email = str(dm.get("email") or "") or None
            role = self._infer_role(title)
            if role in used_roles and role != CommitteeRole.INFLUENCER:
                role = CommitteeRole.INFLUENCER
            used_roles.add(role)
            strength = 55.0
            if role in {CommitteeRole.CHAMPION, CommitteeRole.ECONOMIC_BUYER}:
                strength = 75.0
            if item.replied:
                strength += 10.0
            if item.meeting_scheduled:
                strength += 8.0
            members.append(
                CommitteeMember(
                    name=name,
                    role=role,
                    title=title or None,
                    email=email,
                    relationship_strength=min(100.0, strength),
                    evidence=[f"title:{title or 'n/a'}", f"role:{role.value}"],
                )
            )
        required = list(CommitteeRole)
        missing = [r.value for r in required if r not in used_roles]
        coverage = round((len(used_roles) / max(1, len(required))) * 100.0, 2)
        return BuyingCommittee(
            members=members,
            coverage=coverage,
            missing_roles=missing,
            evidence=[f"members:{len(members)}", f"coverage:{coverage}"],
        )

    def _infer_role(self, title: str) -> CommitteeRole:
        t = title.lower()
        for role, patterns in TITLE_MAP:
            if any(p in t for p in patterns):
                return role
        return CommitteeRole.INFLUENCER
