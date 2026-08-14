from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContextRuleCategory(StrEnum):
    PAIN = "pain"
    GOAL = "goal"
    TRIGGER = "trigger"
    IMPACT = "impact"
    STAGE = "stage"
    MATURITY = "maturity"
    PRESSURE = "pressure"
    DNA = "dna"


class ContextRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    name: str
    category: ContextRuleCategory
    version: int = 1
    enabled: bool = True
    priority: int = Field(default=100, ge=1)
    weight: float = Field(default=1.0, ge=0.0, le=2.0)
    conditions: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    explanation: str


class ContextRuleCatalog:
    def __init__(self, rules: list[ContextRule]) -> None:
        self._rules = sorted(rules, key=lambda rule: rule.priority)

    def enabled(self, category: ContextRuleCategory | None = None) -> list[ContextRule]:
        rules = [rule for rule in self._rules if rule.enabled]
        if category is not None:
            return [rule for rule in rules if rule.category == category]
        return rules

    def all(self) -> list[ContextRule]:
        return list(self._rules)
