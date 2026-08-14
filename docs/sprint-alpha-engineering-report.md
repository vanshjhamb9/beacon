# Beacon Alpha — Revenue Dataset Perfection

**Date:** 2026-07-24  
**Objective:** Stop building features. Improve data quality until Beacon reliably produces outbound-ready companies.

## Verdict

`packages/beacon_alpha/` (`alpha-v1`) enforces the founder cold-email test, identity gate, contact waterfall (composed from RQP), Intent 2.0 service buckets, conservative 80+ scoring, Top-10 founder queue, source transparency, dedupe, Manual QA ratings (analytics only), and live-outreach acceptance lock.

## Rules

| # | Outcome |
|---|---|
| 1 | Cold-email admission — reject if not worth Vansh's next email |
| 2 | Identity+website+description+industry+country+evidence+opportunity+source required |
| 3 | Contact enrichment after identity passes — never fabricate |
| 4 | Intent 2.0 buckets (AI Automation, SaaS, Custom, Mobile, E-comm, Enterprise) + structured scores |
| 5 | Score weights Identity25/Website15/Intent20/Service20/Contacts10/Evidence10 — **80+ only** |
| 6 | Founder Queue = **Top 10** dense cards |
| 7 | Source transparency panel |
| 8 | Dedupe: domain / LinkedIn / legal / normalized name / website hash |
| 9 | Manual QA workspace (Excellent→Wrong Intent) — analytics only, never auto-tunes rules |
| 10 | Live outreach locked until acceptance metrics pass |

## Migration

`20260724_0034` — `alpha_snapshots`, `alpha_qa_decisions`, `alpha_acceptance_gates`, `alpha_founder_queue`

## API

`/beacon-alpha/*` — evaluate, founder-queue, qa/pending, qa decide, analytics, acceptance

## UI

`/beacon-alpha` — Top 10 + Manual QA (internal)

## Lock

`LIVE_OUTREACH_ENABLED = False` until acceptance criteria are met.

## Follow-ups

1. Apply Alembic `0034`
2. `POST /beacon-alpha/process-pending`
3. Review Top 10 + rate via Manual QA
4. Unlock Gmail/WhatsApp only after acceptance goes green
