from worker.celery_app import celery_app


def test_live_revenue_worker_registered() -> None:
    assert "worker.live_revenue_tasks" in (celery_app.conf.include or [])
    schedule = celery_app.conf.beat_schedule or {}
    assert "refresh-live-revenue-command-center" in schedule
    assert schedule["refresh-live-revenue-command-center"]["task"] == "live_revenue.refresh_command_center"


def test_live_revenue_task_importable() -> None:
    from worker.live_revenue_tasks import refresh_command_center, refresh_company

    assert refresh_command_center.name == "live_revenue.refresh_command_center"
    assert refresh_company.name == "live_revenue.refresh_company"


def test_composes_sales_intelligence_reply_engine() -> None:
    from live_revenue_execution import LiveRevenueExecutionService

    result = LiveRevenueExecutionService().classify_reply("Not interested, remove me")
    assert result.classification.value == "Not Interested"
