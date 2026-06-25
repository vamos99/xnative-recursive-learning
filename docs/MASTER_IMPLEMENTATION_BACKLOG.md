# XNative Ana Uygulama Backlogu

Durum: Aktif ve baglayici plan  
Baslangic tarihi: 2026-06-22  
Kapsam: Yerel-oncelikli, X API kullanmayan, multimodal ve kendi performansindan ogrenebilen tek hesap sistemi

## 1. Baglayici calisma kurallari

Bu belge uygulama sirasinin tek dogru kaynagidir. Bir faz, kendisinden onceki fazin kabul kriterleri gecmeden `tamamlandi` sayilmaz. `docs/FINAL_QA_REPORT.md`, `project_board.md` ve teslim belgeleri bu listedeki durumlarla ayni olmak zorundadir.

Otonomi, sistemin veri toplama sonrasindaki analiz, zenginlestirme, aday uretme, siralama, raporlama ve kontrollu ogrenme adimlarini kendi basina calistirmasi anlamina gelir. X uzerinde paylasma, begenme, takip etme, repost veya yanit verme otomatiklestirilmeyecektir. Yayina alma ve takip karari insan onayinda kalir.

Durum kodlari:

- `BEKLIYOR`: Calisma baslamadi.
- `DEVAM`: Uygulama veya dogrulama suruyor.
- `BLOKE`: Belgelenmis bir dis engel var.
- `TAMAM`: Kod, test, performans ve belge kabul kapilari gecti.

Degisiklik turleri:

- `DUZELT`: Var olan hatali davranisi onar.
- `GELISTIR`: Calisan davranisin kalitesini veya kapsamini artir.
- `EKLE`: Yeni yetenek veya artefakt olustur.
- `KALDIR`: Yaniltici, eski veya kullanilmayan yapiyi temizle.
- `BELGELE`: Karar, sinir veya kullanim bilgisini kalici hale getir.

## 2. Oncelik ve sira

### Faz 0 - Gercek durum, paket ve yonetisim

Amac: Yaniltici teslim iddialarini kaldirmak ve tekrar uretilebilir bir baslangic olusturmak.

1. `P0-001` `DUZELT` README klasor ve calistirma komutlarini gercek repo yapisina uyarla. Durum: `TAMAM`.
2. `P0-002` `DUZELT` Final QA raporunu “15 test gecti = sistem tamam” yanilgisindan arindir. Durum: `TAMAM`.
3. `P0-003` `KALDIR` `.pytest_cache`, `__pycache__`, tasinamaz hash yollari ve gecici teslim dosyalarini temizle. Durum: `TAMAM`.
4. `P0-004` `EKLE` pyproject/lockfile, Python surumu, formatter, lint, type-check ve test profilleri. Durum: `TAMAM`.
5. `P0-005` `EKLE` tum gereksinimlere kimlik ve izlenebilirlik matrisi. Durum: `TAMAM`.
6. `P0-006` `BELGELE` “otonom analiz, insan onayli public action” guvenlik siniri. Durum: `TAMAM`.

Kabul kapisi: Temiz kurulum komutu tek bir ortamda calisir; eski ve yeni kod yollarinin hangisinin aktif oldugu belirlidir; belgeler tamamlanmamis ozellikleri tamamlanmis gostermez.

Faz 0 kaniti: `pyproject.toml`, `uv.lock`, `.gitignore`, guncel README/QA/traceability belgeleri; 2026-06-22 kosusunda 15 test, Ruff, format, mypy ve compile kontrolleri gecti. Ayrinti: `ENGINEERING_BASELINE.md`.

### Faz 1 - Alan modeli ve kalici veri omurgasi

Bagimlilik: Faz 0.

