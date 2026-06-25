# XNative Algoritma ve Teknoloji Radari

Durum: Baglayici longlist ve karar cercevesi  
Tarih: 2026-06-22  
Kapsam: Capture'dan kontrollu ogrenmeye kadar tum algoritmik kararlar

## 1. Bu belge neyi cozer?

Bu radar kullanicinin saydigi algoritmalarla sinirli degildir. Projenin her alt problemini ayri ele alir, uygulanabilir algoritma ailelerini karsilastirir ve su dort karardan birini verir:

- `SIMDI`: Ilk dogru ve basit production baseline'i.
- `DENE`: Production bagimliligi olmadan benchmark/challenger.
- `ESIKTE`: Veri, olcek veya donanim esigi gecilirse yeniden degerlendir.
- `RED`: Bu deployment ve problem icin gereksiz ya da zararli complexity.

Radar sabit degildir. Yeni model veya kutuphane ayni puanlama ve hard gate'lerden gecirilerek eklenir. Longlistte bulunmak kurulacagi anlamina gelmez.

## 2. Secim puani ve hard gate

Her challenger 1-5 arasi puanlanir:

| Boyut | Agirlik | Soru |
|---|---:|---|
| Offline kalite | 25 | Dogru segment metriginde baseline'i ne kadar geciyor? |
| Veri uygunlugu | 15 | Etiket, graph, modality ve zaman kapsami yeterli mi? |
| RAM/VRAM/CPU | 15 | 8 GB RAM ve GTX 1050/CPU-only profiline uyuyor mu? |
| Latency/throughput | 10 | Canli ve backfill SLO'sunu karsiliyor mu? |
| Guvenlik/kalibrasyon | 10 | Risk recall ve uncertainty davranisi yeterli mi? |
| Aciklanabilirlik | 10 | Kullanici karar nedenini ve kaniti gorebiliyor mu? |
| Operasyon | 10 | Kurulum, upgrade, backup ve failure maliyeti nedir? |
| Lisans/gizlilik | 5 | Model/veri lisansi ve dis servise veri cikisi uygun mu? |

Toplam puan tek basina yeterli degildir. Su hard gate'lerden biri gecmezse terfi yoktur:

1. Risk recall belirlenen minimumun altina dusmez.
2. Event/thread/duplicate leakage olmayan time-split kullanilir.
3. Peak application RSS 5.5 GB soft limiti ve GPU OOM fallback'i korunur.
4. Offline ve shadow kaniti olmadan champion degismez.
5. Public X action insan onayindan cikmaz.
6. Model, dataset, feature, config ve lisans surumu kayitlidir.

## 3. Capture, ingestion ve stream processing

| Aile | Adaylar | Karar | Projedeki kullanim |
|---|---|---|---|
| Idempotency | Post ID, content hash, idempotency key, unique constraint | `SIMDI` | At-least-once capture'da cift kaydi engeller |
| Commit pattern | Transactional outbox, inbox dedup | `SIMDI` | DB kaydi ve job olusumunu atomik baglar |
| Retry | Exponential backoff, full jitter, retry budget/token bucket | `SIMDI` | Retry storm ve provider/browser yuklenmesini azaltir |
| Rate limit | Token bucket, leaky bucket, fixed/sliding window | `SIMDI`: token bucket | Burst toleransi ve tek yerden quota kontrolu |
| Backpressure | Bounded queue, semaphore, high/low watermark | `SIMDI` | RAM ve tek-agir-model sinirini korur |
| Scheduling | FIFO, priority+aging, EDF, WFQ, shortest-job-first | `SIMDI`: priority+aging; `DENE`: EDF | Live capture, review ve backfill starvation olmadan siralanir |
| Batch | Count/time micro-batch, adaptive batch | `SIMDI`: bounded micro-batch | Embedding throughput; latency ust siniri |
| Stream time | Event time, observed time, watermark | `SIMDI` | Gec gelen metric snapshot ve event sirasi |
| Distributed engine | Kafka, Flink, Spark Streaming, Ray | `RED` | Tek hesap/tek 8 GB makinede operasyon maliyeti faydayi asar |
| Orchestrator | Airflow, Dagster, Prefect | `RED` canli hat; `ESIKTE` offline | SQLite job DAG ilk surum icin yeterlidir |

## 4. Exact ve near-duplicate tespiti

