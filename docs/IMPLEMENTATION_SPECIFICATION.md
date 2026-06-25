# XNative Uygulama Spesifikasyonu

Durum: Uygulamaya hazır bağlayıcı sözleşme  
Sürüm: 1.0  
Tarih: 2026-06-22

## 1. Belge hiyerarşisi

Çelişki halinde öncelik sırası:

1. `MASTER_IMPLEMENTATION_BACKLOG.md`: uygulama sırası ve faz kapıları.
2. `IMPLEMENTATION_SPECIFICATION.md`: kod, veri, API, job ve konfigürasyon sözleşmeleri.
3. `REQUIREMENTS_TRACEABILITY.md`: gereksinim ve kanıt ilişkisi.
4. `ARCHITECTURE_DECISIONS.md`: değiştirilmesi ADR gerektiren kararlar.
5. `ALGORITHM_SELECTION_AND_EXPERIMENT_PLAN.md` ve `ALGORITHM_TECHNOLOGY_RADAR.md`: model/algoritma seçimi.
6. Diğer belgeler: açıklama, operasyon ve kullanıcı rehberi.

Kod bu belgelerden farklı davranacaksa önce ilgili backlog ve ADR güncellenir. “Kod öyle oldu” belge değişikliği için tek başına gerekçe değildir.

## 2. Sistem sınırı

XNative tek hesap için local-first içerik karar ve öğrenme sistemidir.

- Otomatik: capture sonrası doğrulama, arşivleme, feature çıkarımı, event oluşturma, retrieval, sıralama, taslak hazırlama, raporlama ve kontrollü öğrenme.
- İnsan kontrollü: X üzerinde yayın, takip, beğeni, repost, yanıt, quote ve bookmark.
- Yasak: cookie/credential toplama, görünmeyen/private içerik çekme, X rate-limit aşma, proxy rotasyonu, otomatik public action.
- Temel çalışma, API anahtarı ve ücretli servis olmadan devam eder.

## 3. Hedef çalışma topolojisi

Production hedefi tek makinedir:

- `extension`: görünür DOM capture ve disk tabanlı outbox.
- `api`: `127.0.0.1:8000` FastAPI.
- `worker-light`: normalization, DB, FTS, hash ve hafif feature işleri; en fazla 2 eşzamanlı iş.
- `worker-heavy`: OCR/embedding/ASR/vision; tek eşzamanlı iş.
- `db`: SQLite WAL + FTS5.
- `media`: content-addressed yerel dosya alanı.
- `ui`: local review workspace; API üzerinden çalışır, doğrudan SQL yazmaz.

Başlangıçta Redis, Kafka, Celery, Airflow, Milvus, Kubernetes veya ayrı PostgreSQL servisi yoktur.

## 4. Hedef Python paket yapısı

Mevcut `xnative/` korunur; aşağıdaki ownership sınırları tamamlanır:

```text
xnative/
  api/                 # HTTP router, auth, request/response DTO
  capture/             # DOM/manual input contract; DB bilmez
  core/                # config, IDs, clock, errors, enums
  domain/              # Pydantic domain contracts; framework bağımsız
  db/                  # migrations, repositories, unit-of-work
  ingestion/           # normalize, exact dedup, event candidate
  jobs/                # durable queue, claim/retry/dead-letter
  media/               # store, exact/perceptual hash, OCR, frame/ASR
  nlp/                 # lexical/dense text feature adapters
  retrieval/           # FTS, dense, RRF, event/source retrieval
  graph/               # typed edges, metapath, PPR; GNN adapter later
  scoring/             # feature schema, risk, utility, calibration
  generation/          # template/local/provider chain and policy
  learning/            # feedback, evaluation, registry, drift, bandit
  ui/                  # API client and review screens
  observability/       # metrics, structured log, diagnostics
```

Kurallar:

- Router, worker ve UI doğrudan SQL kullanmaz; repository/unit-of-work kullanır.
- Domain modelleri FastAPI, SQLite row veya Streamlit nesnesine bağımlı olmaz.
- Feature hesapları saf fonksiyon veya versionlanmış adapter olur.
- Provider/model adapteri interface arkasındadır; import edilmemesi core akışı bozmaz.
- Türetilmiş her çıktı `model_version`, `feature_version`, `config_hash` ve provenance taşır.

## 5. Ortak kimlik ve zaman sözleşmesi

