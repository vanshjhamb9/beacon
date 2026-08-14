# Target Account Intelligence Engine (TAI)

Master brain of Beacon Revenue OS. Companies are scored against Ideal Customer Profiles (ICPs) before Sales Copilot or Campaigns run automatically.

## Package

`packages/target_account_engine/`

Engines: Fit, Intent, Budget, Urgency, Accessibility, Competition → weighted **Revenue Opportunity Score** (`tai-v1`).

## Default ICPs

1. Custom AI Solutions  
2. COMAI  
3. Website Development  
4. Mobile App Development  

## Pipeline gate

When `TARGET_ACCOUNT_GATE_ENABLED=true` (default):

- Sales Copilot auto-processing only includes **top-tier** target accounts
- Campaign auto-creation only includes **top-tier** companies with approved packages

Manual generate/approve APIs remain available.

## APIs

- `GET /api/v1/targets`
- `GET /api/v1/targets/{id}`
- `GET /api/v1/targets/dashboard`
- `GET|POST /api/v1/icp`
- `PUT|DELETE /api/v1/icp/{id}`
- `POST /api/v1/hunter/start`
- `GET /api/v1/hunter/status`

## Worker

`targets.process_accounts` — beat schedule 128s (before copilot 135s).

## Hunter Mode

Triggered when revenue score > `TARGET_ACCOUNT_HUNTER_THRESHOLD` (default 75). Deepens enrichment task list (technology, DMs, funding, news, website audit, products, customers, hiring, reviews, social).

## Self-improvement

Outcome-driven recommendations only. Never automatic retrain.