| Veri | Adaylar | Karar | Not |
|---|---|---|---|
| Post kimligi | X post ID + canonical URL | `SIMDI` | Birincil exact anahtar |
| Byte duplicate | SHA-256 | `SIMDI` | Medya content-addressed store |
| Image perceptual | dHash, pHash, wHash, color hash | `SIMDI`: dHash+pHash | Crop/overlay direnci golden sette olculur |
| Image local feature | ORB keypoint + RANSAC | `DENE` | Crop/repost vakalarinda pHash challenger; SIFT lisans/compute ayrica incelenir |
| Image structural | SSIM | `DENE` rerank | Ayni boyuta normalize edilmis adaylarda; global scan degil |
| Text lexical | SimHash, MinHash shingles | `DENE` | Buyuk arsivde embedding oncesi ucuz candidate generation |
| Semantic duplicate | Sentence embedding cosine | `SIMDI` Faz 6 | Paraphrase; event ve entity kanitiyla birlikte |
| Index | LSH/banding, Hamming prefix bucket | `ESIKTE` | Linear scan SLO'su asilinca |

## 5. NLP ve metin anlama

| Problem | Baseline | Challenger | Ertelenen/reddedilen |
|---|---|---|---|
| Dil/normalization | Unicode, URL/mention/emoji policy, char n-gram | fastText language ID | LLM ile her metni normalize etme |
| Lexical relevance | Word+char TF-IDF, BM25 | BM25F field weights | Salt keyword |
| Classification | MultinomialNB, logistic/SGD elastic-net | Linear SVM + calibration, HistGB on compact features | LSTM/GRU ilk model degil |
| Dense representation | multilingual-E5-small benzeri 384-d encoder | BGE/MiniLM family benchmark | Buyuk encoder'i surekli RAM'de tutma |
| Rerank | Logistic feature reranker | Small cross-encoder | Her kayitta LLM rerank |
| Entity extraction | Dictionary/gazetteer + regex + fuzzy match | spaCy/transformer NER | Sadece generative extraction |
| Topic discovery | NMF on TF-IDF | BERTopic/HDBSCAN offline | LDA'yi canli event classifier sayma |
| Sentiment/stance | Rule lexicon + supervised linear | Small transformer | Sentiment'i engagement ile esitleme |
| Irony/humor | Weak labels + context features | Small transformer/VLM escalation | Tek model skoruyla kesin ironi karari |
| Claim extraction | Pattern + entity/relation candidates | Constrained LLM JSON adapter | Kaynaksiz claim'i gercek kabul etme |

Karar: Turkce sosyal medya dilinde word ve character feature birlikte tutulur. Dense encoder lexical retrieval'in yerine gecmez; RRF ile birlesir. LSTM ancak en az 50 bin temiz sequence etiketi ve word-order ablation kazanci varsa challenger olur.

## 6. Computer vision ve medya anlama

| Problem | Adaylar | Karar | Kullanim |
|---|---|---|---|
| Image-text ortak uzay | CLIP/OpenCLIP, MobileCLIP, SigLIP | `DENE`: kucuk OpenCLIP/MobileCLIP | Zero-shot topic, retrieval, alignment |
| Saf image feature | DINOv2 small, MobileNet/EfficientNet | `DENE`: yalniz CLIP'in kacirdigi visual similarity varsa | Logo/forma/sahne benzerligi |
| Object detection | YOLO nano/small, MobileNet-SSD | `ESIKTE` | Top/saha/skor tabelasi icin golden set CLIP'i gecerse |
| OCR | Tesseract, EasyOCR, PaddleOCR | `SIMDI`: Tesseract; digerleri `DENE` | Skor tabelasi, ekran goruntusu, meme metni |
| Face recognition | ArcFace vb. | `RED` varsayilan | Gizlilik ve gereksiz biyometrik risk; insan/oyuncu entity'si text/eventten |
| NSFW/safety | Rule metadata + small classifier | Provider safety/VLM challenger | False positive/negative slice zorunlu |
| Caption | BLIP/small VLM, Gemini | `ESIKTE` | Yalniz belirsiz ve yuksek degerli medya |
| Image quality | Blur, entropy, resolution, edge density | NIMA benzeri model | Basit feature yetmezse challenger |

CLIP OCR degildir, factual verification yapmaz ve Turkce domain prompt'larinda otomatik guvenilir sayilmaz. Prompt ensemble, class prior, calibration ve domain golden set zorunludur.

## 7. Video ve audio