- Uygulama kimlikleri standart kütüphane UUIDv4 string olarak üretilir; sıralama kimlikten değil `created_at` ve cursor'dan yapılır.
- X post ID varsa `platform_post_id` ayrı unique alanıdır.
- Tüm timestamp alanları UTC ISO-8601 olarak API'de, UTC integer microsecond olarak DB'de saklanır.
- `captured_at`: extension/API'nin gördüğü zaman.
- `platform_created_at`: DOM'da güvenilir şekilde görülen platform zamanı; yoksa `null`.
- `observed_at`: metric snapshot zamanı.
- `created_at`/`updated_at`: yerel kayıt zamanı.
- Soft-delete gereken tablolar `deleted_at` taşır; audit/feedback fiziksel silinmez.

## 6. Domain sözleşmeleri

### 6.1 CapturedPost

Zorunlu alanlar:

| Alan | Tip | Kural |
|---|---|---|
| `id` | UUIDv4 | Yerel kimlik |
| `schema_version` | int | Başlangıç `1` |
| `platform` | literal | `x` |
| `platform_post_id` | str/null | Varsa unique |
| `canonical_url` | URL | `https://x.com/.../status/...` normalize edilir |
| `author_handle` | str | Lowercase; `@` saklanmaz |
| `visible_text` | str | En fazla 20.000 karakter |
| `quote_post` | object/null | ID/URL/author/text ayrık alanlar |
| `media` | list | En fazla 4 asset |
| `visible_metrics` | object | Like/repost/reply/view nullable non-negative int |
| `platform_created_at` | datetime/null | UTC |
| `captured_at` | datetime | UTC |
| `capture_source` | enum | `extension`, `manual_json`, `manual_csv`, `fixture` |
| `selector_version` | str/null | Extension capture'da zorunlu |
| `idempotency_key` | str | SHA-256 canonical payload anahtarı |
| `raw_payload_hash` | str | SHA-256; raw payload saklanmasa da tutulur |

Bir capture boş text taşıyabilir; bu durumda en az bir media veya quote zorunludur.

### 6.2 MediaAsset

| Alan | Tip | Kural |
|---|---|---|
| `id` | UUIDv4 | Yerel kimlik |
| `post_id` | UUIDv4 | FK, cascade fiziksel silme yok |
| `kind` | enum | `image`, `video`, `gif`, `audio`, `unknown` |
| `source_url` | URL/null | Credential/query secret temizlenir |
| `alt_text` | str/null | En fazla 10.000 karakter |
| `mime_type` | str/null | Allowlist ile doğrulanır |
| `byte_size` | int/null | Non-negative |
| `width`,`height`,`duration_ms` | int/null | Non-negative |
| `exact_sha256` | str/null | İndirilen byte varsa |
| `perceptual_hash` | str/null | Gerçek dHash/pHash sonucu |
| `storage_policy` | enum | `metadata`, `thumbnail`, `original` |
| `local_path` | str/null | Media root'a göre relative |
| `availability` | enum | `remote`, `stored`, `missing`, `deleted`, `blocked`, `error` |

### 6.3 Event

`id`, `event_type`, `title`, `status`, `started_at`, `last_seen_at`, `confidence`, `post_count`, `source_count`, `entity_ids`, `cluster_version`, `created_at`, `updated_at`.

`status`: `candidate`, `active`, `cooling`, `closed`, `merged`. Merge geri alınabilir; `merged_into_event_id` ve audit kaydı zorunludur.

### 6.4 Candidate ve Suggestion

- Candidate: kaynak post/event, feature snapshot, utility bileşenleri, risk ve selector nedeni.
- Suggestion: candidate, variant family, draft text, evidence IDs, policy sonuçları ve review state.
- Review state: `pending`, `approved`, `edited`, `rejected`, `ignored`, `expired`.
- Approved olmak X üzerinde yayınlandığı anlamına gelmez. `manual_post` ayrı feedback olayıdır.

### 6.5 Feedback ve PerformanceSnapshot

Feedback append-only'dir:

- `action`: `approve`, `edit`, `reject`, `ignore`, `manual_post`, `undo`.
- `reason_codes`: versionlanmış enum listesi.
- `original_text`, `edited_text`, `edit_distance` yalnız uygun action'da.
- `actor`: başlangıçta `local_user`.
- `occurred_at`, `model_version`, `feature_version`, `suggestion_id`.

PerformanceSnapshot append-only'dir; platform metriği, gözlem zamanı ve giriş yöntemi taşır. Aynı post ve `observed_at` için unique constraint vardır.

## 7. SQLite fiziksel şema

Migration aracı: Alembic değil, ilk sürümde versionlanmış saf SQL migration runner. Dosya adı `NNNN_description.sql`; `schema_migrations(version, checksum, applied_at)` tablosu checksum doğrular.

