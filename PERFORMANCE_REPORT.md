# PERFORMANCE REPORT — Beacon AI

**Audit Date:** 2026-08-08

---

## Database Performance

### Database Size

| Metric | Value | Status |
|--------|-------|--------|
| Total Size | 1,605 MB | WARNING (large for 203 leads) |
| Largest Table | revenue_replays (116 MB) | WARNING |

### Top 10 Tables by Size

| Table | Size | Rows | Status |
|-------|------|------|--------|
| revenue_replays | 116 MB | 0 | WARNING (bloat) |
| account_journeys | 97 MB | 0 | WARNING (bloat) |
| revenue_memory | 95 MB | 0 | WARNING (bloat) |
| revenue_operation_snapshots | 82 MB | 0 | WARNING (bloat) |
| aip_account_profiles | 79 MB | 0 | WARNING (bloat) |
| igf_resolution_runs | 49 MB | 0 | WARNING (bloat) |
| rdi_snapshots | 46 MB | 0 | WARNING (bloat) |
| website_profiles | 43 MB | 39,185 | PASS |
| igf_identity_evidence | 37 MB | 0 | WARNING (bloat) |
| aip_field_sources | 34 MB | 0 | WARNING (bloat) |

**Observation:** Many large tables have 0 rows but significant size, suggesting:
- Table bloat from deleted records
- Large index overhead
- JSONB column storage

### Index Statistics

| Metric | Value | Status |
|--------|-------|--------|
| Total Indexes | 1,110 | WARNING (high for 459 tables) |
| Avg Indexes per Table | 2.4 | WARNING |
| Unused Indexes | All showing 0 scans | WARNING |

**Recommendation:** Run `ANALYZE;` to refresh statistics. Consider dropping unused indexes.

---

## Connector Performance

### Latency by Source

| Source | Avg Latency | Status |
|--------|-------------|--------|
| devto | 2,168 ms | PASS |
| github_trending | 5,997 ms | PASS |
| sec_edgar | 11,342 ms | WARNING |
| rss | 11,812 ms | WARNING |
| hacker_news | 132,303 ms | CRITICAL (2.2 minutes) |
| product_hunt | 119,421 ms | CRITICAL (2.0 minutes) |
| reddit | 29,851 ms | WARNING |

**Critical:** Hacker News and ProductHunt collectors take 2+ minutes per run.

### Collection Volume (Last Run)

| Source | Records Today | Records Total |
|--------|---------------|---------------|
| product_hunt | 318 | 798 |
| sec_edgar | 74 | 74 |
| hacker_news | 69 | 123 |
| rss | 50 | 117 |
| github_trending | 1 | 2 |
| devto | 0 | 0 |
| reddit | 0 | 0 |

---

## Ecommerce Detector Performance

| Metric | Value | Status |
|--------|-------|--------|
| HTTP Timeout | 15 seconds | PASS |
| User-Agent | Static, incomplete | WARNING |
| Error Handling | Silent (except: pass) | CRITICAL |
| Cloudflare Handling | None | CRITICAL |

**Root Cause of Performance Issues:**
1. The `EcommerceDetector` silently swallows all HTTP errors
2. No retry logic for failed requests
3. No connection pooling
4. Static User-Agent triggers bot detection
5. No headless browser for JavaScript-rendered sites

---

## API Performance

| Metric | Value | Status |
|--------|-------|--------|
| Total Routes | 584 | PASS |
| API Routes | 580 | PASS |
| Health Check | /api/v1/health | PASS |
| Auth | None (unauthenticated) | WARNING |
| Rate Limiting | Not configured | WARNING |

---

## Celery Performance

| Metric | Value | Status |
|--------|-------|--------|
| Beat Schedule | 80+ tasks | PASS |
| Broker | Redis (not running) | CRITICAL |
| Worker Status | Not running | CRITICAL |
| Task Serialization | JSON | PASS |

---

## Memory Considerations

| Component | Estimated Memory | Status |
|-----------|-----------------|--------|
| PostgreSQL | ~200 MB | PASS |
| Python (API) | ~100 MB | PASS |
| Python (Worker) | ~150 MB | PASS |
| Redis | ~50 MB | PASS (when running) |
| Total | ~500 MB | PASS |

---

## Slow Queries Detected

No slow query log analysis was possible (no query logging enabled). However, based on table sizes:

1. **revenue_replays** (116 MB, 0 rows) — Potential table bloat
2. **account_journeys** (97 MB, 0 rows) — Potential table bloat
3. **website_profiles** (43 MB, 39,185 rows) — Largest active table

**Recommendation:** Enable `log_min_duration_statement` in PostgreSQL for query profiling.

---

## Optimization Suggestions

### Critical

1. **Fix Redis connection** — Without Redis, all async tasks fail
2. **Fix HTTP client** — Add proper User-Agent, retry logic, connection pooling
3. **Add logging to EcommerceDetector** — Silent failures hide performance issues

### High

4. **Run VACUUM ANALYZE** — Reclaim space from bloat, update statistics
5. **Review 1,110 indexes** — Consider dropping unused indexes
6. **Enable query logging** — Profile slow queries
7. **Add API rate limiting** — Prevent abuse

### Medium

8. **Implement connection pooling** — For HTTP requests to external sites
9. **Add caching** — For repeated API calls
10. **Profile Celery task execution** — Identify slow tasks

### Low

11. **Compress JSONB columns** — For large text fields
12. **Partition large tables** — If growth continues
13. **Add monitoring** — Prometheus/Grafana for production metrics
