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
- Added extension local-storage capture outbox, retry backoff, bounded outbox, accepted-after-queue DOM marking and reduced permissions.
- Added Phase 3 durable job state transitions, attempt tracking, lease recovery, retry/dead-letter handling and a normalize-capture worker runner.
- Added Phase 3 runtime controls: generic job enqueue/dedupe, bounded backpressure, resource-class admission limits, priority aging, durable cursors, versioned cache invalidation, worker loop and handler savepoint rollback.
- Added browser-visible capture parser and extension improvements.
- Added fixture/manual import flow.
- Added text cleaning, AI/news phrase filtering, quality filtering and style memory.
- Added media risk, OCR fallback and pHash-style hashing utilities.
- Added risk, event, source candidate, novelty/fatigue and final decision scoring.
- Added template-based X-native draft generator that works without LLM.
- Added feedback store, online weight updates and weekly report.
- Added pytest test suite with 36 passing tests, including Phase 1 storage, Phase 2 API capture and Phase 3 job queue/runtime acceptance tests.
- Added Dockerfile, docker-compose.yml and `.env.example`.

## Validation

`.venv/bin/pytest -q` -> 36 passed.
`.venv/bin/ruff check xnative tests scripts/docs/build_master_plan.py` -> passed.
`.venv/bin/ruff format --check xnative tests scripts/docs/build_master_plan.py` -> passed.
`.venv/bin/mypy xnative` -> passed.
`node --check extension/background.js` -> passed.
`node --check extension/content.js` -> passed.
`python -m json.tool extension/manifest.json` -> passed.
