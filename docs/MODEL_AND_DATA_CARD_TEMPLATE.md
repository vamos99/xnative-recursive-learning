# XNative Model ve Veri Kartı Şablonu

Durum: Her öğrenilmiş model/embedding/threshold için zorunlu  
Tarih: 2026-06-22

## Model kartı

- Model ID/sürüm:
- Backlog/experiment ID:
- Problem ve karar yüzeyi:
- Champion/challenger durumu:
- Baseline:
- Model ailesi ve lisansı:
- Input feature/modality:
- Output ve calibration yöntemi:
- Eğitim ortamı/donanımı:
- Inference hedefi ve fallback:
- Hyperparameter/seed:
- Dataset snapshot/split hash:
- Primary metric ve practical uplift:
- Risk/calibration/segment guardrail:
- p50/p95/p99, peak RSS/VRAM ve artefakt boyutu:
- Bilinen başarısızlık dilimleri:
- Yasak kullanım:
- Shadow süresi/örnek sayısı:
- Promotion kararı ve onaylayan:
- Rollback modeli ve prosedürü:

## Veri kartı

- Dataset ID/sürüm/hash:
- Kaynak ve toplama yöntemi:
- Görünür/izinli veri sınırı:
- Tarih aralığı:
- Satır ve unique event/source sayıları:
- Text/image/video/quote/missing dağılımı:
- Dil ve event type dağılımı:
- Label tanımı ve annotator süreci:
- Weak/pseudo label oranı:
- Duplicate/event/thread isolation:
- Train/validation/test zamanları:
- Sensitive/privacy/telif alanları:
- Retention/delete politikası:
- Bias ve coverage boşlukları:
- Kullanılmaması gereken amaçlar:
- Leakage audit sonucu:

## Deney karar özeti

| Alan | Champion | Challenger | Fark | CI | Gate | Karar |
|---|---:|---:|---:|---|---|---|
| Primary quality | | | | | | |
| Risk recall | | | | | Hard | |
| Calibration/Brier | | | | | Hard | |
| Worst segment | | | | | Hard | |
| p95 latency | | | | | Hard | |
| Peak RSS/VRAM | | | | | Hard | |

