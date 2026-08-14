# ICE v1 Architecture

Compose-only identity coverage on top of Collectors → CRE → EROWD → IGF → GT → Sales → RH → FQ.

## Providers

1. Product Hunt GraphQL (`PRODUCT_HUNT_DEVELOPER_TOKEN`) — never HTML scrape
2. GitHub identity — metadata + optional live `/repos/{owner}/{repo}` homepage
3. Website intelligence — About/Team/Contact crawl → emails/DMs/LinkedIn
4. Domain intelligence — DNS/SSL/MX trust signals (not identity invention)

## Persistence

Append-only: snapshots, provider results, alias graph, domain intel, collector metrics, recovery queue, daily reports (`20260724_0041`).

## Rule

Unknown > incorrect. No provider writes companies directly — evidence only → IGF admit.