Zorunlu tablolar:

```text
captured_posts, media_assets, post_metrics, capture_inbox
jobs, job_attempts, dead_letters
entities, events, event_posts, graph_nodes, graph_edges
features, embeddings, model_outputs
candidates, suggestions, feedback_events, performance_snapshots
sources, source_candidates, source_reliability_snapshots
style_examples, model_registry, experiment_runs
audit_log, settings
captured_posts_fts (FTS5)
```

Temel constraint/indexler:

- `captured_posts(platform, platform_post_id)` partial unique, ID null değilse.
- `captured_posts(idempotency_key)` unique.
- `media_assets(exact_sha256)` non-unique index; aynı blob content store'da tek dosya.
- `jobs(dedupe_key)` active-state partial unique.
- `jobs(status, priority, available_at, created_at)` claim index.
- `features(owner_type, owner_id, feature_name, feature_version)` unique.
- `embeddings(owner_type, owner_id, model_version)` unique.
- `graph_edges(src_id, edge_type, dst_id, observed_at)` unique.
- `feedback_events(suggestion_id, occurred_at)` index.
- Tüm foreign keyler `PRAGMA foreign_keys=ON` altında test edilir.

SQLite ayarları:

```text
journal_mode=WAL
synchronous=NORMAL
foreign_keys=ON
busy_timeout=5000
temp_store=MEMORY
```

Transaction kısa tutulur. Model inference transaction içinde yapılmaz.

## 8. API sözleşmesi

Ana prefix `/api/v1`. `/capture`, mevcut extension için geçici compatibility alias'tır ve `/api/v1/captures` ile aynı handler'a gider.

| Method/path | Başarı | Amaç |
|---|---:|---|
| `GET /health` | 200 | Process canlı; dependency kontrol etmez |
| `GET /ready` | 200/503 | DB, migration, disk ve queue readiness |
| `POST /api/v1/captures` | 202 | Capture inbox + job atomik oluşturma |
| `POST /capture` | 202 | Geçici alias; response header `Deprecation: true` |
| `GET /api/v1/inbox` | 200 | Cursor pagination ve filtre |
| `GET /api/v1/posts/{id}` | 200 | Post, media ve provenance |
| `GET /api/v1/events` | 200 | Event listesi |
| `GET /api/v1/events/{id}` | 200 | Evidence ve komşular |
| `GET /api/v1/suggestions` | 200 | Pending/history review kuyruğu |
| `GET /api/v1/suggestions/{id}` | 200 | Skor açıklaması ve kanıt |
| `POST /api/v1/suggestions/{id}/feedback` | 201 | Append-only feedback |
| `GET /api/v1/source-candidates` | 200 | Approve/watch/reject adayları |
| `POST /api/v1/source-candidates/{id}/decision` | 201 | İnsan kararı; follow yapmaz |
| `GET /api/v1/jobs` | 200 | Queue/dead-letter görünümü |
| `POST /api/v1/jobs/{id}/retry` | 202 | Yetkili manual retry |
| `GET /api/v1/diagnostics` | 200 | Secret-redacted durum paketi |

Capture response:

```json
{
  "capture_id": "uuidv4",
  "job_id": "uuidv4",
  "status": "accepted",
  "duplicate": false
}
```

Hata gövdesi:

```json
{
  "error": {
    "code": "CAPTURE_VALIDATION_FAILED",
    "message": "User-safe message",
    "correlation_id": "uuidv4",
    "details": {}
  }
}
```

Standart statuslar: validation `422`, auth `401`, bulunamadı `404`, conflict/idempotency `409`, payload büyük `413`, rate limit `429`, dependency hazır değil `503`.

Pagination cursor tabanlıdır; varsayılan `limit=50`, maksimum `200`. Liste endpointleri büyük nested model output döndürmez.

## 9. Local API güvenliği

- Varsayılan bind yalnız `127.0.0.1`.
- Extension ve UI, kurulumda üretilen en az 32-byte local bearer token kullanır.
- Token loglanmaz; `.env` Git dışıdır.
- CORS yalnız extension origin ve açıkça ayarlanmış local UI originine izin verir.
- Capture body limiti 512 KiB; medya byte'ı capture JSON içinde alınmaz.
- URL allowlist `x.com`, `twitter.com` ve izinli media hostlarıdır.
- Log redaction: token, cookie, authorization, query secret ve local absolute path.

## 10. Job queue sözleşmesi

Durumlar:

