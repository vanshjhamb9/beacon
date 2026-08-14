# Operation First Client — Day 1 Report

## Philosophy

Beacon is treated as **feature complete**. No new engines. Only work that increases:

```
Revenue Ready Companies
```

## Day 1 mission

Product Hunt official website + public contact recovery.

## What shipped

| Change | Why it increases RR |
| --- | --- |
| PH collector: official site discovery + public contact crawl | Website/email/DM evidence on launch signals |
| Atom `/r/p/{id}` + maker extraction | Attributed redirect + maker name from live feed |
| EROWD honors `ofc_skip_company` | No company without official website |
| Weak sources signal-only (RSS/HN/Reddit/IH/SEC) | Stops fake/noisy company creation |
| Collectors disabled in `.env` for those sources | Matches OFC Priority 4 |
| CTO Console `/cto` | One ops screen; Production LOCKED badge |
| Company page → OFC one-pager | Hide unknowns; founder-usable brief |
| Founder Queue Top 10 | Company / Why today / Buyer / Email / Service / Evidence / Send (LOCKED) |
| Contact recovery on verified-domain companies | Same-domain emails from live sites only |

## Live evidence (honest)

### Product Hunt feed (this network)

| Metric | Count |
| --- | ---: |
| Events sampled | 40 |
| Official websites resolved | **0** |
| Skipped (no official website) | 40 |
| Atom `/r/p/` redirects extracted | yes (per entry) |
| Maker names from Atom | yes (per entry) |

**Blocker:** Product Hunt HTML and `/r/p/` redirects return **Cloudflare 403** from this environment (browser challenge also). We do **not** guess domains. Redirect URLs + makers are stored as evidence for when resolution is possible (token/proxy/browser unlock).

### Existing verified-domain companies (contact recovery)

| Metric | Count |
| --- | ---: |
| Companies with primary domain | 11 |
| Same-domain business emails recovered | **6** |
| LinkedIn recovered | 4 |
| Plausible phones recovered | 1 |
| Named decision makers (role on site) | **0** |

Raw: `ofc-day1-contact-recovery-live-report.json`

## OFC ladder (current vs target)

| Stage | Target | Current (honest) |
| --- | ---: | ---: |
| Real companies | 100 | 11 |
| Verified websites | 50 | 11 |
| Verified business emails | 40 | 6 |
| Named decision makers | 25 | 0 |
| Revenue Ready | 20 | 0 (production LOCKED) |
| Founder Queue | 10 | 0 |
| Emails sent | 5 | 0 (LOCKED) |
| Meeting booked | 1 | 0 |

## Day 2 mission (recommended)

**Decision maker discovery on the 6 email-ready companies** — LinkedIn/About/Team pages only; never invent names. Promote only when role evidence exists (Founder/CEO/CTO…).

## Day 3 mission (recommended)

**Email verification + Founder Queue fill** — only same-domain verified emails; rebuild rev acceptance; keep Send LOCKED until ≥20 Revenue Ready.

## CTO rule still in force

> Every PR must answer: *Did this increase the number of real, verified, outbound-ready companies?* If no — don't merge.
