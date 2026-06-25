# XNative Mimari Karar Kaydı

Durum: Kabul edildi  
Tarih: 2026-06-22

Her ADR bağlayıcıdır. Değişiklik yeni bir ADR ile “superseded” yapılır; eski karar sessizce silinmez.

## ADR-001: X API ve public action yok

- Karar: Görünür browser capture ve manual import kullanılır; X üzerinde otomatik eylem yapılmaz.
- Gerekçe: Maliyet, platform güvenliği, kullanıcı şartı ve denetlenebilirlik.
- Sonuç: Extension cookie/credential toplamaz; yayın/takip insan kontrolündedir.

## ADR-002: Tek makine local-first deployment

- Karar: İlk production hedefi 9. nesil i5, 8 GB RAM, GTX 1050 ve CPU-only fallback'tir.
- Sonuç: Bir ağır worker, en fazla iki hafif worker; uygulama RSS soft limit 5.5 GB.
- Yeniden değerlendirme: Ayrı 16+ GB sunucu ve ölçülmüş throughput ihtiyacı.

## ADR-003: SQLite source of truth

- Karar: SQLite WAL + FTS5 metadata, audit, queue, feedback ve registry'nin tek doğruluk kaynağıdır.
- Sonuç: Repository/unit-of-work zorunlu; migration checksum'lıdır.
- Yeniden değerlendirme: Çok kullanıcılı yazma yükü SQLite SLO'sunu tekrarlı biçimde aşarsa.

## ADR-004: SQLite durable job queue

- Karar: Redis/Celery/Kafka yerine lease, retry, priority aging ve dead-letter destekli SQLite queue.
- Sonuç: Tek servis operasyonu; idempotency ve kısa transaction zorunlu.
- Yeniden değerlendirme: Ölçülmüş queue contention veya ayrı worker hostu ihtiyacı.

## ADR-005: Metadata-first arşiv

- Karar: Varsayılan metadata+visible evidence; thumbnail policy-based; original media opt-in.
- Sonuç: Link kaybına karşı minimum kanıt korunur, telif ve disk riski sınırlanır.

## ADR-006: Türetilmiş vector index

- Karar: SQLite metadata source of truth; exact matrix/FAISS yeniden kurulabilir türetilmiş index.
- Sonuç: FAISS yalnız benchmark eşiğinde; index backup zorunlu değil, rebuild prosedürü zorunlu.
- Red: Hedef 8 GB makinede Milvus.

## ADR-007: Baseline-first algoritma merdiveni

- Karar: Deterministic/rule -> classical sparse -> small pretrained encoder -> optional provider.
- Sonuç: LSTM, GNN, neural ranker veya meta-sezgisel yöntem adından dolayı eklenmez; champion gate gerekir.

## ADR-008: Confidence-aware late fusion

- Karar: Modality feature ve missingness ayrı saklanır; ilk fusion açıklanabilir late fusion'dır.
- Sonuç: Eksik medya negatif kanıt sayılmaz. CLIP OCR veya fact checker değildir.

## ADR-009: Typed graph önce, GNN sonra

- Karar: SQLite typed graph, metapath ve PPR ilk baseline'dır.
- Sonuç: Node2Vec/R-GCN/GraphSAGE/HGT ancak veri ve offline uplift kapısıyla.

## ADR-010: Human review değiştirilemez güvenlik sınırı

- Karar: Model risk/policy filtresini kaldıramaz ve public action üretemez.
- Sonuç: Bandit/RL yalnız güvenli ton/format seçimine uygulanabilir.

## ADR-011: Provider adapter ve local fallback

- Karar: Gemini/Groq/Hugging Face erişimi opsiyoneldir; core akış `provider=none` ile çalışır.
- Sonuç: Timeout, quota, 429 telemetry, circuit breaker ve data minimization zorunlu.

## ADR-012: Model registry ve geri alma

- Karar: Model/feature/config sürümü olmadan öğrenilmiş çıktı yazılamaz.
- Sonuç: Offline -> shadow -> champion; eski champion rollback için tutulur.

## ADR-013: API versionlama ve compatibility alias

- Karar: Ana API `/api/v1`; eski extension `/capture` geçici alias.
- Sonuç: Alias deprecation header taşır ve Phase 2 sonunda extension ana path'e geçirilir.

## ADR-014: UI API üzerinden çalışır

- Karar: Review UI doğrudan SQLite açmaz.
- Sonuç: Yetki, validation, pagination, audit ve ileride UI değişimi tek API sözleşmesinde kalır.

## ADR-015: Derin model eğitimi hedef makinede yok

- Karar: Hedef cihaz inference ve classical/online öğrenme çalıştırır.
- Sonuç: Neural fine-tune ayrı güçlü ortamda ve artefakt/lisans kaydıyla yapılabilir; core gereksinimi değildir.

