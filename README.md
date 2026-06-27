# XNative Recursive Learning - Local-first Multimodal X Content System

> **Current status (2026-06-25): Phase 1 data backbone, Phase 2 API capture
> route/outbox work, and Phase 3 durable worker core are implemented.** The
> fixture-based scoring helpers, storage/API/job tests and worker runtime unit
> path run, but recorded DOM fixture capture, review UI, multimodal learning and
> Docker acceptance are not yet end-to-end complete.
> Do not treat the archived `TEST_OUTPUT.txt` or earlier Final QA document as a
> production-readiness statement.

XNative Recursive Learning is a local-first, human-approved content performance system for a single football-focused X account.

The project is not a news bot. It does not use X API, does not require Gemini/OpenAI/Claude, and does not perform automatic public actions. The MVP reads visible post data from a user-controlled browser capture flow or from manual/fixture import, analyses text + quote context + media metadata, generates X-native short Turkish football post suggestions, and keeps all publish decisions under human control.

## What changed in this version

- X API dependency removed from the target architecture.
- Paid model/API dependency removed from the default path.
- SQLite local-first data layer added.
- Phase 1 domain contracts, checksum migrations, repository/unit-of-work,
  idempotent capture persistence, durable job claim and feature provenance added.
- Phase 2 API route wiring added for `/health`, `/ready`, `/api/v1/captures`
  and temporary `/capture`.
- Browser extension permissions reduced and local outbox retry added for backend
  downtime. DOM posts are marked captured only after the background outbox accepts
  them.
- Capture parsing now filters avatar/UI media, redacts credential-like raw fields,
  carries parse-quality metadata and supports user-started manual archive import.
- A recorded DOM capture payload fixture now verifies parser -> API -> DB
  behavior and post/quote media scope preservation.
- A Playwright browser QA script runs the content script against a recorded DOM
  fixture and verifies the captured payload before background delivery.
- A background-service-worker QA script delivers that payload to the local API
  and verifies SQLite persistence without X API or credentials.
- Durable job queue state transitions, lease recovery, retry/dead-letter handling
  and a normalize-capture worker runner were added.
- Phase 3 worker runtime now includes generic job enqueue/dedupe, bounded
  backpressure, resource-class admission limits, priority aging, durable cursors,
  versioned cache invalidation, durable token bucket admission, micro-batch
  execution and a bounded worker loop.
- Queue/dead-letter visibility was added through `GET /api/v1/jobs`, manual
  retry through `POST /api/v1/jobs/{id}/retry`, and a Streamlit operations panel.
- Browser extension capture contract improved.
- Manual fixture import and sample mode added.
- Text, quote, media alt text, OCR fallback, pHash-style hashing, risk scoring, event scoring, source candidate scoring, draft generation, feedback learning, and weekly report modules added.
- Pytest coverage added for the local MVP.
- Docker and Docker Compose added.

## Core principles

1. **No X API in MVP** - no bearer token, developer account, paid endpoint, or write API.
2. **No mandatory paid service** - optional LLM fields exist, but template + style fallback works without keys.
3. **No automatic public action** - no tweet, retweet, like, follow, reply, or quote-tweet automation.
4. **Human approval** - suggestions remain pending until reviewed.
5. **X-native football language** - short, natural, contextual; not corporate news tone.
6. **RSS/news only as support** - verification/context only, not the main learning source.
7. **Local-first** - SQLite, local cache, fixtures, and offline sample mode.

## Current planning sources

- `docs/MASTER_IMPLEMENTATION_BACKLOG.md` - binding implementation order.
- `docs/IMPLEMENTATION_SPECIFICATION.md` - exact domain, DB, API, job, config and error contracts.
- `docs/ARCHITECTURE_DECISIONS.md` - accepted architecture decisions.
- `docs/REQUIREMENTS_TRACEABILITY.md` - requirement and evidence matrix.
- `docs/TEST_PLAN.md` - phase acceptance IDs and release evidence.
- `docs/TARGET_ARCHITECTURE.md` - target system architecture.
- `docs/ML_MULTIMODAL_LEARNING_STRATEGY.md` - NLP/CV/learning design.
- `docs/ALGORITHM_AND_PERFORMANCE_PLAN.md` - complexity, SLO and benchmark plan.
- `docs/ALGORITHM_TECHNOLOGY_RADAR.md` - project-wide algorithm decision radar.
- `docs/DATA_LIFECYCLE_AND_ARCHIVING.md` - archive and retention policy.
- `docs/GITHUB_REPOSITORY_PLAN.md` - repo name, ignored artifacts, commit/PR and Projects board plan.
- `docs/DOCUMENT_STATUS.md` - authoritative reading order and document status.

## Baseline developer run

```bash
cd twitter_agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest -q
PYTHONPATH=. python -m xnative.sample_pipeline
```

The current tests exercise helper functions, the fixture sample, Phase 1 storage
contracts, Phase 2 API capture persistence, parser hygiene, payload limits,
validation, manual archive import, recorded DOM payload fixture flow and the
browser content-script fixture flow and the Phase 3 job queue/worker runtime core,
including dead-letter visibility/retry,
stage error taxonomy, token bucket admission and micro-batch execution.
They do not yet prove the recorded DOM
fixture -> API -> database -> review -> feedback workflow. See the traceability
matrix for the missing acceptance coverage.

Optional browser QA:

```bash
scripts/qa/content_script_browser_check.sh
scripts/qa/background_api_db_check.sh
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API: http://localhost:8000/health
- UI: http://localhost:8501
- Worker: runs sample local pipeline

## Browser extension capture

The extension captures only content visible in the user's browser tab:

- post text
- author handle
- display name
- timestamp
- post URL
- quote tweet context
- media preview URL
- alt text when available
- visible metrics where present

It does not collect cookies, passwords, 2FA, hidden data, or credentials. It does not publish, like, follow, repost, reply, or quote.

## Main modules

- `xnative/capture` - visible DOM/manual fixture parsing.
- `xnative/domain` - Pydantic domain contracts and enums.
- `xnative/ingestion` - normalization, deduplication, event building.
- `xnative/media` - media metadata, optional OCR fallback, hashing, risk.
- `xnative/nlp` - text cleaning, language fallback, style memory, quality filters.
- `xnative/scoring` - event, candidate, risk, novelty/fatigue, final decision scores.
- `xnative/generation` - template fallback suggestions and optional LLM adapter.
- `xnative/learning` - feedback storage, online weight updates, weekly reports.
- `xnative/db` - SQLite migrations, repositories, unit-of-work and seed.
- `xnative/api` - optional FastAPI health/capture/suggestion routes.
- `xnative/ui` - optional Streamlit panel stub.

## Production boundary

The MVP creates suggestions and exports reviewable drafts. It does not post automatically. If future versions add publishing, that must be a separate, explicit, human-approved workflow.
