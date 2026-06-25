# XNative Hedef Mimarisi

## Mimari hedef

Sistem tek hesap icin yerel-oncelikli bir “icerik karar ve ogrenme sistemi”dir. X API veya otomatik public action kullanmaz. Kullanici tarafindan gorulen icerik tarayici uzantisi ya da manual import ile yerel sisteme girer; analiz, aday bulma, siralama, taslak uretme ve raporlama otonomdur; yayin ve takip karari insan onaylidir.

## Temel tasarim ilkeleri

1. Offline-first: Tum kritik akış API anahtari olmadan calisir.
2. Composable pipeline: Source, Hydrator, Filter, Feature, Scorer, Selector ve SideEffect sinirlari aciktir.
3. Multimodal evidence: Metin, quote, OCR, gorsel, video, ses, yazar ve zaman sinyalleri ayri saklanir; sonra birlestirilir.
4. Uncertainty-aware: Eksik veri sifir kanit demektir; negatif kanit degildir.
5. Human-controlled actions: Sistem onerir ve ogrenir; X uzerinde otomatik eylem yapmaz.
6. Provenance-first: Her feature, skor ve taslak kaynak veri/model/config surumune izlenebilir.
7. Budget-aware: Pahali model sadece ucuz asamalar belirsiz kaldiginda calisir.

## Mantiksal katmanlar

### 1. Capture edge

- Chrome/Chromium extension gorunur DOM'u parse eder.
- Manual JSON/CSV import gelistirme ve kurtarma yoludur.
- Extension bir local outbox tutar; backend onayi olmadan kaydi teslim edilmis saymaz.
- X bookmark otomasyonu yapilmaz. Yerel arsive kayit ve X URL saklama kullanilir.

### 2. Local API

- FastAPI yalnızca localhost'a bind olur.
- Pydantic sozlesmeleri payload boyutu, alan tipi ve schema version kontrolu yapar.
- Capture endpoint hizli sekilde kalici inbox ve job kaydi olusturup `202` doner.
- Health process durumunu, readiness ise DB/migration/worker durumunu gosterir.

### 3. Storage

- SQLite: metadata, olaylar, skorlar, feedback, model registry ve job queue.
- FTS5: lexical retrieval.
- Content-addressed local media store: opsiyonel thumbnail/orijinal medya.
- Embeddingler ilk surumde SQLite metadata + ayri NumPy/memmap shard; exact ground-truth sonrasi olculmus esikte FAISS adapteri. Milvus hedef 8 GB makinede kullanilmaz.
- Tum tablolar migration ve provenance alanlari tasir.

### 4. Worker ve pipeline

- SQLite job queue ile tek makinede en az operasyonel karmasiklik.
- I/O isleri kontrollu async; CPU/model isleri process pool veya ayri worker.
- Stage bazli timeout, retry, dead-letter ve idempotency.
- Backfill ile yeni model/feature eski kayitlara tekrar uygulanabilir.

### 5. Multimodal feature extraction

- Text: normalization, language, entities, topics, sentiment/tone, claims, embedding.
- Image: dimensions, exact hash, pHash, OCR, embedding, caption ve safety signals.
- Video/audio: sinirli frame, OCR, embedding, opsiyonel ASR.
- Cross-modal: text-image benzerligi, tamamlayicilik, ironic/contrast aday sinyali.
- Lazy escalation: metadata -> cheap local model -> heavier local model -> optional free-tier.

### 6. Event memory ve retrieval

- Postlar event/entity graph etrafinda gruplanir.
- Hybrid retrieval BM25 + dense similarity + recency + source diversity kullanir.
- Text, entity, author, pHash ve format tabanli novelty/fatigue hesaplanir.
- “Futbol kelimesi yok” durumu entity, image, quote ve komsu olay kanitlariyla telafi edilir.

### 7. Candidate ve ranking

- In-network benzeri kaynak: kullanicinin gorunur akisinda izledigi hesaplar.
- Out-of-network benzeri kaynak: quote/repost baglantilari ve semantik yakin hesaplar.
- Filter: duplicate, stale, seen, blocked, unsafe ve dusuk guven.
- Scorer: coklu aksiyon olasiligi/utility; risk negatif agirliktir.
- Selector: top-K + MMR/diversity + exploration budget.
- Post-selection: son risk, tekrar, kaynak ve telif kontrolu.

