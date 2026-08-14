"""Outreach Draft Generator for Beacon.

Generates personalized outreach drafts based on:
- Exact trigger (what they're hiring/looking for)
- Their likely requirement (evidence-based)
- Inowix capability that maps to it
- Why outsourcing/partnering may be useful (without assuming)
- Short CTA (15-minute technical discovery call)
- Source reference (why Beacon selected them)

Every draft is unique per company. No generic templates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class OutreachDraft:
    """A personalized outreach draft for one company."""
    company_name: str
    contact_name: str
    contact_role: str
    subject: str
    body: str
    source_url: str
    beacon_reason: str
    trigger: str
    requirement: str
    service_match: str
    outsourcing_angle: str
    cta: str
    channel: str  # email, linkedin
    status: str = "draft"


def generate_outreach(draft: OutreachDraft) -> str:
    """Format an outreach draft for display."""
    return f"""
{'='*70}
COMPANY: {draft.company_name}
CONTACT: {draft.contact_name} ({draft.contact_role})
CHANNEL: {draft.channel}
STATUS: {draft.status}
{'='*70}

SUBJECT: {draft.subject}

{draft.body}

---
SOURCE: {draft.source_url}
BEACON REASON: {draft.beacon_reason}
TRIGGER: {draft.trigger}
REQUIREMENT: {draft.requirement}
SERVICE MATCH: {draft.service_match}
OUTSOURCING ANGLE: {draft.outsourcing_angle}
CTA: {draft.cta}
{'='*70}
"""


def save_drafts(drafts: list[OutreachDraft], output_file: str) -> None:
    """Save all drafts to JSON."""
    data = []
    for d in drafts:
        data.append({
            "company": d.company_name,
            "contact_name": d.contact_name,
            "contact_role": d.contact_role,
            "subject": d.subject,
            "body": d.body,
            "source_url": d.source_url,
            "beacon_reason": d.beacon_reason,
            "trigger": d.trigger,
            "requirement": d.requirement,
            "service_match": d.service_match,
            "outsourcing_angle": d.outsourcing_angle,
            "cta": d.cta,
            "channel": d.channel,
            "status": d.status,
        })
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(drafts)} outreach drafts to {output_file}")
