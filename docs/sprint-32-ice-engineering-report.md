# Sprint 32 — ICE v1 Engineering + Live Audit

## North star

Increase **Revenue Ready** companies without fabricating identity.

## Delivered

| Area | Path |
| --- | --- |
| Package | `packages/identity_coverage/` (`ice-v1`) |
| Migration | `20260724_0041` |
| API | `/api/v1/identity-coverage/*` |
| UI | `/identity-coverage` |
| Workers | `identity_coverage.*` |
| PH API resolver | GraphQL when `PRODUCT_HUNT_DEVELOPER_TOKEN` set |
| GitHub resolver | Per-repo homepage recovery |

## Before → After (live)

| KPI | Before | After | Target |
| --- | ---: | ---: | ---: |
| Verified companies | 26 | 44 | 200 |
| Official websites | 26 | 44 | 200 |
| Business emails | 11 | 15 | 100 |
| Decision makers | 0 | 3 | 50 |
| Sales Ready | 0 | 0 | 40 |
| Revenue Ready | 0 | 0 | 20 |

GitHub live fetches this run: **54** · Companies created/linked: **18**

## Collector notes

- Conversation sources remain non-identity (IGF).
- PH without developer token: **signal only** (correct — no guessing).
- Top rejections: see live JSON `audit.top_rejections`.

## Vansh-ready answer

> If Vansh logs into Beacon tomorrow morning, are there at least 20 real companies with verified websites, business emails, named decision makers, and clear buying intent that he can confidently contact?

**NO**

Meetings possible (impact): 0 · Pipeline value: $0

## Unlock path to targets

1. Set `PRODUCT_HUNT_DEVELOPER_TOKEN` (official API) — unlocks ~762 PH signals with websites
2. Set `GITHUB_TOKEN` — raise per-repo homepage recovery past rate limits
3. Day mission: decision-maker crawl on email-ready domains → Sales Ready → Revenue Ready

Raw: `sprint-32-ice-live-audit.json`
