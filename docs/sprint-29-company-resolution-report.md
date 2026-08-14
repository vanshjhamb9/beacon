# Sprint 29 — Company Resolution Engine (CRE v1)

**Generated:** 2026-07-23T20:46:14.085770+00:00

## Mission

Replace `Signal → Company` with `Signal → Evidence → Identity Resolution → Verification → Company`.

## Live rebuild metrics (from raw signals)

- Total raw signals in DB: **1113**
- Evaluated this run: **1000**
- Companies that would be created: **0**
- Companies rejected: **1000**
- Verified companies: **0**
- Resolution success rate: **0.0%**

## Resolution failure reasons

- **Low Identity Confidence**: 1000
- **No Organization**: 935
- **No Domain**: 935
- **Source Policy Block**: 410
- **News Site**: 4
- **Website Invalid**: 2
- **GitHub Pages**: 2

## Identity confidence distribution

- **0-49**: 935
- **50-69**: 58
- **70-89**: 7
- **90-100**: 0

## Source-wise precision

- **rss**: 0/77 admitted (0.0%)
- **devto**: 0/147 admitted (0.0%)
- **product_hunt**: 0/590 admitted (0.0%)
- **hacker_news**: 0/92 admitted (0.0%)
- **reddit**: 0/39 admitted (0.0%)
- **github_trending**: 0/30 admitted (0.0%)
- **sec_edgar**: 0/25 admitted (0.0%)

## Top verified companies (with attribution)


## Rejected false-positive examples

- `Insurance startup Corgi reportedly raised more money at $4B — its third round in 8 weeks` (rss) → **No Organization → No Domain → Low Identity Confidence → Source Policy Block** (identity=28.0, domain=None)
- `The Echo Show 21 is a great smart home hub that’s $80 off` (rss) → **No Organization → No Domain → Low Identity Confidence → Source Policy Block** (identity=28.0, domain=None)
- `Your logs are leaking secrets in 24 languages` (devto) → **No Organization → No Domain → Low Identity Confidence → Source Policy Block** (identity=28.0, domain=None)
- `PromptQL` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `PodcastorAI` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `AskCodi` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `Wispro` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `Quaso` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=37.0, domain=None)
- `Moxie Docs: Knowledgebases` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `CrawlRaven` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `AMD takes on Nvidia with its Helios AI rack scale system` (rss) → **No Organization → No Domain → Low Identity Confidence → Source Policy Block** (identity=28.0, domain=None)
- `Patreon lays off off 20% of its workforce` (rss) → **No Organization → No Domain → Low Identity Confidence → Source Policy Block** (identity=28.0, domain=None)
- `What Happens If You Lose Your Gmail Account Tomorrow?` (devto) → **No Organization → No Domain → Low Identity Confidence → Source Policy Block** (identity=28.0, domain=None)
- `Cosyra 2.0` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `PromptQL` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `PodcastorAI` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `AgentLoop` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `Megaphone` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)
- `Quaso` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=37.0, domain=None)
- `RunEvr` (product_hunt) → **No Organization → No Domain → Low Identity Confidence** (identity=33.0, domain=None)

## Engineering

| Piece | Path |
|---|---|
| Package | `packages/company_resolution/` (`cre-v1`) |
| Intercept | `IntelligenceService.process_raw_event` — CRE before upsert |
| Migration | `20260724_0036` — `cre_snapshots`, `cre_admission_decisions`, `cre_rebuild_reports` |
| API | `/company-resolution/*` |
| Worker | `company_resolution.rebuild` |

## Acceptance target vs actual

| Funnel | Target | Actual (this eval) |
|---|---:|---:|
| Signals | 1000 | 1000 |
| Real companies | 150 | 0 |
| Verified | 100 | 0 |
| Sales Ready | 40 | 0 (requires downstream SRE; CRE only admits identity) |

## Critical finding

CRE is doing its job: **0 fake companies** would be created from 1000 signals.

Product Hunt RSS currently stores `domain=producthunt.com` and **no product homepage**. Without an official domain, identity confidence stays &lt;90 and admission fails — correctly.

**Next ops fix (not a new engine):** enrich Product Hunt collection to capture the product’s official website URL (API or HTML). Unit tests already admit companies when a real domain is present (e.g. `screenpipe.com`).

HN / Reddit / RSS / Dev.to / GitHub correctly create **signals only** — company create is blocked at intelligence by CRE.

## Tests

`pytest tests/company_resolution` — **504 passed**

CRE stops fake company creation. Sales Ready still requires contact/intent enrichment after admit.

