from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "beacon_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "worker.tasks",
        "worker.quality_tasks",
        "worker.intelligence_tasks",
        "worker.context_tasks",
        "worker.opportunity_tasks",
        "worker.improvement_tasks",
        "worker.revenue_tasks",
        "worker.enrichment_tasks",
        "worker.verification_tasks",
        "worker.decision_tasks",
        "worker.copilot_tasks",
        "worker.campaign_tasks",
        "worker.communication_tasks",
        "worker.target_account_tasks",
        "worker.revenue_hunter_tasks",
        "worker.founder_os_tasks",
        "worker.sales_intelligence_tasks",
        "worker.live_revenue_tasks",
        "worker.production_validation_tasks",
        "worker.autonomous_sales_agent_tasks",
        "worker.revenue_operations_tasks",
        "worker.account_journey_tasks",
        "worker.client_execution_tasks",
        "worker.global_opportunity_acquisition_tasks",
        "worker.account_intelligence_tasks",
        "worker.revenue_optimization_tasks",
        "worker.acquisition_tasks",
        "worker.runtime_ops_tasks",
        "worker.sales_readiness_tasks",
        "worker.revenue_data_recovery_tasks",
        "worker.revenue_quality_recovery_tasks",
        "worker.beacon_alpha_tasks",
        "worker.ground_truth_tasks",
        "worker.company_resolution_tasks",
        "worker.entity_resolution_tasks",
        "worker.company_intelligence_tasks",
        "worker.revenue_execution_validation_tasks",
        "worker.identity_coverage_tasks",
        "worker.revenue_data_acquisition_tasks",
        "worker.dataset_unlock_tasks",
        "worker.operations_center_tasks",
        "worker.intelligence_center_tasks",
        "worker.ecommerce_leads_tasks",
        "worker.revenue_intelligence_tasks",
        "worker.sales_account_tasks",
        "worker.lead_discovery_tasks",
        "worker.buying_event_tasks",
        "worker.buying_event_enrichment_tasks",
        "worker.mega_extraction_tasks",
        "worker.b2b_partner_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "collect-reddit": {
            "task": "collectors.collect_source",
            "schedule": settings.reddit_collector.interval_seconds,
            "args": ("reddit",),
        },
        "collect-rss": {
            "task": "collectors.collect_source",
            "schedule": settings.rss_collector.interval_seconds,
            "args": ("rss",),
        },
        "collect-hacker-news": {
            "task": "collectors.collect_source",
            "schedule": settings.hacker_news_collector.interval_seconds,
            "args": ("hacker_news",),
        },
        "collect-product-hunt": {
            "task": "collectors.collect_source",
            "schedule": settings.product_hunt_collector.interval_seconds,
            "args": ("product_hunt",),
        },
        "collect-github-trending": {
            "task": "collectors.collect_source",
            "schedule": settings.github_trending_collector.interval_seconds,
            "args": ("github_trending",),
        },
        "collect-sec-edgar": {
            "task": "collectors.collect_source",
            "schedule": settings.sec_edgar_collector.interval_seconds,
            "args": ("sec_edgar",),
        },
        "collect-devto": {
            "task": "collectors.collect_source",
            "schedule": settings.devto_collector.interval_seconds,
            "args": ("devto",),
        },
        "persist-raw-events": {
            "task": "collectors.persist_raw_events",
            "schedule": 10,
        },
        "monitor-acquisition-connectors": {
            "task": "acquisition.monitor_connectors",
            "schedule": 120,
        },
        "generate-acquisition-daily-report": {
            "task": "acquisition.generate_daily_report",
            "schedule": 86_400,
        },
        "process-quality-events": {
            "task": "quality.process_raw_events",
            "schedule": 15,
        },
        "process-intelligence-events": {
            "task": "intelligence.process_raw_events",
            "schedule": 30,
        },
        "process-context-signals": {
            "task": "context.process_signals",
            "schedule": 45,
        },
        "process-opportunities": {
            "task": "opportunity.process_companies",
            "schedule": 60,
        },
        "process-revenue-opportunities": {
            "task": "revenue.process_opportunities",
            "schedule": 75,
        },
        "process-lead-enrichment": {
            "task": "enrichment.process_opportunities",
            "schedule": 90,
        },
        "process-data-verification": {
            "task": "verification.process_enrichments",
            "schedule": 105,
        },
        "process-decision-discovery": {
            "task": "decision.process_companies",
            "schedule": 120,
        },
        "process-target-accounts": {
            "task": "targets.process_accounts",
            "schedule": 128,
        },
        "process-sales-readiness": {
            "task": "sales_readiness.process_pending",
            "schedule": 130,
        },
        "process-revenue-data-recovery": {
            "task": "revenue_data_recovery.process_pending",
            "schedule": 125,
        },
        "process-revenue-quality": {
            "task": "revenue_quality.process_pending",
            "schedule": 127,
        },
        "process-beacon-alpha": {
            "task": "beacon_alpha.process_pending",
            "schedule": 129,
        },
        "process-ground-truth": {
            "task": "ground_truth.process_pending",
            "schedule": 131,
        },
        "process-company-intelligence": {
            "task": "company_intelligence.process_verified",
            "schedule": 120,
        },
        "process-revenue-execution-validation": {
            "task": "revenue_execution_validation.rebuild",
            "schedule": 180,
        },
        "daily-revenue-execution-report": {
            "task": "revenue_execution_validation.daily_report",
            "schedule": 86400,
        },
        "process-identity-coverage": {
            "task": "identity_coverage.process_pending",
            "schedule": 240,
        },
        "retry-identity-coverage": {
            "task": "identity_coverage.retry_missing",
            "schedule": 600,
        },
        "daily-identity-coverage-report": {
            "task": "identity_coverage.daily_report",
            "schedule": 86400,
        },
        "process-revenue-data-acquisition": {
            "task": "revenue_data_acquisition.process_pending",
            "schedule": 300,
        },
        "recover-rdap-contacts": {
            "task": "revenue_data_acquisition.recover_contacts",
            "schedule": 900,
        },
        "recover-rdap-decision-makers": {
            "task": "revenue_data_acquisition.recover_decision_makers",
            "schedule": 1200,
        },
        "daily-revenue-data-acquisition-report": {
            "task": "revenue_data_acquisition.daily_report",
            "schedule": 86400,
        },
        "odu-monitor-connectors": {
            "task": "operations.monitor_connectors",
            "schedule": 300,
        },
        "odu-recover-websites": {
            "task": "operations.recover_websites",
            "schedule": 900,
        },
        "odu-recover-contacts": {
            "task": "operations.recover_contacts",
            "schedule": 1200,
        },
        "odu-daily-audit": {
            "task": "operations.daily_audit",
            "schedule": 86400,
        },
        "daily-ground-truth-report": {
            "task": "ground_truth.daily_report",
            "schedule": 86400,
        },
        "daily-revenue-quality-kpi": {
            "task": "revenue_quality.daily_kpi",
            "schedule": 86400,
        },
        "daily-revenue-data-recovery": {
            "task": "revenue_data_recovery.daily_report",
            "schedule": 86400,
        },
        "process-revenue-hunter": {
            "task": "revenue_hunter.process_accounts",
            "schedule": 132,
        },
        "refresh-founder-os-brief": {
            "task": "founder_os.refresh_brief",
            "schedule": 300,
        },
        "process-sales-copilot": {
            "task": "copilot.process_packages",
            "schedule": 135,
        },
        "process-campaign-intelligence": {
            "task": "campaigns.process_pending",
            "schedule": 150,
        },
        "process-communication-queue": {
            "task": "communication.process_queue",
            "schedule": 20,
        },
        "sync-gmail-replies": {
            "task": "communication.sync_gmail_replies",
            "schedule": 60,
        },
        "refresh-sales-intelligence-from-replies": {
            "task": "sales_intelligence.refresh_from_replies",
            "schedule": 70,
        },
        "refresh-live-revenue-command-center": {
            "task": "live_revenue.refresh_command_center",
            "schedule": 90,
        },
        "refresh-production-validation": {
            "task": "production_validation.refresh_report",
            "schedule": 120,
        },
        "refresh-asa-work-queue": {
            "task": "autonomous_sales_agent.refresh_work_queue",
            "schedule": 180,
        },
        "refresh-asa-morning-brief": {
            "task": "autonomous_sales_agent.refresh_morning_brief",
            "schedule": 86_400,
        },
        "refresh-roc-dashboard": {
            "task": "revenue_operations.refresh_dashboard",
            "schedule": 120,
        },
        "refresh-roc-forecast": {
            "task": "revenue_operations.refresh_forecast",
            "schedule": 300,
        },
        "refresh-roc-alerts": {
            "task": "revenue_operations.refresh_alerts",
            "schedule": 60,
        },
        "roc-daily-learning": {
            "task": "revenue_operations.daily_learning",
            "schedule": 86_400,
        },
        "journey-refresh-accounts": {
            "task": "journey.refresh_accounts",
            "schedule": 180,
        },
        "journey-calculate-engagement": {
            "task": "journey.calculate_engagement",
            "schedule": 90,
        },
        "journey-plan-followups": {
            "task": "journey.plan_followups",
            "schedule": 120,
        },
        "journey-analytics-daily": {
            "task": "journey.analytics_daily",
            "schedule": 86_400,
        },
        "aep-refresh-health": {
            "task": "client_execution.refresh_health",
            "schedule": 180,
        },
        "aep-detect-upsells": {
            "task": "client_execution.detect_upsells",
            "schedule": 43_200,
        },
        "aep-refresh-dashboard": {
            "task": "client_execution.refresh_dashboard",
            "schedule": 300,
        },
        "goap-refresh-sources": {
            "task": "collector.refresh_sources",
            "schedule": 300,
        },
        "goap-score-sources": {
            "task": "collector.score_sources",
            "schedule": 600,
        },
        "goap-build-graph": {
            "task": "collector.build_graph",
            "schedule": 600,
        },
        "goap-update-benchmarks": {
            "task": "collector.update_benchmarks",
            "schedule": 3600,
        },
        "goap-detect-intent": {
            "task": "collector.detect_new_intent",
            "schedule": 300,
        },
        "goap-refresh-websites": {
            "task": "collector.refresh_websites",
            "schedule": 1800,
        },
        "goap-refresh-jobs": {
            "task": "collector.refresh_jobs",
            "schedule": 900,
        },
        "goap-refresh-reviews": {
            "task": "collector.refresh_reviews",
            "schedule": 1800,
        },
        "goap-refresh-funding": {
            "task": "collector.refresh_funding",
            "schedule": 1800,
        },
        "goap-daily-report": {
            "task": "collector.daily_report",
            "schedule": 86_400,
        },
        "aip-refresh-profiles": {
            "task": "account.refresh_profiles",
            "schedule": 300,
        },
        "aip-refresh-contacts": {
            "task": "account.refresh_contacts",
            "schedule": 600,
        },
        "aip-refresh-technology": {
            "task": "account.refresh_technology",
            "schedule": 900,
        },
        "aip-refresh-websites": {
            "task": "account.refresh_websites",
            "schedule": 900,
        },
        "aip-refresh-ai-scores": {
            "task": "account.refresh_ai_scores",
            "schedule": 600,
        },
        "aip-refresh-sales-scores": {
            "task": "account.refresh_sales_scores",
            "schedule": 600,
        },
        "aip-refresh-relationship-graph": {
            "task": "account.refresh_relationship_graph",
            "schedule": 900,
        },
        "aip-daily-validation": {
            "task": "account.daily_validation",
            "schedule": 86_400,
        },
        "roip-collect-metrics": {
            "task": "optimization.collect_metrics",
            "schedule": 300,
        },
        "roip-calculate-scores": {
            "task": "optimization.calculate_scores",
            "schedule": 600,
        },
        "roip-generate-benchmarks": {
            "task": "optimization.generate_benchmarks",
            "schedule": 900,
        },
        "roip-generate-recommendations": {
            "task": "optimization.generate_recommendations",
            "schedule": 900,
        },
        "roip-daily-report": {
            "task": "optimization.daily_report",
            "schedule": 86_400,
        },
        "roip-weekly-report": {
            "task": "optimization.weekly_report",
            "schedule": 604_800,
        },
        "refresh-communication-oauth": {
            "task": "communication.refresh_oauth",
            "schedule": 600,
        },
        "snapshot-communication-health": {
            "task": "communication.snapshot_health",
            "schedule": 180,
        },
        "evaluate-intelligence-improvement": {
            "task": "improvement.evaluate",
            "schedule": 300,
        },
        "runtime-ops-beat-heartbeat": {
            "task": "runtime_ops.beat_heartbeat",
            "schedule": 60,
        },
        "boc-refresh-metrics": {
            "task": "operations_center.refresh_metrics",
            "schedule": 60,
        },
        "boc-hourly-snapshot": {
            "task": "operations_center.hourly_snapshot",
            "schedule": 3600,
        },
        "bic-sync": {
            "task": "intelligence_center.sync",
            "schedule": 60,
        },
        "ecommerce-discovery": {
            "task": "ecommerce.discovery_worker",
            "schedule": 21600,  # Every 6 hours
            "kwargs": {"limit": 500, "country": "India"},
        },
        "sales-account-refresh": {
            "task": "sales_intelligence.refresh_accounts",
            "schedule": 14400,  # Every 4 hours
            "kwargs": {"limit": 500},
        },
        "revenue-intelligence-analyze": {
            "task": "revenue_intelligence.analyze_leads",
            "schedule": 14400,  # Every 4 hours
            "kwargs": {"limit": 500},
        },
        "detect-comai-events": {
            "task": "buying_events.detect_comai_events",
            "schedule": 900,  # Every 15 minutes
        },
        "detect-inowix-events": {
            "task": "buying_events.detect_inowix_events",
            "schedule": 900,  # Every 15 minutes
        },
        "detect-cyber-events": {
            "task": "buying_events.detect_cyber_events",
            "schedule": 900,  # Every 15 minutes — opportunistic RawEvent scan
        },
        "run-cyber-discovery-daily": {
            "task": "buying_events.run_cyber_discovery_daily",
            "schedule": crontab(hour=3, minute=30),  # 09:00 IST
        },
        "generate-outreach-queue": {
            "task": "buying_events.generate_outreach_queue",
            "schedule": 3600,  # Every hour
        },
        "collect-pain-signals": {
            "task": "collectors.collect_source",
            "schedule": 900,  # Every 15 minutes
            "args": ("pain_signals",),
        },
        "process-verified-buying-events": {
            "task": "buying_events.process_verified_buying_events",
            "schedule": 300,  # Every 5 minutes
        },
        "enrich-buying-event-contacts": {
            "task": "buying_events.enrich_contacts",
            "schedule": 600,  # Every 10 minutes
        },
        "mega-extract-leads": {
            "task": "lead_engine.mega_extract_with_enrichment",
            "schedule": 1200,  # Every 20 minutes
            "kwargs": {"limit": 40, "enrich_founders": True},
        },
        "discover-b2b-partners": {
            "task": "b2b_partners.discover_partners",
            "schedule": 21600,  # Every 6 hours
        },
    },
)
