"""Execution readiness enums — clr/er-v1."""

from __future__ import annotations

from enum import StrEnum


class ExecutionMode(StrEnum):
    PLANNING = "PLANNING"
    READY = "READY"
    EXECUTING = "EXECUTING"


class ProviderKind(StrEnum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    GRAPH = "graph"
    META_WHATSAPP = "meta_whatsapp"
    SENDGRID = "sendgrid"
    SMTP = "smtp"


class Capability(StrEnum):
    GENERATE_PROSPECTS = "generate_prospects"
    GENERATE_CAMPAIGNS = "generate_campaigns"
    GENERATE_DRAFTS = "generate_drafts"
    SCORE_OPPORTUNITIES = "score_opportunities"
    RECOMMENDATIONS = "recommendations"
    DRAFT_APPROVAL = "draft_approval"
    TEST_SEND = "test_send"
    SEND_EMAIL = "send_email"
    SEND_WHATSAPP = "send_whatsapp"
    MONITOR_OPENS = "monitor_opens"
    TRACK_REPLIES = "track_replies"
    SCHEDULE_FOLLOWUPS = "schedule_followups"
    COUNT_CONTACTED = "count_contacted"
    COUNT_DELIVERIES = "count_deliveries"
    COUNT_MEETINGS = "count_meetings"
    LEARNING = "learning"
    REVENUE_ATTRIBUTION = "revenue_attribution"


PLANNING_ALLOWED = frozenset(
    {
        Capability.GENERATE_PROSPECTS,
        Capability.GENERATE_CAMPAIGNS,
        Capability.GENERATE_DRAFTS,
        Capability.SCORE_OPPORTUNITIES,
        Capability.RECOMMENDATIONS,
    }
)

READY_ALLOWED = PLANNING_ALLOWED | frozenset(
    {
        Capability.DRAFT_APPROVAL,
        Capability.TEST_SEND,
    }
)

EXECUTING_ALLOWED = READY_ALLOWED | frozenset(
    {
        Capability.SEND_EMAIL,
        Capability.SEND_WHATSAPP,
        Capability.MONITOR_OPENS,
        Capability.TRACK_REPLIES,
        Capability.SCHEDULE_FOLLOWUPS,
        Capability.COUNT_CONTACTED,
        Capability.COUNT_DELIVERIES,
        Capability.COUNT_MEETINGS,
        Capability.LEARNING,
        Capability.REVENUE_ATTRIBUTION,
    }
)

FORBIDDEN_NEXT_STEP_PHRASES = (
    "monitor opens",
    "prepare follow-up",
    "schedule follow-up",
    "reply tracking",
    "wait for reply",
    "follow-up",
)
