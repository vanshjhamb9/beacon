"""Beacon Feedback Loop System.

Tracks outcomes from outreach to learn what works:
- Which intent signals convert best
- Which outsourcing angles resonate
- Which company profiles respond
- Which service matches close

Eventually, Beacon's scoring should be based on actual conversion data,
not just theoretical rules.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).parent


@dataclass
class OutreachRecord:
    """Tracks one outreach attempt and its outcome."""
    company: str
    contact_name: str
    contact_role: str
    channel: str  # email, linkedin
    subject: str
    trigger: str  # what we reached out about
    requirement: str  # what we think they need
    service_match: str  # which Inowix service
    outsourcing_angle: str  # the pitch angle
    sent_date: str
    reply_date: str = ""
    reply_type: str = ""  # positive, neutral, negative, no_reply
    reply_notes: str = ""
    meeting_booked: bool = False
    meeting_date: str = ""
    proposal_sent: bool = False
    proposal_value: str = ""
    closed_won: bool = False
    closed_lost: bool = False
    loss_reason: str = ""
    feedback_for_beacon: str = ""
    source_url: str = ""
    beacon_score_at_send: float = 0.0


# ============================================================
# FEEDBACK LEARNING RULES
# ============================================================

# These get updated as real data comes in
LEARNING_RULES = {
    "hiring_intent_conversion": {
        "description": "Which hiring intent signals convert best",
        "data": [],
        "insights": [],
    },
    "outsourcing_angle_effectiveness": {
        "description": "Which outsourcing angles resonate",
        "data": [],
        "insights": [],
    },
    "company_profile_response_rate": {
        "description": "Which company profiles respond",
        "data": [],
        "insights": [],
    },
    "service_match_close_rate": {
        "description": "Which service matches close deals",
        "data": [],
        "insights": [],
    },
}


def create_tracking_csv(output_file: str) -> None:
    """Create a CSV template for the9-person outreach test."""
    headers = [
        "company", "contact_name", "contact_role", "channel", "subject",
        "trigger", "requirement", "service_match", "outsourcing_angle",
        "sent_date", "reply_date", "reply_type", "reply_notes",
        "meeting_booked", "meeting_date", "proposal_sent", "proposal_value",
        "closed_won", "closed_lost", "loss_reason",
        "feedback_for_beacon", "source_url", "beacon_score_at_send",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

    print(f"Created tracking CSV at {output_file}")


def update_tracking_csv(csv_file: str, record: dict) -> None:
    """Add or update a record in the tracking CSV."""
    import pandas as pd

    df = pd.read_csv(csv_file)
    # Find existing row or append new one
    mask = df["company"] == record.get("company", "")
    if mask.any():
        for key, value in record.items():
            if key in df.columns:
                df.loc[mask, key] = value
    else:
        new_row = pd.DataFrame([record])
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(csv_file, index=False)
    print(f"Updated tracking for {record.get('company', 'unknown')}")


def analyze_feedback(csv_file: str) -> dict:
    """Analyze feedback data to generate learning insights."""
    import pandas as pd

    df = pd.read_csv(csv_file)

    insights = {
        "total_sent": len(df[df["sent_date"].notna()]),
        "total_replies": len(df[df["reply_type"].notna() & (df["reply_type"] != "no_reply")]),
        "positive_replies": len(df[df["reply_type"] == "positive"]),
        "meetings_booked": len(df[df["meeting_booked"] == True]),
        "proposals_sent": len(df[df["proposal_sent"] == True]),
        "deals_won": len(df[df["closed_won"] == True]),
        "deals_lost": len(df[df["closed_lost"] == True]),
        "reply_rate": 0,
        "positive_rate": 0,
        "meeting_rate": 0,
        "close_rate": 0,
    }

    total = insights["total_sent"]
    if total > 0:
        insights["reply_rate"] = round(insights["total_replies"] / total * 100, 1)
        insights["positive_rate"] = round(insights["positive_replies"] / total * 100, 1)
        insights["meeting_rate"] = round(insights["meetings_booked"] / total * 100, 1)
        insights["close_rate"] = round(insights["deals_won"] / total * 100, 1)

    # Per-trigger analysis
    trigger_stats = {}
    for _, row in df.iterrows():
        trigger = row.get("trigger", "")
        if trigger not in trigger_stats:
            trigger_stats[trigger] = {"sent": 0, "replies": 0, "meetings": 0}
        trigger_stats[trigger]["sent"] += 1
        if row.get("reply_type") not in ("", "no_reply"):
            trigger_stats[trigger]["replies"] += 1
        if row.get("meeting_booked"):
            trigger_stats[trigger]["meetings"] += 1

    insights["per_trigger"] = trigger_stats

    # Per-service analysis
    service_stats = {}
    for _, row in df.iterrows():
        service = row.get("service_match", "")
        if service not in service_stats:
            service_stats[service] = {"sent": 0, "replies": 0, "meetings": 0}
        service_stats[service]["sent"] += 1
        if row.get("reply_type") not in ("", "no_reply"):
            service_stats[service]["replies"] += 1
        if row.get("meeting_booked"):
            service_stats[service]["meetings"] += 1

    insights["per_service"] = service_stats

    # Loss reasons
    loss_reasons = df[df["closed_lost"] == True]["loss_reason"].tolist()
    insights["loss_reasons"] = loss_reasons

    # Feedback for Beacon
    beacon_feedback = df[df["feedback_for_beacon"].notna()]["feedback_for_beacon"].tolist()
    insights["beacon_feedback"] = beacon_feedback

    return insights


def generate_learning_report(csv_file: str, output_file: str) -> None:
    """Generate a learning report from feedback data."""
    insights = analyze_feedback(csv_file)

    report = []
    report.append("=" * 60)
    report.append("BEACON FEEDBACK LEARNING REPORT")
    report.append(f"Generated: {date.today().isoformat()}")
    report.append("=" * 60)
    report.append("")
    report.append("OVERALL METRICS")
    report.append(f"  Sent: {insights['total_sent']}")
    report.append(f"  Replies: {insights['total_replies']} ({insights['reply_rate']}%)")
    report.append(f"  Positive: {insights['positive_replies']} ({insights['positive_rate']}%)")
    report.append(f"  Meetings: {insights['meetings_booked']} ({insights['meeting_rate']}%)")
    report.append(f"  Proposals: {insights['proposals_sent']}")
    report.append(f"  Won: {insights['deals_won']} ({insights['close_rate']}%)")
    report.append(f"  Lost: {insights['deals_lost']}")
    report.append("")

    report.append("PER-TRIGGER CONVERSION")
    for trigger, stats in insights.get("per_trigger", {}).items():
        rate = round(stats["replies"] / stats["sent"] * 100, 1) if stats["sent"] > 0 else 0
        report.append(f"  {trigger}: {stats['sent']} sent, {stats['replies']} replies ({rate}%)")
    report.append("")

    report.append("PER-SERVICE CONVERSION")
    for service, stats in insights.get("per_service", {}).items():
        rate = round(stats["replies"] / stats["sent"] * 100, 1) if stats["sent"] > 0 else 0
        report.append(f"  {service}: {stats['sent']} sent, {stats['replies']} replies ({rate}%)")
    report.append("")

    if insights.get("loss_reasons"):
        report.append("LOSS REASONS")
        for reason in insights["loss_reasons"]:
            report.append(f"  - {reason}")
        report.append("")

    if insights.get("beacon_feedback"):
        report.append("BEACON FEEDBACK")
        for fb in insights["beacon_feedback"]:
            report.append(f"  - {fb}")
        report.append("")

    report_text = "\n".join(report)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to {output_file}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    csv_file = str(PROJECT_ROOT / "exports" / "outreach_tracking_9_test.csv")
    report_file = str(PROJECT_ROOT / "exports" / "beacon_learning_report.txt")

    # Create tracking CSV
    create_tracking_csv(csv_file)

    # Pre-populate with the9 test companies
    drafts = json.load(open(PROJECT_ROOT / "exports" / "outreach_drafts_9_test.json", encoding="utf-8"))
    import pandas as pd
    df = pd.DataFrame(drafts)
    df["sent_date"] = ""
    df["reply_date"] = ""
    df["reply_type"] = ""
    df["reply_notes"] = ""
    df["meeting_booked"] = False
    df["meeting_date"] = ""
    df["proposal_sent"] = False
    df["proposal_value"] = ""
    df["closed_won"] = False
    df["closed_lost"] = False
    df["loss_reason"] = ""
    df["feedback_for_beacon"] = ""
    df["beacon_score_at_send"] = 60.0
    df.to_csv(csv_file, index=False)
    print(f"Pre-populated tracking CSV with {len(df)} companies")
    print(f"CSV at: {csv_file}")
