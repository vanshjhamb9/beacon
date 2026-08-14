# IGF v1 — Identity Graph Foundation

## Philosophy

```
Signal → Identity Candidate → Identity Graph → Official Website → Verified Company → Enrichment → Revenue Ready
```

A company **does not exist** until Identity Graph admits it.

## Delivered

| Area | Path |
| --- | --- |
| Package | `packages/identity_graph/` (`igf-v1`) |
| Migration | `20260724_0040` |
| API | `/api/v1/identity-graph/*` |
| Dashboard | `/identity-graph` |
| Gate | `IntelligenceService` requires IGF admit after EROWD |
| Tests | **909** deterministic (`tests/identity_graph`) |
| Architecture | `docs/igf-v1-architecture.md` |

## Live funnel (honest)

| Metric | Before | After IGF rebuild |
| --- | ---: | ---: |
| Signals evaluated | ~1100 | **1325** |
| Identity candidates | — | **1325** |
| Official websites (admitted unique) | 11 | **15+** (26 companies w/ domain) |
| Active canonical companies | 0 | **26** |
| Companies in DB | 11 | **26** |
| Same-domain business emails | 6 | **9–11** |
| Named decision makers | 0 | **0** |
| Revenue Ready | 0 | **0** (production LOCKED) |

## Source roles working

- Conversation (HN/Reddit/RSS/Dev.to) → **SIGNAL_ONLY**, never create company
- Intent (SEC) → never create
- Identity (GitHub w/ homepage, Product Hunt w/ website) → admit when evidence exists
- Top failure: **No Official Website** (1309) — expected while PH is Cloudflare-blocked

## CTO acceptance — NOT MET yet

| Gate | Target | Live | Status |
| --- | ---: | ---: | --- |
| Verified official websites | 100 | ~26 | ❌ |
| Business emails | 50 | ~11 | ❌ |
| Named decision makers | 30 | 0 | ❌ |
| Revenue Ready | 20 | 0 | ❌ |
| Zero fabricated | — | yes | ✅ |
| Evidence attribution | — | yes | ✅ |

## What unblocks the ladder next

1. **Product Hunt developer token / unblocked redirect resolution** — 762 PH signals waiting
2. **GitHub token** — rate limit hit; need authenticated search for more homepage repos
3. **Day 2: decision-maker recovery** on the 26 verified-domain companies
4. Optional: licensed enrichment (Clearbit/PDL) for domain resolution at scale

## North star check

> If Vansh opens Beacon tomorrow, does he see ≥20 companies he can confidently email?

**Not yet.** IGF foundation is live and correctly refusing conversation noise; identity volume is still the bottleneck.

Raw: `igf-v1-live-report.json`
