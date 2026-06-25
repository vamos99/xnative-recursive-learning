# Muhendislik Baseline Kaniti

Tarih: 2026-06-25  
Faz: P0 tamam; P1/P2 kanitlari ve P3 worker runtime cekirdegi eklendi

## Ortam

- Python: 3.13.5 yerel gelistirme ortami.
- Destek hedefi: Python 3.11-3.13.
- Paket kaynagi: `pyproject.toml`.
- Kilit: `uv.lock`.
- Izole ortam: `.venv` (Git disi).

## Dogrulanan komutlar

```text
.venv/bin/pytest -q
46 passed in 0.53s

.venv/bin/ruff check xnative tests scripts/docs/build_master_plan.py
All checks passed

.venv/bin/ruff format --check xnative tests scripts/docs/build_master_plan.py
80 files already formatted

.venv/bin/mypy xnative
Success: no issues found in 74 source files

.venv/bin/python -m compileall -q xnative tests scripts/docs
exit 0

node --check extension/background.js
exit 0

node --check extension/content.js
exit 0

python -m json.tool extension/manifest.json
exit 0
```

## Belge QA

- Master DOCX: 9 sayfa render edildi; tum sayfalar goruldu.
- Master PDF: 7 sayfa `pypdf` ile dogrulandi; builder ayni kaynak ve stil sisteminden uretir.
- DOCX accessibility audit: 0 high, 0 medium, 0 low finding.
- DOCX ZIP CRC: temiz.
- Draw.io XML ve Excalidraw JSON: parse kontrolleri gecti.
- Algoritma teknoloji radari: capture, dedup, NLP, CV, video, multimodal fusion, event, retrieval, graph/HIN, ranking, bandit, optimizer, active learning, drift, cache ve evaluation aileleri kararlandirildi.

## Faz 1 kod kaniti

- Domain sozlesmeleri: `xnative/domain/`.
- Migration runner ve checksum: `xnative/db/migration_runner.py`, `xnative/db/migrations/0001_initial.sql`.
- Repository/unit-of-work: `xnative/db/repositories.py`.
- Acceptance testleri: `tests/integration/test_phase1_storage.py`.
- Kanitlanan kapilar: Pydantic validation, idempotent capture, tek aktif job, FK rollback, migration checksum ve feature provenance.

## Faz 2 kismi kod kaniti

- API app factory ve router kaydi: `xnative/api/main.py`.
- Capture/readiness endpointleri: `xnative/api/routes/capture.py`, `xnative/api/routes/health.py`.
- Extension outbox ve izinler: `extension/background.js`, `extension/manifest.json`.
- Extension content capture davranisi: `extension/content.js`.
- Acceptance testleri: `tests/integration/test_phase2_api_capture.py`.
- Kanitlanan kapilar: `/health`, `/ready`, `POST /api/v1/captures`, gecici `/capture` alias, DB persistence, idempotent duplicate response, 413 payload limiti, 422 validation, parser query temizleme, credential-like raw-field redaction, avatar/UI media filtreleme, parse-quality selector propagation, manual archive fixture persistence, recorded DOM payload fixture persistence, post/quote media scope preservation, extension JS syntax ve manifest JSON parse.

## Faz 3 kismi kod kaniti

- Durable job gecisleri: `xnative/db/repositories.py`.
- Worker runtime migration: `xnative/db/migrations/0002_worker_runtime.sql`.
- Worker rate-limit migration: `xnative/db/migrations/0003_worker_rate_limits.sql`.
- Worker runner ve handler: `xnative/worker/scheduler.py`, `xnative/worker/jobs.py`.
- Queue/dead-letter API ve UI: `xnative/api/routes/jobs.py`, `xnative/ui/streamlit_app.py`.
- Acceptance testleri: `tests/integration/test_phase3_jobs.py`.
- Kanitlanan kapilar: completed job, attempt kaydi, expired lease recovery, retryable failure, max attempt sonrasi dead-letter, unknown job type dead-letter, generic enqueue/dedupe, bounded backpressure, priority aging, resource admission, durable cursor, versioned cache invalidation, durable token bucket, bounded micro-batch, bounded worker loop, stage timeout/fatal hata ayrimi, handler hata rollback, dead-letter listeleme, replay audit, API job gorunumu ve Streamlit helper.

## Sinirlar

- Bu baseline mevcut 46 testin gectigini kanitlar; gercek Chrome content-script -> API -> DB -> review -> feedback akisini kanitlamaz.
- Docker Compose konfigurasyonu parse edildi; yerel Docker daemon calismadigi icin runtime health acceptance yapilmadi.
- Multimodal model kalitesi ve performans SLO'lari henuz benchmark edilmedi.
