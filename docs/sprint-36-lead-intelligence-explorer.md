# Sprint 36 — Lead Intelligence Explorer (LIX v1)

## Mission

Transform Beacon into a fully explainable intelligence platform. Every lead has a replayable lifecycle from first signal to Revenue Ready.

No GPT. No AI. No new scoring engine. Observability only.

## Package

`packages/lead_intelligence/`

- `lead_timeline.py`
- `lead_explainer.py`
- `evidence_chain.py`
- `enrichment_history.py`
- `provider_history.py`
- `score_breakdown.py`
- `stage_history.py`
- `explorer_service.py`
- `router.py`

## Database

Migration: **`20260727_0049`** (after BIC `20260726_0049`)

Append-only tables:

- `lead_events`
- `lead_stage_history`
- `lead_provider_history`
- `lead_score_breakdown`
- `lead_field_history`
- `lead_evidence_chain`

## APIs

| Endpoint | Role |
| --- | --- |
| `GET /api/v1/explorer/search` | Instant lookup |
| `GET /api/v1/explorer/company/{id}` | Full explorer payload |
| `GET /api/v1/explorer/timeline` | Timeline |
| `GET /api/v1/explorer/evidence` | Evidence chain |
| `GET /api/v1/explorer/providers` | Provider history |
| `GET /api/v1/explorer/score` | Score breakdown |
| `GET /api/v1/explorer/history` | Field + stage history |
| `GET /api/v1/explorer/replay` | Lead replay frames |
| `GET /api/v1/explorer/contribution` | Connector contribution |
| `POST /api/v1/explorer/sync` | Sync append-only history from live facts |

## UI

`/lead-explorer` — Lead Intelligence Explorer (sidebar)

Integrations:

- Operations feed → Lead Explorer
- Revenue Ready list → Lead Explorer
- Analytics industries / companies → Lead Explorer
- Discoveries cards → Lead Explorer

## Future providers

Reserved provider cards: Hunter, Apollo, LinkedIn, People Data Labs, Clearbit, Crunchbase, BuiltWith, Wappalyzer, Google Maps, Meta, OpenCorporates.
