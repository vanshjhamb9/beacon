# IGF v1 Architecture

## North star

Increase **Revenue Ready Companies**. Identity Graph is the only path from signal → company.

## Flow

```
Signal
  → Entity Extraction (CandidateEngine)
  → Evidence Collection (IdentityProviders)
  → Website Discovery v2 (graph → metadata → GitHub → LinkedIn → Crunchbase → OG/JSON-LD → EROWD compose)
  → Identity Scoring
  → Canonical Merge
  → Admit / Reject / Signal-only
  → Business Enrichment (downstream CIR / GT / REV)
```

## Rules

1. Conversation sources never create identity.
2. Intent sources never create identity.
3. Every field is `IdentityEvidence` with source, confidence, collector, timestamp.
4. Unknown > incorrect. Never guess domains.
5. Compose with EROWD discovery — do not redesign EROWD/CRE/CIR.

## Persistence (append-only)

- `igf_resolution_runs`
- `igf_identity_candidates`
- `igf_identity_evidence`
- `igf_canonical_companies`
- `igf_funnel_snapshots`

## Compatibility

- Existing `/entity-resolution`, `/company-intelligence`, `/revenue-execution-validation` remain.
- Live ingest: EROWD gate then IGF gate in `IntelligenceService.process_raw_event`.

## Live migration

1. `alembic upgrade head` → `20260724_0040`
2. `POST /identity-graph/rebuild?limit=1500`
3. Re-collect GitHub (homepage required) for new identity candidates
4. Run contact recovery on verified domains
5. Measure Identity Resolution Funnel + Revenue Ready downstream
