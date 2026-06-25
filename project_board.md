# XNative Project Board

The authoritative ordered backlog is `docs/MASTER_IMPLEMENTATION_BACKLOG.md`.
This board is a compact status view and must not contain unsupported completion
claims.

## Completed baseline

- Phase 0: packaging, lockfile, cleanup, quality tools and evidence baseline.
- Phase 1: domain contracts, SQLite migration, repository/UoW and storage tests.
- Phase 2 partial: API capture route, readiness routes, bounded payload handling, parser hygiene, manual archive fixture persistence and extension outbox retry.
- Phase 3 partial: durable job state machine, retry/dead-letter, resource admission, priority aging, backpressure, cursor/cache, token bucket, micro-batch, worker loop, API job view and Streamlit dead-letter panel.
- Baseline architecture, multimodal, performance, archive and provider policies.
- Editable Mermaid, draw.io and Excalidraw planning diagrams.
- Current master DOCX/PDF planning documents and visual QA.

## In progress

- Phase 2 remaining: real Chrome recorded DOM fixture E2E and browser-level quote/main media boundary.
- Phase 3 remaining: full domain pipeline stage chain beyond normalize.
- P14 documentation remains continuously synchronized with implementation.

## Next - Phase 4 plus Phase 2 gaps

- P2-005..007: recorded DOM fixture quality, quote/main media boundary and manual archive flow.
- P4-001..007: exact SHA vs perceptual hash, metadata-first archive, optional thumbnail/original policy and media lifecycle.
- P11 later: review/dead-letter UI visibility.

## Blocked release claims

- Browser capture DOM fixture end-to-end.
- Real review UI.
- Multimodal NLP/CV pipeline.
- Persistent recursive learning.
- Docker runtime acceptance.

## Guardrails

- No mandatory X API or paid service.
- No automatic public action.
- Local fallback for every optional provider.
- Human approval for publishing and following.
