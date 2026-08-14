# Intelligence Improvement Engine

The Intelligence Improvement Engine continuously evaluates Beacon's decision quality. It does not generate opportunities, call GPT, or automatically change production rules.

## Inputs

The engine consumes measurable outcomes from existing systems:

- Quality feedback and quality reports
- Context feedback and ground truth corrections
- Opportunity feedback, scores, lifecycle, metrics, and outcomes
- Collector quality and latency signals

## Outputs

All outputs are append-only:

- learning events and normalized feedback events
- ground truth labels
- collector, rule, classifier, context, opportunity, and recommendation accuracy
- prediction history and conversion outcomes
- weight adjustment recommendations requiring approval
- experiment runs and results
- model and rule version history

## Optimization Policy

The engine never mutates production rules automatically. It generates recommendations such as increasing or reducing weights, changing confidence thresholds, and flagging low-performing collectors or rules for review.

## API

- `GET /api/v1/improvement/overview`
- `GET /api/v1/improvement/collectors`
- `GET /api/v1/improvement/rules`
- `GET /api/v1/improvement/opportunities`
- `GET /api/v1/improvement/experiments`
- `GET /api/v1/improvement/recommendations`

## Experiments

Experiments are versioned and append-only. They support A/B testing scoring rules, decay strategies, recommendation logic, and rule weights while preserving complete history.
