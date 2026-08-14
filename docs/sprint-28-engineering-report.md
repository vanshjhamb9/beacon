# Sprint 28 Engineering Report — Sales Readiness Engine (SRE v1)

**Date:** 2026-07-23  
**Objective:** Convert raw opportunities into sales-ready accounts a founder can confidently contact today.

## Verdict

SRE v1 (`sre-v1`) sits after Production Hardening and before Revenue Hunter. It classifies every company with evidence-first identity, website, technology, intent, contacts, outreach, trust, service matches, and revenue potential — never fabricating missing fields (`UNKNOWN`).

## Pipeline

```text
Collectors → GOAP → AIP → Production Hardening → Sales Readiness → Revenue Hunter → Campaigns → Gateway → Founder OS
```

Revenue Hunter `pending_inputs` now requires latest SRE snapshot with `eligible_for_revenue_hunter` and status in `{SALES READY, ENTERPRISE READY}`.

## Compliance

| Rule | Status |
|---|---|
| No new collectors | ✅ |
| No new AI modules | ✅ |
| No redesign of completed engines | ✅ |
| Compose-only | ✅ |
| Append-only DB | ✅ `20260724_0031` |
| Never fabricate | ✅ `UNKNOWN` sentinel |
| Evidence on fields | ✅ `AttributedField` |

## Package

`packages/sales_readiness/`

| Module | Output |
|---|---|
| Identity Completeness | `identity_complete` |
| Website Intelligence | Grade A+…F |
| Technology Readiness | CRM/CMS/… + maturity |
| Buying Intent | Very High…Low |
| Service Matching v2 | Concrete services + value bands |
| Contact Completeness | Role coverage % |
| Outreach Readiness | Can we contact today? |
| Trust | 0–100 breakdown |
| Classifier | NOT READY → ENTERPRISE READY |
| Revenue Potential | Deal / probability / cycle / founder time |

## Migration

`20260724_0031` ← `20260724_0030`

Tables: `sales_readiness_snapshots`, `sales_identity_scores`, `sales_contact_readiness`, `sales_intent_scores`, `sales_service_matches_v2`, `sales_revenue_potential`, `sales_trust_scores`

## API

`/api/v1/sales-readiness/*`

- `GET /company/{id}`
- `POST /company/{id}/evaluate`
- `GET /dashboard`
- `GET /search`
- `GET /trust`
- `GET /outreach-ready`
- `GET /high-intent`
- `GET /enterprise`

## Worker

`sales_readiness.process_pending` @ 130s (before Revenue Hunter @ 132s)

## UI

- Company page: executive Sales Readiness summary (evidence-first)
- Opportunities: Sales Ready / Enterprise / Intent / Deal / Email / Phone / Hiring AI filters
- Founder Queue: only CONTACT READY / SALES READY / ENTERPRISE READY (`visible_in_founder_queue`)

## Tests

`tests/sales_readiness/` — 300+ deterministic cases including performance (500 evals &lt; 5s), RH gate, founder queue admission, contracts, migration, dashboard presence.

## Definition of Done checklist

| Question | Answered by |
|---|---|
| Who is this company? | Identity + website |
| What do they do? | Industry + tech + website grade |
| Why now? | Buying intent signals |
| Which services? | Service Matching v2 |
| Who to contact? | Contact completeness roles |
| How to contact today? | Outreach readiness |
| How valuable? | Revenue potential |
| Why recommend? | Trust + evidence timeline |
