# CONNECTOR HEALTH — Beacon AI

**Audit Date:** 2026-08-08

---

## Signal Source Connectors

| Connector | Enabled | Healthy | Success Rate | Errors | Status |
|-----------|---------|---------|--------------|--------|--------|
| hacker_news | Yes | Yes | 87.2% | 5 | WARNING |
| rss | Yes | Yes | 81.5% | 5 | WARNING |
| devto | Yes | Yes | 100% | 0 | PASS |
| github_trending | Yes | Yes | 100% | 0 | PASS |
| product_hunt | Yes | Yes | 100% | 0 | PASS |
| reddit | Yes | No | 21.4% | 22 | FAILED |
| sec_edgar | Yes | No | 21.4% | 11 | FAILED |
| indie_hackers | Yes | No | 0% | 18 | FAILED |
| yc | Yes | No | 0% | 0 | IDLE |
| google_play | Yes | No | 0% | 0 | IDLE |
| app_store | Yes | No | 0% | 0 | IDLE |

**Disabled Connectors (Not Configured):**

| Connector | Status |
|-----------|--------|
| wappalyzer | Idle (reserved) |
| people_data_labs | Idle (reserved) |
| linkedin | Idle (reserved) |
| hunter | Idle (reserved) |
| google_maps | Idle (reserved) |
| crunchbase | Idle (reserved) |
| clearbit | Idle (reserved) |
| builtwith | Idle (reserved) |
| apollo | Idle (reserved) |

---

## Source Health Monitor

| Source | Status | Consecutive Failures | Avg Latency |
|--------|--------|---------------------|-------------|
| devto | HEALTHY | 0 | 2,168 ms |
| github_trending | HEALTHY | 0 | 5,997 ms |
| product_hunt | HEALTHY | 0 | 119,421 ms |
| rss | HEALTHY | 0 | 11,812 ms |
| hacker_news | HEALTHY | 0 | 132,303 ms |
| reddit | HEALTHY | 0 | 29,851 ms |
| sec_edgar | HEALTHY | 0 | 11,342 ms |
| indie_hackers | DOWN | 118 | N/A |

---

## Failure Analysis

### Reddit (FAILED)
- **Error:** `429 Too Many Requests` from `api.pullpush.io`
- **Cause:** Rate limiting by Reddit API
- **Impact:** Cannot collect Reddit signals
- **Fix:** Implement rate limiting, use Reddit OAuth API, or reduce collection frequency

### SEC EDGAR (FAILED)
- **Error:** `Feed URL returned HTML instead of RSS/Atom`
- **Cause:** SEC changed their page structure, URL no longer returns RSS
- **Impact:** Cannot collect SEC filing signals
- **Fix:** Update SEC EDGAR feed URL to correct RSS endpoint

### Indie Hackers (FAILED)
- **Error:** `No collector registered for source 'indie_hackers'`
- **Cause:** Collector module not implemented or not registered
- **Impact:** 118 consecutive failures
- **Fix:** Implement Indie Hackers collector or disable the connector

### Hacker News (WARNING)
- **Error:** `No collector registered for source 'hacker_news'`
- **Note:** Connector shows healthy but has registration issues
- **Impact:** May not be collecting data properly despite showing healthy

### RSS (WARNING)
- **Error:** `No collector registered for source 'rss'`
- **Note:** Same registration issue as hacker_news
- **Impact:** RSS collection may be degraded

---

## Connector Platform (OCP v1)

### Architecture Issues

1. **No concrete connector implementations** — The platform defines the infrastructure (ABC, registry, manager, router) but has no real connector classes. Only `NullConnector` for testing exists.

2. **ConnectorHealthEngine is dead code** — Sophisticated health classification exists but is never called by the runtime pipeline.

3. **In-memory-only state** — Deduplication, stats, and history are all lost on restart.

4. **Sequential execution only** — `max_concurrency` config exists but parallel execution is not implemented.

5. **Single-route architecture** — All events route to `live_opportunity_discovery` regardless of type.

---

## Summary

| Category | Count |
|----------|-------|
| Total Connectors | 20 |
| Enabled | 11 |
| Healthy | 5 |
| Degraded | 2 |
| Failed | 3 |
| Idle | 8 (disabled/not configured) |

**Overall Connector Health: 45% (DEGRADED)**

**Critical Issues:**
1. Reddit blocked by rate limiting
2. SEC EDGAR feed URL broken
3. Indie Hackers collector not registered
4. No concrete connector implementations in OCP
5. 8+ connectors disabled with no configuration
