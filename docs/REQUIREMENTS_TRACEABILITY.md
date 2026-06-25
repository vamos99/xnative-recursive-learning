# Gereksinim Izlenebilirlik Matrisi

## Kullanim

Bu matris, gereksinimlerin belge/kod/test kanitlarini baglar. Exact sozlesme `IMPLEMENTATION_SPECIFICATION.md`, test kimlikleri `TEST_PLAN.md` icindedir. Kanit olmadan durum `TAMAM` yapilamaz.

| Gereksinim | Backlog | Mevcut durum | Zorunlu kanit |
|---|---|---|---|
| X API olmadan capture | P2-001..007 | API capture route'u DB'ye yaziyor; payload/validation siniri ve extension localhost outbox/retry var; DOM fixture E2E henuz eksik | `tests/integration/test_phase2_api_capture.py` + extension -> API -> DB E2E |
| API key olmadan sample | P0-004, P3 | Kismen calisiyor | Temiz kurulum acceptance |
| Yerel SQLite | P1 | Phase 1 veri omurgasi tamam: checksum migration, WAL/PRAGMA, repository/UoW ve FK testleri var | `tests/integration/test_phase1_storage.py` + P1-DB-001..005 |
| Dedup | P1, P3, P4 | Capture idempotency DB seviyesinde tamam; ingestion/media dedup sonraki fazlarda | Idempotency integration + P3/P4 pipeline testleri |
| Gercek pHash | P4-001..002 | Yok; SHA kisaltmasi var | Similar-image fixture |
| OCR fallback | P5-002 | Fonksiyon iskeleti, pipeline disi | Mock + gercek opsiyonel test |
| Quote context | P5, P6 | Basit text concat | Retrieval/event integration |
| Multimodal anlama | P5 | Yok | Golden multimodal set |
| Event memory | P6 | Basit keyword event | Cluster/retrieval metrics |
| Kaynak adayi | P7 | Sabit feature skoru | History + uncertainty test |
| Cok hedefli ranking | P8 | Sabit formula | Offline metrics + explain |
| Farkli taslaklar | P9 | Ayni 3 sabit taslak | Diversity/style tests |
| Feedback learning | P10 | DB helper var, pipeline disi | Feedback -> model -> score E2E |
| Gercek review UI | P11 | Bos Streamlit dosyasi | UI E2E ve screenshot QA |
| Worker/retry | P3, P12 | Durable job tablosu, capture enqueue, generic enqueue/dedupe, tekil claim, lease recovery, savepoint rollback, retry, backpressure, resource admission, priority aging, cursor/cache, token bucket, micro-batch, worker loop, API job gorunumu ve Streamlit dead-letter panel temeli var | `tests/integration/test_phase3_jobs.py` + restart/runtime UI smoke testi |
| Arsiv/retention | P4 | Yok | Quota/GC/deletion tests |
| Docker acceptance | P13 | Config parse olur; runtime kaniti yok | Health/readiness compose test |
| Dokuman dogrulugu | P14 | Uygulama dokumanlari v1.0 final; kod kanitlari fazlarla eklenecek | Kod-test-doc cross-check + generated DOCX/PDF QA |
| Hedef donanimda surekli calisma | P5-009, P12 | Tasarim guncellendi; benchmark yok | 8 GB/i5/GTX 1050 soak ve OOM testi |
| Gemini opsiyonel enrichment | P9-004, P9-007 | Politika dogrulandi; adapter yok | Proje tier/kota/cost/fallback integration |
| Algoritma secimi ve model terfisi | P5-010..012, P6-007..010, P8-008..010, P10-008..010, P12-007..008, P13-007 | Karar matrisi ve teknoloji radari var; deney altyapisi yok | Time-split benchmark + resource profile + champion/challenger kaydi |
| CLIP tabanli gorsel-metin kaniti | P5-012 | Karar ve benchmark kapisi var; adapter yok | Turkce zero-shot/retrieval golden set + CPU/GPU/RAM profili |
| Typed graph/HIN ve GNN | P6-008, P6-010 | Sema karari var; graph omurgasi yok | Metapath/PPR baseline + GNN challenger time-split ablation |
| Yerel vector index | P6-009 | TF-IDF var; dense index yok | Exact recall ground-truth + FAISS latency/RAM benchmarki |
| Veri hatti algoritmalari | P3-007 | Bounded backpressure, priority aging, resource-class admission, durable token bucket, micro-batch ve full-jitter retry temeli var; soak profili yok | Retry storm, queue starvation, restart ve memory-pressure testleri |

## Kanit standardi

Bir satir `TAMAM` olabilmek icin:

1. Kod/migration yolu.
2. Otomatik test adi ve sonucu.
3. Varsa benchmark/SLO sonucu.
4. Guncel mimari veya operasyon belgesi.
5. `TEST_PLAN.md` icindeki ilgili kabul ID'si ve result artefakti.
