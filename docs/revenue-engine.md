# Revenue Engine

The Revenue Engine is Beacon's Minimum Viable Revenue Intelligence Layer. It converts Opportunity, Context, Company DNA, Quality, and Knowledge Graph evidence into deterministic service matches, buyer personas, deal ranges, and sales playbooks for internal prioritization.

It does not call GPT, generate outreach, build CRM workflows, or replace Collection, Quality, Intelligence, Context, Opportunity, or Intelligence Improvement.

## Inputs

The engine consumes persisted outputs from upstream layers:

- Opportunity decisions through `opportunities` and `opportunity_evidence`
- Context intelligence through pains, goals, business contexts, and company profiles (Company DNA)
- Quality through linked `quality_reports`
- Knowledge Graph company nodes through `knowledge_graph_nodes`
- Configurable service catalog through `services` and `service_rules`

## Outputs

Every run creates append-only records:

- `solution_matches`
- `buyer_personas`
- `deal_estimates`
- `sales_playbooks`
- `recommendation_history`
- Supporting tables: `deal_predictions`, `sales_cycles`, `revenue_history`, `revenue_metrics`

No recommendation is overwritten. Newer opportunity evidence produces a new solution match.

## Matching

Service matching is deterministic. It scores enabled catalog services using:

- Opportunity score, confidence, and quality
- Matching terms against narrative, pains, goals, technology stack, and evidence text
- Target pain and industry overlap
- Knowledge graph reference density

It returns primary service, optional secondary service, confidence, and reasoning.

## Buyer Personas

Persona inference is rule-based and limited to:

Founder, CEO, COO, CTO, Engineering Manager, Support Head, Operations Head, Marketing Head.

Each persona includes confidence and explanation.

## Deal Estimation

Deal estimation returns ranges only:

- Project size: small, medium, large, enterprise
- Budget range: small, medium, large, enterprise
- Implementation complexity from the matched service configuration

It does not produce point forecasts or CRM pipeline stages.

## Playbooks

Playbooks are structured and deterministic:

- Business Pain
- Recommended Service
- Why
- Conversation Angle
- Decision Maker
- Expected Outcome
- Risk

## API

- `GET /api/v1/revenue/opportunities`
- `GET /api/v1/revenue/company/{id}`
- `GET /api/v1/revenue/company/{id}/playbook`
- `GET /api/v1/revenue/statistics`

Company responses include company, opportunity score, business pain, recommended service, buyer persona, estimated budget range, priority, evidence, reason, and playbook.

## Worker

Celery task `revenue.process_opportunities` runs after Opportunity processing, seeds the service catalog when empty, and persists revenue recommendations for pending opportunities.

## Explainability

Every recommendation stores match evidence, persona explanations, estimate explanation, priority explanation, and a full recommendation history snapshot.
