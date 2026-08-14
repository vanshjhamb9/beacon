# Beacon Operator Dashboard

Opportunity Intelligence Workspace for founders, sales teams, agencies, AI consultancies, and SaaS companies.

Primary question: **Who should I contact today and why?**

## Stack

- Next.js 15 App Router
- TypeScript
- Tailwind CSS
- TanStack Query
- Framer Motion (subtle)
- Recharts (pipeline/quality/collector only)
- Lucide icons

## Run

```bash
# from repo root
cp apps/dashboard/.env.local.example apps/dashboard/.env.local
npm run dashboard:dev
```

Requires Beacon API at `http://localhost:8000` (`NEXT_PUBLIC_API_URL`).

## Routes

| Path | Purpose |
|------|---------|
| `/` | Today's opportunities, pipeline health, ranks, deltas |
| `/opportunities` | Virtualized filtered table + bulk review |
| `/opportunities/[id]` | Opportunity workspace + review actions |
| `/companies` | Company directory |
| `/companies/[id]` | Full company workspace (DNA, timeline, revenue, playbook, evidence) |
| `/search` | Universal search |
| `/quality` | Quality Engine dashboard |
| `/improvement` | Improvement Engine read-only views |
| `/settings` | Theme, profile, API health, refresh, service catalog |

## Component map

### Layout
- `components/layout/sidebar.tsx` — primary navigation
- `components/layout/topbar.tsx` — global search, sync, collectors, notifications entry

### UI primitives
- `components/ui/button.tsx`
- `components/ui/card.tsx`
- `components/ui/badge.tsx`
- `components/ui/input.tsx`
- `components/ui/skeleton.tsx`
- `components/ui/states.tsx` — empty/error/section labels

### Features
- `features/home/home-workspace.tsx`
- `features/opportunities/*` — cards, table, detail, review actions
- `features/companies/*` — directory + company workspace
- `features/search/search-workspace.tsx`
- `features/quality/quality-workspace.tsx`
- `features/improvement/improvement-workspace.tsx`
- `features/settings/settings-workspace.tsx`

### Data
- `lib/api/client.ts` — fetch helpers
- `lib/api/beacon.ts` — typed Beacon API surface
- `lib/types/api.ts` — shared response types

## Design notes

- Dark-first charcoal + teal accent
- Plus Jakarta Sans / JetBrains Mono
- Soft elevation, generous spacing, minimal charts
- No CRM, outreach, or GPT surfaces
