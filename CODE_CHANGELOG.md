# Code Changelog

Code changes were allowed in this revision.

## Main code changes

- Added `xnative/` local-first MVP package.
- Added SQLite schema and seed logic.
- Added Phase 1 implementation contracts in `xnative/domain/`.
- Added checksum-based SQL migration runner and `0001_initial.sql`.
- Added repository/unit-of-work layer for idempotent capture persistence, durable job claim and feature provenance.
- Added Phase 2 API route wiring for `/health`, `/ready`, `/api/v1/captures`, and temporary `/capture`.
- Added capture payload size/validation handling.
- Added capture parser hygiene: avatar/UI media filtering, credential-like raw-field redaction, query stripping, parse-quality propagation and manual archive fixture persistence.
- Added recorded DOM capture payload fixture coverage for parser -> API -> DB persistence and post/quote media scope preservation.
- Added Playwright CLI browser QA script for content-script DOM fixture capture behavior.
- Added background service-worker -> local API -> SQLite QA script.
- Added extension local-storage capture outbox, retry backoff, bounded outbox, accepted-after-queue DOM marking and reduced permissions.
- Added Phase 3 durable job state transitions, attempt tracking, lease recovery, retry/dead-letter handling and a normalize-capture worker runner.
- Added Phase 3 runtime controls: generic job enqueue/dedupe, bounded backpressure, resource-class admission limits, priority aging, durable cursors, versioned cache invalidation, worker loop and handler savepoint rollback.
- Added queue/dead-letter operations: `GET /api/v1/jobs`, `POST /api/v1/jobs/{id}/retry`, replay audit logging and a Streamlit queue/dead-letter panel.
- Added Phase 3 runtime algorithms: durable token bucket admission, bounded micro-batch execution and retryable/fatal/stage-timeout job error taxonomy.
- Added browser-visible capture parser and extension improvements.
- Added fixture/manual import flow.
- Added text cleaning, AI/news phrase filtering, quality filtering and style memory.
- Added media risk, OCR fallback, exact SHA-256 media hashing and dHash64 perceptual hashing utilities.
- Added content-addressed local media store manifest, reference counting and unreferenced media garbage collection.
- Added SQLite-backed media lifecycle records for local media objects, logical references and remote URL snapshots.
- Added media garbage-collection policy for quota/LRU cleanup, min-free-byte targets and protected original media.
- Added media lifecycle audit events for local object upserts, reference changes and remote snapshot records.
- Added bounded video/audio lifecycle planning for frame offsets, duration gates and limited audio extraction decisions.
- Added local multimodal evidence baseline for text, quote, alt/OCR, audio-video presence, relationship signals and missingness.
- Added offline text benchmark harness for TF-IDF, HashingVectorizer, MultinomialNB, logistic regression and SGD with time-split leakage audit.
- Added risk, event, source candidate, novelty/fatigue and final decision scoring.
- Added template-based X-native draft generator that works without LLM.
- Added feedback store, online weight updates and weekly report.
- Added pytest test suite with Phase 1 storage, Phase 2 API capture/parser/manual archive/recorded DOM payload, Phase 3 job queue/runtime and Phase 4 media hash/store acceptance tests.
- Added Dockerfile, docker-compose.yml and `.env.example`.

## Validation

`.venv/bin/pytest -q` -> 46 passed.
`.venv/bin/ruff check xnative tests scripts/docs/build_master_plan.py` -> passed.
`.venv/bin/ruff format --check xnative tests scripts/docs/build_master_plan.py` -> passed.
`.venv/bin/mypy xnative` -> passed.
`node --check extension/background.js` -> passed.
`node --check extension/content.js` -> passed.
`python -m json.tool extension/manifest.json` -> passed.
