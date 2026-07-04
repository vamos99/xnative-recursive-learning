# Algoritma Secimi ve Deney Plani

Durum: Baglayici teknik karar kaydi  
Tarih: 2026-06-22  
Hedef donanim: 9. nesil i5, 8 GB RAM, GTX 1050; CPU-only calisma zorunlu

## 1. Karar ilkesi

Algoritma adi degil, problem sinifi ve olculebilir sonuc secimi belirler. Her yeni model once mevcut baseline'a karsi ayni zaman bolmeli veri setinde denenir. Kalite artisi; latency, peak RAM/VRAM, disk, enerji, aciklanabilirlik ve hata maliyetiyle birlikte raporlanmadan model production champion olamaz.

Bu projede varsayilan sira:

1. Deterministic kural ve indeks.
2. Ucuz istatistiksel baseline.
3. Incremental veya nonlinear challenger.
4. Transfer-learning tabanli kucuk encoder.
5. Yalnizca belirsiz ve degerli kayitlarda harici buyuk model.

LSTM, transformer, genetik algoritma veya Adam gibi isimler sirf yaygin olduklari icin eklenmez. Her biri asagidaki terfi kapilarindan gecmek zorundadir.

## 2. Mevcut kodun algoritmik gercegi

| Alan | Mevcut yontem | Sorun | Planlanan yon |
|---|---|---|---|
| Metin benzerligi | TF-IDF bigram + cosine | Her stil ornegi eklenince matrisi yeniden kurar; semantik baglam zayif | Kucuk koleksiyonda TF-IDF; buyumede HashingVectorizer/FTS5 ve dense retrieval |
| Novelty | `SequenceMatcher` | Karakter benzerligi; paraphrase, entity ve medya tekrarini kacirir | Lexical + entity + embedding + pHash ensemble |
| Event tipi | Keyword eslesmesi | Dolayli futbol baglamini ve cok anlamliligi kacirir | Weak supervision + embedding + zaman/entity cluster |
| Event/candidate skoru | Sabit lineer agirlik | Kalibrasyon ve veriden ogrenme yok | Aciklanabilir baseline, sonra kalibre lojistik/gradient boosting |
| Risk | Keyword ve sabit agirlik | Dil, ironi ve baglam duyarliligi dusuk | High-recall kural + classifier + zorunlu insan incelemesi |
| Kaynak guveni | Sabit EMA | Az ornekli kaynakta asiri emin olabilir | Beta-Bernoulli shrinkage + decay |
| Exploration | Durumsuz epsilon-greedy | Context, posterior ve kalici kol istatistigi yok | Thompson Sampling veya LinUCB; yalniz guvenli format/ton |
| Online agirlik | Sinirli toplamsal update | Feature olcegine ve variance'a duyarlı | Normalize feature + regularized online learner; registry/rollback |
| Medya hash | Kisaltılmış SHA-256, adi pHash | Near-duplicate bulamaz | Exact SHA-256 + gercek dHash/pHash |
| Multimodal fusion | Yok | Metin ve medya kanitlari ortak karar uretemiyor | Confidence-aware late fusion; eksik modality maskesi |

## 3. Problem bazli karar matrisi

