"""
Test Script for Outreach Automation
Verifies all components work together.
"""
import sys
from pathlib import Path

# Add project root and packages to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages"))


def test_rate_limiter():
    """Test rate limiter."""
    from packages.outreach_automation.rate_limiter import RateLimiter

    limiter = RateLimiter()

    # Test can_send - may be False if outside active hours
    result = limiter.can_send("reddit")
    print(f"  can_send(reddit): {result}")
    assert limiter.can_send("invalid") == False

    # Test get_stats
    stats = limiter.get_stats()
    assert "reddit" in stats
    assert stats["reddit"]["sent_today"] == 0

    print("[PASS] Rate limiter test passed")


def test_queue():
    """Test outreach queue."""
    from packages.outreach_automation.queue import OutreachQueue, QueueStatus

    queue = OutreachQueue(queue_file=Path("test_queue.json"))

    # Test enqueue
    item = queue.enqueue(
        channel="reddit",
        recipient="test_user",
        body="Test message",
        subject="Test",
    )
    assert item.status == QueueStatus.PENDING

    # Test get_stats
    stats = queue.get_stats()
    assert stats["pending"] >= 1

    # Cleanup
    queue.cancel(item.id)
    print("[PASS] Queue test passed")


def test_reply_tracker():
    """Test reply tracker."""
    from packages.outreach_automation.reply_tracker import ReplyTracker, ReplyChannel

    tracker = ReplyTracker(tracker_file=Path("test_replies.json"))

    # Test record_reply
    reply = tracker.record_reply(
        opportunity_id="test_opp",
        channel=ReplyChannel.REDDIT,
        original_message_id="test_msg",
        reply_content="Interested!",
        reply_from="test_user",
    )
    assert reply.status.value == "replied"

    # Test get_pending_replies
    pending = tracker.get_pending_replies()
    assert len(pending) >= 1

    # Cleanup
    tracker.replies.clear()
    tracker._save_replies()
    print("[PASS] Reply tracker test passed")


def test_ai_drafter():
    """Test AI reply drafter."""
    from packages.outreach_automation.ai_reply_drafter import AIReplyDrafter

    drafter = AIReplyDrafter()

    # Test draft_reply
    result = drafter.draft_reply(
        "I'm interested in your services. Tell me more!",
        {"requirement": "SaaS MVP development"},
    )
    assert "reply" in result
    assert "category" in result

    # Test sentiment analysis
    sentiment = drafter.analyze_sentiment("I'm interested in your services!")
    assert sentiment["sentiment"] == "positive"

    print("[PASS] AI drafter test passed")


def test_reddit_provider():
    """Test Reddit provider."""
    from packages.communication_gateway.reddit.reddit import RedditProvider, SandboxRedditProvider
    import asyncio

    # Test sandbox provider
    sandbox = SandboxRedditProvider()
    from packages.communication_gateway.models.types import OutboundMessage, ChannelType, ProviderName

    message = OutboundMessage(
        channel=ChannelType.REDDIT,
        provider=ProviderName.SANDBOX_REDDIT,
        to_address="test_user",
        body_text="Test message",
    )

    # sandbox.send is async, so we need to run it in an event loop
    result = asyncio.run(sandbox.send(message))
    assert result.state.value == "sent"
    assert result.sandbox == True

    print("[PASS] Reddit provider test passed")


def test_smtp_provider():
    """Test SMTP provider."""
    from packages.communication_gateway.email.smtp import SMTPEmailProvider, SandboxSMTPEmailProvider

    # Test sandbox provider
    sandbox = SandboxSMTPEmailProvider()
    from packages.communication_gateway.models.types import OutboundMessage, ChannelType, ProviderName

    message = OutboundMessage(
        channel=ChannelType.EMAIL,
        provider=ProviderName.SANDBOX_EMAIL,
        to_address="test@example.com",
        subject="Test",
        body_text="Test message",
    )

    result = sandbox.send(message)
    assert result.state.value == "sent"
    assert result.sandbox == True

    print("[PASS] SMTP provider test passed")


def test_scheduler():
    """Test outreach scheduler."""
    from packages.outreach_automation.scheduler import OutreachScheduler

    scheduler = OutreachScheduler()

    # Test schedule_outreach
    item = scheduler.schedule_outreach(
        channel="reddit",
        recipient="test_user",
        body="Test message",
        immediate=True,
    )
    assert item is not None

    # Test get_stats
    stats = scheduler.get_stats()
    assert "queue" in stats

    # Cleanup
    scheduler.queue.cancel(item.id)
    print("[PASS] Scheduler test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("OUTREACH AUTOMATION TEST SUITE")
    print("=" * 60)

    tests = [
        test_rate_limiter,
        test_queue,
        test_reply_tracker,
        test_ai_drafter,
        test_reddit_provider,
        test_smtp_provider,
        test_scheduler,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
