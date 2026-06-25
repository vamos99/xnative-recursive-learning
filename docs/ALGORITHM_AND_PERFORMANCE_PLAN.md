# Algoritma ve Performans Plani

## Hedefler

Sistem once dogru ve izlenebilir, sonra hizli olmalidir. Her agir modelin ucuz bir fallback'i vardir. Performans kararlarinda veri hacmi, donanim, latency, bellek, disk ve model kalitesi birlikte olculur.

Hedef donanim:

- 9. nesil Intel Core i5, 8 GB RAM, GTX 1050.
- GTX 1050 VRAM miktari bilinmedigi icin 2 GB VRAM tabani varsayilir; kurulum preflight'i gercek degeri kaydeder.
- Isletim sistemi ve driver/CUDA uyumu kurulumda dogrulanir; CPU-only mod tam desteklenir.

Baslangic kapasite varsayimi:

- 1 aktif hesap.
- Gunluk 500-5.000 gorunur post capture.
- 100 bin post metadata kaydi.
- 10-50 bin opsiyonel medya thumbnail'i.
- Eszamanli 1 UI kullanicisi, 1-4 worker.

Hedef cihazda worker siniri:

- 1 agir inference worker.
- En fazla 2 hafif I/O/normalization worker.
- Uygulama RSS soft limit 5.5 GB; 6 GB ustunde agir is kabul edilmez ve model unload tetiklenir.
- Isletim sistemi ve browser icin en az 2 GB bosluk korunur.

## Asama karmasikligi

| Islem | Yaklasim | Zaman | Bellek | Not |
|---|---|---:|---:|---|
| Capture normalize | Alan bazli parse | O(N) | O(1)/post | Payload limiti uygulanir |
| Exact dedup | Indexed SHA/post ID | O(1) ort. | O(N) indeks | SQLite unique index |
| pHash kucuk veri | Hamming scan | O(M) | O(M) | Once exact hash, sonra pHash |
| pHash buyuk veri | Prefix bucket/LSH | O(B) beklenen | O(M) | B ilgili bucket boyu |
| FTS retrieval | SQLite FTS5/BM25 | Yaklasik O(log N + K) | indeks | Top-K ile sinirla |
| Dense retrieval kucuk | Matrix dot product | O(Nd) | O(Nd) | Batch/quantization |
| Dense retrieval buyuk | HNSW/ANN | O(log N) beklenen | O(Nd) | Recall/latency olculur |
| Rule scoring | Feature agirliklari | O(NF) | O(F) | F sabit ve kucuk |
| MMR selection | Pairwise top pool | O(K^2) | O(K^2) | K 50-200 arasi |
| Event clustering | Windowed ANN + union | O(N log N) beklenen | O(N) | Zaman penceresi zorunlu |
| OCR | Pixel/model bagimli | pahali | model bagimli | Cache ve confidence gate |
| Video | S frame | O(S) inference | sinirli | S varsayilan 3-8 |
| Weekly report | Indexed aggregate | O(R log N) | O(R) | Materialized summary opsiyonu |

## Model secim merdiveni

1. Deterministic metadata/rule: her kayitta.
2. Lexical NLP ve FTS: her metinde.
3. Kucuk multilingual embedding: yeni/degisen icerikte bir kez.
4. Image embedding/OCR: medya varsa ve cache miss ise.
5. VLM/caption veya buyuk LLM: belirsizlik yuksek, potansiyel deger yuksek ve butce uygunsa.

Bu cascade, pahali modeli tum postlarda calistirmaktan daha ucuz ve daha izlenebilirdir.

Hedef cihaz icin varsayilan model profili:

- Text embedding: 384 boyut, ONNX int8 veya benzer kucuk multilingual encoder.
- OCR: Tesseract CPU; EasyOCR yalniz benchmark ile belirgin kalite artisi verirse.
- Image embedding: ViT-B/32 veya daha kucuk encoder, batch 1-4; GPU OOM'da CPU fallback.
- ASR: Whisper tiny/base int8, yalniz secilmis ses/video islerinde.
- VLM/LLM: varsayilan olarak Gemini adapteri veya baska opsiyonel servis; yerelde surekli yuklu degil.
- Training: online bounded agirlik, logistic regression veya LightGBM; deep learning training bu makinede yapilmaz.

## Algoritma secimleri

Algoritma seciminin baglayici baseline/challenger matrisi, veri esikleri, reddedilen yaklasimlar ve terfi protokolu `ALGORITHM_SELECTION_AND_EXPERIMENT_PLAN.md` belgesindedir. Capture, NLP, CV, video, graph, vector index, ranking, bandit, optimizer, drift, active learning, cache ve deney ailelerinin genis longlist'i `ALGORITHM_TECHNOLOGY_RADAR.md` belgesindedir. Bu bolum operasyonel ozeti verir.

### Retrieval