| Problem | Varsayilan | Challenger | Simdilik kullanma | Terfi kosulu |
|---|---|---|---|---|
| Text relevance/classification | TF-IDF veya HashingVectorizer + regularized logistic/SGD | MultinomialNB hiz baseline'i; kucuk multilingual embedding | LSTM/RNN training | Macro-F1 ve calibration artar; p95/RSS butcesi gecmez |
| Incremental text learning | HashingVectorizer + averaged `SGDClassifier(loss=log_loss, partial_fit)` | Passive-Aggressive veya calibrated linear SVM | Tum corpusu her feedbackte yeniden fit | Rolling log-loss ve forgetting testi champion'dan iyi |
| Lexical retrieval | SQLite FTS5/BM25 | Character n-gram TF-IDF | Global Python matrisi | Recall@K ve p95 birlikte daha iyi |
| Semantic retrieval | 384-dim multilingual embedding + brute-force top-K | HNSW, yalniz esik asilirsa | Buyuk cross-encoder'i her kayitta calistirma | 100-250 bin vektor veya brute-force p95 SLO asimi |
| Hybrid retrieval | BM25 + dense Reciprocal Rank Fusion | Ogrenilmis hafif reranker | Tek basina dense ya da keyword | NDCG@K/Recall@K uplift ve segment parity |
| Event clustering | Zaman pencereli candidate graph + union-find | DBSCAN/HDBSCAN offline benchmark | Global K-Means'i canli event kimligi sayma | Pairwise F1, fragmentation/merge hata orani iyilesir |
| Multimodal fusion | Kalibre late-fusion logistic regression | HistGradientBoosting/LightGBM | Uctan uca multimodal deep training | Missing-modality ve contradiction setinde net uplift |
| Candidate ranking | Normalize weighted utility | Kalibre logistic multi-action; sonra LambdaMART | Tek engagement skoru, kontrolsuz neural ranker | NDCG@K, approval, diversity ve risk recall kapilari |
| Source reliability | Beta posterior + zaman decay | Hiyerarsik Bayes | Yalniz ham ortalama/EMA | Calibration ve cold-start Brier skoru iyilesir |
| Safe exploration | Thompson Sampling | Context yeterliyse LinUCB | Risk/claim/public action exploration | Regret azalir; risk ve kota ihlali sifir |
| Threshold secimi | Validation utility, risk-recall kisiti | Segment bazli threshold | Elle sabit 61/75 gibi esikler | Holdout ve shadow sette kararlilik |
| Hyperparameter arama | Random search/successive halving | Optuna TPE, ihtiyac olursa | Genetic/PSO/grid patlamasi | Ayni compute butcesinde anlamli uplift |
| Worker planlama | Deterministic priority + resource semaphore | Kucuk knapsack/EDF heuristic | Meta-sezgisel scheduler | Kuyruk/SLO simulasyonunda kanitli kazanc |

Kod-backed P5-010 baslangici: `xnative/evaluation/text_benchmark.py`, TF-IDF+MultinomialNB, TF-IDF+logistic regression ve HashingVectorizer+SGD modellerini ayni zaman sirali split uzerinde kosar. Rapor; class count, train/test zaman siniri, duplicate text hash overlap uyarisi, accuracy, macro-F1 ve train/predict surelerini dondurur. Bu omurga learning curve ve calibration raporunun altyapisidir; tek basina champion model karari degildir.

## 3.1 Genis teknoloji radari

Durumlar:

- `SIMDI`: Veri omurgasi kurulur kurulmaz varsayilan cozum.
- `BENCHMARK`: Bagimlilik production'a eklenmeden kontrollu deney.
- `SONRA`: Veri/olcek esigi olusursa challenger.
- `KULLANMA`: Hedef donanim veya problem icin maliyeti faydasini asmaktadir.

