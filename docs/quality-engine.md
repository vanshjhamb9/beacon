# Quality Engine

The Quality Engine is the validation gate between raw internet collection and Beacon Intelligence. Intelligence workers only process raw events that have an accepted `quality_reports` record.

## Pipeline Stages

1. Schema validation
2. Normalization
3. Spam detection
4. Source trust
5. Freshness
6. Completeness
7. Entity confidence
8. Duplicate detection
9. Overall quality scoring

Each stage emits a metric row with score, pass/fail, latency, reason codes, and details. Reports are append-only and preserve processing history.

## Tables

- `quality_reports`
- `quality_metrics`
- `quality_rules`
- `source_statistics`
- `spam_patterns`
- `quality_audit`
- `quality_feedback`

## APIs

- `GET /api/v1/quality/events`
- `GET /api/v1/quality/events/{id}`
- `GET /api/v1/quality/sources`
- `GET /api/v1/quality/statistics`
- `GET /api/v1/quality/report?report_id=...`
- `GET /api/v1/quality/rules`
- `POST /api/v1/quality/review`
- `GET /api/v1/quality/dashboard`

## Learning Foundation

Human review is stored in `quality_feedback` and `quality_audit`. Future ML systems can train on accepted signals, rejected signals, false positives, false negatives, corrected decisions, and reviewer notes without changing the quality pipeline contract.
