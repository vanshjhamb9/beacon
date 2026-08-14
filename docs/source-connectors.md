# Source Connectors (GOAP)

Every connector exposes: connector_id, connector_name, health, availability, last_run, signals/companies/opportunities found, duplicates, latency, errors, quality/trust/coverage/freshness/ROI scores.

## Access modes

| Mode | Behavior |
|---|---|
| `public_feed` | Compliant public feeds/APIs |
| `public_jobs` | Public job listings only — no private profile scraping |
| `licensed` | Disabled until credentials supplied |
| `interface_only` | Contract only — no unsupported crawler |

## Catalog highlights

- Current: Reddit, RSS, HN, Product Hunt, GitHub, Dev.to, IndieHackers, SEC  
- Jobs: LinkedIn public jobs, Google Jobs, Wellfound (interface), YC Jobs  
- News: TechCrunch, VentureBeat, YourStory, Inc42, EU Startups, BetaList  
- Licensed: Crunchbase (pending credentials)  
- Reviews: Clutch/GoodFirms/DesignRush/UpCity/Capterra/G2 (interface), SaaSHub, AlternativeTo  
- Commerce ecosystems + public procurement + company blogs / careers / changelogs / docs  

See `packages/global_opportunity_acquisition/connectors/catalog.py`.
