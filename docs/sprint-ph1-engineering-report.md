# Sprint PH-1 Engineering Report — Production Hardening (Revenue Readiness)

**Date:** 2026-07-23  
**Objective:** Stop shipping unverifiable demo leads. Only surface opportunities a founder would confidently contact today.

## Verdict

PH-1 delivers an evidence-first admission + readiness layer (`ph1-v1`) that rejects fake identities, hides low-quality leads (<70), classifies contact readiness, replaces hardcoded production health with live probes, and simplifies founder/opportunity surfaces.

## North-star question

> Would a founder confidently contact this lead today?

If no → never appear in Founder Queue / Opportunities v2.

## Compliance

| Rule | Status |
|---|---|
| No new AI modules | ✅ |
| No architecture redesign | ✅ |
| Compose-only | ✅ |
| Append-only DB | ✅ (`20260724_0030`) |
| Never fabricate contacts | ✅ |
| Every health metric from live probes | ✅ |
| Backward compatible with prior sprints | ✅ |

## Package

`packages/production_hardening/`

| Engine | Role |
|---|---|
| Opportunity Admission Gate | Reject no domain/source/evidence/use-case, fake names, platforms, repos |
| Company Identity Validator | Confidence threshold 55 |
| Contact Readiness Engine | NOT_READY / PARTIAL / CONTACT_READY / SALES_READY |
| Lead Quality Scorer | 100-pt score; hide < 70 |
| Duplicate Resolution | Domain / LinkedIn / legal / alias merge plans |
| Live Health Telemetry | Maps Redis/DB/Celery/OAuth/collector probes → component_signals |
| Trust Metrics | QA conversion + verification % |
| Noise Collapser | Collapse repeated evidence/signals |

## Migration

`20260724_0030` (revises `20260724_0029`)

Tables: `ph_admission_decisions`, `ph_contact_readiness`, `ph_company_merges`, `ph_trust_snapshots`

## API

`/api/v1/production-hardening/*`

- `GET /company/{id}` — Founder card (compose)
- `POST /company/{id}/evaluate` — Persist readiness + admission
- `GET /opportunities` — Opportunities v2 (admitted + score ≥ 70)
- `GET /trust` — Trust dashboard metrics
- `GET /duplicates` — Merge plans
- `GET /health/signals` — Live component signals

Production Validation `/production-validation/health` now injects live signals (no hardcoded Email/WhatsApp 95%).

## UI

| Surface | Change |
|---|---|
| Company page | Founder Workspace v2 header (identity, source, score, DM, email, phone, evidence, readiness) |
| Opportunities | List v2 columns + filters; only quality-visible leads |
| Trust Dashboard | `/trust` internal QA metrics |
| Production Health | Live telemetry badge; real rates when unconfigured → 0% |

## Tests

`tests/production_hardening/` — 200+ cases covering admission fakes, identity, readiness, scoring bands, dedupe, trust, live health, contracts, migration.

## Success criteria

| Criterion | Status |
|---|---|
| Verified identity required | ✅ gate + identity |
| Evidence shown | ✅ evidence cards + collected_from |
| Fake companies disappear | ✅ FAKE_NAME_PATTERNS + platform reject |
| Duplicates planned | ✅ merge engine |
| Real production health | ✅ LiveHealthTelemetry |
| Contact readiness visible | ✅ statuses + founder queue flag |
| Sources transparent | ✅ collected_from timestamps |
| Simpler UI | ✅ founder card above fold |

## Follow-ups

1. Apply Alembic `20260724_0030` in each environment
2. Batch `POST /production-hardening/company/{id}/evaluate` over existing companies
3. Wire enricher attribution into more contact fields without fabricating
4. Optionally persist duplicate merges into canonical company graphs