| Teknoloji/algoritma | Projede ne ise yarar | Karar | Gerekce ve kapi |
|---|---|---|---|
| Character n-gram TF-IDF | Turkce ekler, yazim hatasi, kisaltma ve hashtag benzerligi | `SIMDI` | Word n-gram ile ortak sparse baseline; cok ucuz ve aciklanabilir |
| MultinomialNB | Cok hizli text baseline ve pipeline smoke modeli | `SIMDI` | Champion olmak zorunda degil; lojistik/SGD kazancini olcmek icin referans |
| Logistic/SGD + elastic-net | Relevance, risk ve modality fusion | `SIMDI` | Sparse feature, calibration ve `partial_fit` hedef donanima uygundur |
| Adam + L1 penalty | Neural modelde feature/weight sparsity denemesi | `SONRA` | Sparse lineer model icin `SGDClassifier` L1/elastic-net daha basit; AdamW weight decay L1 degildir. Neural fine-tune olursa proximal/explicit L1 ayri benchmark edilir |
| AdamW | Pretrained encoder'in sinirli fine-tune'i | `SONRA` | Yalniz yeterli etiket ve baska makinede egitim; yerel surekli sistemde inference-only |
| OpenCLIP/CLIP | Image-text retrieval, zero-shot topic, uyum/uyumsuzluk ve medya cluster feature'i | `BENCHMARK` | Kucuk pretrained ViT-B/32 veya verimli MobileCLIP sinifi; OCR yerine gecmez, yerelde sifirdan egitilmez |
| Cross-encoder/VLM | Zor text-image contradiction ve ince baglam | `SONRA` | Yalniz belirsiz yuksek-deger kayitta Gemini/local adapter escalation |
| SimHash/MinHash + LSH | Buyuk metin arsivinde near-duplicate aday uretme | `BENCHMARK` | Exact hash sonrasi; embedding aramasindan once ucuz duplicate kapisi |
| Real pHash/dHash | Crop/resize/encode degismis medya tekrari | `SIMDI` | SHA-256 exact hash'ten ayri tutulur; Hamming bucket ile buyur |
| FAISS `IndexFlatIP` | Dense exact top-K ve ANN'e gecis baseline'i | `BENCHMARK` | NumPy brute-force SLO asilirsa CPU sidecar; recall/latency/RAM birlikte olculur |
| FAISS HNSW/IVF-PQ | 100 binler/milyonlar seviyesinde hiz ve bellek optimizasyonu | `SONRA` | `IndexFlatIP` recall ground-truth; IVF-PQ ancak RAM baskisi ve yeterli training vectoru varsa |
| Milvus standalone/cluster | Dagitik vector DB, metadata filtreleme ve buyuk servis olcegi | `KULLANMA` | Standalone minimum 8 GB, onerilen 16 GB RAM; hedef cihaz 8 GB ve tek hesap icin servis operasyonu gereksiz |
| Typed property graph | Post, account, event, entity, media ve interaction provenance | `SIMDI` | SQLite edge tablolarinda kurulur; once sorgulanabilir veri modeli, sonra graph ML |
| Personalized PageRank | Kaynak/event yakinligi ve aday genisletme | `BENCHMARK` | Az etiketle aciklanabilir graph baseline; time decay ve edge-type weight gerekir |
| Weighted metapath/count features | TwHIN benzeri cok iliskili sinyal | `SIMDI` | GNN'den once author-post-event-media yollarini feature yapar; ablation kolaydir |
| Node2Vec/metapath2vec | Graph embedding ve link prediction | `SONRA` | Yeterli ve stabil edge yokken anlamsiz; random-walk leakage ve zaman split'i test edilir |
| GraphSAGE/R-GCN | Inductive typed-neighborhood embedding | `SONRA` | Basit metapath/PPR'yi gecmesi ve ayni RAM butcesinde calismasi gerekir |
| HGT/HAN GNN | Cok node/edge tipinde attention tabanli temsil | `SONRA` | TwHIN/HGT web-scale fikrini kopyalamak yok; en az 50 bin node, 500 bin guvenilir typed edge ve net supervised hedef olmadan kurulmaz |
| Louvain/Leiden | Offline topluluk/kaynak ekosistemi kesfi | `BENCHMARK` | Canli event clustering yerine kullanilmaz; temporal stability ve resolution hassasiyeti raporlanir |
| DBSCAN/HDBSCAN | Degisken boyutlu event/media cluster | `BENCHMARK` | Zaman penceresi ve candidate generation sonrasi; global O(N^2) distance matrisi kurulmaz |
| MMR/xQuAD | Ayni yazar/olay/format tekrarini azaltma | `SIMDI` | Top-K havuzunda deterministic diversity; GNN veya banditten once gelir |
| LambdaMART/LightGBM ranker | Nonlinear pairwise ranking | `SONRA` | Yeterli preference cifti ve group-aware time split olmadan kullanilmaz |
| Thompson Sampling/LinUCB | Guvenli ton ve format exploration | `SONRA` | Logged propensity, kalici posterior, minimum sample ve gunluk kota zorunlu |
| PSI/JS divergence + rolling loss | Feature/prediction drift | `SIMDI` | Basit ve gozlenebilir baseline; ADWIN/Page-Hinkley challenger olabilir |
| Genetic algorithm/PSO/SA | Non-differentiable kombinatoryal arama | `KULLANMA` | Mevcut threshold, ranking ve worker problemi daha basit constrained/random-search cozumlerine sahip |

