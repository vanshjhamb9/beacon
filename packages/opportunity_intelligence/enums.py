"""Enums for the Opportunity Intelligence Platform foundation."""

from __future__ import annotations

from enum import StrEnum


class SignalCategory(StrEnum):
    HIRING = "HIRING"
    FUNDING = "FUNDING"
    EXPANSION = "EXPANSION"
    LEADERSHIP = "LEADERSHIP"
    TECH_STACK = "TECH_STACK"
    CUSTOMER_PAIN = "CUSTOMER_PAIN"
    PRODUCT = "PRODUCT"
    PARTNERSHIP = "PARTNERSHIP"
    COMPLIANCE = "COMPLIANCE"
    SECURITY = "SECURITY"
    MARKET = "MARKET"


class SourceTier(StrEnum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"


class BuyingWindow(StrEnum):
    IMMEDIATE = "Immediate"
    WARM = "Warm"
    FUTURE = "Future"
    DORMANT = "Dormant"


class FreshnessBucket(StrEnum):
    ZERO_TO_SEVEN = "0-7 days"
    EIGHT_TO_THIRTY = "8-30 days"
    THIRTY_ONE_TO_SIXTY = "31-60 days"
    SIXTY_ONE_TO_NINETY = "61-90 days"
    NINETY_ONE_TO_ONE_EIGHTY = "91-180 days"
    ONE_EIGHTY_PLUS = "180+ days"


class OpportunityStatus(StrEnum):
    ACTIVE = "active"
    REJECTED = "rejected"
    ARCHIVED = "archived"