| Problem | Baseline | Challenger | Karar |
|---|---|---|---|
| Frame secimi | Uniform 3-8 frame + keyframe | Shot-boundary histogram, scene detection | `SIMDI` uniform; `DENE` shot boundary |
| Motion | Frame difference | Optical flow | `ESIKTE`; futbol aksiyonu icin kalite artisi kanitlanirsa |
| Video-text | Frame CLIP pooling | Mobile video-text encoder | `ESIKTE`; surekli video modeli yok |
| Speech | Whisper tiny/base int8 | Distil/alternative ASR benchmark | `SIMDI` secilmis kayitta |
| Audio event | Log-mel + small classifier/CLAP | `ESIKTE` | Kalabalik/tezahurat sinyali gercek uplift verirse |
| Temporal fusion | Mean/max/attention pooling | Small temporal transformer | `ESIKTE`; etiket ve sequence ihtiyaci olmadan eklenmez |

## 8. Multimodal fusion ve uncertainty

| Aile | Karar | Neden |
|---|---|---|
| Rule/score late fusion | `SIMDI` | Her modality katkisi ve missingness aciklanabilir |
| Calibrated logistic fusion | `SIMDI` etiket sonrasi | Az veride stabil ve ucuz |
| Gradient boosting fusion | `DENE` | Nonlinear contradiction/missing interactionlarini yakalar |
| Mixture-of-experts/gated fusion | `ESIKTE` | Yeterli missing-modality ve contradiction etiketi ister |
| Cross-attention transformer | `ESIKTE` | Hedef cihaz ve veri hacmi icin agir |
| VLM direct decision | `RED` champion; `ESIKTE` escalation | Maliyet, nondeterminism ve aciklanabilirlik |
| Probability calibration | Sigmoid; sonra isotonic/temperature | `SIMDI` | Utility ve threshold icin kalibre olasilik |
| Abstention | Confidence+evidence threshold | `SIMDI` | Belirsiz kaydi review'a yollar |
| Conformal prediction | Split conformal/Mondrian | `DENE` | Yeterli exchangeable calibration verisi ve segment kapsami varsa |

## 9. Event detection, trend ve clustering

| Problem | Baseline | Challenger | Karar |
|---|---|---|---|
| Event candidate | Entity+time window+retrieval neighbor | Learned pair classifier | `SIMDI` baseline |
| Cluster merge | Union-find on candidate edges | Temporal DBSCAN/HDBSCAN | `DENE` |
| Burst | EWMA z-score, Poisson rate ratio | Kleinberg burst, CUSUM/Page-Hinkley | `DENE` |
| Change point | Rolling robust z-score | BOCPD | `ESIKTE` |
| Topic offline | NMF | BERTopic | `DENE`; canli event ID degil |
| Community | Weighted connected components | Leiden/Louvain | `DENE` kaynak ekosistemi icin |
| Novelty | Lexical+entity+dense+pHash | Learned novelty ranker | `SIMDI` ensemble |

Global K-Means canli event kimligi icin uygun degildir: cluster sayisi sabit varsayimi ve zaman davranisi yanlistir. K-Means yalniz offline centroid/quantization veya topic kesfi challenger'i olabilir.

## 10. Retrieval, vector search ve storage index

| Katman | Secim | Gecis esigi |
|---|---|---|
| Metadata/filter | SQLite B-tree/covering/partial index | Her zaman |
| Lexical | FTS5 BM25/BM25F | Her zaman |
| Dense exact | NumPy/memmap cosine; FAISS IndexFlatIP benchmark | Ilk ground-truth |
| Dense ANN | FAISS HNSW | 100-250 bin vektor veya p95 SLO asimi |
| Compression | Scalar quantization, IVF-PQ | RAM/disk limiti; recall kaybi kabul kapisi |
| Hybrid | Reciprocal Rank Fusion | Lexical+dense her ikisi hazirsa |
| Rerank | Feature logistic, small cross-encoder | Top 20-100 adayda |
| Vector DB | Milvus | `RED` hedef cihaz; baska >=16 GB server/scale ADR'si olmadan yok |

FAISS bir index kutuphanesidir; metadata, migration, audit ve transactional ana veri tabani degildir. SQLite source of truth kalir, vector index yeniden kurulabilir turetilmis artefakttir.

## 11. Graph/HIN ve network algoritmalari

| Seviye | Adaylar | Karar |
|---|---|---|
| Typed graph schema | Account/post/event/entity/media/topic/format node ve typed edge | `SIMDI` |
| Local feature | Degree, recency, weighted metapath, common neighbors, Adamic-Adar | `SIMDI` |
| Diffusion | Personalized PageRank, random walk with restart | `DENE` |
| Community | Leiden/Louvain | `DENE` offline |
| Embedding | Node2Vec, metapath2vec | `ESIKTE` stabil graph |
| Link prediction | Logistic/GBDT on graph features | `DENE` GNN'den once |
| GNN | GraphSAGE, R-GCN | `ESIKTE` |
| Heterogeneous attention | HAN, HGT | `ESIKTE`: >=50k node, >=500k guvenilir edge ve supervised hedef |
| Industry TwHIN kopyasi | Global Twitter graph embedding | `RED` | Gerekli global follow/engagement graph'i yok |

