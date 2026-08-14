# Sprint 22 Engineering Report — Autonomous Sales Agent (ASA v1)

**Date:** 2026-07-23  
**Objective:** Make Beacon behave like a full-time AI Business Development Manager while keeping the founder in control of approvals, meetings, proposals, and closes.

## Verdict

Sprint 22 delivers compose-only **Autonomous Sales Agent** (`asa-v1`): deterministic sales workflow, configurable follow-up intelligence, append-only relationship timeline, meeting packs, single next-best-action recommendations, case-study matching, objection tracking, observe-only sales memory, founder work queue, and morning brief. No completed engines were redesigned.

## Architecture

```text
Existing engines (Revenue Hunter · SI · LRE · Campaign · Gateway · Founder OS · PRV)
        │  (read / compose signals only)
        ▼
AutonomousSalesAgentPipeline (asa-v1)
  Workflow · Follow-up · Timeline · Meeting · NBA
  Case Study · Objections · Memory · Work Queue · Morning Brief
        │
        ▼
Append-only runs + transitions + timeline + work-queue snapshots
        │
        ▼
API + Celery + Founder Work Queue / Morning Brief dashboards
```

## Deliverables

| Area | Status |
|---|---|
| `packages/autonomous_sales_agent/` | ✅ |
| API `/autonomous-sales-agent/*` | ✅ |
| Migration `20260723_0023` | ✅ |
| Worker work-queue @180s / morning brief @86400s | ✅ |
| Founder Work Queue UI | ✅ `/founder-work-queue` |
| Morning Brief UI | ✅ `/morning-brief` |
| 10 modules | ✅ |
| Append-only architecture | ✅ |
| Deterministic / no GPT | ✅ |
| Compose-only (no redesign) | ✅ |

## Package layout

```text
packages/autonomous_sales_agent/
  models/ types.py
  workflow/ followup/ timeline/ meeting/ actions/
  casestudy/ objections/ memory/ queue/ brief/
  pipelines/asa_pipeline.py
  services/engine.py
  analytics/ rules/ scheduler/ repository/ api/
```

## Founder contract

Founder only sees / acts on:

- Meet today  
- Proposal pending  
- Negotiation  
- Needs approval  
- High intent reply  
- Urgent follow-up  

Everything else is automated (`wait` / system follow-up paths).

## Tests

Suite: `tests/autonomous_sales_agent/`

Coverage areas: components, pipeline, workflow, timeline, follow-up, meeting intelligence, morning brief, API, migration, dashboard, regression, performance (100 workflow evals &lt; 3s).

## Non-goals (honored)

- No redesign of SI / LRE / PRV / Founder OS / Campaign / Gateway  
- No GPT / LLM calls in ASA  
- No mutation of existing engine scoring logic  

## Follow-ups

1. Run Alembic `20260723_0023` in each environment  
2. Point production morning-brief beat to founder timezone if needed  
3. Optionally surface ASA pack on company detail pages  