- Baslangic: FTS5 BM25 + multilingual dense embedding reciprocal-rank fusion.
- Rerank: recency, source reliability, event relevance, modality confidence.
- Buyume esigi: 100-250 bin embedding veya brute-force p95 hedefi asildiginda HNSW.

### Event clustering

- Zaman penceresi + entity overlap + dense similarity + pHash.
- Tek sabit threshold yerine event type ve confidence'a gore esik.
- Cluster merge geri alinabilir ve provenance'li olmali.

### Ranking

- V0: normalize edilmis aciklanabilir agirlikli utility.
- V1: yeterli etiket sonrasi regularized logistic regression veya LightGBM.
- Derin ranker ancak veri hacmi ve offline uplift bunu hakli cikarirsa.
- Coklu aksiyonlar tek engagement skoruna erken sikistirilmaz.

### Exploration

- Epsilon-greedy veya Thompson Sampling sadece guvenli ton/format kollarinda.
- Riskli konu/claim/media exploration disidir.
- Gunluk exploration kotasi ve minimum exploitation payi vardir.

### Learning

- Online agirliklar bounded ve decay'li.
- Edit distance, reject reason ve performance metric ayri sinyallerdir.
- Exposure, saat, takipci buyuklugu ve event tipiyle normalize edilmemis ham like sayisi dogrudan reward olmaz.

### Text classification ve optimizasyon

- Az ve orta etiket hacminde TF-IDF/HashingVectorizer + MultinomialNB hiz baseline'i ve regularized logistic/SGD kalite challenger'i kullanilir.
- Incremental ogrenme, vocabulary rebuild yerine HashingVectorizer + `partial_fit` destekli SGD ile benchmark edilir.
- LSTM/RNN ilk secim degildir; yalniz yeterli sequence etiketi ve kanitli learning-curve kazanci varsa challenger olabilir.
- Sparse lineer modelde `optimal/adaptive` learning-rate benchmark edilir; Adam/AdamW yalniz transformer fine-tuning gibi uygun differentiable modellerde kullanilir.
- Genetic algorithm, PSO ve benzeri meta-sezgiseller mevcut ranking/threshold/worker problemlerine varsayilan olarak eklenmez; once random search, successive halving ve deterministik scheduler kullanilir.

### Calibration ve model terfisi

- Kucuk veride sigmoid calibration; isotonic yalniz yeterli ayri calibration verisiyle denenir.
- Random split yerine event/thread/duplicate izolasyonlu zaman split'i kullanilir.
- Challenger; offline, shadow ve sinirli kontrollu deneyden gecmeden champion olamaz.
- Kalite artisi risk recall, p95 latency, peak RSS/VRAM veya calibration hard gate'ini bozuyorsa model terfi etmez.

## SLO taslagi

- `POST /capture`: p95 < 150 ms; agir analiz yapmadan 202 donmeli.
- Inbox sorgusu: 100 bin kayitta p95 < 300 ms.
- Ucuz text feature: p95 < 100 ms/post CPU.
- Image hash + thumbnail: p95 < 300 ms/medya.
- OCR/image embedding: p95 donanima gore benchmark ile sabitlenir; UI thread'i bloklamaz.
- Suggestion queue: mevcut feature'larla p95 < 500 ms.
- Worker hata kaybi: 0; retry/dead-letter ile izlenebilir.

## Optimizasyon kurallari

- Profilsiz optimizasyon yapma; her degisiklik benchmark ile kanitlanir.
- N+1 query yasak; batch fetch ve uygun indeks kullan.
- Modeli her istekte yukleme; lazy singleton ve idle unload.
- Embedding/OCR/caption sonucunu `content_hash + model_version + config_hash` ile cache'le.
- UI sorgularinda pagination zorunlu; buyuk JSON payload dondurme.
- Video frame sayisi, dosya boyutu ve duration kesin limitlidir.
- Backfill dusuk oncelikli kuyrukta, canli capture'dan ayri calisir.
- p50/p95/p99, throughput, peak RSS, disk growth ve cache hit birlikte raporlanir.
- GPU VRAM, CUDA/driver uygunlugu ve OOM sayisi diagnostics raporuna girer.
- Model scheduler ayni anda yalniz tek agir modeli bellekte tutar.

## Benchmark ve regresyon

Benchmark seti en az su segmentleri tasir:

- Metin-only Turkce futbol.
- Futbol kelimesi olmayan ama gorsel/quote ile futbol olan.
- Alakasiz metin + alakali medya.
- Alakali metin + alakasiz/ironik medya.
- Duplicate/near-duplicate gorsel ve metin.
- Video/OCR/ASR fallback.
- Kriz, telif, siyaset ve misinformation riski.

Her release kalite ve performans baseline'ina karsi olculur. Hiz artisi risk recall veya relevance kalitesini belirlenen toleransin altina dusuremez.
