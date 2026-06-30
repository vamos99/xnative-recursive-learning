# XNative Teknik Uygulama Rehberi

Durum: Final implementer girişi  
Sürüm: 1.0  
Tarih: 2026-06-22

## 1. Başlangıç noktası

Bu belge implementer için kısa yönlendirmedir. Exact alan, endpoint, job, config ve hata sözleşmeleri `IMPLEMENTATION_SPECIFICATION.md` içindedir. Uygulama sırası yalnız `MASTER_IMPLEMENTATION_BACKLOG.md` üzerinden değiştirilir.

## 2. Mimari özet

```text
Extension/manual input
-> localhost FastAPI
-> SQLite inbox + durable job queue
-> idempotent light/heavy pipeline
-> metadata/media/FTS/derived vector index
-> event + typed graph + retrieval
-> risk + multi-action ranking + diversity
-> generation + policy
-> review API/UI
-> feedback + evaluation + registry + rollback
```

SQLite tek doğruluk kaynağıdır. UI ve worker repository/unit-of-work katmanını kullanır. FAISS gibi indexler türetilmiş ve yeniden kurulabilir artefakttır.

## 3. Uygulama bağımlılık sırası

1. Domain contract ve migration.
2. Repository, audit, provenance ve idempotency.
3. Capture API ve extension outbox.
4. Durable queue ve stage runner.
5. Media lifecycle ve gerçek pHash.
6. NLP/CV/multimodal feature adapterleri.
7. Event, hybrid retrieval ve typed graph.
8. Source/ranking/generation.
9. Feedback, evaluation, drift ve controlled learning.
10. Review UI, observability, security ve release.

Bir sonraki fazın adapter veya modeli önceki veri sözleşmesini atlayamaz.

## 4. Başlangıç algoritmaları

- Lexical: FTS5 BM25 + word/character TF-IDF.
- Classification: MultinomialNB baseline; regularized logistic/online SGD champion adayı.
- Media: SHA-256 exact, dHash/pHash near-duplicate, Tesseract OCR.
- Multimodal: confidence-aware late fusion; küçük CLIP yalnız benchmark sonrası.
- Event: entity/time candidate graph + union-find.
- Retrieval: BM25+dense RRF; exact vector ground-truth, FAISS eşikte.
- Graph: typed edge + weighted metapath/PPR; GNN eşikte.
- Ranking: explainable multi-action utility + MMR.
- Source reliability: Beta posterior + decay.
- Learning: model registry; bandit başlangıçta kapalı.

Detaylı red/dene/eşikte kararları teknoloji radarındadır.

## 5. Kritik teknik invariantlar

- Capture DB commit olmadan `202` dönmez.
- Model inference DB transaction içinde çalışmaz.
- Aynı dedupe key için iki aktif job oluşmaz.
- Missing modality negatif evidence değildir.
- Risk/policy filtresi öğrenen model tarafından kaldırılamaz.
- Public X action side-effect'i yoktur.
- Model/feature/config version olmadan derived output yazılmaz.
- Provider yokluğu core job'ı `dead` yapmaz; local fallback çalışır.

## 6. Compatibility ve migration

- Ana API `/api/v1`; `/capture` extension için geçici alias.
- Prototipteki 0-100 skorlar hedefte 0-1 canonical ölçeğe taşınır.
- Mevcut `xnative/db/database.py` migration runner ile değiştirilir; veri kaybı olmadan fixture migration testi gerekir.
- Media hashing artık exact SHA-256 ve `dhash64-v1` perceptual hash olarak ayrıdır; legacy `phash` uyumluluk alanı perceptual hash değerine eşitlenir.
- Sabit formüller ve toplamsal online weights yalnız baseline/challenger karşılaştırması için korunur; production champion sayılmaz.

## 7. Hata ve fallback sırası

```text
provider unavailable -> local model -> lexical/rule -> partial evidence
GPU OOM -> unload -> CPU/cheap fallback -> retry if necessary
DOM drift -> selector metric/circuit -> manual import
remote media missing -> metadata/alt/quote evidence
worker crash -> lease recovery
model regression -> champion rollback
```

## 8. Doğrulama

Core komutları `TEST_PLAN.md` içindedir. Faz tamamlanması için ayrıca ilgili integration, performance, security ve document evidence gerekir. Mevcut 15 test sadece baseline helper davranışını kanıtlar.

## 9. Diyagramlar

- `diagrams/architecture_overview.mmd`: container/flow görünümü.
- `diagrams/capture_sequence.mmd`: capture transaction ve retry.
- `diagrams/learning_loop.mmd`: evaluation/champion/rollback.
- `diagrams/domain_erd.mmd`: domain ilişkileri.
- `diagrams/job_state.mmd`: durable queue state machine.
