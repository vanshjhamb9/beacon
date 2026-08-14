# Lead Enrichment Engine

The Lead Enrichment Engine turns qualified Beacon opportunities into sales-ready lead profiles operators can review before manual outreach.

## Position in the pipeline

Collectors → Quality → Intelligence → Context → Opportunity → Revenue → **Lead Enrichment**

Celery Beat task: `enrichment.process_opportunities` (every 90s)

Pending selection requires:

1. A revenue `solution_matches` row at/after the opportunity
2. Opportunity status `qualified` / `high_intent`, or deal priority `high` / `critical`
3. No `enrichment_reports` row at/after the opportunity timestamp

## Package layout

```text
packages/lead_enrichment/
  models/types.py
  connectors/          # website, DNS/MX, public profiles, technology, licensed providers
  extractors/          # company, contacts, people, jobs/team
  validators/
  scoring/
  pipelines/
  services/
  repository/protocols.py
  metrics/
  api/
```

## API

- `GET /api/v1/enrichment/company/{id}`
- `GET /api/v1/enrichment/opportunity/{id}`
- `POST /api/v1/enrichment/refresh/{id}`

## Persistence

Append-only tables:

| Table | Purpose |
|-------|---------|
| `enrichment_reports` | Full `SalesReadyLeadProfile` snapshot + confidence scores |
| `enriched_company_profiles` | Normalized company profile fields (named to avoid collision with Context DNA `company_profiles`) |
| `company_contacts` | Public business emails/phones |
| `company_people` | Decision makers / leadership |
| `company_social_profiles` | LinkedIn, GitHub, X, etc. |
| `company_technologies` | Stack and technology signals |
| `company_team_insights` | Team size / hiring insights |
| `company_jobs` | Open roles |
| `company_enrichment_history` | Append-only action log |
| `enrichment_sources` | Source attribution rows |

## Output

`SalesReadyLeadProfile` includes company profile, technology stack, decision makers, public contacts, team insights, social profiles, estimated budget, priority, why-now, best outreach angle (from Revenue playbook — not generated copy), evidence chain, source attribution, and enrichment confidence.

## Source policy

Only lawful, publicly available, licensed, or user-provided sources. Licensed connectors (BuiltWith, Wappalyzer, Crunchbase) activate only when API keys are configured.
