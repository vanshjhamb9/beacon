# Production Runbook (Beacon)

## Daily founder loop

1. Open Home → check **What should I do now?**
2. Open **Revenue** for pipeline / replies / meetings
3. Open **Production Health** for FAIL/WARNING components
4. Clear **Approval Center** before any send
5. Reply in **Inbox**; meetings → proposal center

## Incident response

| Symptom | First action |
|---|---|
| OAuth expired | Refresh OAuth; block sends until healthy |
| Bounce spike | Stop campaigns; re-verify emails |
| Worker offline | Restart Celery worker+beat |
| Queue blocked | Drain outgoing/retry; check provider quotas |
| Duplicate sends | Inspect idempotency keys; pause campaign |
| Migration drift | `alembic upgrade head` |

## Recovery

- Prefer append-only replay (webhooks, LRE tracking, PRV snapshots)
- Never delete audit rows
- Re-run `production_validation.refresh_report` after infra recovery

## Monitoring

- `/production-validation/health` every 30s (UI)
- Celery beat: production validation @120s
- Existing `/system-health` and `/diagnostics` remain available
