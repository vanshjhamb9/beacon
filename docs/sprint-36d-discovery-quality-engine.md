# Sprint 36D — Discovery Quality Engine (DQE v1)

## Mission

Beacon currently discovers companies. It must now discover buying opportunities.

Sprint 36D builds a deterministic quality gate between data collection and Opportunity Intelligence. No company reaches Revenue Ready simply because it exists. Every company must prove it deserves attention.

## Pipeline Change

```
Collectors
    ↓
Opportunity Connector Platform
    ↓
Discovery Quality Engine (NEW)
    ↓
Live Opportunity Discovery
    ↓
Opportunity Intelligence
    ↓
Identity
    ↓
Revenue Ready
```

## Philosophy

- Discovery is not the same as opportunity.
- Beacon should reject far more companies than it accepts.
- The quality engine aggressively filters poor opportunities before they consume downstream resources.

## Core Principle

The engine never creates companies. The engine only decides:

- **ACCEPT**
- **REJECT**
- **HOLD**

Nothing else.

## Quality Gate Pipeline

Every opportunity must pass ALL gates:

1. Freshness
2. Buying Signal
3. Website Quality
4. Company Validation
5. Source Trust
6. Duplicate Check
7. Competitor Check
8. Activity Check
9. Industry Rules
10. Region Rules
11. AI Company Filter
12. ICP Filter

Fail any critical rule → **Reject.**

## Package Structure

```
packages/discovery_quality_engine/
├── __init__.py
├── quality_engine.py          # Core schemas, enums, domain models
├── freshness_engine.py        # Stale signal rejection
├── buying_signal_engine.py    # Buying signal validation
├── company_filter.py          # Company name validation
├── signal_filter.py           # Signal data integrity
├── duplicate_engine.py        # Domain/company/opportunity dedup
├── competitor_engine.py       # Competitor/client/demo filter
├── industry_filter.py         # Industry rules
├── region_filter.py           # Region rules
├── source_quality.py          # Source trust scoring
├── website_quality.py         # Website quality gate
├── company_age.py             # Company age filter
├── technology_filter.py       # AI company filter
├── activity_engine.py         # Recent activity validation
├── quality_dashboard.py       # Aggregated metrics
├── quality_metrics.py         # Metrics collection
├── quality_reports.py         # Daily/weekly reports
├── quality_scheduler.py       # Periodic evaluation triggers
├── dqe_orchestrator.py        # Full pipeline orchestrator
└── tests/
    ├── test_quality_engine.py
    ├── test_freshness_engine.py
    ├── test_buying_signal_engine.py
    ├── test_company_filter.py
    ├── test_signal_filter.py
    ├── test_duplicate_engine.py
    ├── test_competitor_engine.py
    ├── test_industry_filter.py
    ├── test_region_filter.py
    ├── test_source_quality.py
    ├── test_website_quality.py
    ├── test_company_age.py
    ├── test_technology_filter.py
    ├── test_activity_engine.py
    ├── test_quality_dashboard.py
    ├── test_quality_metrics.py
    ├── test_quality_reports.py
    ├── test_quality_scheduler.py
    ├── test_dqe_orchestrator.py
    └── test_edge_cases.py
```

## Freshness Limits

| Signal             | Maximum Age |
|--------------------|-------------|
| Hiring             | 30 days     |
| Funding            | 90 days     |
| Product Launch     | 30 days     |
| Technology Adoption| 60 days     |
| Partnership        | 45 days     |
| Expansion          | 90 days     |
| Conference         | 15 days     |
| Award              | 30 days     |
| Press Release      | 30 days     |
| Government Tender  | Until expiry|

## Source Trust Scores

| Source           | Trust Score |
|------------------|-------------|
| LinkedIn         | 98          |
| Company Website  | 97          |
| Crunchbase       | 95          |
| Government       | 95          |
| SEC EDGAR        | 95          |
| GitHub           | 88          |
| Twitter          | 82          |
| Product Hunt     | 80          |
| RSS              | 71          |
| Unknown Blog     | 42          |

Minimum trust threshold: **60.0**

## Configuration Files

### config/competitors.yaml
Controls competitor, partner, client, demo, and internal test company lists.

### config/ideal_customer_profile.yaml
Controls industries, countries, employee range, funding stages, revenue range, company age, technology filters, business models, and decision maker types.

Both files are fully configurable without code changes.

## API Endpoints

All endpoints are read-only:

| Endpoint                           | Description                    |
|------------------------------------|--------------------------------|
| GET /api/v1/quality/dashboard      | Quality dashboard summary      |
| GET /api/v1/quality/rejections     | Rejection details              |
| GET /api/v1/quality/connectors     | Connector quality scores       |
| GET /api/v1/quality/companies      | Company quality metrics        |
| GET /api/v1/quality/signals        | Signal quality metrics         |
| GET /api/v1/quality/reports/daily  | Daily quality report           |
| GET /api/v1/quality/reports/weekly | Weekly quality report          |
| GET /api/v1/quality/failures       | Failure details                |
| GET /api/v1/quality/freshness      | Freshness statistics           |

## Database Tables

Append-only tables via Alembic migration `20260729_0054_discovery_quality_engine.py`:

- `quality_events` — All quality gate decisions
- `quality_decisions` — Per-gate decision records
- `quality_rejections` — Rejection details
- `quality_snapshots` — Periodic metric snapshots
- `connector_quality` — Per-connector quality metrics
- `company_quality` — Per-company quality metrics
- `signal_quality` — Per-signal-type quality metrics
- `quality_reports` — Generated daily/weekly reports

## CTO Acceptance Criteria

- [ ] Why was a company accepted or rejected? → Deterministic reasons in every QualityEvent
- [ ] What percentage of collected signals pass the quality gate? → acceptance_rate in dashboard
- [ ] Which connectors produce the highest-quality opportunities? → connector_quality in dashboard
- [ ] How many stale opportunities were rejected today? → freshness_failures in dashboard
- [ ] How many AI companies, competitors, duplicates, and low-quality websites were filtered out? → Individual counters in dashboard
- [ ] Does every accepted opportunity have a recent buying signal within the freshness window? → Buying signal gate enforces this
- [ ] Are expired opportunities automatically removed from active discovery? → Opportunity expiry system
- [ ] Can the ICP be changed through configuration without code changes? → ideal_customer_profile.yaml
- [ ] Can new connectors plug into the quality engine without modifying its logic? → Source-agnostic architecture
- [ ] Are all quality decisions deterministic, evidence-backed, append-only, and fully auditable? → Append-only database, deterministic rules

## Future Source Preparation

Architecture designed for these connectors to plug in later:

- LinkedIn Company Activity, Jobs, Hiring
- Google Jobs, Greenhouse, Lever, Ashby, Workday
- GitHub, StackShare, BuiltWith, Wappalyzer
- Crunchbase, SEC EDGAR, Product Hunt, YC, Google News
- Government Tender Portals
- Reddit, Hacker News, Dev.to, RSS

DQE remains source-agnostic and evaluates normalized evidence regardless of origin.
