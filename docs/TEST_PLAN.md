# XNative Test ve Kabul Planı

Durum: Bağlayıcı release sözleşmesi  
Tarih: 2026-06-22

## 1. Genel kurallar

- Her test bir backlog veya requirement ID taşır.
- Network/model bağımlı testler marker ile ayrılır; core suite anahtarsız ve offline geçer.
- Time, random seed, provider ve model adapterleri testte enjekte edilir.
- Test fixture'ı gerçek kullanıcı credential/cookie veya private içerik taşımaz.
- “HTTP 200” tek başına başarı değildir; DB state, audit, job ve fallback doğrulanır.

## 2. Test katmanları

| Katman | Hedef süre | Zorunlu kullanım |
|---|---:|---|
| Unit | <30 sn | Saf domain, parser, scoring, algorithm ve validation |
| Repository/migration | <60 sn | Constraint, transaction, rollback, concurrency |
| Integration | <3 dk | API -> DB -> queue -> worker stage |
| Contract | <2 dk | Extension DOM ve API schema compatibility |
| Model/golden | Ayrı profil | Multimodal kalite ve regression |
| UI E2E | Ayrı profil | Review/feedback akışı ve accessibility |
| Performance | Release/nightly | SLO, RSS/VRAM, disk ve soak |
| Security/privacy | Release | Auth, bind, CSP, redaction, retention |

## 3. Faz kabul matrisi

| Test ID | Backlog | Senaryo | Beklenen |
|---|---|---|---|
| `P1-DB-001` | P1-001..003 | Aynı platform ID/idempotency iki kez | Tek post, tek aktif job |
| `P1-DB-002` | P1-002 | Migration boş ve fixture DB'de | Aynı schema checksum, veri kaybı yok |
| `P1-DB-003` | P1-002 | FK ihlali | Transaction rollback |
| `P1-DB-004` | P1-004 | İki worker aynı işi claim eder | Yalnız biri `running` |
| `P1-DB-005` | P1-005 | Feature yazımı | Source/model/config provenance tam |

2026-06-23 kod kaniti: `tests/integration/test_phase1_storage.py`, `P1-DB-001` ile `P1-DB-005` icin otomatik acceptance kapsami ekler. Bu test dosyasi P1 veri omurgasini kanitlar; P2/P3 extension, API endpoint ve worker runtime akisini kanitlamaz.
| `P2-CAP-001` | P2-001..003 | Extension capture backend açık | 202, outbox silinir, DB/job oluşur |
| `P2-CAP-002` | P2-003 | Backend kapalı sonra açılır | Outbox kaybetmez, jitter retry ile teslim |
| `P2-CAP-003` | P2-004 | Capture kapalı/açık | DOM kaydı erken işaretlenmez |
| `P2-CAP-004` | P2-005 | Quote + media fixture | Avatar/UI media diye alınmaz |
| `P2-SEC-001` | P2 | Cookie/Authorization DOM/storage | Payload ve logda yok |

2026-06-27 kismi kod kaniti: `tests/integration/test_phase2_api_capture.py`, `P2-001` icin `/health`, `/ready`, `/api/v1/captures`, gecici `/capture` alias, 413 payload limiti ve 422 validation davranisini dogrular. Ayni dosya parser seviyesinde query temizleme, credential-like raw-field redaction, avatar/UI media filtreleme, parse-quality selector propagation, manual archive fixture persistence, kaydedilmis DOM payload fixture -> API -> DB persistence ve post/quote media scope preservation davranisini dogrular. `scripts/qa/content_script_browser_check.sh` Playwright CLI ile gercek browser ortaminda content-script DOM fixture capture davranisini dogrular. `scripts/qa/background_api_db_check.sh` background service-worker -> local API -> SQLite persistence akisini dogrular. `node --check extension/background.js`, `node --check extension/content.js` ve `python -m json.tool extension/manifest.json` extension outbox/content JS syntax ve manifest parse kontrolunu dogrular.
| `P3-JOB-001` | P3-001..003 | Worker running halde ölür | Lease sonrası iş yeniden alınır |
| `P3-JOB-002` | P3-003 | Retryable hata 5 kez | Full jitter, sonra dead-letter |
| `P3-JOB-003` | P3-007 | Backfill + live capture | Live iş starvation olmadan önce |
| `P3-JOB-004` | P3-007 | Memory pressure | Heavy admission durur, API canlı |

