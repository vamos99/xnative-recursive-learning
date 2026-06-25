# XNative Review Workspace - Urun Tasarim Brifi

Durum: Final urun ve etkilesim sozlesmesi; gorsel concept secimi P11 baslangic kapisidir.

## Urun

Tek bir futbol odakli X hesabi icin yerel capture, multimodal analiz, kaynak/olay kesfi, taslak onayi ve ogrenme calisma alani.

## Ana kullanici

Hesap sahibi veya icerik editoru. Teknik log okumadan “ne oldu, neden onerildi, risk ne, ne yapmaliyim?” sorularini yanitlamak ister.

## Birincil akis

1. Extension gorunur postu yerel inbox'a kaydeder.
2. Sistem metin, quote, medya, OCR ve olay baglamini analiz eder.
3. Aday olaylar ve taslaklar kanit/aciklama ile siralanir.
4. Kullanici approve, revise, reject veya ignore eder.
5. Sonradan performans girilir/yakalanir; sistem neyin ise yaradigini raporlar.

## Zorunlu yuzeyler

- Dashboard: sistem sagligi, queue, son olaylar, riskler, ogrenme trendi.
- Capture Inbox: post, quote, medya, OCR, dedup ve provenance.
- Suggestions Queue: varyant, skor, neden, risk, medya ve eylemler.
- Source Candidates: kanit, belirsizlik, watch/approve/reject.
- Style Memory: onayli ornekler, benzerlik ve kaldirma.
- Reports: performans, hata segmentleri, exploration ve model drift.
- Settings: local/free-tier, model, threshold, retention ve blocked terms.

## Tasarim ilkeleri

- Operasyonel, masaustu-oncelikli; mobilde temel review akisi korunur.
- Tablo/liste tabanli yogunluk; her seyi karta donusturme.
- Risk ve belirsizlik renk disinda ikon/metinle de kodlanir.
- Kritik deger hover olmadan gorulur.
- Live/stale/offline/partial durumlari aciktir.
- Evidence drawer, model aciklamasi ve audit trail erisilebilirdir.

## Baglayici bilgi mimarisi

- Sol rail: Dashboard, Inbox, Suggestions, Events, Sources, Style, Reports, Jobs, Settings.
- Ust durum cubugu: API/worker/DB/model durumu, queue age, son capture ve offline/partial etiketi.
- Ana liste: server-side filter, cursor pagination, keyboard selection ve kayitli URL state.
- Sag evidence paneli: source post/quote/media/OCR, feature contribution, risk, provenance ve audit.
- Review actionlari: approve, edit, reject, ignore; action nedeni klavye ile erisilebilir.
- Destructive action modal ve undo/audit davranisi tasir.

## Durum sozlesmesi

- `live`: veri SLO icinde.
- `stale`: son guncelleme SLO'yu asmis; eski zaman acikca yazilir.
- `offline`: API/worker erisilemez; sahte veri gosterilmez.
- `partial`: bazi modality/model ciktisi yok; mevcut kanit ve eksik kisim ayrilir.
- `empty`: neden bos oldugu ve yapilacak ilk islem yazilir.
- `error`: correlation ID, guvenli mesaj ve retry/diagnostics eylemi.

## Gorsel uygulama kapisi

P11 basladiginda bu bilgi mimarisini degistirmeyen tam ekran ve mobil durumlari iceren uc gorsel yon uretilir. Kullanici secimi yalniz gorsel sistem ve yogunluk tercihini belirler; endpoint, state, accessibility ve review akis sozlesmelerini degistirmez. Secilmis gorsel hedef olmadan production UI kodlanmaz; ancak API ve domain fazlari bu secimi beklemez.
