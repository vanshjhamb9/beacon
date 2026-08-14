# Operations Guide — Beacon Production

## Quality gates (local)

```bash
make ci
```

Or individually: `make compile`, `make lint`, `make test`, `make e2e`, `make security`, `make recovery`.

## Deploy checklist

1. `alembic upgrade head` (through `20260723_0022`)
2. Confirm Redis + Postgres healthy
3. Start API + worker (beat enabled)
4. Verify `/api/v1/production-validation/health` returns PASS/WARNING (not FAIL blockers)
5. Confirm OAuth status before production sends
6. Open `/production-health` and `/revenue-dashboard`

## Performance budgets

- Production validation: 100 evals &lt; 2s
- Mixed load smoke: 200 PRV + 100 LRE &lt; 5s
- Dashboard refresh interval: 30s

## Testing guide

```bash
pytest tests/production_validation -q
pytest tests/e2e -q
pytest tests/security -q
pytest tests/recovery -q
pytest tests/performance -q
```
