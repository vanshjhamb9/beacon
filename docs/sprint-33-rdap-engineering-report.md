# Sprint 33 — RDAP v1 Engineering + Live Audit

## North star

> How many new companies entered the Revenue Ready pipeline today?

Success is measured by Verified Companies → Business Emails → Decision Makers → Sales Ready → Revenue Ready — not signals collected.

## Delivered

| Area | Path |
| --- | --- |
| Package | `packages/revenue_data_acquisition/` (`rdap-v1`) |
| Migration | `20260724_0042` |
| API | `/api/v1/revenue-data-acquisition/*` |
| UI | `/revenue-data-acquisition` |
| Workers | `revenue_data_acquisition.*` |

Compose-only with ICE / IGF / EROWD. No GPT. Never fabricate.

## Before → After (live)

| KPI | Before (ICE baseline) | After | Target |
| --- | ---: | ---: | ---: |
| Verified companies | 44 | 44 | ≥75 |
| Official websites | 44 | 44 | ≥75 |
| Business emails | 15 | 15 | ≥40 |
| Decision makers | 3 | 3 | ≥15 |
| Sales Ready | 0 | 1 | ≥10 |
| Revenue Ready | 0 | 0 | ≥5 |

GitHub live fetches: **54** · Companies created/linked: **0** · Companies crawled: **44**

## Connector-by-connector revenue yield

| Connector | Grade | Yield % | Companies | Emails | DMs |
| --- | --- | ---: | ---: | ---: | ---: |
| github_trending | Excellent | 0.0 | 33 | 22 | 18 |
| devto | Average | 0.0 | 4 | 3 | 0 |
| hacker_news | Average | 0.0 | 4 | 3 | 0 |
| unknown | Good | 0.0 | 2 | 2 | 0 |
| rss | Average | 0.0 | 1 | 1 | 1 |
| product_hunt | Poor | 0.0 | 0 | 0 | 0 |
| reddit | Disabled | 0.0 | 0 | 0 | 0 |
| sec_edgar | Disabled | 0.0 | 0 | 0 | 0 |

### Yield funnel rows

| Connector | Signals | Websites | Companies | Emails | DMs | RR | Yield % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| github_trending | 103 | 49 | 33 | 22 | 18 | 0 | 0.0 |
| devto | 204 | 4 | 4 | 3 | 0 | 0 | 0.0 |
| hacker_news | 122 | 4 | 4 | 3 | 0 | 0 | 0.0 |
| unknown | 2 | 2 | 2 | 2 | 0 | 0 | 0.0 |
| rss | 111 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| product_hunt | 787 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| reddit | 39 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| sec_edgar | 25 | 0 | 0 | 0 | 0 | 0 | 0.0 |

## Top rejection reasons

| Reason | Count |
| --- | ---: |
| Website Missing | 1333 |
| Email Missing | 16 |
| Decision Maker Missing | 16 |

## Top Revenue / Sales Ready companies (evidence)

| Company | Domain | Email | Decision Maker | Sales Ready | Revenue Ready |
| --- | --- | --- | --- | --- | --- |
| GitHub: zapier/wade-skills | zapier.com | privacy@zapier.com | Marcelo Lebre (Co-Founder) | True | False |

## Manual verification sample

- All emails recovered only from official website same-domain crawl.
- Decision makers only from Team/About/Leadership/Press pages (no LinkedIn scraping).
- Unknown preferred over guessed domains.
- Fabricated data count: **0**

## Vansh-ready answer

> If Vansh opens Beacon tomorrow morning, are there at least five real companies with verified websites, verified business emails, named decision makers, clear buying intent, and sufficient confidence that he could begin outreach immediately?

**NO**

## Acceptance status

**INCOMPLETE** — implementation + 855 deterministic tests shipped; live KPI targets not met; Vansh-ready remains **NO**.

| Gate | Result |
| --- | --- |
| Compose-only RDAP package | Pass |
| Migration `20260724_0042` | Pass |
| API + UI + workers | Pass |
| ≥800 tests | Pass (855) |
| Fabricated data | Pass (0) |
| Verified companies ≥75 | Fail (44) |
| Business emails ≥40 | Fail (15) |
| Decision makers ≥15 | Fail (3) |
| Sales Ready ≥10 | Fail (1) |
| Revenue Ready ≥5 | Fail (0) |
| ≥5 outreach-ready companies | Fail |

## Root cause (live)

- **787 Product Hunt signals → 0 companies** without `PRODUCT_HUNT_DEVELOPER_TOKEN` (Cloudflare blocks HTML; GraphQL required).
- GitHub live homepage fetches (54) did not admit new IGF companies (duplicates / non-identity / no new domains).
- Public-site crawl on the existing 44 domains found no additional same-domain emails or named DMs beyond ICE’s prior recovery.

## Unlock path

1. Set `PRODUCT_HUNT_DEVELOPER_TOKEN` — unlocks PH GraphQL official websites (primary path to ≥75 companies)
2. Set `GITHUB_TOKEN` — raise homepage recovery past rate limits
3. Re-run `python scripts/rdap_v1_live_audit.py` after tokens → expect email/DM/Sales Ready lift on new domains

Raw: `sprint-33-rdap-live-audit.json`