### 8. Generation ve review

- Style memory'den benzer basarili ornekler secilir.
- Template/local model/opsiyonel provider zinciri varyant uretir.
- Quality ve policy filtreleri sonrasinda pending queue'ya girer.
- UI approve/edit/reject/ignore kararlarini ve gerekcelerini kaydeder.

### 9. Learning ve evaluation

- Feedback ve performans snapshotlari immutable event olarak saklanir.
- Baslangicta aciklanabilir agirlik/EMA; yeterli veri olunca supervised ranker.
- Contextual bandit yalniz guvenli ton/format exploration'inda kullanilir.
- Champion/challenger, shadow scoring, offline evaluation ve rollback zorunludur.

## X algoritmasindan alinacak ve alinmayacak noktalar

Resmi `xai-org/x-algorithm` deposunun 2026 mimarisi retrieval -> hydration -> filtering -> scoring -> selection -> post-selection asamalarini, coklu engagement olasiliklarini ve author diversity azaltimini gosterir. XNative bu composable yapidan yararlanir.

Alinacaklar:

- Pipeline stage ayrimi ve bagimsiz asamalarin paralel calismasi.
- In-network/out-of-network aday kaynaklari fikri.
- Coklu pozitif ve negatif aksiyon sinyali.
- Previously-seen, dedup, age, muted/risk ve post-selection filtreleri.
- Diversity attenuation ve side-effect/audit ayrimi.

Alinmayacaklar:

- Global corpus, Kafka ve dagitik online serving.
- 3 GB Phoenix modelini urun omurgasi yapmak.
- X'in dahili impression, follow graph veya erisilemeyen ozel feature'lari.
- Kullanici izni disinda public aksiyon veya gizli veri toplama.

Kaynak: https://github.com/xai-org/x-algorithm (erisilen surum: 2026-06-22).

## Deployment profilleri

### Hedef surekli calisma bilgisayari

- 9. nesil Intel Core i5.
- 8 GB sistem RAM'i.
- NVIDIA GeForce GTX 1050; VRAM miktari kurulumda olculmeli, tasarim 2 GB alt sinirina gore calismali.
- Python, FastAPI, SQLite/FTS5 ve browser extension.
- Tek agir model worker'i, en fazla iki hafif I/O/CPU isi.
- Tesseract OCR ve lexical pipeline CPU'da; GPU yalniz uyumluluk/benchmark gecerse kucuk vision veya embedding inference icin.
- Ayni anda VLM, ASR ve image encoder bellekte tutulmaz; lazy-load ve is bitiminde unload uygulanir.
- Yerel buyuk LLM/VLM egitimi veya surekli calismasi hedef disidir.

Bu bilgisayar sistemin surekli servis makinesidir. Gelistirme bilgisayarindaki daha yuksek kapasite, production mimarisi icin varsayim yapilmasina neden olamaz.

### Minimum offline yetenek

- Rule/FTS5/BM25, 384 boyutlu quantized multilingual embedding, pHash ve Tesseract.
- Kucuk image encoder ONNX/CPU veya uyumluysa GTX 1050.
- Whisper tiny/base int8 yalniz secili videolarda ve sirali kuyrukta.
- Logistic regression/LightGBM inference; bu cihazda derin model training yok.

### Gelismis yerel profil

- 16+ GB RAM ve daha yeni GPU bulunursa buyuk batch, daha guclu VLM/ASR ve ANN profili ayri deployment olarak etkinlestirilebilir.
- Hedef 8 GB makine bu profile otomatik gecmez.

### Opsiyonel bulut yardimi

- Yalniz adapter arkasinda, acik kullanici secimiyle.
- Kota, timeout, circuit breaker ve yerel fallback zorunlu.
- Ham özel veri yerine minimize/anonimize edilmis istek.
- Ucretsiz kota urunun calisma garantisi degildir.
