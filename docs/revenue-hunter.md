# Revenue Hunter Mode

Beacon's autonomous BD brain for **Operation First Client**.

Every morning the founders see who to contact — only companies with a high probability of buying.

## Pipeline

```text
Filter → Service Match → Pain Points → Website Intelligence
→ Why Now V2 → Revenue Dossier → A+/A Prioritization → Work Queue
```

Scoring version: `rh-v1`

## Filters

| Dimension | Values |
|---|---|
| Countries | USA, Canada, UK, Australia, Germany, Singapore, UAE, Saudi Arabia, India |
| Size | 10-25, 25-50, 50-100, 100-250, 250-500, 500+ |
| Industry | SaaS, Ecommerce, Healthcare, Fintech, Manufacturing, Logistics, Education, Real Estate, Construction, Legal, Marketing, Technology |
| Funding | Bootstrapped, Seed, Series A–C, Public |
| Revenue | Startup, SMB, Mid Market, Enterprise |

## Services

COMAI, Custom AI, Website, Mobile App, SaaS, Internal Software, Automation, AI Chatbot, CRM, ERP, Multi Agent Systems

## Priority grades

| Grade | Score | Campaigns |
|---|---|---|
| A+ | ≥ 85 | Yes |
| A | ≥ 70 | Yes |
| B | ≥ 55 | No (default) |
| C | ≥ 40 | No |
| D | < 40 | No |

Filter failures are hard-capped ≤ 39 (never campaign-eligible).

## API

| Method | Path |
|---|---|
| GET | `/api/v1/revenue-hunter/taxonomy` |
| GET | `/api/v1/revenue-hunter/dossiers` |
| GET | `/api/v1/revenue-hunter/dossiers/{id}` |
| GET | `/api/v1/revenue-hunter/dashboard` |
| GET | `/api/v1/revenue-hunter/work-queue` |
| POST | `/api/v1/revenue-hunter/work-queue/{id}/action` |
| POST | `/api/v1/revenue-hunter/process` |

Work queue actions: `approve`, `send`, `reply`, `book_meeting`, `skip`, `defer`

## Worker

Celery beat `revenue_hunter.process_accounts` at schedule **132s** (after TAI @ 128, before copilot @ 135).

## Dashboard

`/revenue-hunter` — Today's Top Opportunities with Approve / Send / Reply / Book Meeting.
