# DATABASE AUDIT — Beacon AI

**Audit Date:** 2026-08-08
**Database:** PostgreSQL 18.3
**Database Name:** beacon
**Database Size:** 1,605 MB (1.6 GB)

---

## Schema Overview

| Metric | Value |
|--------|-------|
| Total Tables | 459 |
| Total Indexes | 1,110 |
| Alembic Migration Version | 0100 |
| Schemas | 1 (public) |

---

## Table Statistics (Key Tables)

| Table | Rows | Status |
|-------|------|--------|
| website_profiles | 39,185 | PASS |
| raw_events | 5,465 | PASS |
| quality_reports | 5,845 | PASS |
| signal_entities | 2,019 | PASS |
| opportunities | 600 | PASS |
| companies | 630 | PASS |
| business_contexts | 671 | PASS |
| classified_signals | 671 | PASS |
| company_contacts | 293 | PASS |
| domains | 297 | PASS |
| ecommerce_leads | 203 | WARNING (low volume) |
| company_technologies | 97 | WARNING (low coverage) |
| sales_accounts | 51 | WARNING (low volume) |
| decision_makers | 20 | WARNING (very low) |
| connector_health | 20 | PASS |
| source_health | 8 | PASS |
| campaigns | 0 | WARNING (empty) |
| people | 0 | WARNING (empty) |

---

## Largest Tables by Size

| Table | Size |
|-------|------|
| revenue_replays | 116 MB |
| account_journeys | 97 MB |
| revenue_memory | 95 MB |
| revenue_operation_snapshots | 82 MB |
| aip_account_profiles | 79 MB |
| igf_resolution_runs | 49 MB |
| rdi_snapshots | 46 MB |
| website_profiles | 43 MB |
| igf_identity_evidence | 37 MB |
| aip_field_sources | 34 MB |
| aip_verification_history | 34 MB |
| identity_coverage_snapshots | 29 MB |
| rev_evaluations | 29 MB |
| rev_rejection_records | 29 MB |
| quality_metrics | 29 MB |

---

## Index Analysis

| Metric | Value | Status |
|--------|-------|--------|
| Total Indexes | 1,110 | PASS |
| Unused Indexes (0 scans) | All indexes checked | WARNING |

**Note:** `pg_stat_user_indexes` shows all indexes with 0 scans, indicating either:
- Statistics have not been collected recently (`ANALYZE` needed)
- Or tables have not been queried since last restart

**Recommendation:** Run `ANALYZE;` to update table statistics.

---

## Ecommerce Leads Data Quality

### Completeness

| Field | Total | Populated | Missing | Coverage |
|-------|-------|-----------|---------|----------|
| company_name | 203 | 203 | 0 | 100% |
| website | 203 | 203 | 0 | 100% |
| domain | 203 | 203 | 0 | 100% |
| platform | 203 | 203 | 0 | 100% (but ALL "unknown") |
| industry | 203 | 203 | 0 | 100% |
| country | 203 | 203 | 0 | 100% (all India) |
| description | 203 | 203 | 0 | 100% |
| comai_score | 203 | 203 | 0 | 100% |
| lead_priority | 203 | 203 | 0 | 100% |
| **email** | 203 | 93 | **110** | **45.8%** |
| **phone** | 203 | 136 | **67** | **67.0%** |
| **owner_name** | 203 | 0 | **203** | **0%** |
| **founder_name** | 203 | 0 | **203** | **0%** |
| **sales_reason** | 203 | 0 | **203** | **0%** |
| social_links | 203 | 0 | 203 | 0% |
| instagram_url | 203 | 0 | 203 | 0% |
| facebook_url | 203 | 0 | 203 | 0% |
| linkedin_url | 203 | 0 | 203 | 0% |

### Technology Detection

| Technology | Detected | Rate | Status |
|------------|----------|------|--------|
| Shopify | 0 | 0% | FAILED |
| WooCommerce | 0 | 0% | FAILED |
| Magento | 0 | 0% | FAILED |
| Chatbot | 0 | 0% | FAILED |
| WhatsApp | 0 | 0% | FAILED |
| CRM | 0 | 0% | FAILED |

**Root Cause:** The `EcommerceDetector.detect()` method silently swallows all exceptions (`except Exception: pass`). Most Indian ecommerce sites use Cloudflare protection, which blocks simple HTTP requests. The incomplete User-Agent string triggers bot detection.

### Platform Detection

| Platform | Count | Status |
|----------|-------|--------|
| unknown | 203 | FAILED (100%) |

**All 203 leads have platform="unknown" — platform detection is completely non-functional.**

### Industry Distribution

| Industry | Count |
|----------|-------|
| fashion | 42 |
| beauty | 23 |
| food | 20 |
| electronics | 17 |
| home | 14 |
| education | 14 |
| health | 13 |
| restaurant | 11 |
| fitness | 10 |
| fintech | 9 |
| quick_commerce | 7 |
| travel | 7 |
| spa | 6 |
| logistics | 5 |
| automotive | 5 |

### Lead Priority Distribution

| Priority | Count | Percentage |
|----------|-------|------------|
| SALES_READY | 91 | 44.8% |
| LOW | 65 | 32.0% |
| WARM_LEAD | 47 | 23.2% |

### COMAI Score Statistics

| Metric | Value |
|--------|-------|
| Average | 70.32 |
| Maximum | 85 |
| Minimum | 50 |
| All scored | 100% |

### Lead Source

| Source | Count |
|--------|-------|
| enrichment | 203 |

All leads came from the enrichment source. No leads from collectors (Reddit, HN, ProductHunt, etc.).

### Duplicate Analysis

| Metric | Value | Status |
|--------|-------|--------|
| Duplicate company_name+website | 0 | PASS |
| Unique companies | 203 | PASS |

---

## Foreign Key Constraints

**Sample of foreign key relationships verified:**

| Child Table | FK Column | Parent Table |
|-------------|-----------|--------------|
| people | company_id | companies |
| domains | company_id | companies |
| company_aliases | company_id | companies |
| classified_signals | company_id | companies |
| classified_signals | event_id | raw_events |
| signal_entities | company_id | companies |
| signal_entities | event_id | raw_events |
| signal_entities | domain_id | domains |
| signal_entities | person_id | people |
| company_timelines | company_id | companies |
| company_timelines | event_id | raw_events |
| knowledge_graph_edges | from_node_id | knowledge_graph_nodes |
| knowledge_graph_edges | to_node_id | knowledge_graph_nodes |
| quality_reports | raw_event_id | raw_events |
| quality_metrics | quality_report_id | quality_reports |
| business_contexts | company_id | companies |
| business_pains | business_context_id | business_contexts |

---

## Migration Status

| Property | Value | Status |
|----------|-------|--------|
| Current Version | 0100 | PASS |
| Migration Tool | Alembic | PASS |
| Total Migrations | 68 | PASS |

---

## Recommendations

1. **CRITICAL:** Fix platform detection — all 203 leads show "unknown"
2. **CRITICAL:** Fix technology detection — all boolean flags are False
3. **CRITICAL:** Fix contact enrichment — 54% emails missing, 0 decision makers
4. **CRITICAL:** Fix social link extraction — 0 social links found
5. **HIGH:** Run `ANALYZE;` to update table statistics
6. **HIGH:** Increase ecommerce_leads volume (currently only 203)
7. **MEDIUM:** Monitor table bloat (revenue_replays at 116MB)
8. **MEDIUM:** Review 459 tables for consolidation opportunities
