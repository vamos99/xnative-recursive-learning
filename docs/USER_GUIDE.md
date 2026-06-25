# XNative Kullanıcı ve Baseline Çalıştırma Rehberi

Durum: Mevcut baseline için doğru; hedef ürün akışı ayrıca belirtilmiştir.  
Tarih: 2026-06-22

## 1. Mevcut doğrulanmış baseline

```bash
cd /Users/halilkiyak/Documents/twitter_agent
source .venv/bin/activate
pytest -q
python -m xnative.sample_pipeline
```

Bu komut fixture/helper baseline'ını çalıştırır. Extension -> API -> DB -> durable worker -> UI akışını henüz kanıtlamaz.

## 2. Extension durumu

Extension klasörü yüklenebilir, ancak mevcut FastAPI `/capture` route'unu kaydetmediği için capture E2E tamamlanmış değildir. Faz 2 tamamlanana kadar extension üretim capture aracı sayılmaz.

Güvenlik sınırı değişmez: extension yalnız görünür DOM'u okur; cookie, password, 2FA veya hidden/private veri toplamaz ve public action yapmaz.

## 3. Hedef kullanıcı akışı

1. Extension veya manual import postu local inbox'a kaydeder.
2. Sistem text, quote, media/OCR ve event bağlamını işler.
3. Duplicate, risk, source ve modality evidence görünür.
4. Suggestion queue gerekçe ve taslak varyantları sunar.
5. Kullanıcı approve, edit, reject veya ignore eder.
6. Kullanıcı X üzerinde paylaşımı manuel yapar.
7. Performance snapshot sonrası sistem segment bazlı rapor ve challenger önerir.

## 4. Kullanım disiplini

- Tek güvenilmez kaynaktan kesin claim üretme.
- Telif/izin nedeni olmadan original media arşivleme.
- `partial/stale` sonucu tam analiz gibi değerlendirme.
- Model confidence'ını doğruluk kanıtı sayma.
- Riskli öneriyi policy/human review dışında yayınlama.

Operasyon ve incident adımları `OPERATIONS_RUNBOOK.md` içindedir.

