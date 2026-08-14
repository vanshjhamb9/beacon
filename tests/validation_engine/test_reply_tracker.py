"""Tests for ReplyTracker."""

from __future__ import annotations

import pytest

from validation_engine import REPLY_TYPES
from validation_engine.reply_tracker import ReplyTracker


class TestReplyTrackerRecordReply:
    def test_record_valid_reply(self, reply_tracker: ReplyTracker) -> None:
        event = reply_tracker.record_reply("company_1", "positive")
        assert event.company_id == "company_1"
        assert event.reply_type == "positive"

    def test_record_invalid_reply_type_raises(self, reply_tracker: ReplyTracker) -> None:
        with pytest.raises(ValueError, match="Invalid reply type"):
            reply_tracker.record_reply("company_1", "invalid")

    def test_record_all_reply_types(self, reply_tracker: ReplyTracker) -> None:
        for reply_type in REPLY_TYPES:
            event = reply_tracker.record_reply("company_1", reply_type)
            assert event.reply_type == reply_type

    def test_record_with_evidence(self, reply_tracker: ReplyTracker) -> None:
        evidence = {"email_id": "abc123"}
        event = reply_tracker.record_reply("company_1", "positive", evidence=evidence)
        assert event.evidence == evidence

    def test_record_with_source(self, reply_tracker: ReplyTracker) -> None:
        event = reply_tracker.record_reply("company_1", "positive", source="outlook")
        assert event.source == "outlook"

    def test_record_with_reply_time(self, reply_tracker: ReplyTracker) -> None:
        event = reply_tracker.record_reply("company_1", "positive", reply_time_seconds=3600.0)
        assert event.reply_time_seconds == 3600.0

    def test_record_with_confidence(self, reply_tracker: ReplyTracker) -> None:
        event = reply_tracker.record_reply("company_1", "positive", confidence=0.9)
        assert event.confidence == 0.9


class TestReplyTrackerGetRepliesForCompany:
    def test_get_empty_replies(self, reply_tracker: ReplyTracker) -> None:
        replies = reply_tracker.get_replies_for_company("nonexistent")
        assert replies == []

    def test_get_replies_filtered(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_1", "negative")
        reply_tracker.record_reply("company_2", "positive")
        replies = reply_tracker.get_replies_for_company("company_1")
        assert len(replies) == 2


class TestReplyTrackerGetAllReplies:
    def test_get_all_empty(self, reply_tracker: ReplyTracker) -> None:
        replies = reply_tracker.get_all_replies()
        assert replies == []

    def test_get_all_after_recording(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        replies = reply_tracker.get_all_replies()
        assert len(replies) == 2


class TestReplyTrackerFilteredViews:
    def test_positive_replies(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        positive = reply_tracker.get_positive_replies()
        assert len(positive) == 1

    def test_negative_replies(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "negative")
        reply_tracker.record_reply("company_2", "positive")
        negative = reply_tracker.get_negative_replies()
        assert len(negative) == 1

    def test_bounces(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "bounce")
        reply_tracker.record_reply("company_2", "positive")
        bounces = reply_tracker.get_bounces()
        assert len(bounces) == 1

    def test_auto_replies(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "auto_reply")
        auto = reply_tracker.get_auto_replies()
        assert len(auto) == 1

    def test_no_response(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "no_response")
        no_response = reply_tracker.get_no_response()
        assert len(no_response) == 1


class TestReplyTrackerRates:
    def test_reply_rate_empty(self, reply_tracker: ReplyTracker) -> None:
        rate = reply_tracker.get_reply_rate()
        assert rate == 0.0

    def test_reply_rate_calculated(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "no_response")
        rate = reply_tracker.get_reply_rate()
        assert rate == 50.0

    def test_positive_reply_rate_empty(self, reply_tracker: ReplyTracker) -> None:
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == 0.0

    def test_positive_reply_rate_calculated(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        reply_tracker.record_reply("company_3", "no_response")
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == pytest.approx(33.33, rel=0.01)


class TestReplyTrackerAvgReplyTime:
    def test_avg_reply_time_none(self, reply_tracker: ReplyTracker) -> None:
        avg = reply_tracker.get_avg_reply_time()
        assert avg is None

    def test_avg_reply_time_calculated(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive", reply_time_seconds=100.0)
        reply_tracker.record_reply("company_2", "positive", reply_time_seconds=200.0)
        avg = reply_tracker.get_avg_reply_time()
        assert avg == 150.0


class TestReplyTrackerCounts:
    def test_reply_type_counts(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "positive")
        reply_tracker.record_reply("company_3", "negative")
        counts = reply_tracker.get_reply_type_counts()
        assert counts["positive"] == 2
        assert counts["negative"] == 1


class TestReplyTrackerByConnector:
    def test_replies_by_connector(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive", source="linkedin")
        reply_tracker.record_reply("company_2", "negative", source="email")
        reply_tracker.record_reply("company_3", "positive", source="linkedin")
        linkedin_replies = reply_tracker.get_replies_by_connector("linkedin")
        assert len(linkedin_replies) == 2
