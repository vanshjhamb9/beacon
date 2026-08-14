"""
Beacon Outreach Automation Package
Handles automated outreach across Reddit, IndieHackers, Product Hunt, and Email.
"""
from .queue import OutreachQueue, QueueItem, QueueStatus
from .rate_limiter import RateLimiter
from .reply_tracker import ReplyTracker, ReplyRecord, ReplyChannel, ReplyStatus
from .ai_reply_drafter import AIReplyDrafter
from .scheduler import OutreachScheduler

__all__ = [
    "OutreachQueue",
    "QueueItem",
    "QueueStatus",
    "RateLimiter",
    "ReplyTracker",
    "ReplyRecord",
    "ReplyChannel",
    "ReplyStatus",
    "AIReplyDrafter",
    "OutreachScheduler",
]
