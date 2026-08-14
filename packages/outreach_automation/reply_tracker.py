"""
Reply Tracker for Beacon Outreach
Tracks replies across all outreach channels.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Optional
from uuid import uuid4


class ReplyStatus(StrEnum):
    PENDING = "pending"
    REPLIED = "replied"
    NO_REPLY = "no_reply"
    BOUNCED = "bounced"
    AUTO_REPLY = "auto_reply"


class ReplyChannel(StrEnum):
    REDDIT = "reddit"
    INDIEHACKERS = "indiehackers"
    EMAIL = "email"
    PRODUCTHUNT = "producthunt"


@dataclass
class ReplyRecord:
    """A recorded reply from an outreach."""
    id: str = field(default_factory=lambda: str(uuid4()))
    opportunity_id: str = ""
    campaign_id: str = ""
    channel: ReplyChannel = ReplyChannel.EMAIL
    original_message_id: str = ""
    reply_content: str = ""
    reply_from: str = ""
    reply_at: datetime = field(default_factory=datetime.now)
    status: ReplyStatus = ReplyStatus.REPLIED
    ai_drafted_reply: Optional[str] = None
    founder_approved: bool = False
    founder_decision: Optional[str] = None
    sent_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "campaign_id": self.campaign_id,
            "channel": self.channel.value,
            "original_message_id": self.original_message_id,
            "reply_content": self.reply_content,
            "reply_from": self.reply_from,
            "reply_at": self.reply_at.isoformat(),
            "status": self.status.value,
            "ai_drafted_reply": self.ai_drafted_reply,
            "founder_approved": self.founder_approved,
            "founder_decision": self.founder_decision,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class ReplyTracker:
    """Tracks replies across all outreach channels."""

    def __init__(self, tracker_file: Optional[Path] = None):
        self.tracker_file = tracker_file or Path("exports/outreach/replies.json")
        self.replies: list[ReplyRecord] = []
        self._load_replies()

    def _load_replies(self):
        """Load replies from file if exists."""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, "r") as f:
                    data = json.load(f)
                    for reply_data in data.get("replies", []):
                        reply = ReplyRecord(
                            id=reply_data["id"],
                            opportunity_id=reply_data.get("opportunity_id", ""),
                            campaign_id=reply_data.get("campaign_id", ""),
                            channel=ReplyChannel(reply_data["channel"]),
                            original_message_id=reply_data.get("original_message_id", ""),
                            reply_content=reply_data.get("reply_content", ""),
                            reply_from=reply_data.get("reply_from", ""),
                            reply_at=datetime.fromisoformat(reply_data["reply_at"]),
                            status=ReplyStatus(reply_data["status"]),
                            ai_drafted_reply=reply_data.get("ai_drafted_reply"),
                            founder_approved=reply_data.get("founder_approved", False),
                            founder_decision=reply_data.get("founder_decision"),
                            sent_at=datetime.fromisoformat(reply_data["sent_at"]) if reply_data.get("sent_at") else None,
                        )
                        self.replies.append(reply)
            except Exception:
                pass

    def _save_replies(self):
        """Save replies to file."""
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "replies": [reply.to_dict() for reply in self.replies],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.tracker_file, "w") as f:
            json.dump(data, f, indent=2)

    def record_reply(
        self,
        opportunity_id: str,
        channel: ReplyChannel,
        original_message_id: str,
        reply_content: str,
        reply_from: str,
        campaign_id: str = "",
    ) -> ReplyRecord:
        """Record a new reply."""
        reply = ReplyRecord(
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            channel=channel,
            original_message_id=original_message_id,
            reply_content=reply_content,
            reply_from=reply_from,
        )
        self.replies.append(reply)
        self._save_replies()
        return reply

    def get_replies_for_opportunity(self, opportunity_id: str) -> list[ReplyRecord]:
        """Get all replies for an opportunity."""
        return [r for r in self.replies if r.opportunity_id == opportunity_id]

    def get_pending_replies(self) -> list[ReplyRecord]:
        """Get replies that need AI drafting."""
        return [
            r for r in self.replies
            if r.status == ReplyStatus.REPLIED and not r.ai_drafted_reply
        ]

    def get_pending_approval(self) -> list[ReplyRecord]:
        """Get AI-drafted replies pending founder approval."""
        return [
            r for r in self.replies
            if r.ai_drafted_reply and not r.founder_approved and not r.founder_decision
        ]

    def update_reply_status(self, reply_id: str, status: ReplyStatus):
        """Update reply status."""
        for reply in self.replies:
            if reply.id == reply_id:
                reply.status = status
                self._save_replies()
                return

    def add_ai_draft(self, reply_id: str, draft: str):
        """Add AI-drafted reply."""
        for reply in self.replies:
            if reply.id == reply_id:
                reply.ai_drafted_reply = draft
                self._save_replies()
                return

    def approve_reply(self, reply_id: str, decision: str = "approve"):
        """Founder approves/rejects reply."""
        for reply in self.replies:
            if reply.id == reply_id:
                reply.founder_decision = decision
                reply.founder_approved = decision == "approve"
                self._save_replies()
                return

    def get_stats(self) -> dict:
        """Get reply statistics."""
        total = len(self.replies)
        replied = len([r for r in self.replies if r.status == ReplyStatus.REPLIED])
        pending_draft = len(self.get_pending_replies())
        pending_approval = len(self.get_pending_approval())

        by_channel = {}
        for reply in self.replies:
            channel = reply.channel.value
            by_channel[channel] = by_channel.get(channel, 0) + 1

        return {
            "total_replies": total,
            "replied": replied,
            "pending_ai_draft": pending_draft,
            "pending_approval": pending_approval,
            "by_channel": by_channel,
        }
