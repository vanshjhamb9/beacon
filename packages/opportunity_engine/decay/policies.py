from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from opportunity_engine.models.types import OpportunityEvidenceItem


class DecayPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_type: str
    half_life_days: float = Field(gt=0)
    floor_weight: float = Field(default=0.15, ge=0.0, le=1.0)


class DecayPolicyCatalog:
    def __init__(self, policies: list[DecayPolicy] | None = None) -> None:
        self._policies = {policy.signal_type: policy for policy in (policies or default_decay_policies())}

    def weight(self, evidence: OpportunityEvidenceItem, *, now: datetime | None = None) -> float:
        current_time = now or datetime.now(UTC)
        age_days = max((current_time - evidence.occurred_at).total_seconds() / 86400.0, 0.0)
        policy = self._policies.get(evidence.category, self._policies["default"])
        decayed = 0.5 ** (age_days / policy.half_life_days)
        return round(max(policy.floor_weight, decayed) * evidence.weight, 4)


def default_decay_policies() -> list[DecayPolicy]:
    return [
        DecayPolicy(signal_type="default", half_life_days=45.0),
        DecayPolicy(signal_type="funding", half_life_days=90.0),
        DecayPolicy(signal_type="expansion", half_life_days=75.0),
        DecayPolicy(signal_type="hiring", half_life_days=45.0),
        DecayPolicy(signal_type="customer_complaints", half_life_days=30.0),
        DecayPolicy(signal_type="layoffs", half_life_days=60.0),
        DecayPolicy(signal_type="technology_migration", half_life_days=60.0),
    ]
