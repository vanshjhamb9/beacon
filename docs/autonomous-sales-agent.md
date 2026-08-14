# Autonomous Sales Agent (ASA v1)

Beacon's compose-only AI Business Development Manager layer.

**Scoring version:** `asa-v1`  
**Package:** `packages/autonomous_sales_agent/`  
**API:** `/api/v1/autonomous-sales-agent/*`

## Mission

Automate everything except founder-critical work:

1. Approve outreach  
2. Attend meetings  
3. Write proposals  
4. Close deals  

## Modules

| # | Module | Responsibility |
|---|---|---|
| 1 | Sales Workflow Engine | Deterministic stage machine + audited transitions |
| 2 | Follow-up Intelligence | Configurable 2/5/8/12/20-day cadence |
| 3 | Relationship Timeline | Append-only event history |
| 4 | Meeting Intelligence | Pre-meeting pack |
| 5 | Next Best Action | Exactly one action + confidence/reason/evidence/impact |
| 6 | Case Study Recommendation | Industry library matching |
| 7 | Objection Tracker | Frequency / industry / size / win-rate |
| 8 | Sales Memory | Observe-only pattern insights |
| 9 | Founder Work Queue | Meet / proposal / negotiation / approval / high-intent / urgent |
| 10 | Morning Brief | Priorities, meetings, replies, risks, attention, forecast, follow-ups |

## Hard rules

- Deterministic only — no GPT dependency  
- Compose only — no redesign of completed engines  
- Append-only persistence for runs, transitions, timeline, work-queue snapshots  

## Workflow stages

`lead_discovered → qualified → research_complete → decision_makers_found → sales_package_ready → campaign_created → founder_approval → email_sent → whatsapp_sent → reply_received → meeting_requested → meeting_booked → proposal_pending → proposal_sent → negotiation → won | lost | follow_up | archived`

Every transition stores: timestamp, reason, evidence, actor, next_action.

## Follow-up defaults (configurable)

| Days | Recommendation |
|---|---|
| 2 | Follow-up email |
| 5 | Value email |
| 8 | WhatsApp |
| 12 | Final email |
| 20 | Archive |

## API

- `GET /company/{id}`
- `POST /refresh/{id}`
- `GET /work-queue`
- `GET /morning-brief`
- `POST /morning-brief/refresh`
- `GET /timeline/{id}`
- `GET /dashboard`
- `POST /refresh-batch`

## Dashboard

- `/morning-brief`
- `/founder-work-queue`

## Worker

- `autonomous_sales_agent.refresh_work_queue` @ 180s  
- `autonomous_sales_agent.refresh_morning_brief` @ 86400s  

## Migration

`20260723_0023` — `autonomous_sales_agent_runs`, `asa_workflow_transitions`, `asa_timeline_events`, `asa_work_queue_snapshots`