1. `P1-001` `EKLE` Pydantic tabanli `CapturedPost`, `MediaAsset`, `Event`, `Candidate`, `Suggestion`, `Feedback`, `PerformanceSnapshot` sozlesmeleri.
2. `P1-002` `DUZELT` SQLite semasina foreign key, unique constraint, index, migration ve schema version ekle.
3. `P1-003` `EKLE` repository/unit-of-work katmani; API ve worker dogrudan SQL yazmasin.
4. `P1-004` `EKLE` WAL, busy timeout, kisa transaction, retry ve idempotency key davranisi.
5. `P1-005` `EKLE` audit log, provenance, model versioni ve feature versioni.
6. `P1-006` `EKLE` veri siniflandirmasi: metadata, gorunur icerik, yerel medya, turetilmis feature ve kullanici geri bildirimi.

Kabul kapisi: Ayni post iki kez geldiginde tek kayit olusur; kopuk foreign key olusmaz; migration bos ve dolu veritabaninda test edilir; tum turetilmis kayitlar kaynak post ve model surumune izlenebilir.

Faz 1 kaniti: 2026-06-23 kosusunda `xnative/domain/`, `xnative/db/migrations/0001_initial.sql`, `xnative/db/migration_runner.py` ve `xnative/db/repositories.py` eklendi. `tests/integration/test_phase1_storage.py` P1 domain validation, migration checksum, idempotent capture, FK rollback, tekil job claim ve feature provenance kapilarini dogrular. Bu faz API route, extension outbox, worker loop veya review UI tamamlandi anlamina gelmez.

### Faz 2 - Guvenilir gorunur tarayici yakalama

Bagimlilik: Faz 1.

1. `P2-001` `DUZELT` FastAPI router kayitlari; `POST /capture`, `GET /health`, `GET /ready` gercek endpoint olsun.
2. `P2-002` `DUZELT` extension manifestine sadece gereken localhost izni; gereksiz `activeTab/scripting` izinlerini denetle.
3. `P2-003` `DUZELT` basarili response alindiktan sonra cache'e alma; disk tabanli retry outbox ve exponential backoff.
4. `P2-004` `DUZELT` capture kapaliyken DOM elemanini isaretlememe; acilinca yeniden tarama.
5. `P2-005` `GELISTIR` avatar/UI gorseli ile post medyasini ayir; quote ve ana post DOM sinirlarini test et.
6. `P2-006` `EKLE` DOM selector surumu, parse kalite metrigi, circuit breaker ve manual import fallback.
7. `P2-007` `EKLE` kullanici-baslatimli “yerel arsive kaydet” akisi; X uzerinde otomatik bookmark yapma.

Kabul kapisi: Gercek veya kaydedilmis DOM fixture ile extension -> API -> DB akisi calisir; backend gecici kapaliyken veri kaybolmaz; credential/cookie toplanmaz; payload boyutu ve frekansi sinirlidir.

Faz 2 kismi kanit: 2026-06-23 kosusunda `P2-001` icin `xnative/api/main.py`, `xnative/api/routes/health.py` ve `xnative/api/routes/capture.py` guncellendi. `POST /api/v1/captures`, gecici `POST /capture` alias'i, `GET /health` ve `GET /ready` gercek route olarak baglandi; capture handler Phase 1 repository katmanina yazar. `tests/integration/test_phase2_api_capture.py` route, readiness, idempotency, 413 payload limiti, 422 validation ve alias deprecation header davranisini dogrular. `P2-002` icin `extension/manifest.json` gereksiz `activeTab/scripting` izinlerinden arindirildi ve yalniz X + localhost host izinleri birakildi. `P2-003` icin `extension/background.js` basarili HTTP cevabi sonrasi outbox'tan dusen, backend kapaliyken local storage'da bekleyen, bounded outbox kullanan ve exponential backoff ile tekrar deneyen akisa gecti. `P2-004` icin `extension/content.js` post'u yalniz background outbox kabulunden sonra `xnativeCaptured` olarak isaretler; capture kapaliyken veya kabul basarisizken DOM tekrar denenebilir kalir. `P2-005..007` henuz tamam degildir; kaydedilmis DOM fixture kalite testi, ana/quote medya ayrimi ve manual archive akisi sonraki adimdir.