## 3.2 CLIP ve multimodal karar

CLIP, image ve text'i ortak embedding uzayina getirerek su feature'lari saglar:

1. Acik futbol kelimesi olmasa da forma, saha, skor tabelasi veya oyuncu goruntusunu zero-shot label prompt'lariyla adaylama.
2. Post metni, quote ve gorsel arasinda uyum, tamamlayicilik veya celiski sinyali.
3. Text-to-image ve image-to-image arsiv aramasi.
4. Ayni sablon/meme ailesini semantic olarak gruplama.

Ancak CLIP skoru tek basina gercek/yanlis veya alakali/alakasiz karari degildir. Turkce prompt seti, OCR, entity/event history ve media missingness ayri tutulur. Ilk benchmark; pretrained kucuk OpenCLIP/MobileCLIP sinifi, batch 1-4, CPU ve GTX 1050 profili, int8/ONNX uygunlugu ve lisans kaydini kapsar. ViT-L/H gibi buyuk modeller varsayilan olmaz.

## 3.3 Heterogeneous information network ve GNN karar

Yerel graph semasi TwHIN'i kopyalamaz; kullanicinin gorunur ve izinli verisinden su node/edge tiplerini kurar:

- Node: `account`, `post`, `event`, `entity`, `media`, `topic`, `format`, `suggestion`.
- Edge: `authored`, `quotes`, `reposts_visible`, `mentions`, `contains_media`, `belongs_event`, `mentions_entity`, `similar_to`, `user_approved`, `user_rejected`.

Ilk modeller weighted edge count, time-decayed metapath, Personalized PageRank ve regularized tabular ranker'dir. Bu baselinelar aciklanabilir ve az veride calisir. Node2Vec/metapath2vec ancak graph stabil oldugunda; GraphSAGE/R-GCN/HGT ise basit graph feature'larini zaman split'inde anlamli bicimde gectiginde challenger olur. X'in global follow/engagement graph'i gorunmedigi icin TwHIN sonucunu yerel veride elde edecegimizi varsaymak yanlistir.

## 3.4 Vector index ve veri tabani karari

Gecis sirasi baglayicidir:

1. 384 boyutlu embeddingleri SQLite metadata + disk/memmap matrisinde tut; exact cosine/dot-product ground-truth olustur.
2. Gercek corpus ve query setinde NumPy ile FAISS `IndexFlatIP` CPU'yu karsilastir.
3. 100-250 bin vektor veya p95 SLO asiminda FAISS HNSW'yi benchmark et.
4. RAM limiti asilirsa IVF-PQ/quantization'i recall kaybiyla birlikte dene.
5. Milvus ancak baska, en az 16 GB RAM'li sunucu, coklu kullanici ve milyonlarca vektor gibi yeni deployment siniri olursa ADR ile tekrar degerlendirilir.

## 3.5 Veri hatti algoritmalari

| Ihtiyac | Secim | Neden |
|---|---|---|
| Tekrarsiz isleme | Idempotency key + unique constraint + transactional outbox | At-least-once retry altinda cift yazimi engeller |
| Kuyruk sirasi | Priority queue + resource class + aging | Canli capture'i backfill'in onunde tutar; starvation'i onler |
| Retry | Capped exponential backoff + full jitter + retry token bucket | Ayni anda tekrar yuklenmeyi ve retry storm'u azaltir |
| Backpressure | Bounded queue + semaphore + high/low watermark | 8 GB RAM'de sinirsiz is/model yuklemesini engeller |
| Batch | Boyut veya sure dolunca micro-batch | Embedding throughput'u artirir, latency'yi sinirlar |
| Checkpoint | Stage/version bazli durable cursor | Yeniden baslatmada kaldigi yerden ve idempotent devam eder |
| Rate limit | Token bucket | Browser capture ve provider RPM/TPM butcesini tek yerde uygular |
| Cache | Segmented LRU + TTL + content/model/config hash | Sicak feature'i korur, model degisiminde dogru invalidation |
| Ornekleme | Stratified reservoir sampling | Sinirli review/label butcesinde nadir risk ve modality segmentlerini korur |
| Zaman | Event-time + observed-at + watermark | Gec gelen metric snapshot'ini yanlis event sirasi saymaz |

