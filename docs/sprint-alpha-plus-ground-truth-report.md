# Sprint Alpha+ — Ground Truth Recovery

**Date:** 2026-07-24  
**Objective:** Stop feature development. Improve one KPI: would Vansh confidently email this company today?

## Verdict

`packages/ground_truth/` (`alpha-plus-v1`) delivers one Company Truth Profile, Contact Waterfall 2.0, attributed fields, evidence timeline, intelligence card, Top-10 founder queue, rejection funnel with explanations, daily improvement report, and a hard production lock.

## North-star question

> Would Vansh confidently send an email to this company today?

If any of the 7 truth questions is unknown → never Founder Queue.

## Rules

| # | Deliverable |
|---|---|
| 1 | 7 truth questions required |
| 2 | ONE Company Truth Profile |
| 3 | Contact Waterfall 2.0 (optional providers only when present) |
| 4 | Evidence-first attributed fields |
| 5 | Company Timeline → WHY NOW |
| 6 | Single Intelligence Card |
| 7 | Founder Queue Top 10 |
| 8 | Quality funnel dashboard |
| 9 | Rejection explanations |
| 10 | Daily improvement / morning report |
| 12 | Production lock (Email/WhatsApp/Campaign/FQ) |

## Migration

`20260724_0035` — `gt_snapshots`, `gt_daily_reports`, `gt_acceptance_gates`, `gt_founder_queue`

## API / UI

- `/ground-truth/*`
- `/ground-truth` workspace — funnel + Top 10 + morning report

## Lock

`LIVE_OUTREACH_ENABLED = False` / `PRODUCTION_SEND_LOCKED = True` until acceptance KPIs pass.

Gates: identity, website, evidence, intent, DM-or-email, readiness ≥80, not dup/fake, source known, trust ≥90, all 7 questions answered.

## Tests

`pytest tests/ground_truth` — **567 passed**

## CTO note

After this sprint: **stop infrastructure**. Next milestone is **closing the first client**.
Every future improvement should come from real sales conversations — not another engine.
