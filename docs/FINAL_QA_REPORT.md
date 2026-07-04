# Baseline QA and Remediation Report

Date: 2026-06-22  
Status: Not release-ready

## Verified

- ZIP integrity and Python syntax checks passed during the baseline review.
- Fifteen baseline pytest tests pass in the pinned local development environment.
- The fixture sample reads ten posts and generates score/draft structures without API keys.
- No automatic tweet, like, follow, repost, reply or quote action was found.
- The new `xnative/` path has no mandatory paid model or X API dependency.
- Docker Compose configuration parses after creating `.env` from `.env.example`.

## Release blockers

- The extension/API route and localhost outbox issues have Phase 2 code coverage, including recorded DOM fixture, browser content-script fixture and background -> API -> DB fixture QA.
- The Streamlit file defines `run_app()` but never calls it; the required review workflow does not exist.
- The sample pipeline does not persist posts, events, media or suggestions and does not use learned weights.
- All ten fixture posts receive the same three template texts.
- Exact SHA-256 and `dhash64-v1` perceptual image hashing are separated; content-addressed local storage, manifest refcount, retention TTL metadata-only transition, deleted URL snapshot, SQLite lifecycle records, media lifecycle audit events, protected-original quota/LRU policy, unreferenced-file GC, bounded video/GIF frame planning and audio duration gates have unit/integration coverage. Real media decode/OCR/ASR remains Phase 5 work.
- OCR, media storage, style retrieval, novelty, bandit and learning helpers are disconnected from the main pipeline.
- A local multimodal evidence baseline now combines text, quote, alt/OCR, audio-video presence, relationship signals and missingness without paid APIs; embedding, CLIP and ASR are still missing.
- Hardware preflight now has test-covered RSS soft limit, CPU fallback, GPU/VRAM gate, single-heavy-model admission decisions and a no-heavy-model `xnative-preflight` report CLI; real target-machine soak is still missing.
- The worker now has a durable/retryable Phase 3 core and queue/dead-letter operations panel, but the full pipeline stage chain is still missing.
- Docker runtime health was not verified because the local Docker daemon was unavailable.
- Tests now cover recorded DOM fixture integration and Phase 4 media hashing basics; they still do not cover OCR integration, UI, Docker health or end-to-end learning.

## Binding next work

Implementation follows `MASTER_IMPLEMENTATION_BACKLOG.md`. A future Final QA may
mark a requirement complete only when the traceability matrix includes code,
automated test, performance/security impact and updated documentation evidence.

The implementation documentation is final at version 1.0, but documentation
readiness does not change this code-level `Not release-ready` status.
