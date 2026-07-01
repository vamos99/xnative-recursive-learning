# XNative Project Board

The authoritative ordered backlog is `docs/MASTER_IMPLEMENTATION_BACKLOG.md`.
This board is a compact status view and must not contain unsupported completion
claims.

## Completed baseline

- Phase 0: packaging, lockfile, cleanup, quality tools and evidence baseline.
- Phase 1: domain contracts, SQLite migration, repository/UoW and storage tests.
- Phase 2 partial: API capture route, readiness routes, bounded payload handling, parser hygiene, recorded DOM payload fixture, browser content-script fixture, background -> API -> DB QA, manual archive fixture persistence and extension outbox retry.
- Phase 3 partial: durable job state machine, retry/dead-letter, resource admission, priority aging, backpressure, cursor/cache, token bucket, micro-batch, worker loop, API job view and Streamlit dead-letter panel.
- Phase 4 partial: exact SHA-256 media hash separated from `dhash64-v1` perceptual hash, Hamming threshold helper, small-batch cluster test, content-addressed local store, manifest refcount, SQLite lifecycle records, lifecycle audit events, retention snapshots, protected-original quota/LRU policy, unreferenced-file GC and bounded video/audio lifecycle gates.
- Baseline architecture, multimodal, performance, archive and provider policies.
- Editable Mermaid, draw.io and Excalidraw planning diagrams.
- Current master DOCX/PDF planning documents and visual QA.

## In progress

- Phase 2 remaining: live X selector drift smoke.
- Phase 3 remaining: full domain pipeline stage chain beyond normalize.
- Phase 4 remaining: none after the video/audio lifecycle PR is merged; real decode/OCR/ASR moves to Phase 5.
- P14 documentation remains continuously synchronized with implementation.

## Next - Phase 4 plus Phase 2 gaps

- P2-005..007: recorded DOM fixture quality, quote/main media boundary and manual archive flow.
- P4-003..007: metadata-first archive, optional thumbnail/original policy, media lifecycle and video/audio limits are code-backed; next implementation focus can move to P5 media understanding adapters after merge.
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
