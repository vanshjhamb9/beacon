# Revenue Optimization Intelligence Platform (ROIP v1)

Compose-only analytics layer that learns from outreach, replies, meetings, proposals, and closed deals.

## Position

```text
GOAP → AIP → Revenue Hunter → Sales Intelligence → Campaigns → Gateway → Live Revenue → ROIP → Founder OS
```

## Rules

- Deterministic only (no GPT)
- Append-only storage (`roip_*` tables)
- Recommendations never auto-apply
- Founder approval required for every optimization action
- Every recommendation includes evidence

## Package

`packages/revenue_optimization/` — version `roip-v1`

## Modules

1. Email Performance  
2. Subject Line Intelligence  
3. CTA Intelligence  
4. Follow-up Intelligence  
5. Industry Conversion  
6. Founder Performance  
7. Offer Intelligence  
8. Case Study Intelligence  
9. Reply Intelligence V2  
10. Revenue Learning  
11. Revenue Benchmarks  
12. Optimization Recommendations  

## API

Prefix: `/api/v1/revenue-optimization`

- `GET /dashboard`
- `GET /company/{id}`
- `GET /campaign/{id}`
- `GET /founder`
- `GET /industry`
- `GET /offers`
- `GET /recommendations`
- `GET /benchmarks`
- `GET /learning`
- `GET /replies`
- `GET /search`
- `POST /refresh`

## Workers

- `optimization.collect_metrics`
- `optimization.calculate_scores`
- `optimization.generate_benchmarks`
- `optimization.generate_recommendations`
- `optimization.daily_report`
- `optimization.weekly_report`

## Dashboard

`/revenue-optimization` — Overview, Email, WhatsApp, Industry, Founder, Offers, Replies, Subjects, CTA, Benchmarks, Learning, Recommendations.
