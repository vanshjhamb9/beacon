"""Live Revenue Operations Platform (LROP v1) — Sprint 38.

Beacon as a Live Revenue Operating System.

Architecture:
    Collectors → OCP → DQE → LOVP → Opportunity Intelligence → Revenue Ready
                                              ↓
                                    Live Revenue Operations Platform
                                              ↓
                                    Revenue Inbox → Human Review → Sales Pipeline
                                              ↓
                                    Outreach → Replies → Meetings → Proposal
                                              ↓
                                    Negotiation → Won / Lost → Learning
                                              ↓
                                    Connector ROI

LROP_VERSION = "lrop-v1"
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


# === Enums ===

class OpportunityStage(str, Enum):
    NEW = "new"
    REVIEW = "review"
    APPROVED = "approved"
    OUTREACH_READY = "outreach_ready"
    CONTACTED = "contacted"
    REPLIED = "replied"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"
    SPAM = "spam"
    NOT_ICP = "not_icp"


class InboxAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ARCHIVE = "archive"
    SPAM = "spam"
    COMPETITOR = "competitor"
    FUTURE_OPPORTUNITY = "future_opportunity"
    WATCHLIST = "watchlist"
    DUPLICATE = "duplicate"
    MERGE = "merge"
    DELETE = "delete"
    ASSIGN = "assign"


class AgingColor(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class FeedbackType(str, Enum):
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"
    WRONG_COMPANY = "wrong_company"
    ALREADY_CUSTOMER = "already_customer"
    COMPETITOR = "competitor"
    BAD_SIGNAL = "bad_signal"
    WRONG_TIMING = "wrong_timing"
    BAD_CONTACT = "bad_contact"
    NEED_MORE_RESEARCH = "need_more_research"


class FilterPeriod(str, Enum):
    MINUTES_15 = "15_minutes"
    MINUTES_30 = "30_minutes"
    HOURS_1 = "1_hour"
    HOURS_6 = "6_hours"
    HOURS_12 = "12_hours"
    TODAY = "today"
    YESTERDAY = "yesterday"
    DAYS_7 = "7_days"
    DAYS_30 = "30_days"
    CUSTOM = "custom"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


# === Constants ===

EXPIRATION_RULES = {
    "Hiring": 30,
    "Funding": 90,
    "Launch": 30,
    "Technology Migration": 60,
    "Conference": 15,
    "Award": 30,
    "Press": 30,
    "Government": 365,
    "Expansion": 60,
    "Compliance": 90,
    "Digital Transformation": 90,
    "Infrastructure Upgrade": 60,
    "Cloud Migration": 60,
    "Automation": 60,
    "New Office": 60,
    "ERP Migration": 90,
    "CRM Migration": 60,
    "Technology Replacement": 60,
    "Executive Hiring": 60,
    "Partnership": 60,
    "API Launch": 30,
    "Marketplace Launch": 30,
}

AGING_THRESHOLDS = {
    AgingColor.GREEN: 7,
    AgingColor.YELLOW: 14,
    AgingColor.ORANGE: 30,
    AgingColor.RED: 60,
}


LROP_VERSION = "lrop-v1"