2026-06-25 kismi kod kaniti: `tests/integration/test_phase3_jobs.py`, `P3-JOB-001` ve `P3-JOB-002` icin lease recovery, completed job, retry, savepoint rollback, dead-letter listesi ve replay davranisini dogrular. `P3-JOB-003` ve `P3-JOB-004` icin live is sirasi, priority aging ve resource-class admission testleri eklendi. `GET /api/v1/jobs`, `POST /api/v1/jobs/{id}/retry`, Streamlit queue/dead-letter helper'i, durable token bucket bloklama, stage timeout/fatal hata ayrimi ve bounded micro-batch otomatik test edilir. Bu kanit tam domain pipeline stage zincirini henuz kapsamaz.
| `P4-MED-001` | P4-001..002 | Aynı byte ve resize/crop fixture | SHA exact; pHash near-duplicate ayrımı |
| `P4-MED-002` | P4-005 | Aynı blob iki post | Tek dosya, iki referans |
| `P4-MED-003` | P4-004..006 | Kota ve silinmiş URL | Policy ile GC; metadata/audit kalır |
| `P4-MED-004` | P4-007 | Video/GIF/audio duration metadata | Bounded frame planı; uzun/missing duration reject; audio extraction kararı |

2026-06-30 kismi kod kaniti: `tests/unit/test_media_hashing.py`, `P4-MED-001` icin tam SHA-256 exact dedup ile `dhash64-v1` perceptual hash ayrimini dogrular. Ayni byte fixture exact/perceptual hash esitligini korur; kucuk gorsel degisikligi exact SHA'yi degistirirken Hamming threshold icinde near-duplicate kalir; farkli gorsel threshold disinda kalir; kucuk batch cluster sonucu `[[0, 1], [2]]` olarak dogrulanir. Ayni dosyanin iki logical reference ile tek content-addressed kopya olusturmasi, referanslar birakildiktan sonra dry-run/real GC ile silinebilmesi, retention TTL sonrasi local dosyanin metadata-only kayda donmesi, quota/LRU policy'nin en eski unreferenced medyayi silmesi, original policy'yi korumasi ve silinmis remote URL icin minimum snapshot tutulmasi `P4-MED-002` ve `P4-MED-003` icin kismi kanittir. `tests/integration/test_phase1_storage.py` DB-backed media lifecycle repository'nin refcount, duplicate reference, release, remote snapshot idempotency ve media lifecycle audit eventlerini dogrular. `tests/unit/test_video_audio_lifecycle.py`, `P4-MED-004` icin video/gif bounded frame offset plani, uzun/missing duration reject, audio-only duration gate, GIF audio skip ve deterministic frame marker davranisini dogrular. Gercek video decode, OCR ve ASR Faz 5 adapter kapsaminda test edilecektir.
| `P5-MM-001` | P5-001..008 | Futbol kelimesi yok, görsel futbol | Belirsiz değilse topic evidence üretir |
| `P5-MM-002` | P5-006 | Alakalı text + alakasız media | Contradiction/intent hypotheses; spam kesinliği yok |
| `P5-MM-003` | P5-008 | Media eksik | Missing flag; relevance sıfırlanmaz |
| `P5-MM-004` | P5-009 | GPU OOM/model yok | CPU/cheap fallback; job kaybolmaz |
| `P5-ALG-001` | P5-010 | NB/logistic/SGD time split | Leakage audit ve learning curve raporu |
| `P5-CLIP-001` | P5-012 | Türkçe zero-shot golden set | Quality + CPU/GPU/RSS raporu |
| `P6-RET-001` | P6-002 | Lexical ve semantic query set | BM25, dense, RRF Recall@K/NDCG raporu |
| `P6-EVT-001` | P6-004,007 | Aynı/farklı temporal event | False merge ve fragmentation ölçülür |
| `P6-GRAPH-001` | P6-008 | Typed edge/metapath/PPR | Edge provenance ve time-decay doğru |
| `P6-VEC-001` | P6-009 | Exact vs FAISS | Recall ground-truth, latency/RAM gate |
| `P7-SRC-001` | P7-003 | Az ve çok örnekli source | Bayesian uncertainty/cold-start cezası |
| `P7-SRC-002` | P7-005 | Approve/watch/reject | Audit var; follow side-effect yok |
| `P8-RNK-001` | P8-001..007 | Ranking golden set | Explain, NDCG, diversity, risk recall |
| `P8-RNK-002` | P8-006,009 | Threshold calibration | Holdout utility; risk hard gate korunur |
| `P9-GEN-001` | P9-001..006 | Farklı event/style | Çeşitli taslak; near-copy yok |
| `P9-GEN-002` | P9-005 | Kaynaksız/yüksek riskli claim | Kesin dil yok; review/blocked |
| `P9-PRV-001` | P9-007 | 429/quota/key yok | Local fallback; secret redacted |
| `P10-LRN-001` | P10-001..004 | Feedback + metric snapshot | Versionlanmış reward ve segment baseline |
| `P10-LRN-002` | P10-005,009 | Safe bandit shadow | Propensity, regret, quota; risk kolu yok |
| `P10-LRN-003` | P10-006..010 | Drift/degradation | Alarm, champion freeze/rollback |
| `P11-UI-001` | P11-001..004 | Capture -> review -> feedback | UI'da tam akış ve gerçek state |
| `P11-A11Y-001` | P11-006 | Keyboard/screen reader/contrast | Kritik hata yok |
| `P12-SLO-001` | P12-001..004 | 100k post synthetic DB | Inbox/suggestion SLO ve RSS bütçesi |
| `P12-SEC-001` | P12-005 | Non-local bind/auth/CSP/input | Güvenli varsayılan ve 4xx |
| `P12-DR-001` | P12-006 | Backup -> corrupt -> restore | Integrity ve veri sayıları eşleşir |
| `P13-OFF-001` | P13-003 | Tam offline/no-key | Core acceptance geçer |
| `P13-SOAK-001` | P13 | 24 saat hedef cihaz | Job kaybı yok, RSS limiti ve disk trendi |

