# AI Sales Copilot Foundation (Sprint 13)

Transforms qualified Beacon opportunities into evidence-grounded Sales Intelligence Packages for human review.

## Boundaries

- Reads only from existing Beacon engines (Company, Opportunity, Revenue, Enrichment, Verification, Decision, Context, Quality, Timeline, Evidence).
- Never queries collectors directly.
- Does **not** send email, WhatsApp, LinkedIn, Gmail, or Calendly messages (Sprint 14).

## Package

`packages/sales_copilot/`

- LLM provider abstraction: OpenAI, Anthropic, Gemini, OpenRouter, plus deterministic `grounded`
- Versioned prompts with generation metadata (tokens, latency, cost estimate)
- Immutable package versions on every regeneration
- Automatic quality scoring and grounding validation

## API

- `GET /api/v1/copilot/company/{id}`
- `GET /api/v1/copilot/opportunity/{id}`
- `POST /api/v1/copilot/generate/{id}`
- `POST /api/v1/copilot/regenerate/{id}`
- `POST /api/v1/copilot/review/{id}`
- `GET /api/v1/copilot/history/{id}`

## Database

Migration `20260720_0013` (after outcome intelligence `0012`):

- `sales_packages`, `sales_drafts`, `sales_templates`, `sales_prompt_versions`
- `sales_generation_logs`, `sales_feedback`, `sales_versions`

## Configuration

```env
SALES_COPILOT_PROVIDER=grounded
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
```

Default provider is `grounded` (template generation from Beacon evidence only).
