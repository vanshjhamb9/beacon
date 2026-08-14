"""Tests for MeetingTracker."""

from __future__ import annotations

import pytest

from validation_engine import MEETING_TYPES
from validation_engine.meeting_tracker import MeetingTracker


class TestMeetingTrackerRecordMeeting:
    def test_record_valid_meeting(self, meeting_tracker: MeetingTracker) -> None:
        event = meeting_tracker.record_meeting("company_1", "scheduled")
        assert event.company_id == "company_1"
        assert event.meeting_type == "scheduled"

    def test_record_invalid_meeting_type_raises(self, meeting_tracker: MeetingTracker) -> None:
        with pytest.raises(ValueError, match="Invalid meeting type"):
            meeting_tracker.record_meeting("company_1", "invalid")

    def test_record_all_meeting_types(self, meeting_tracker: MeetingTracker) -> None:
        for meeting_type in MEETING_TYPES:
            event = meeting_tracker.record_meeting("company_1", meeting_type)
            assert event.meeting_type == meeting_type

    def test_record_with_duration(self, meeting_tracker: MeetingTracker) -> None:
        event = meeting_tracker.record_meeting("company_1", "completed", duration_minutes=45.0)
        assert event.duration_minutes == 45.0

    def test_record_with_notes(self, meeting_tracker: MeetingTracker) -> None:
        event = meeting_tracker.record_meeting("company_1", "completed", notes="Discussed pricing")
        assert event.notes == "Discussed pricing"

    def test_record_with_next_action(self, meeting_tracker: MeetingTracker) -> None:
        event = meeting_tracker.record_meeting(
            "company_1", "completed", next_action="Send proposal"
        )
        assert event.next_action == "Send proposal"

    def test_record_with_calendar_link(self, meeting_tracker: MeetingTracker) -> None:
        event = meeting_tracker.record_meeting("company_1", "scheduled", calendar_link="https://cal.com/abc")
        assert event.calendar_link == "https://cal.com/abc"


class TestMeetingTrackerGetMeetingsForCompany:
    def test_get_empty_meetings(self, meeting_tracker: MeetingTracker) -> None:
        meetings = meeting_tracker.get_meetings_for_company("nonexistent")
        assert meetings == []

    def test_get_meetings_filtered(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "scheduled")
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "scheduled")
        meetings = meeting_tracker.get_meetings_for_company("company_1")
        assert len(meetings) == 2


class TestMeetingTrackerFilteredViews:
    def test_completed_meetings(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "cancelled")
        completed = meeting_tracker.get_completed_meetings()
        assert len(completed) == 1

    def test_cancelled_meetings(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "cancelled")
        cancelled = meeting_tracker.get_cancelled_meetings()
        assert len(cancelled) == 1

    def test_no_shows(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "no_show")
        no_shows = meeting_tracker.get_no_shows()
        assert len(no_shows) == 1

    def test_scheduled_meetings(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "scheduled")
        scheduled = meeting_tracker.get_scheduled_meetings()
        assert len(scheduled) == 1


class TestMeetingTrackerRates:
    def test_meeting_rate_empty(self, meeting_tracker: MeetingTracker) -> None:
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 0.0

    def test_meeting_rate_calculated(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "cancelled")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 50.0

    def test_no_show_rate_empty(self, meeting_tracker: MeetingTracker) -> None:
        rate = meeting_tracker.get_no_show_rate()
        assert rate == 0.0

    def test_no_show_rate_calculated(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "no_show")
        meeting_tracker.record_meeting("company_3", "no_show")
        rate = meeting_tracker.get_no_show_rate()
        assert rate == pytest.approx(66.67, rel=0.01)


class TestMeetingTrackerAvgDuration:
    def test_avg_duration_none(self, meeting_tracker: MeetingTracker) -> None:
        avg = meeting_tracker.get_avg_duration()
        assert avg is None

    def test_avg_duration_calculated(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed", duration_minutes=30.0)
        meeting_tracker.record_meeting("company_2", "completed", duration_minutes=60.0)
        avg = meeting_tracker.get_avg_duration()
        assert avg == 45.0


class TestMeetingTrackerCounts:
    def test_meeting_type_counts(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "completed")
        meeting_tracker.record_meeting("company_3", "cancelled")
        counts = meeting_tracker.get_meeting_type_counts()
        assert counts["completed"] == 2
        assert counts["cancelled"] == 1