Heterophily riski nedeniyle “bagli node'lar benzerdir” varsayimi otomatik kabul edilmez. Edge-type ablation, temporal leakage ve cold-start testi olmadan GNN terfi etmez.

## 12. Source reliability ve Bayesian modeller

| Aile | Karar | Kullanim |
|---|---|---|
| Beta-Bernoulli | `SIMDI` | Dogru/yanlis veya basarili/basarisiz ikili sinyal, credible interval |
| Bayesian shrinkage | `SIMDI` | Az ornekli hesabi global/segment prior'a ceker |
| EMA with decay | `SIMDI` yalniz trend | Son performansi izler; uncertainty yerine gecmez |
| Kalman filter/state-space | `DENE` | Zamanla degisen source quality |
| Hierarchical Bayes | `ESIKTE` | Lig/konu/source segmentinde yeterli veri |
| Raw average | `RED` | Sample size ve exposure bias'ini yok sayar |

## 13. Ranking, diversity ve cok hedefli karar

| Aile | Karar | Kullanim |
|---|---|---|
| Explainable weighted utility | `SIMDI` | Ilk champion; normalize ve versionlanmis feature |
| Logistic multi-action | `SIMDI` etiket sonrasi | Approve/edit/reject/risk olasiliklari |
| HistGB/LightGBM | `DENE` | Nonlinear tabular ranking/fusion |
| LambdaMART | `ESIKTE` | >=20k preference pair ve query/event group |
| Neural ranker | `RED` ilk surum | Veri ve donanim gerekcesi yok |
| MMR | `SIMDI` | Relevance-diversity |
| xQuAD | `DENE` | Topic/author coverage |
| DPP | `ESIKTE` | MMR yetersiz kalirsa; matris maliyeti |
| Pareto/constrained utility | `SIMDI` politika | Risk hard constraint, kalite/diversity soft objective |
| Meta-sezgisel rank optimization | `RED` | Differentiable/convex veya basit discrete alternatifler yeterli |

## 14. Exploration, bandit ve reinforcement learning

| Aday | Karar | Kosul |
|---|---|---|
| Epsilon-greedy | `SIMDI` test baseline'i | Production champion degil; decay ve kota |
| UCB1 | `DENE` | Contextsiz format kolu |
| Thompson Sampling | `SIMDI` ilk production bandit | Bayesian uncertainty ve basit operasyon |
| LinUCB/contextual TS | `ESIKTE` | Yeterli context/kol exposure |
| IPS/SNIPS/Doubly Robust | `SIMDI` bandit oncesi logging | Logged propensity ile offline policy eval |
| Full reinforcement learning | `RED` | Reward gecikmeli/sparse, simulator yok, risk yuksek |

Bandit yalniz ton, format, uzunluk ve medya sunumunda calisir. Claim, politics, crisis, telif, privacy, source truth veya public action exploration'a acilmaz.

## 15. Optimizer ve hyperparameter arama

| Problem | Secim | Red/erteleme |
|---|---|---|
| Sparse linear text | SGD `optimal/adaptive`, L1/elastic-net | Adam gereksiz |
| Logistic small batch | LBFGS/SAGA/liblinear probleme gore | Tek solver'i her yerde kullanma |
| Tree model | Histogram boosting + early stopping | Derin grid search |
| Neural fine-tune | AdamW + warmup/cosine + gradient clipping | Hedef cihazda training |
| Neural L1 sparsity | Proximal/explicit L1 challenger | “AdamW = L1” yanilgisi |
| Hyperparameter | Random search -> successive halving/ASHA -> TPE | Exhaustive grid |
| Non-differentiable | Basit heuristic/ILP once | Genetic/PSO/CMA-ES/SA varsayilan degil |
| Threshold | Validation utility subject to risk recall | Elle magic number |

## 16. Active learning ve weak supervision

| Aday | Karar | Neden |
|---|---|---|
| Uncertainty sampling | `SIMDI` | En belirsiz kaydi review'a getirir |
| Diversity/core-set sampling | `SIMDI` | Ayni eventten tekrar etiketlemeyi azaltir |
| Uncertainty + diversity hybrid | `SIMDI` | Review butcesi icin varsayilan |
| Query-by-committee | `DENE` | NB/logistic/embedding uyusmazligi yararli sinyal |
| Weak rules/label functions | `SIMDI` | Keyword, entity, OCR, source ve event sinyallerini kaydeder |
| Generative label model/Snorkel | `ESIKTE` | Cok ve cakisan label function olursa |
| Self-training/pseudo-label | `ESIKTE` | Calibration ve confirmation-bias kontrolu |

