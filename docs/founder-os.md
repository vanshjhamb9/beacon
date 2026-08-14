# Founder Revenue OS

Beacon's daily operating system for founders (`fos-v1`).

Composes existing engines — does **not** redesign revenue_hunter, outcomes, campaigns, or communication.

## Morning answers

1. What happened yesterday?
2. What should I do today?
3. Who should I contact?
4. Who replied?
5. Who booked meetings?
6. Who needs proposals?
7. Where is the revenue?

## Modules

| Module | Package path |
|---|---|
| Daily Brief | `founder_os.brief` |
| Command Center | `founder_os.command` |
| Founder Assistant | `founder_os.assistant` |
| Revenue Tasks | `founder_os.tasks` |
| Revenue Timeline | `founder_os.timeline` |
| Sales KPIs | `founder_os.kpi` |
| Recommendations | `founder_os.recommendations` |
| Proposal Queue | `founder_os.proposals` |
| Meeting Intelligence | `founder_os.meetings` |
| Analytics | `founder_os.analytics` |

## APIs

Prefix: `/api/v1/founder-os`

- `GET /command-center`
- `POST /refresh`
- `GET /brief`
- `GET /assistant`
- `GET /tasks`
- `POST /tasks/{id}/complete`
- `GET /kpis`
- `GET /recommendations`
- `GET /proposals`
- `GET /meetings`
- `GET /timeline/{company_id}`
- `POST /analytics/track`

## Worker

`founder_os.refresh_brief` every 300s.

## Dashboard

Home (`/`) is the Founder Revenue OS screen — Good Morning, mission, top companies, queues, tasks, recommendations.
