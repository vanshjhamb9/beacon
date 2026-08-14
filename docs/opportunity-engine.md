# Opportunity Engine

The Opportunity Engine is Beacon's decision-making core. It transforms validated business intelligence into actionable opportunities backed by evidence. It does not call GPT, generate outreach, build CRM workflows, or replace the existing Quality, Intelligence, or Context engines.

## Inputs

The engine consumes persisted outputs from existing layers:

- Quality reports
- Entity resolution and company memory through `companies`
- Signal classification through `classified_signals`
- Knowledge and timeline evidence through `company_timelines`
- Context intelligence through `business_contexts`, pains, goals, decision signals, technology signals, and company profiles

## Outputs

Every run creates append-only records:

- `opportunities`
- `opportunity_scores`
- `opportunity_evidence`
- `opportunity_history`
- `opportunity_recommendations`
- `opportunity_timeline`
- `opportunity_feedback`
- `opportunity_conflicts`
- `opportunity_lifecycle`
- `opportunity_metrics`

No score, lifecycle state, recommendation, or feedback is overwritten.

## Scoring

The engine calculates independent scores for opportunity strength, timing, confidence, urgency, growth, technology fit, AI readiness, automation readiness, decision confidence, and budget probability. Each score stores its explanation, weight, and supporting evidence references.

## Decisions

Lifecycle states are rule-driven:

Observed, Watching, Emerging, Qualified, High Intent, Contacted, Meeting, Proposal, Won, Lost, Archived.

Recommendations are deterministic:

Ignore, Watch, Collect More Evidence, Contact Within 30 Days, Contact Within 7 Days, Contact Today, Escalate, Archive.

## Explainability

Each opportunity exposes evidence, score breakdown, confidence breakdown, narrative, timeline, supporting signals, contradicting signals, recommendation reasons, and delta information explaining what changed.

## Learning Foundation

Human reviews, outcome labels, corrections, lifecycle history, and metrics are stored for future training hooks. No ML training is implemented in this sprint.
