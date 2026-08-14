"""
Rate Limiter for Outreach Automation
Enforces daily limits and delays between messages.
"""
import random
from datetime import datetime, timedelta
from typing import Optional


class RateLimiter:
    """Rate limiter for outreach messages across channels."""

    def __init__(self):
        self.daily_limits = {
            "reddit": {"max_per_day": 15, "min_delay": 300, "max_delay": 900},
            "indiehackers": {"max_per_day": 10, "min_delay": 600, "max_delay": 1800},
            "email": {"max_per_day": 15, "min_delay": 300, "max_delay": 900},
            "producthunt": {"max_per_day": 5, "min_delay": 900, "max_delay": 3600},
        }
        self.active_hours = (9, 22)  # 9am-10pm only
        self.sent_today: dict[str, list[datetime]] = {ch: [] for ch in self.daily_limits}
        self.last_sent: dict[str, Optional[datetime]] = {ch: None for ch in self.daily_limits}

    def can_send(self, channel: str) -> bool:
        """Check if we can send a message on this channel."""
        if channel not in self.daily_limits:
            return False

        now = datetime.now()

        # Check active hours
        if not (self.active_hours[0] <= now.hour < self.active_hours[1]):
            return False

        # Clean old entries (before today)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.sent_today[channel] = [
            t for t in self.sent_today[channel] if t >= today_start
        ]

        # Check daily limit
        limit = self.daily_limits[channel]
        if len(self.sent_today[channel]) >= limit["max_per_day"]:
            return False

        # Check minimum delay
        last = self.last_sent[channel]
        if last:
            elapsed = (now - last).total_seconds()
            if elapsed < limit["min_delay"]:
                return False

        return True

    def get_delay(self, channel: str) -> float:
        """Get random delay for next message on this channel."""
        if channel not in self.daily_limits:
            return 600

        limit = self.daily_limits[channel]
        return random.uniform(limit["min_delay"], limit["max_delay"])

    def record_send(self, channel: str):
        """Record that a message was sent."""
        now = datetime.now()
        self.sent_today[channel].append(now)
        self.last_sent[channel] = now

    def get_stats(self, channel: Optional[str] = None) -> dict:
        """Get rate limiting stats."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        channels = [channel] if channel else list(self.daily_limits.keys())
        stats = {}

        for ch in channels:
            # Clean old entries
            self.sent_today[ch] = [t for t in self.sent_today[ch] if t >= today_start]

            limit = self.daily_limits.get(ch, {})
            sent = len(self.sent_today[ch])
            remaining = limit.get("max_per_day", 0) - sent

            stats[ch] = {
                "sent_today": sent,
                "remaining": max(0, remaining),
                "max_per_day": limit.get("max_per_day", 0),
                "next_available": self._next_available(ch),
            }

        return stats

    def _next_available(self, channel: str) -> Optional[datetime]:
        """Get next available send time."""
        if self.can_send(channel):
            return datetime.now()

        last = self.last_sent.get(channel)
        if last:
            delay = self.daily_limits.get(channel, {}).get("min_delay", 600)
            return last + timedelta(seconds=delay)

        return None