### Faz 3 - Ingestion, is kuyrugu ve idempotent pipeline

Bagimlilik: Faz 2.

1. `P3-001` `EKLE` SQLite tabanli job queue: `pending/running/retry/dead/completed`. Durum: `TAMAM`.
2. `P3-002` `EKLE` pipeline asamalari: source, hydrate, normalize, filter, feature, event, score, select, side-effect. Durum: `DEVAM`.
3. `P3-003` `EKLE` stage timeout, retry sinifi, dead-letter ve yeniden oynatma. Durum: `DEVAM`.
4. `P3-004` `GELISTIR` bagimsiz medya/NLP feature islerini sinirli paralel calistir. Durum: `DEVAM`.
5. `P3-005` `EKLE` post, medya ve model-ciktisi cache anahtarlari; version degisince kontrollu invalidation. Durum: `DEVAM`.
6. `P3-006` `EKLE` batch ve incremental/backfill modlari. Durum: `DEVAM`.
7. `P3-007` `EKLE` priority aging, resource semaphore, bounded backpressure, micro-batch, durable cursor, token-bucket ve full-jitter retry algoritmalari. Durum: `TAMAM`.

Kabul kapisi: Worker yeniden baslatilinca is kaybi veya cift yazim olmaz; bir asama hatasi tum pipeline'i bozmaz; dead-letter kaydi UI'dan gorulur.

Faz 3 kismi kanit: 2026-06-25 kosusunda `xnative/db/repositories.py` generic job enqueue/dedupe, active dedupe, bounded backpressure, priority aging, resource-class admission limit, expired lease recovery, retry/dead gecisi, dead-letter yazimi, durable cursor, versioned cache repository, dead-letter listeleme, replay, micro-batch claim ve DB tabanli token bucket davranislarini destekleyecek sekilde genisletildi. `xnative/db/migrations/0002_worker_runtime.sql` incremental cursor/cache tablolarini, `xnative/db/migrations/0003_worker_rate_limits.sql` rate-limit bucket tablosunu ekler. `xnative/worker/scheduler.py` savepoint izolasyonlu tek is runner, stage timeout/fatal/retryable hata siniflandirmasi, token bucket admission, micro-batch runner ve kontrollu `run_worker_loop` saglar; `xnative/worker/jobs.py` `normalize_capture` handler'ina sahiptir. `xnative/api/routes/jobs.py` queue/dead-letter gorunumu ve manual retry endpointlerini, `xnative/ui/streamlit_app.py` ise Streamlit operasyon panelini saglar. `tests/integration/test_phase3_jobs.py` completed normalize job, lease recovery, retry -> dead-letter, unknown job type, resource semaphore, priority aging/live is sirasi, backpressure, cursor/cache, handler hata rollback, API job gorunumu, UI helper, dead-letter replay, token bucket bloklama, stage timeout/fatal hata ayrimi ve micro-batch davranisini dogrular. Kalanlar: tam domain pipeline stage zinciri ve domain stage output sozlesmelerinin normalize disindaki asamalara uygulanmasi.

### Faz 4 - Medya saklama, arsivleme ve yasam dongusu

Bagimlilik: Faz 1 ve 3.

1. `P4-001` `DUZELT` SHA kisaltmasini “pHash” diye adlandirmayi birak; SHA-256 exact dedup ve gercek perceptual hash'i ayir.
2. `P4-002` `EKLE` dHash/pHash, Hamming threshold ve thumbnail tabanli benzer medya cluster testi.
3. `P4-003` `EKLE` varsayilan metadata-only arsiv: X URL, gorunur metin, alt text, metrik snapshot ve provenance.
4. `P4-004` `EKLE` opsiyonel yerel thumbnail/orijinal medya politikalari; telif/izin ve disk kotasi.
5. `P4-005` `EKLE` content-addressed media store, referans sayimi, TTL, LRU ve garbage collection.
6. `P4-006` `EKLE` bozuk/deleted URL durumu ve minimum kanit snapshot'i.
7. `P4-007` `EKLE` video icin sinirli frame sampling, audio extraction ve duration limiti.

