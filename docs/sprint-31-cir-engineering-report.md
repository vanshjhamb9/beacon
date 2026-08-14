# Sprint 31 — Company Intelligence Reconstruction (CIR v1)

## Mission

> If I were the founder of Urban Webworks, what do I need to know before sending the very first email?

CIR reconstructs verified companies into business understanding, ICP, technology, buying signals,
service match, opportunity narrative, contacts, and revenue readiness — evidence only, no GPT.

## Pipeline

```
Verified Company (EROWD) → Website Understanding → Business → Products → ICP → Technology
→ Buying Signals → Service Match v3 → Narrative → Contacts → Revenue Readiness → Founder Card
```

## Delivered

| Area | Path |
| --- | --- |
| Package | `packages/company_intelligence/` (`cir-v1`) |
| Migration | `20260724_0038` — 8 append-only CIR tables |
| API | `/company-intelligence/*` |
| Worker | `company_intelligence.process_verified` every 120s (EROWD-admitted only) |
| Dashboard | `/company-intelligence` |
| Founder card | `CirExecutiveSummary` on company page |
| RH compose | CIR readiness/signals/tech/narrative into `RevenueHunterInput.metadata` |
| Founder Queue | CIR: Revenue Ready / Priority Account only; GT soft-gate when CIR present |

## Acceptance (500 verified companies)

| Metric | Value | Target |
| --- | ---: | ---: |
| Business profile % | 84.0 | ≥80 |
| Industry + ICP % | 84.0 | ≥70 |
| Technology + service % | 84.0 | ≥60 |
| Contact % | 84.0 | ≥40 |
| False fabrications | 0 | 0 |
| Founder queue eligible | 420 | RR/PA only |
| Elapsed | 806.27 ms | <5000 |

## Classification distribution

```json
{
  "Priority Account": 420,
  "Rejected": 80
}
```

## Compose-only guarantees

- Did **not** redesign Revenue Hunter, Sales Readiness, Ground Truth, Founder Queue core, CRE, or EROWD.
- CIR never runs before EROWD admission (`SKIPPED` otherwise).
- Every readiness score includes evidence breakdown.

Raw metrics: `sprint-31-cir-live-report.json`.
