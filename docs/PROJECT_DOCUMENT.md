# XNative Recursive Learning - Proje Tanımı

Durum: Final ürün kapsamı  
Sürüm: 1.0  
Tarih: 2026-06-22

## 1. Amaç

XNative, tek bir futbol odaklı X hesabı için görünür içerikten öğrenen, multimodal kanıtları birleştiren, olay ve kaynak adayları bulan, X-native Türkçe taslaklar hazırlayan ve sonuçlarından kontrollü biçimde öğrenen local-first karar destek sistemidir.

Sistem bir haber botu veya otomatik sosyal medya hesabı değildir. Analiz ve öneri üretimi otonom; bütün public X eylemleri insan kontrollüdür.

## 2. Kullanıcı ve temel iş akışı

Ana kullanıcı hesap sahibi veya içerik editörüdür.

```text
Görünür capture/manual import
-> yerel arşiv ve multimodal analiz
-> event/source/candidate retrieval
-> risk ve çok hedefli ranking
-> taslak varyantları
-> insan review
-> manual post/performance feedback
-> segmentli evaluation ve kontrollü öğrenme
```

## 3. Kapsam

- Görünür browser DOM ve manual JSON/CSV capture.
- Text, quote, OCR, image, sınırlı video/audio ve author/event bağlamı.
- Exact ve perceptual duplicate kontrolü.
- Event/entity memory, hybrid lexical+dense retrieval ve typed graph.
- Source candidate discovery; approve/watch/reject, otomatik follow yok.
- Multi-action utility, risk, novelty/fatigue ve diversity.
- Template/local/optional-provider taslak zinciri.
- Review, feedback, performance snapshot, model registry ve rollback.
- Yerel dashboard, inbox, suggestion queue, source review, reports ve settings.
- 8 GB RAM/GTX 1050 hedefinde CPU-only fallback.

## 4. Kapsam dışı

- X API'yi zorunlu veya ücretli bağımlılık yapmak.
- Tweet, like, follow, repost, reply, quote veya bookmark otomasyonu.
- Cookie, credential, private/gizli içerik toplama.
- Proxy rotation, rate-limit bypass veya büyük ölçekli scraping.
- İlk sürümde multi-account/SaaS, Kafka/Kubernetes/Milvus.
- Hedef makinede büyük LLM/VLM/GNN eğitimi.
- Model skorunu gerçeklik veya hukuki izin kanıtı saymak.

## 5. Başarı ölçütleri

Ürün başarısı test sayısı veya dosya varlığıyla ölçülmez. Minimum release sonucu:

1. Extension/manual capture -> API -> SQLite -> durable worker -> suggestion -> review -> feedback akışı veri kaybı olmadan çalışır.
2. API anahtarı ve ücretli servis olmadan core akış tamamlanır.
3. “Futbol” kelimesi olmayan multimodal örneklerde kanıt ve belirsizlik üretir.
4. Duplicate, yüksek risk ve kaynak kanıtsız iddia güvenli biçimde engellenir/review'a alınır.
5. Her skor ve taslak kaynak, feature/model/config sürümüne izlenebilir.
6. Hedef cihazda SLO, RSS/VRAM ve 24 saat soak kapıları geçer.
7. Yeni model offline ve shadow gate geçmeden champion olmaz; rollback çalışır.
8. X üzerinde otomatik public action bulunmaz.

## 6. Maliyet ve servis politikası

Varsayılan yol yerel ve anahtarsızdır. Google AI/Gemini veya başka provider yalnız belirsiz ve yüksek değerli kayıtta, açık enablement ve bütçe altında adapter olarak kullanılabilir. Kota, ödeme veya servis kesintisi core işi kaybettirmez.

## 7. Veri ve gizlilik

- Metadata-first arşiv varsayılandır.
- Thumbnail policy-based, original media opt-in ve kota kontrollüdür.
- Ham payload minimize edilir; loglar secret/ham içerik taşımaz.
- Kullanıcı post, author veya tarih aralığına göre silme başlatabilir.
- Feedback/audit append-only; silinen içerik audit'e tekrar kopyalanmaz.

## 8. Otonomi sınırı

Sistem capture sonrası işleme, analiz, enrichment, ranking, taslak, rapor ve güvenli model değerlendirmesini kendi çalıştırır. Kullanıcının onayı olmadan platform davranışı üretmez. Bu sınır model veya konfigürasyonla kapatılamaz.

## 9. Teslim ve yönetim

- Uygulama sırası: `MASTER_IMPLEMENTATION_BACKLOG.md`.
- Kod sözleşmesi: `IMPLEMENTATION_SPECIFICATION.md`.
- Algoritma kararları: `ALGORITHM_SELECTION_AND_EXPERIMENT_PLAN.md` ve `ALGORITHM_TECHNOLOGY_RADAR.md`.
- Kabul kanıtı: `REQUIREMENTS_TRACEABILITY.md` ve `TEST_PLAN.md`.
- Mevcut kod durumu: `FINAL_QA_REPORT.md` baseline raporu.

