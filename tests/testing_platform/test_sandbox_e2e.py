from testing_platform import SandboxPipelineE2E
from testing_platform.services.platform import TestingPlatformService as QAPlatform


def test_sandbox_pipeline_e2e_passes() -> None:
    result = SandboxPipelineE2E().run()
    assert result.mode == "sandbox"
    assert result.passed, [step.model_dump() for step in result.steps if not step.passed]
    names = [step.name for step in result.steps]
    assert "sales_package" in names
    assert "campaign_plan_and_approve" in names
    assert "sandbox_send_reply_stop" in names
    assert "sandbox_meeting" in names
    assert "conversation_center" in names
    assert "outcome_recorded" in names


def test_system_health_builder() -> None:
    report = QAPlatform().system_health(
        {
            "database": {"status": "ok", "score": 100, "latency_ms": 2},
            "redis": {"status": "ok", "score": 100, "latency_ms": 1},
            "communication": {"status": "ok", "score": 100},
        },
        mode="sandbox",
    )
    assert report.overall_score >= 90
    assert report.status == "ok"