Kafka, Airflow, Spark, Ray veya dagitik stream processor bu tek-makine/tek-hesap surumunde kullanilmaz. SQLite job tablosu, WAL, kisa transaction ve sinirli worker yeterlidir; dagitik bilesen ancak olculmus throughput veya operasyon siniri olursa eklenir.

## 4. Veri hacmine gore model merdiveni

Asagidaki sayilar otomatik dogru kabul edilen bilimsel sabitler degil, ilk operasyon politikasidir. Learning curve her release'te esikleri yeniden degerlendirir.

| Kullanilabilir temiz etiket | Izin verilen ana yaklasim | Yasak veya ertelenen |
|---:|---|---|
| 0-199 | Kural, BM25/TF-IDF, pretrained embedding, MultinomialNB sadece deney | Otonom model terfisi, deep training |
| 200-1.999 | Stratified/time-split ile logistic veya online SGD; sigmoid calibration | Isotonic calibration, LSTM, buyuk boosting aramasi |
| 2.000-19.999 | HistGradientBoosting/LightGBM fusion challenger; segment analizi | Uctan uca multimodal training |
| 20.000+ preference cifti | Pairwise ranker ve contextual bandit shadow deneyi | Guvenlik filtresini ogrenene devretme |
| 50.000+ temiz sequence etiketi | LSTM/GRU yalniz challenger olabilir | Benchmark olmadan production kullanimi |

LSTM bu proje icin ilk secim degildir. Kisa sosyal medya metninde uzun sekans modellemesinin maliyeti, az etiket ve hedef cihazda egitim/inference kisitlari nedeniyle lineer sparse modeller ve pretrained multilingual encoder daha uygun baslangictir. LSTM ancak sequence-order ablation'i gercek bir ihtiyac gosterdiginde ve yukaridaki veri/performans kapilarini gectiginde denenir.

## 5. Optimizasyon algoritmalari hakkinda karar

- Gradient descent ailesi, differentiable model parametreleri icindir. Sparse text icin SGD'nin `optimal` veya benchmark ile `adaptive` learning-rate profili kullanilir.
- Adam/AdamW, transformer fine-tuning gerekirse uygundur; sabit is kurali agirliklarini guncellemek icin gereksiz state ve ayar maliyeti yaratir.
- Meta-sezgisel yontemler, gradient olmayan ve kombinatoryal bir objective ortaya cikarsa challenger olur. Mevcut ranking threshold'u veya worker sirasi icin genetic algorithm, PSO, simulated annealing eklemek gerekmez.
- Hyperparameter aramada once random search ve successive halving kullanilir. TPE/Optuna ancak deney sayisi ve kosullu arama uzayi bunu gerektirirse eklenir.
- Her optimizer icin seed, arama uzayi, compute butcesi, early stopping ve secilmeyen denemeler registry'de saklanir.

## 6. Kalibrasyon, dogrulama ve veri sizintisi

- Random split yerine zaman bolmeli train/validation/test kullanilir; ayni event, thread veya near-duplicate farkli bolumlere sizamaz.
- Kucuk kalibrasyon setinde sigmoid/Platt; yeterli ve dengeli veri olmadan isotonic kullanilmaz.
- Classification: macro-F1, PR-AUC, log-loss, Brier, calibration error ve risk recall.
- Retrieval/ranking: Recall@K, NDCG@K, MRR, coverage, author/event diversity ve fatigue.
- Clustering: pairwise precision/recall/F1, cluster fragmentation ve false merge.
- Online learning: rolling regret, posterior calibration, exploration payi ve segment degradation.
- Multimodal: text-only, image-only, quote-only, missing-modality ve contradiction slice raporu zorunludur.