Kabul kapisi: Benzer gorseller cluster olur; ayni dosya tek kez saklanir; kota asiminda kontrollu temizlik yapilir; silinen X linki kaydin geri kalanini bozmaz.

### Faz 5 - Multimodal icerik anlama

Bagimlilik: Faz 3 ve 4.

1. `P5-001` `EKLE` Turkce/çokdilli metin normalization, dil tespiti, entity ve konu adaylari.
2. `P5-002` `EKLE` OCR adapteri: Tesseract/EasyOCR secilebilir; alt text fallback; confidence ve bounding box saklama.
3. `P5-003` `EKLE` gorsel embedding ve zero-shot etiketleme adapteri; model yoksa renk/edge/metadata fallback.
4. `P5-004` `EKLE` image caption/VLM adapteri; sadece belirsiz orneklerde ve butce uygunsa calistir.
5. `P5-005` `EKLE` video frame embedding, OCR ve opsiyonel yerel Whisper ASR.
6. `P5-006` `EKLE` text-image uyum, tamamlayicilik ve bilincli uyumsuzluk sinyalleri.
7. `P5-007` `EKLE` “futbol kelimesi yok ama futbol baglami var” weak-supervision test seti.
8. `P5-008` `EKLE` modality missingness ve confidence calibration; eksik medya “alakasiz” sayilmasin.
9. `P5-009` `EKLE` 8 GB RAM/GTX 1050 hardware preflight, CPU fallback, tek-agir-model scheduler ve OOM recovery.
10. `P5-010` `EKLE` text algoritma benchmarki: TF-IDF/HashingVectorizer, MultinomialNB, logistic regression ve online SGD; zaman split'i ve learning curve.
11. `P5-011` `EKLE` confidence-aware late-fusion baseline; logistic model ile HistGradientBoosting/LightGBM challenger ve missing-modality ablation.
12. `P5-012` `EKLE` kucuk pretrained OpenCLIP/MobileCLIP benchmarki: zero-shot Turkce prompt, image-text retrieval, contradiction feature, CPU/GPU/ONNX-int8 ve lisans profili.

Kabul kapisi: Metin, gorsel, quote ve OCR tek basina veya birlikte konu kaniti uretebilir; her modality katkisi aciklanabilir; model yoklugunda pipeline calismaya devam eder.

### Faz 6 - Olay belleği, baglam ve semantik arsiv

Bagimlilik: Faz 5.

1. `P6-001` `EKLE` entity/event graph: kisi, takim, lig, mac, transfer, meme, kriz ve zaman baglantilari.
2. `P6-002` `EKLE` lexical + vector hybrid retrieval; FTS5 BM25 ve embedding rerank.
3. `P6-003` `EKLE` quote/thread/author/medya cluster baglantilari.
4. `P6-004` `EKLE` ayni olay icin zaman pencereli birlestirme, kaynak sayisi ve velocity.
5. `P6-005` `EKLE` novelty/fatigue: metin, entity, semantik embedding, medya pHash ve format tekrari.
6. `P6-006` `EKLE` belirsiz veya domain-disi ama yuksek etkileşim potansiyelli “exploration” havuzu.
7. `P6-007` `EKLE` event clustering benchmarki: zaman pencereli graph/union-find baseline ile DBSCAN/HDBSCAN challenger; fragmentation ve false-merge metrikleri.
8. `P6-008` `EKLE` typed local HIN: account/post/event/entity/media/topic/format node'lari; weighted metapath ve Personalized PageRank baseline.
9. `P6-009` `EKLE` vector index gecis benchmarki: NumPy exact -> FAISS IndexFlatIP -> HNSW/IVF-PQ; recall/latency/RAM kapisi, Milvus hedef cihazda yasak.
10. `P6-010` `EKLE` yeterli graph olceginde Node2Vec/metapath2vec, GraphSAGE/R-GCN ve HGT challenger deneyi; leakage, ablation ve explainability.

