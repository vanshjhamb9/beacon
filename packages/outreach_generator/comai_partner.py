"""Re-export partner drafting into outreach_generator package."""

from __future__ import annotations

from comai_partner_outreach.config import load_config
from comai_partner_outreach.drafting import (
    PartnerDraft,
    draft_for_step,
    draft_partner_final,
    draft_partner_fu1,
    draft_partner_fu2,
    draft_partner_intro,
)

__all__ = [
    "PartnerDraft",
    "draft_for_step",
    "draft_partner_final",
    "draft_partner_fu1",
    "draft_partner_fu2",
    "draft_partner_intro",
    "load_config",
]
