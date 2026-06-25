# Veri Yasam Dongusu ve Arsivleme

## Ana karar

Yalniz X linki tutmak az yer kaplar fakat link silinirse, kullanici adi degisirse veya DOM erisilemezse ogrenme kaniti kaybolur. Tum orijinal medyayi indirmek ise disk, telif ve gizlilik maliyeti yaratir. Bu nedenle katmanli saklama kullanilir.

## Saklama seviyeleri

### Seviye A - Metadata-only, varsayilan

- X post URL ve gorunur post ID.
- Capture zamani, post zamani, author handle/display name.
- Gorunur text, quote text, alt text ve gorunur metrik snapshot.
- Medya URL, type, dimensions ve hash metadata.
- Kaynak DOM/schema surumu.

### Seviye B - Minimal kanit

- Seviye A.
- Kucuk thumbnail veya secili video keyframe.
- OCR/ASR/caption ve embedding.
- Kullanici onayi veya risk incelemesi icin yeterli gorunur snapshot.

### Seviye C - Yerel orijinal medya, opt-in

- Yalniz kullanici secimi, izin/telif gerekcesi ve disk kotasiyla.
- Content-addressed tek kopya.
- Retention ve silme tarihi.

## X uzerinde arsivleme

- Sistem otomatik bookmark, like veya repost yapmaz.
- UI kullaniciya X linkini acar; bookmark islemi kullanici tarafindan yapilir.
- Yerel arsiv X bookmark'tan bagimsizdir.
- Link erisilemez hale gelirse `unavailable/deleted/private/unknown` durumu saklanir.

## Retention politikasi

- Ham capture payload: varsayilan 30 gun; normalization/provenance sonrasi otomatik minimize edilir.
- Metadata, gorunur text/quote/alt text: kullanici silme talebine kadar.
- Thumbnail/keyframe: varsayilan 180 gun; aktif event, onayli style evidence ve risk kaniti korunur.
- Orijinal medya: yalniz opt-in; kayit aninda retention nedeni ve bitis tarihi zorunlu.
- Embedding/OCR/caption: model surumu aktifken; stale surum 30 gun grace sonrasi yeniden uretilebilir cache olarak temizlenebilir.
- Feedback, audit ve model registry: kalici; kullanici silme talebinde icerik alani temizlenir, olay/provenance kimligi korunur.
- Uygulama logu: 30 gun; diagnostics paketleri 7 gun; secret ve ham icerik redaction zorunlu.

## Silme ve yeniden uretme

- Kullanici post, author veya tarih araligi bazinda silebilir.
- Derived feature ve medya referanslari cascade/garbage collection ile temizlenir.
- Audit log silme olayini kaydeder ancak silinen icerigi tekrar saklamaz.
- Model cache silinirse feature backfill ile yeniden uretilebilir.

## Disk butcesi

- Varsayilan toplam media kotasi 10 GB.
- Disk %85 veya media kotasi %90 yuksek su seviyesinde yeni original medya indirme durur; metadata capture devam eder.
- Disk %95 seviyesinde heavy media job admission durur ve kullaniciya kritik uyari verilir.
- LRU tek basina yeterli degildir; onaylanmis style evidence, audit ve aktif event medyasi korunur.
- Aylik rapor metadata, thumbnail, original, model ve log kullanimini ayri gosterir.
