# XNative Project Board

The authoritative ordered backlog is `docs/MASTER_IMPLEMENTATION_BACKLOG.md`.
This board is a compact status view and must not contain unsupported completion
claims.

## Completed baseline

- Phase 0: packaging, lockfile, cleanup, quality tools and evidence baseline.
- Phase 1: domain contracts, SQLite migration, repository/UoW and storage tests.
- Phase 2 partial: API capture route, readiness routes, bounded payload handling, parser hygiene, recorded DOM payload fixture, browser content-script fixture, background -> API -> DB QA, manual archive fixture persistence and extension outbox retry.
- Phase 3 partial: durable job state machine, retry/dead-letter, resource admission, priority aging, backpressure, cursor/cache, token bucket, micro-batch, worker loop, API job view and Streamlit dead-letter panel.
- Phase 4 done: exact SHA-256 media hash separated from `dhash64-v1` perceptual hash, Hamming threshold helper, small-batch cluster test, content-addressed local store, manifest refcount, SQLite lifecycle records, lifecycle audit events, retention snapshots, protected-original quota/LRU policy, unreferenced-file GC and bounded video/audio lifecycle gates.
- Baseline architecture, multimodal, performance, archive and provider policies.
- Editable Mermaid, draw.io and Excalidraw planning diagrams.
- Current master DOCX/PDF planning documents and visual QA.

## In progress

- Phase 2 remaining: live X selector drift smoke.
- Phase 3 remaining: full domain pipeline stage chain beyond normalize.
- Phase 5 partial: local multimodal evidence baseline for text, quote, visual alt/OCR, audio-video presence, relationship signal, missingness and offline text benchmark harness with learning-curve points.
- P14 documentation remains continuously synchronized with implementation.

## Todo roadmap

- Phase 5 remaining: real OCR adapter integration, visual embedding/caption fallback, video frame OCR/embedding, optional local ASR, real-data learning-curve report, confidence-aware late fusion and OpenCLIP/MobileCLIP benchmark.
- Phase 6: retrieval, event memory, FTS5/vector-ready contract, temporal clustering, novelty/fatigue and typed graph baselines.
- Phase 7: source discovery, reliability learning, uncertainty and approve/watch/reject workflow.
- Phase 8: candidate generation, multi-objective ranking, MMR/diversity, calibration and threshold gates.
- Phase 9: event/style-aware draft generation, safety gates and optional quota-aware provider fallback.
- Phase 10: feedback, reward, bandit experiments, drift/degradation, model registry and rollback.
- Phase 11: real review UI and operational dashboard.
- Phase 12: observability, security, backup/restore and performance gates.
- Phase 13: release test matrix and acceptance gates.
- Phase 14: final code-aligned docs, diagrams, cards and QA release package.

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