Kabul kapisi: Sistem kelime eslesmesi olmadan onceki benzer olaylari bulur; ayni olay/medya tekrarlarini azaltir; kanit yetersizse kesin sinif yerine belirsizlik bildirir.

### Faz 7 - Kaynak ve takip adayi ogrenimi

Bagimlilik: Faz 6.

1. `P7-001` `EKLE` kullanicinin gorunur akisi, quote/repost agi ve basarili postlardan kaynak adayi cikarma.
2. `P7-002` `EKLE` kaynak profil feature'lari: erken sinyal, dogruluk, konu kapsami, medya kalitesi, ozgunluk, risk ve tekrar.
3. `P7-003` `EKLE` Bayesian/EMA reliability update; az ornekli hesaplara belirsizlik cezasi.
4. `P7-004` `EKLE` diversity ve echo-chamber siniri.
5. `P7-005` `EKLE` approve/watch/reject akisi; otomatik follow yok.
6. `P7-006` `EKLE` source drift ve uzun sure etkisiz hesap tespiti.

Kabul kapisi: Her aday icin ornekler, neden, belirsizlik ve risk gorulur; sistem takip islemini kendi basina yapmaz; kaynak puani tek viral posta dayanmaz.

### Faz 8 - Aday uretimi ve cok hedefli siralama

Bagimlilik: Faz 6 ve 7.

1. `P8-001` `EKLE` X-algorithm benzeri composable Source/Hydrator/Filter/Scorer/Selector yapisi.
2. `P8-002` `EKLE` coklu hedefler: approve, edit, manual_post, engagement, dwell, ignore, reject, risk.
3. `P8-003` `EKLE` ilk asama aciklanabilir weighted ranker; feature normalization ve missing-value policy.
4. `P8-004` `EKLE` yeterli etiket olunca LightGBM/XGBoost veya lojistik model champion-challenger.
5. `P8-005` `EKLE` MMR/diversity, author fatigue, event fatigue ve exploration kotasi.
6. `P8-006` `EKLE` probability calibration ve threshold secimi.
7. `P8-007` `EKLE` offline NDCG@K, Precision@K, coverage, diversity, calibration ve risk recall.
8. `P8-008` `EKLE` veri hacmi/model merdiveni, experiment registry, time-split veri sizintisi kontrolu ve learning-curve terfi kapisi.
9. `P8-009` `EKLE` validation utility + minimum risk-recall kisitli threshold optimizasyonu; elle sabit esikleri kaldir.
10. `P8-010` `EKLE` yeterli preference cifti sonrasi pairwise ranker/LambdaMART challenger; tek engagement hedefi kullanma.

Kabul kapisi: Skor her feature katkisini aciklar; yeni model mevcut modeli offline ve shadow metriklerde gecmeden champion olmaz; risk filtresi siralamadan sonra da tekrar uygulanir.

### Faz 9 - X-native taslak uretimi ve guvenlik

Bagimlilik: Faz 5, 6 ve 8.

1. `P9-001` `DUZELT` sabit uc metin yerine olay, ton, quote, medya ve style memory ile kosullu varyantlar.
2. `P9-002` `EKLE` retrieval-augmented style examples; birebir kopya ve yakin kopya engeli.
3. `P9-003` `EKLE` reaction, dry humor, neutral, quote-context, media-contrast ve exploration formatlari.
4. `P9-004` `EKLE` template -> local small LLM -> optional free-tier provider fallback zinciri.
5. `P9-005` `EKLE` claim verification, crisis, toxicity, politics, copyright ve privacy policy kapilari.
6. `P9-006` `EKLE` kalite, dogallik, uzunluk, tekrar, style-fit ve hallucination kontrolleri.
7. `P9-007` `EKLE` Gemini adapteri: free/paid proje tespiti, RPM/TPM/RPD telemetry, token/cost budget, 429 retry ve local fallback.

