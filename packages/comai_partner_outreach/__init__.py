"""COMAI Partner Outreach — upload → draft → auto-send → replies → follow-ups."""

from __future__ import annotations

from comai_partner_outreach.config import load_config, PartnerOutreachConfig
from comai_partner_outreach.drafting import draft_for_step, PartnerDraft
from comai_partner_outreach.ingest import parse_upload, IngestResult
from comai_partner_outreach.service import PartnerOutreachService

__all__ = [
    "PartnerDraft",
    "PartnerOutreachConfig",
    "PartnerOutreachService",
    "IngestResult",
    "draft_for_step",
    "load_config",
    "parse_upload",
]