## 7. Performans ve karmasiklik butcesi

| Yontem | Fit/Update | Inference | Bellek notu |
|---|---:|---:|---|
| MultinomialNB | O(ND) | O(D) | Sparse ve cok ucuz baseline |
| Logistic/SGD sparse | O(E x NNZ) | O(NNZ) | 8 GB icin uygun; incremental olabilir |
| TF-IDF global rebuild | O(ND) | O(NNZ) | Her eklemede rebuild yasak; batch gerekir |
| HashingVectorizer | O(NNZ) | O(NNZ) | Vocabulary tutmaz; collision benchmark edilir |
| HistGradientBoosting | Yaklasik O(TND) | O(T x depth) | Yalniz kompakt tabular fusion feature'lari |
| Brute-force dense | Yok/append | O(Nd) | Float16/memmap; SLO esigine kadar basit |
| HNSW | O(N log N) beklenen | O(log N) beklenen | Ek indeks RAM'i; erken eklenmez |
| Pairwise MMR | Yok | O(K^2) | Candidate pool K=50-200 ile sinirli |
| LSTM | O(E x N x L x H^2) yaklasik | O(L x H^2) | Hedef cihazda varsayilan degil |

## 8. Champion-challenger terfi protokolu

1. Dataset snapshot, feature/model/config hash ve zaman araligi sabitlenir.
2. Baseline ile challenger ayni split ve compute butcesinde kosar.
3. Ortalama metrik yaninda confidence interval ve kotu segmentler raporlanir.
4. Challenger once offline, sonra kayitsiz shadow scoring, sonra sinirli kullanici kontrollu deneyden gecer.
5. Risk recall, calibration, latency veya bellek hard gate'lerinden biri bozulursa toplam skor yuksek olsa bile terfi etmez.
6. Champion artefakti, rollback nedeni ve onceki surum registry'de tutulur.

## 9. Uygulama sirasi

Bu belge yeni bir paralel uygulama sirasi yaratmaz. Degisiklikler `MASTER_IMPLEMENTATION_BACKLOG.md` sirasinda yapilir:

1. Faz 1-4: veri sozlesmesi, dogru hash, provenance ve tekrar uretilebilir feature omurgasi.
2. Faz 5: text baseline/challenger benchmark ve multimodal late-fusion dataset'i.
3. Faz 6: hybrid retrieval ve zaman pencereli event clustering.
4. Faz 7-8: Bayesian source reliability, calibrated ranker ve threshold secimi.
5. Faz 10: shadow bandit, drift ve rollback.
6. Faz 12-13: resource benchmark, learning curve ve release regression.

## 10. Birincil teknik kaynaklar

- scikit-learn `SGDClassifier`: sparse online/mini-batch ogrenme, `partial_fit` ve learning-rate davranisi.
- scikit-learn out-of-core text classification: HashingVectorizer ile incremental classifier ornegi.
- scikit-learn Naive Bayes: MultinomialNB'nin text count/TF-IDF baseline rolu.
- scikit-learn probability calibration: sigmoid/isotonic ve calibration olcumleri.
- scikit-learn HistGradientBoosting: kompakt tabular nonlinear challenger.
- X open-source recommendation algorithm: source, hydration, filtering, scoring ve selection ayrimi; yerel projeye yalniz mimari fikir olarak uyarlanir.
- OpenAI CLIP makalesi ve OpenCLIP uygulamasi: pretrained image-text embedding ve zero-shot transfer.
- MobileCLIP makalesi: kaynak-kisitli image-text encoder challenger'i.
- Meta FAISS dokumani: exact/approximate dense vector search, hiz-recall-bellek trade-off'u.
- Milvus resmi prerequisite belgesi: standalone minimum 8 GB, onerilen 16 GB RAM.
- TwHIN ve HGT makaleleri: typed relation embedding ve heterogeneous attention; web-scale sonuclar yerel projeye dogrudan genellenmez.
- AWS Builders' Library retry/backoff/jitter: tek retry katmani, token bucket ve jitter ilkeleri.