Kabul kapisi: Farkli olaylar farkli taslaklar uretir; kaynak kaniti olmayan iddia kesin dilde yazilmaz; yuksek riskli taslak otomatik olarak review kuyruğuna girer.

### Faz 10 - Geri bildirim, performans ve kontrollu ogrenme

Bagimlilik: Faz 8 ve 9.

1. `P10-001` `EKLE` approve/edit/reject/ignore/manual_post ve gerekce kaydi.
2. `P10-002` `EKLE` kullanici tarafindan girilen veya gorunur DOM'dan yakalanan zaman serili performans snapshot'i.
3. `P10-003` `EKLE` reward fonksiyonu: onay, edit distance, etkileşim, negatif aksiyon ve risk.
4. `P10-004` `EKLE` segmentli baseline: event type, saat, medya, format, kaynak buyuklugu ve exposure etkisi.
5. `P10-005` `EKLE` contextual bandit yalniz guvenli ton/format seciminde; epsilon decay ve exploration budget.
6. `P10-006` `EKLE` drift, degradation ve “neden tutmadi?” hata siniflandirmasi.
7. `P10-007` `EKLE` rollback, model registry, champion/challenger ve minimum sample gate.
8. `P10-008` `EKLE` Beta-Bernoulli posterior, uncertainty ve zaman decay ile kaynak guveni; sabit EMA'ya karsi calibration testi.
9. `P10-009` `EKLE` Thompson Sampling baseline ve yeterli contextte LinUCB challenger; kalici posterior, regret ve kota telemetry.
10. `P10-010` `EKLE` PSI/JS divergence ve rolling-loss drift baseline; ADWIN/Page-Hinkley challenger ve segment alarm esikleri.

Kabul kapisi: Ogrenme sadece olculebilir ve versionlanmis feedback ile olur; az veride agirliklar kontrolden cikmaz; performans dususu modeli otomatik geri alabilir; public action yine insan onaylidir.

### Faz 11 - API, review UI ve operasyonel dashboard

Bagimlilik: Faz 1-10'un stabil sozlesmeleri.

1. `P11-001` `EKLE` gerçek dashboard, capture inbox, suggestions queue, source candidates, style memory, reports ve settings.
2. `P11-002` `EKLE` approve/reject/revise/ignore ve audit trail.
3. `P11-003` `EKLE` score explanation, modality evidence, provenance ve model confidence.
4. `P11-004` `EKLE` live/stale/offline/partial durumlari, son guncelleme ve retry kontrolu.
5. `P11-005` `EKLE` pagination, server-side filtering, URL-backed state ve export.
6. `P11-006` `EKLE` responsive, keyboard, screen-reader, contrast ve reduced-motion kontrolleri.

Kabul kapisi: En kritik akış capture -> suggestion -> review -> feedback olarak UI'dan tamamlanir; bos veya sahte ekran yoktur; 10 bin kayitta sayfa acilisi belirlenen SLO icinde kalir.

### Faz 12 - Performans, gozlemlenebilirlik ve guvenlik sertlestirme

Bagimlilik: Faz 3-11.

1. `P12-001` `EKLE` latency, throughput, queue depth, cache hit, model time ve hata metrikleri.
2. `P12-002` `EKLE` structured log, correlation ID, health/readiness ve diagnostics bundle.
3. `P12-003` `EKLE` benchmark dataset ve p50/p95/p99 regression testleri.
4. `P12-004` `EKLE` disk/RAM/CPU butceleri, model lazy-load/unload ve batch inference.
5. `P12-005` `EKLE` input validation, localhost-only default bind, auth token, CSP ve secret redaction.
6. `P12-006` `EKLE` backup/restore, SQLite integrity check ve disaster recovery testi.
7. `P12-007` `EKLE` algoritma kaynak profili: fit/inference p50-p99, peak RSS/VRAM, model boyutu, enerji suresi ve cache etkisi.
8. `P12-008` `EKLE` random search/successive-halving deney altyapisi; Optuna TPE yalniz kosullu arama uzayi buyurse eklenir.

