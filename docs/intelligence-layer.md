# Intelligence Layer

The Intelligence Layer converts immutable raw internet events into Beacon's long-term business memory. It does not perform GPT-based opportunity scoring, outreach generation, or dashboard work.

## Flow

1. Raw events are collected and stored in `raw_events`.
2. A scheduled intelligence worker reads received raw events.
3. Entity resolution identifies companies, domains, people, technologies, and products with confidence.
4. Rule-based classification assigns business signal categories.
5. The confidence engine calculates source, entity, classification, freshness, reliability, and overall confidence.
6. Company memory, immutable timeline items, classified signals, and knowledge graph relationships are persisted.

## Tables

- `companies`
- `people`
- `domains`
- `company_aliases`
- `signal_entities`
- `company_timelines`
- `classified_signals`
- `company_relationships`
- `knowledge_graph_nodes`
- `knowledge_graph_edges`

## APIs

- `GET /api/v1/companies`
- `GET /api/v1/companies/{id}`
- `GET /api/v1/companies/{id}/timeline`
- `GET /api/v1/companies/{id}/signals`
- `GET /api/v1/signals`
- `GET /api/v1/knowledge/{id}`

## Beacon Memory

Beacon Memory is built from accumulated evidence over time. Timeline rows are immutable and classified signals preserve confidence explanations. Company rows hold the current aggregate memory view: last seen, signal frequency, historical intent counts, and memory summary.