```text
pending -> running -> completed
pending -> running -> retry -> running
pending -> running -> dead
running -> pending  (lease timeout recovery)
pending/retry -> cancelled (yalnız güvenli admin işlemi)
```

Alanlar: `id`, `job_type`, `payload_ref`, `status`, `priority`, `resource_class`, `dedupe_key`, `attempt_count`, `max_attempts`, `available_at`, `lease_owner`, `lease_expires_at`, `last_error_code`, timestamps.

Varsayılanlar:

- Priority: live capture `100`, user action `90`, retry `70`, report `40`, backfill `20`.
- Aging: bekleyen her 5 dakikada effective priority +1; üst sınır 99.
- Retry: 5 deneme; 2, 8, 32, 120, 300 saniye üst sınırları içinde full jitter.
- Lease: hafif iş 60 saniye, ağır iş 10 dakika; heartbeat lease'in üçte birinde.
- Dead-letter: non-retryable hata veya max attempt.
- Resource semaphore: `heavy=1`, `light=2`, `io=2`; toplam process RSS hard admission kontrolü.
- Dedupe key: `job_type:owner_id:feature_or_model_version`.

Claim işlemi tek transaction'da compare-and-set ile yapılır. Worker kapanması `running` işi kaybettirmez; lease dolunca yeniden alınır.

## 11. Pipeline stage sözleşmesi

Bağlayıcı sıra:

```text
capture -> validate -> persist -> normalize -> exact_dedup
-> cheap_features -> event_link -> risk_gate -> candidate_score
-> optional_heavy_features -> rerank -> select -> generate
-> post_policy -> review_queue -> feedback/evaluation
```

Her stage:

- Tek owner kaydı üzerinde idempotent çalışır.
- Input ref ve version alır; output ref, status, latency, warnings ve provenance döndürür.
- `success`, `partial`, `skipped`, `retryable_error`, `fatal_error` sonuçlarından birini üretir.
- Eksik modality `0` score değildir; `missing=true` ve ayrı confidence ile saklanır.
- Ucuz fallback başarısız değilse ağır model zorunlu değildir.
- Risk/policy stage öğrenen model tarafından kaldırılamaz.

Heavy escalation koşulu başlangıç politikası:

- Cheap confidence `<0.55`, veya
- Text-image contradiction `>0.60`, veya
- Candidate utility ilk yüzde 10 içinde ve media feature eksik, veya
- Kullanıcı manual reprocess istedi.

Bu değerler config/version altında tutulur; etiket oluşunca calibration ile değiştirilir.

## 12. Algoritma başlangıç profili

İlk production champion'ları:

| Alan | Champion | Challenger koşulu |
|---|---|---|
| Text retrieval | FTS5 BM25 + word/char TF-IDF | multilingual 384-d embedding + RRF |
| Text classifier | MultinomialNB hız baseline; logistic/SGD kalite champion | Time-split macro-F1/log-loss artışı |
| Media dedup | SHA-256 + dHash/pHash | ORB/SSIM yalnız crop golden sette uplift |
| Vision | Metadata/alt/OCR | Küçük pretrained CLIP benchmark sonrası |
| Fusion | Açıklanabilir rule/late score | Calibrated logistic; sonra HistGB |
| Event | Entity/time candidate graph + union-find | Temporal DBSCAN/HDBSCAN |
| Graph | Weighted metapath + PPR | Node2Vec/GNN veri eşiğinde |
| Ranking | Normalize multi-action utility + MMR | Calibrated logistic, sonra LambdaMART |
| Source trust | Beta posterior + decay | Hierarchical Bayes veri eşiğinde |
| Exploration | Kapalı | Thompson Sampling yalnız güvenli format ve yeterli log sonrası |

Milvus, HGT, LSTM, tam RL ve meta-sezgisel optimizer başlangıç bağımlılığı değildir.

## 13. Model ve experiment registry

Her deney şu alanları taşır:

- `experiment_id`, `backlog_id`, `hypothesis`, `owner`, `started_at`, `completed_at`.
- Dataset snapshot hash, split policy, segment counts ve leakage audit sonucu.
- Feature/model/config/code hash ve lisans.
- Hyperparameter search space, seed listesi ve compute bütçesi.
- Quality, calibration, risk, latency, RSS/VRAM ve disk metrikleri.
- Champion karşılaştırması, confidence interval ve kötüleşen segmentler.
- Karar: `reject`, `repeat`, `shadow`, `promote`, `rollback`.

Promotion hard gate:

