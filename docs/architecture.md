# Beacon AI Architecture

Beacon AI is organized as a modular platform with clear runtime boundaries:

- `apps/api` owns HTTP APIs, dependency injection, error handling, persistence access, and operational endpoints.
- `apps/worker` owns asynchronous background execution through Celery and Redis.
- `apps/dashboard` owns the operator-facing Next.js interface.
- `packages/*` contain reusable domain modules that can be promoted into services as the platform grows.

The backend uses an application factory so tests, workers, and deployment entrypoints can construct the API with explicit settings. Configuration is centralized in `app.core.config.Settings` and loaded from environment variables.

Persistence is built on SQLAlchemy 2.x async sessions and Alembic. All database models should inherit from `BaseModel`, which provides UUID primary keys, `created_at`, `updated_at`, and soft-delete support.

Security primitives are prepared for JWT authentication, password hashing, and role-based authorization. Sprint 2 can add user, organization, and account models on top of these primitives without changing the foundation.

## Signal Collection Engine

Collectors are plugins that inherit from `BaseCollector` and emit `NormalizedEvent` objects. The worker schedules each registered source with Celery Beat, applies Redis-backed rate limiting, removes duplicates with deterministic idempotency keys, and publishes accepted events to Redis Streams.

The Data Acquisition Platform (`packages/data_acquisition`, `/api/v1/acquisition`) audits connector coverage, benchmarks high-value opportunity yield, alerts on failures, and stores daily acquisition reports without changing intelligence engines. Details live in `docs/data-acquisition.md`.

The persistence worker consumes the stream through a Redis consumer group and writes immutable records into `raw_events` with `ON CONFLICT DO NOTHING`. This keeps collection event-driven while preserving database-level idempotency.

Source health is tracked independently in `source_health`, including last success, last failure, consecutive failures, and rolling latency. Operators can read this through `GET /api/v1/sources/health`.

## Beacon Memory

Beacon Memory starts as an accumulated evidence log, not as AI classification. Every public signal is stored as raw evidence with source, URL, title, content, timestamp, metadata, idempotency key, and trace ID. Future entity resolution can attach these raw events to companies and build timelines such as hiring activity, funding, executive posts, launches, support complaints, and geographic expansion.

That timeline becomes the basis for answering the strategic question: who is most likely to become a customer in the next 30-90 days, what evidence supports the prediction, and what action should be taken today.

## Intelligence Layer

The Intelligence Layer builds the knowledge foundation on top of `raw_events`. It performs deterministic entity resolution, rule-based signal classification, confidence scoring, immutable timeline generation, company memory aggregation, and knowledge graph construction. It deliberately does not perform AI opportunity scoring.

The scheduled intelligence worker processes received raw events into:

- Resolved company/domain/person/technology/product entities.
- Classified business signals with urgency, polarity, business function, and confidence.
- Append-only company timeline records.
- Knowledge graph nodes and edges for future recommendation engines.

Details live in `docs/intelligence-layer.md`.

## Quality Engine

The Quality Engine sits between raw event storage and Intelligence. It validates schema, normalizes content, detects spam and duplicates, calculates source trust, freshness, completeness, entity confidence, and overall quality. Intelligence processing is gated to events with accepted quality reports.

Quality rules are persisted and versioned in `quality_rules`, reports and metrics are append-only, and reviewer feedback is stored for future continuous learning. Details live in `docs/quality-engine.md`.

## Context Intelligence Engine

The Context Intelligence Engine runs after Quality and Intelligence. It consumes accepted quality reports, classified signals, entity resolution output, company memory, timelines, and knowledge graph references to infer why a business signal matters.

It produces append-only business context, pains, goals, triggers, impacts, decision signals, technology signals, company DNA snapshots, evidence chains, and feedback history. Details live in `docs/context-engine.md`.

## Opportunity Engine

The Opportunity Engine runs after Context and transforms validated business understanding into explainable opportunities. It aggregates company context, timelines, classified signals, pains, goals, technologies, history, and prior opportunity state.

It stores append-only opportunities, score changes, evidence, lifecycle transitions, recommendations, conflicts, timeline entries, metrics, and feedback for future learning. Details live in `docs/opportunity-engine.md`.

## Revenue Engine

The Revenue Engine runs after Opportunity and produces the Minimum Viable Revenue Intelligence Layer used internally to prioritize software development opportunities. It matches companies to configurable services, infers buyer personas, estimates deal ranges, and generates structured sales playbooks without GPT, CRM, or outreach generation.

It stores append-only solution matches, buyer personas, deal estimates, sales playbooks, recommendation history, and supporting revenue metrics. Details live in `docs/revenue-engine.md`.

## Lead Enrichment Engine

The Lead Enrichment Engine runs after Revenue for high-priority opportunities and produces sales-ready lead profiles. It enriches company, contact, people, technology, team, and social data from lawful public, licensed, or user-provided sources, with field-level source attribution and enrichment confidence scoring.

It does not generate outreach copy, sync CRM records, or call GPT. Details live in `docs/lead-enrichment.md`.

## Data Verification & Coverage Platform

The Data Verification platform runs after Lead Enrichment and measures completeness, coverage, freshness, trust, field conflicts, and connector health for every enriched profile. It stores append-only verification reports and can schedule re-enrichment when freshness expires.

It does not redesign enrichment engines, introduce GPT, CRM, or outreach generation. Details live in `docs/data-verification.md`.

## Intelligence Improvement Engine

The Intelligence Improvement Engine runs after Opportunity and continuously evaluates Beacon's decision quality from outcomes, feedback, prediction errors, collector performance, rule performance, and recommendation accuracy.

It writes append-only learning events, ground truth, performance metrics, prediction history, conversion outcomes, experiment history, rule/model versions, and optimization recommendations for human approval. Details live in `docs/intelligence-improvement.md`.