Kabul kapisi: SLO regression CI'da gorulur; servis LAN'a varsayilan olarak acilmaz; kritik hata audit ve kullanici mesajina donusur; backup geri yuklenebilir.

### Faz 13 - Test matrisi ve release kapilari

Bagimlilik: Tum uygulama fazlari.

1. `P13-001` `GELISTIR` unit testleri negatif, boundary ve property-based durumlarla genislet.
2. `P13-002` `EKLE` extension DOM contract, API/DB, worker retry ve multimodal integration testleri.
3. `P13-003` `EKLE` Docker health, cold-start, offline mode ve no-key acceptance.
4. `P13-004` `EKLE` golden multimodal fixture ve model-version regression.
5. `P13-005` `EKLE` UI E2E, accessibility ve visual regression.
6. `P13-006` `EKLE` security/privacy ve data-retention testleri.
7. `P13-007` `EKLE` calibration, time-split, duplicate leakage, segment degradation ve learning-curve release testleri.

Kabul kapisi: Release checklistte tum P0/P1 kabul testleri gecer; test raporu komut, ortam, commit ve artefakt hash'i icerir.

### Faz 14 - Dokumantasyon, diyagram ve teslimat

Bagimlilik: Her faz kendi belge maddesini gunceller; final teslim Faz 13 sonrasi.

1. `P14-001` `GELISTIR` README quickstart, troubleshooting ve gercek endpointler.
2. `P14-002` `EKLE` C4 context/container/component, DFD, sequence, ERD ve learning loop diyagramlari.
3. `P14-003` `EKLE` model card, data card, risk register ve ADR seti.
4. `P14-004` `GELISTIR` proje ve teknik DOCX/PDF belgelerini kodla ayni surumden uret.
5. `P14-005` `EKLE` operation runbook, backup/restore, model update ve incident proseduru.
6. `P14-006` `DUZELT` QA raporunu yalnizca kanitli kabul sonuclariyla yayinla.
7. `P14-007` `BELGELE` her model icin problem, baseline, challenger, kullanilmama nedeni, veri esigi, complexity ve terfi kaydi.
8. `P14-008` `BELGELE` exact domain, DB, API, job, config, hata ve compatibility sozlesmelerini uygulama spesifikasyonunda tut.
9. `P14-009` `EKLE` risk register, operasyon runbook, model/data card ve faz bazli acceptance ID seti.

Kabul kapisi: Markdown, DOCX ve PDF ayni surum/commit kimligini tasir; tum diyagramlar duzenlenebilir kaynakla gelir; her “implemented” iddiasinin test veya kod referansi vardir.

Planlama belge baseline'i 2026-06-22 tarihinde v1.0 olarak tamamlandi. P14 final release kapanisi, kod fazlari tamamlandiginda gercek commit/artefakt/test kanitlariyla yeniden yapilir.

## 3. Uygulama onceligi

- `P0`: Faz 0-3 ve kirik extension/API/UI girisleri. Bunlar olmadan sistem kullanilamaz.
- `P1`: Faz 4-10. Bunlar urunun multimodal degerini ve ogrenme kalitesini olusturur.
- `P2`: Faz 11-12. Operasyon, arayuz ve olceklenebilirlik.
- `P3`: Faz 13-14. Release guvencesi surekli uygulanir; final kapatma en sonda yapilir.

## 4. Degisiklik yonetimi

Her kod degisikligi en az bir backlog kimligi tasimalidir. Yeni gereksinim once bu belgeye eklenir, bagimliliklari belirlenir, sonra uygulanir. Bir faz tamamlanirken su dort kanit zorunludur:

1. Kod veya migration referansi.
2. Otomatik test sonucu.
3. Performans/guvenlik etkisi.
4. Guncellenen belge ve diyagram referansi.
