# XNative Operasyon Runbook

Durum: Hedef operasyon sözleşmesi  
Tarih: 2026-06-22

Bu komutların core doğrulama kısmı bugün çalışır; servis/backup/model komutları ilgili backlog uygulandığında aynı interface ile sağlanacaktır. Uygulanmamış adım “çalışıyor” sayılmaz.

## 1. Günlük başlangıç kontrolü

1. Disk boşluğu, DB ve token dosya izinlerini kontrol et.
2. API'yi yalnız `127.0.0.1` üzerinde başlat.
3. `GET /health` sonra `GET /ready` kontrol et.
4. Worker queue age/dead-letter ve last heartbeat kontrol et.
5. UI'da `live/stale/offline/partial` durumunu doğrula.

Hedef servis komutları:

```bash
.venv/bin/xnative migrate
.venv/bin/xnative api
.venv/bin/xnative worker --resource light
.venv/bin/xnative worker --resource heavy
.venv/bin/xnative diagnostics
```

CLI P1/P3/P12'de uygulanana kadar mevcut baseline yalnız `python -m xnative.sample_pipeline` ile doğrulanır.

## 2. Health ve readiness anlamı

- Health 200: process loop çalışıyor.
- Ready 200: migration güncel, DB yazılabilir, disk watermark altında ve queue erişilebilir.
- Ready 503: capture kabul edilmez veya güvenli degraded mode uygulanır; hata nedeni diagnostics'te görünür.
- Model/provider arızası core readiness'i düşürmez; `partial` model durumu üretir.

## 3. Capture gelmiyor

1. Extension popup capture açık mı?
2. Local API health/ready ve bearer token doğrula.
3. Extension outbox sayısını ve en eski kaydın yaşını kontrol et.
4. Selector version parse failure artmış mı?
5. Payload `413/422/401/429` kodunu correlation ID ile incele.
6. DOM drift varsa capture circuit'i kapat; fixture/manual import yolunu kullan.
7. Outbox'u silme; selector düzeltmesi sonrası replay et.

## 4. Queue büyüyor

1. Live/backfill job sayı ve yaşını resource class'a göre ayır.
2. Worker heartbeat/lease ve dead-letter nedenlerini kontrol et.
3. Memory/disk watermark veya provider token bucket blokluyor mu?
4. Backfill'i durdur; live priority korunur.
5. Aynı fatal işi sınırsız retry etme.
6. Düzeltme sonrası seçili dead-letter kaydını UI/CLI ile retry et.

## 5. GPU OOM veya yüksek RAM

Hızlı preflight:

```bash
.venv/bin/xnative-preflight --format json --output data/logs/hardware_preflight.json
.venv/bin/xnative-preflight --format text --request-name openclip-small --estimated-ram-mib 768 --estimated-vram-mib 2048
```

Bu komut ağır model yüklemez; RAM/RSS/GPU sinyallerini ve örnek heavy-model admission kararını raporlar. Çıkış kodu `0` ise istek kabul edilmiştir, `2` ise heavy iş durdurulmalı veya daha ucuz fallback seçilmelidir. `data/logs/*` runtime çıktısıdır ve GitHub'a yüklenmez.

1. Yeni heavy admission'ı durdur.
2. Model cache'i unload et; CUDA cache yalnız adapter güvenli noktada temizlenir.
3. İşi CPU/cheap fallback ile retry et.
4. Batch/frame sayısını config sınırına indir.
5. API/light worker'ı ayakta tut.
6. OOM model/config/version ve peak RSS/VRAM'i incident kaydına yaz.

## 6. Disk yüksek watermark

- `%85` veya media kotası `%90`: original download durur, metadata capture sürer.
- `%95`: heavy media job admission durur.
- Önce stale model cache, expired raw payload ve unreferenced blobs temizlenir.
- Audit, feedback, active event evidence ve approved style evidence korunur.
- Garbage collection dry-run raporu olmadan toplu silme yapılmaz.

## 7. Provider outage veya quota

1. Provider circuit'i aç; yeni istek gönderme.
2. Provider job'ını local fallback/partial sonuçla tamamla veya düşük öncelikli retry'a al.
3. 429'da `Retry-After` ve token bucket kullan; katmanlı tekrar yok.
4. Core capture/suggestion queue çalışmaya devam eder.
5. Key/token loglama; diagnostics yalnız provider adı/tier/limit state gösterir.

## 8. Model rollback

1. Drift/risk/SLO alarmında champion promotion ve online update'i freeze et.
2. Registry'de son güvenli champion'u etkinleştir.
3. Feature compatibility kontrol et; gerekirse eski feature version cache'ini kullan.
4. Shadow output'u kullanıcı skorundan ayır.
5. Regression dataset/segment, config ve incident ID ile rollback kaydı oluştur.
6. Root cause olmadan challenger'ı yeniden promote etme.

## 9. Backup ve restore sözleşmesi

Backup sırası:

1. Kısa write quiesce veya SQLite online backup API.
2. DB snapshot + migration list/checksum.
3. Settings ve secret içermeyen diagnostics.
4. Media manifest/hash; medya kopyası retention politikasına göre.
5. Backup hash ve restore test tarihi.

Hedef CLI:

```bash
.venv/bin/xnative backup --output backups/<timestamp>
.venv/bin/xnative integrity-check
.venv/bin/xnative restore --input backups/<timestamp> --verify
```

Restore ayrı temp dizinde doğrulanmadan aktif DB üzerine yazılmaz. `foreign_key_check`, integrity, row count ve örnek hashler geçmelidir.

## 10. Local token rotasyonu

1. Yeni token üret ve `0600` izinle token file'a yaz.
2. API kısa dual-token grace penceresi açar.
3. Extension/UI yeni token'a geçirilir.
4. Eski token iptal edilir; loglarda token değeri aranır.

## 11. Incident kaydı

Zorunlu alanlar: incident ID, başlangıç/bitiş, kullanıcı etkisi, correlation/job/model/config ID, detection, containment, root cause, veri kaybı, düzeltme, test, follow-up backlog ve owner.