- Risk recall gerilemez.
- Primary metric iyileşmesi bootstrap %95 CI ile sıfırın üstünde veya önceden tanımlı minimum practical uplift'i geçer.
- Calibration ve segment guardrail tolerans içinde.
- Hedef cihaz resource/SLO kapıları geçer.
- Shadow en az 7 gün veya 500 uygun karar örneği; hangisi daha geçse.

## 14. Konfigürasyon sözleşmesi

Environment isimleri ve başlangıç değerleri:

```text
XNATIVE_ENV=production
XNATIVE_BIND_HOST=127.0.0.1
XNATIVE_PORT=8000
XNATIVE_DB=data/xnative.sqlite3
XNATIVE_DATA_DIR=data
XNATIVE_MEDIA_DIR=data/media
XNATIVE_LOGS_DIR=data/logs
XNATIVE_LOCAL_TOKEN_FILE=data/secrets/local_api_token
XNATIVE_MAX_CAPTURE_BYTES=524288
XNATIVE_MAX_CAPTURE_POSTS=100
XNATIVE_MAX_MEDIA_PER_POST=4
XNATIVE_DB_BUSY_TIMEOUT_MS=5000
XNATIVE_LIGHT_WORKERS=2
XNATIVE_HEAVY_WORKERS=1
XNATIVE_APP_RSS_SOFT_MB=5632
XNATIVE_RETRY_MAX_ATTEMPTS=5
XNATIVE_RISK_REVIEW_THRESHOLD=0.60
XNATIVE_HEAVY_ESCALATION_CONFIDENCE=0.55
XNATIVE_LLM_PROVIDER=none
XNATIVE_VISION_PROVIDER=local
XNATIVE_RETENTION_RAW_DAYS=30
XNATIVE_RETENTION_THUMBNAIL_DAYS=180
XNATIVE_MEDIA_BUDGET_GB=10
```

Kurallar:

- Config parse hatası startup'ı durdurur; sessiz fallback yok.
- Secret değerler `repr`, log ve diagnostics'e girmez.
- 0-100 prototip skorları Phase 8'de 0-1 canonical ölçeğe migrate edilir.
- Provider `none` iken bütün core acceptance testleri geçer.

## 15. Gözlemlenebilirlik

Her request/job logu JSON ve şu alanları taşır: timestamp, level, correlation_id, capture/job/owner ID, stage, duration_ms, outcome, error_code, model_version. Visible text ve ham provider payload varsayılan loglanmaz.

Zorunlu metrikler:

- Capture accepted/duplicate/rejected, parse failure ve selector version.
- Queue depth/age, retry/dead count, lease recovery.
- Stage p50/p95/p99 ve throughput.
- Model load/inference, cache hit, OOM/fallback.
- DB busy/transaction duration, disk/RSS/VRAM.
- Suggestion review action, calibration ve segment drift.

## 16. Hata sınıfları

- `ValidationError`: retry yok, 4xx.
- `Duplicate`: başarı benzeri idempotent sonuç; yeni job yok.
- `TransientDependencyError`: capped retry + jitter.
- `ModelUnavailable`: local fallback; gerekirse partial.
- `ResourceExhausted`: heavy unload, işi retry; UI/API yaşamaya devam eder.
- `PolicyBlocked`: suggestion review'a veya blocked durumuna; otomatik aşılmaz.
- `PermanentDataError`: dead-letter ve provenance.
- `InvariantViolation`: işlemi durdur, high-severity audit ve readiness 503 gerekebilir.

## 17. Faz 1 için doğrudan dosya planı

İlk kodlama sırası değiştirilemez:

1. `xnative/domain/` altında contract ve enumlar; P1-001.
2. `xnative/db/migrations/0001_initial.sql` ve runner; P1-002.
3. Repository ve unit-of-work interface/SQLite implementasyonu; P1-003.
4. WAL/busy-timeout/idempotency transaction testleri; P1-004.
5. Audit/provenance/model-feature version kayıtları; P1-005.
6. Veri sınıfı ve retention alanları; P1-006.

Faz 1 tamamlanmadan API route, CLIP, FAISS, GNN, ranker veya UI uygulamasına geçilmez.

## 18. Definition of Done

Bir backlog maddesi yalnız şu kanıtların tamamıyla `TAMAM` olur:

1. Kod/migration yolu ve review edilebilir diff.
2. Pozitif, negatif ve boundary otomatik testleri.
3. İlgili SLO/resource/security etkisi.
4. Migration/rollback veya backward compatibility açıklaması.
5. Traceability satırı ve gerekiyorsa ADR/diyagram güncellemesi.
6. Komut, ortam, commit ve artefakt hash'i olan doğrulama sonucu.
