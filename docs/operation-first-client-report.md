# Operation First Client — Live Report

**Finished:** 2026-07-24 (ops passes 1–2)  
**Rule followed:** No new dashboards / AI / scoring engines. Reused existing website connector, contact waterfall, Ground Truth pipeline, service matcher. Soft-deleted garbage. Funnel-first enrichment only.

## Honest verdict

**Not ready to email 10/10.** Production stays **LOCKED**.

Cleanup worked. Contact + decision-maker recovery did **not** reach acceptance. You do **not** yet have 25 enterprise-grade outreach-ready accounts.

---

## 1. Before vs After

| Metric | Before (live DB) | After ops |
|---|---:|---:|
| Active companies | **415** | **11** |
| With real domain | 163 (many fake domains) | **11** coherent |
| Verified websites (live HTTP) | **0** | **11** (of curated survivors) |
| Companies with business email | **0** trustworthy | **9** recovered (role/support/founder) |
| Phone numbers | **1** polluted | **present on several pages** (weak attribution) |
| Decision makers | **0** | **0** |
| Sales Ready (GT unlock) | **0** | **0** |
| Founder Queue (email-every-one) | empty | **not unlocked** |

Funnel used:

```text
415 raw
→ ~121 after fake/no-website reject
→ ~77 after invalid-domain reject  
→ ~22 after media/name-domain coherence
→ 11 curated outreach candidates with live websites
→ 0 Sales Ready (missing DM + truth questions)
```

---

## 2. Top rejection reasons

| Reason | Count (approx cumulative) |
|---|---:|
| no_website | 231 |
| fake_or_non_business_name | 54+ |
| name_domain_incoherent_or_media | 38+ |
| website_unreachable | 15+ |
| invalid_domain (`.tsx`, `.map`, code tokens) | 10+ |
| low_intent_no_evidence | 17 |
| not_outreach_target (tutorials/media/personal) | 11 |

---

## 3. Top collectors (keep)

1. **product_hunt** — ~52% emit  
2. **devto** — ~26% emit  
3. (sec_edgar had emit but is **DOWN** / poor signal)

---

## 4. Worst collectors (disabled in `.env`)

| Collector | Why |
|---|---|
| **indie_hackers** | DOWN — 42 failures, bot protection |
| **sec_edgar** | DOWN — 70+ failures, HTML not RSS |
| **github_trending** | ~99% duplicates; creates repo/noise entities |

Also poor for company identity: **reddit**, **rss**, **hacker_news** (high dup + article-title “companies”).

---

## 5–6. Recovery & verification rates

- Cleanup: **~97%** of original 415 hidden/rejected  
- Among final 11 live sites: **~82%** have at least one recovered business email  
- Decision-maker recovery: **0%**  
- Sales Ready conversion: **0%**

---

## 7. Best accounts available today (not Sales Ready)

These are the only ones left that a founder might *investigate* — **not** a send-all list.

| # | Company | Website | Email recovered | Service | Trust |
|---|---|---|---|---|---:|
| 1 | Screenpipe | screenpipe.com | support@screenpi.pe | AI Knowledge Assistant | 85 |
| 2 | palmier-io | palmier.io | founders@palmier.io | Workflow Automation | 85 |
| 3 | Beyond | fluctara.com | privacy@fluctara.com | AI Knowledge Assistant | 85 |
| 4 | onecli | onecli.sh | support@ / legal@ | Workflow Automation | 85 |
| 5 | MCP | dosync.dev | rgiuliani@dosync.dev | Workflow Automation | 85 |
| 6 | Deep / Pagewatch | pagewatch.tech | support@pagewatch.tech | Workflow Automation | 85 |
| 7 | Reotrucks | reotrucks.com | hello@ / partners@ / press@ | Workflow Automation | 85 |
| 8 | Tangled | tangled.org | team@ / security@ | Workflow Automation | 85 |
| 9 | Monday.com | monday.com | support@monday.com | Workflow Automation | 85 |
| 10 | BorgShield | backup.sh | — | Workflow Automation | 55 |
| 11 | YAFL | yafl.dev | — | Workflow Automation | 55 |

**Would Vansh happily email every one today?** No. Missing named buyers, weak “why now” evidence, several are tools/indie products not enterprise deals, Monday.com is not a realistic first cold-email win.

---

## 8. Evidence

Every remaining company has opportunity_evidence rows from the pipeline. Quality of that evidence is still mostly generic score narratives — not hiring/funding/intent proof strong enough for GT unlock.

---

## 9. Missing data (every survivor)

- **Decision maker** — all 11  
- **Country** — mostly Unknown  
- **Why us / budget indicator** — incomplete  
- **Verified intent evidence** — weak / generic  
- **Phone** — inconsistent attribution  

---

## 10. Exact blockers preventing first outreach

1. **Entity extraction is broken** — HN/Reddit/RSS create companies named “Database”, “Kubernetes”, domains like `main.tsx` / `array.map`.  
2. **0 decision makers** in DB for survivors.  
3. **GT production lock** requires DM-or-email + intent + all 7 questions — emails alone are not enough when intent/DM/country fail.  
4. **Acceptance unmet:** need 25 real, 20 verified sites, 15 DMs, 12 emails, 5 phones, 0 fakes, founder 95% QA.  
5. **Production send stays LOCKED** until founder manually accepts 20 random companies at ≥95%.

---

## What was changed (ops only)

| Change | Path |
|---|---|
| Disabled bad collectors | `.env` — indie_hackers, sec_edgar, github_trending |
| Funnel-first cleanup + enrich script | `scripts/operation_first_client.py` |
| Coherence pass | `scripts/operation_first_client_pass2.py` |
| Soft-deleted garbage companies + scrubbed TechCrunch emails | live Postgres |
| Live JSON | `docs/operation-first-client-live-report.json` |

**No new product engines. No new dashboards.**

---

## Next actions (still not feature-building)

1. **Pause** HN / Reddit / RSS / GitHub from creating `companies` until name+domain extractor is fixed (config/collector gate — not a new engine).  
2. **Only collect** Product Hunt + Dev.to into the company table for 48 hours.  
3. Manually or via existing enrichers: recover **Founder/CEO/CTO** for the 9 email-bearing accounts.  
4. Founder personally QA those 9 — if ≥8 feel emailable, that is the first real queue (still short of 25).  
5. Do **not** unlock Gmail/WhatsApp until acceptance criteria hit.

---

## Success definition status

> "If these were the only 10 companies in the world I could contact today, I would be happy emailing every one of them."

**FAIL today.** Closest honest set is the 9 with emails above — investigate, do not blast.
