# Context Intelligence Engine

The Context Intelligence Engine is Beacon's Brain. It converts accepted, quality-approved, classified signals into explainable business understanding. It does not call GPT, generate outreach, create CRM records, or score opportunities.

## Inputs

Context is built only from accepted quality reports plus existing Intelligence artifacts:

- `quality_reports`
- `classified_signals`
- `companies`
- `raw_events`
- `company_timelines`
- `knowledge_graph_nodes`

## Outputs

The engine produces append-only records for:

- business context
- business pains, goals, triggers, and impacts
- decision and technology signals
- company DNA snapshots
- context evidence, history, and feedback

## API

- `GET /api/v1/context/company/{id}`
- `GET /api/v1/context/company/{id}/dna`
- `GET /api/v1/context/company/{id}/pains`
- `GET /api/v1/context/company/{id}/goals`
- `GET /api/v1/context/company/{id}/timeline`
- `GET /api/v1/context/company/{id}/evidence`
- `GET /api/v1/context/statistics`
- `POST /api/v1/context/feedback`

## Explainability

Every context object contains an evidence chain with source events, timeline references, knowledge graph references, rule references, quality references, confidence breakdown, and explanation text.

## Learning Foundation

Human corrections, accepted context, rejected context, revisions, and ground truth are stored in `context_feedback` and `context_history` for future learning systems. No ML training is implemented in this sprint.
