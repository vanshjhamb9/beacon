# Sprint 36C — Opportunity Connector Platform (OCP v1)

## Overview

Beacon evolves from a lead collector into a **Real-Time Opportunity Intelligence Platform**. Every external source plugs into Beacon using one standardized connector interface.

## Architecture

```
Connector
    ↓
Normalized Evidence Event
    ↓
Live Opportunity Discovery
    ↓
Opportunity Intelligence
    ↓
Identity Graph
    ↓
EROWD
    ↓
CRE
    ↓
ICE
    ↓
Sales Readiness
    ↓
Revenue Ready
    ↓
Founder Queue
```

## Standard Connector Interface

Every connector implements:

| Method | Description |
|--------|-------------|
| `id()` | Unique connector identifier |
| `name()` | Human-readable name |
| `version()` | Semantic version |
| `capabilities()` | Declared capabilities |
| `health()` | Current health snapshot |
| `authenticate()` | Verify credentials |
| `discover()` | Raw payloads from external source |
| `normalize()` | Convert payload → EvidenceEvent |
| `validate()` | Deterministic gatekeeping |
| `emit()` | Push validated event into pipeline |
| `shutdown()` | Graceful teardown |

## Standard Evidence Event

Every connector emits exactly one schema with fields:
`event_id`, `connector_id`, `connector_version`, `company_name`, `headline`, `summary`, `event_type`, `event_category`, `url`, `published_at`, `captured_at`, `country`, `language`, `confidence`, `evidence`, `raw_metadata`, `collector`

## Engineering Rules

- No GPT / AI scoring
- No redesign of existing engines
- Compose only
- Append-only migrations
- Every connector deterministic
- No connector creates companies
- No connector creates opportunities
- Connectors emit evidence only
- Evidence must always include attribution
- Unknown preferred over guessed
- Never fabricate domains/emails/people

## Package Structure

```
packages/opportunity_connector_platform/
    __init__.py
    connector.py          # Standard Connector ABC
    registry.py           # Dynamic connector registry
    manager.py            # Lifecycle orchestrator
    scheduler.py          # Deterministic scheduler
    router.py             # High-level event router
    connector_events.py   # EvidenceEvent + RoutedEvidenceEvent
    connector_capabilities.py  # Capability taxonomy
    connector_config.py   # YAML config loader
    connector_health.py   # Health engine
    connector_metrics.py  # Metric calculations
    connector_dashboard.py  # Dashboard assembly
    connector_quality.py  # ROI quality decisions
    connector_statistics.py  # Statistics rollups
    connector_yield.py    # Revenue yield calculations
    signal_validator.py   # Event validation
    signal_normalizer.py  # Event normalization
    signal_router.py      # Normalize → validate → route
    connector.yaml        # Configuration file
```

## Database Migration

Alembic migration `20260729_0052` creates 10 append-only tables:
- `connector_registry`
- `connector_runs`
- `connector_events`
- `connector_statistics`
- `connector_health`
- `connector_yield`
- `connector_configuration`
- `connector_failures`
- `connector_rate_limits`
- `connector_capabilities`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /connectors` | List all connectors |
| `GET /connectors/{id}` | Get connector details |
| `GET /connectors/health` | Health status |
| `GET /connectors/statistics` | Statistics |
| `GET /connectors/yield` | Revenue yield |
| `GET /connectors/failures` | Failure logs |
| `GET /connectors/feed` | Real-time feed |
| `GET /connectors/events` | Query events |

## Adding a New Connector

1. Create a class implementing `Connector` ABC
2. Register with `ConnectorRegistry`
3. Add config to `connector.yaml`
4. No other changes needed — the pipeline handles everything

## Supported Event Types

Hiring, Funding, Expansion, New Office, Technology Adoption, Migration, Product Launch, Compliance, Procurement, Executive Hire, Partnership, Customer Win, Pricing Change, Acquisition, Security Incident, Infrastructure Upgrade, Hiring Freeze, Layoffs, API Release, SDK Release, Marketplace Listing, Press Release, Conference, Award, Patent, Government Tender, Developer Activity, Community Growth

## Connector Categories

| Category | Connectors |
|----------|-----------|
| Identity | Product Hunt, GitHub, Crunchbase, YC, Company Website |
| Conversation | Reddit, HN, Dev.to, RSS |
| Intent | Google News, Press Releases, Jobs, Greenhouse, Lever, Ashby, Workday |
| Technology | GitHub, StackShare, BuiltWith, Wappalyzer |
| Enrichment | Hunter, Apollo, People Data Labs, LinkedIn, Clearbit |