## 4. Golden dataset dilimleri

Her model release'i şu dilimleri ayrı raporlar:

- Türkçe yalnız metin; slang, typo, emoji, hashtag.
- Futbol kelimesi olmayan futbol görseli/quote'u.
- Alakalı metin + alakasız medya.
- Alakasız metin + alakalı medya.
- İroni, mizah, meme ve screenshot OCR.
- Duplicate/near-duplicate text, image ve video frame.
- Eksik/deleted media ve düşük kalite OCR.
- Kriz, siyaset, telif, privacy, toxicity ve misinformation.
- Yeni/az örnekli source, viral tekil post ve source drift.

## 5. Release komutları

```bash
.venv/bin/pytest -q
.venv/bin/ruff check xnative tests scripts/docs/build_master_plan.py
.venv/bin/ruff format --check xnative tests scripts/docs/build_master_plan.py
.venv/bin/mypy xnative
.venv/bin/python -m compileall -q xnative tests scripts/docs
```

Docker, extension, model, UI E2E ve soak sonuçları ayrı artefakttır; unit test sayısından türetilmez.

## 6. Release kanıt paketi

- Git commit/branch ve çalışma ortamı.
- Test komutu, exit code, süre ve rapor dosyası.
- Migration/schema version ve DB fixture hash.
- Model/dataset/config hash ve lisans.
- SLO/resource raporu.
- Güncel traceability, ADR, diyagram ve QA raporu.
- Bilinen residual risk ve rollback adımı.