## 17. Drift, anomaly ve “neden tutmadi?”

| Alan | Baseline | Challenger |
|---|---|---|
| Feature drift | PSI, JS divergence, KS | MMD |
| Online mean/loss | EWMA, rolling robust z | ADWIN, Page-Hinkley |
| Multivariate anomaly | Robust covariance | Isolation Forest |
| Performance drop | Segment rolling CI | Bayesian change point |
| Root cause | Slice/error taxonomy + SHAP/permutation | Causal model ancak deney tasarimi varsa |

SHAP aciklama skoru nedensellik degildir. “Bu feature sonucu yaratti” iddiasi kontrollu deney veya uygun causal tasarim olmadan yazilmaz.

## 18. Cache, arsiv ve approximate data structures

| Ihtiyac | Secim | Esik |
|---|---|---|
| Feature cache | Segmented LRU + TTL | `SIMDI` |
| Admission | TinyLFU | Cache churn olculurse `DENE` |
| Existence precheck | Bloom filter | DB lookup SLO'su asilirsa `ESIKTE` |
| Cardinality | HyperLogLog | Exact count pahali olursa `ESIKTE` |
| Frequency | Count-Min Sketch + heavy hitters | Trend vocabulary cok buyurse `DENE` |
| Review sample | Stratified reservoir | `SIMDI` |
| Compression | zstd; thumbnail/webp policy | `SIMDI` benchmark |
| Analytical snapshot | Parquet partition | Buyuk offline report/backfill `ESIKTE` |

Approximate structure source of truth olmaz; hata siniri belgelenir ve exact fallback korunur.

## 19. Evaluation algoritmalari ve deney tasarimi

| Alan | Zorunlu yontem |
|---|---|
| Split | Time split + event/thread/duplicate group isolation |
| Imbalance | PR-AUC, macro-F1, per-slice recall; accuracy tek basina yok |
| Ranking | NDCG@K, Recall/Precision@K, MRR, coverage, diversity |
| Calibration | Reliability diagram, Brier, log-loss, ECE |
| Clustering | Pairwise F1, fragmentation, false merge, temporal stability |
| Online | Logged propensity, IPS/SNIPS/DR, regret, guardrail metric |
| Uncertainty | Coverage-risk curve ve abstention quality |
| Significance | Bootstrap CI; coklu deneyde duzeltme |
| Efficiency | p50/p95/p99, throughput, peak RSS/VRAM, disk/model size |

## 20. Baglayici uygulama karari

Ilk uygulama dalgasi su teknolojilerle sinirlidir:

1. SQLite WAL + transactional outbox + bounded priority queue + jitter/token bucket.
2. SHA-256 + gercek dHash/pHash; semantic duplicate daha sonra.
3. Character/word TF-IDF, BM25, MultinomialNB ve regularized logistic/online SGD baseline seti.
4. Kucuk multilingual text embedding; FTS5+dense RRF.
5. Tesseract + kucuk pretrained CLIP benchmarki; confidence-aware late fusion.
6. Typed graph semasi + weighted metapath/PPR feature; GNN yok.
7. Explainable multi-action utility + MMR; kalibre logistic challenger.
8. Bayesian source reliability; bandit production'a veri olusmadan girmez.
9. Exact vector ground-truth; FAISS yalniz corpus/SLO esigiyle. Milvus yok.
10. Time-split, calibration, resource profile ve model registry her challenger icin zorunlu.

Bu siradan sapma, benchmark kaniti ve ADR gerektirir.

## 21. Kaynak omurgasi

- X For You open-source algorithm: composable retrieval/scoring/selection mimarisi.
- scikit-learn official docs: sparse linear, Naive Bayes, calibration, out-of-core learning ve boosting.
- OpenAI CLIP, OpenCLIP ve MobileCLIP: image-text representation ve efficient challenger.
- multilingual-E5: multilingual retrieval/clustering/classification embedding ailesi.
- DINOv2: self-supervised general visual feature challenger'i.
- FAISS official repository/wiki; Milvus official hardware prerequisites.
- TwHIN ve Heterogeneous Graph Transformer makaleleri; PyTorch Geometric heterogeneous graph dokumani.
- Kleinberg burst detection; AWS retry/backoff/jitter rehberi.

