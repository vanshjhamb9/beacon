from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleCategory(StrEnum):
    SCHEMA = "schema"
    NORMALIZATION = "normalization"
    SPAM = "spam"
    TRUST = "trust"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    ENTITY = "entity"
    DUPLICATE = "duplicate"
    SCORING = "scoring"


class QualityRuleDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    name: str
    category: RuleCategory
    version: int = 1
    enabled: bool = True
    priority: int = Field(default=100, ge=1)
    threshold: float = Field(default=0.0, ge=0.0, le=100.0)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    parameters: dict[str, Any] = Field(default_factory=dict)


class RuleCatalog:
    def __init__(self, rules: list[QualityRuleDefinition]) -> None:
        self._rules = sorted(rules, key=lambda rule: rule.priority)

    def enabled(self, category: RuleCategory | None = None) -> list[QualityRuleDefinition]:
        rules = [rule for rule in self._rules if rule.enabled]
        if category is not None:
            rules = [rule for rule in rules if rule.category == category]
        return rules

    def by_key(self, key: str) -> QualityRuleDefinition | None:
        for rule in self._rules:
            if rule.key == key:
                return rule
        return None

    def all(self) -> list[QualityRuleDefinition]:
        return list(self._rules)
