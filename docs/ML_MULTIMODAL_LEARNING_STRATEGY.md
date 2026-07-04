# Multimodal ML ve Kendi Kendine Ogrenme Stratejisi

## Problem tanimi

Bir postun degeri yalnız metindeki acik futbol kelimelerinden gelmez. Kanit asagidaki kombinasyonlardan biri olabilir:

- Metin futbolu aciklar, medya destekler.
- Metin belirsizdir, gorsel oyuncu/takim/maci gosterir.
- Metin ve medya tek basina belirsizdir; quote, yazar ve ayni zaman penceresindeki olay baglami anlam kazandirir.
- Metin konuya uygundur, medya bilincli sekilde alakasiz/ironiktir ve format performans yaratir.
- Icerik futbol disidir fakat hesabin kitlesinde kontrollu exploration icin degerlidir.

Bu nedenle tek bir “football/not football” classifier yeterli degildir.

## Weak-supervision golden seti

İlk kod-backed sentetik dilim `tests/fixtures/multimodal_weak_supervision.json`
dosyasıdır. Bu fixture, metin içinde doğrudan futbol terimi yokken alt text,
OCR veya quote bağlamının topic evidence üretip üretmediğini test eder. Gerçek
veri, kullanıcı credential'ı veya özel hesap içeriği içermez.

## Temsil modeli

Her post icin ayri feature gruplari saklanir:

- `text_evidence`: entities, topics, claim, sentiment, tone, embedding.
- `quote_evidence`: quote text, author, relation ve embedding.
- `visual_evidence`: OCR, alt text, objects/concepts, image embedding, pHash.
- `audio_video_evidence`: frame concepts, OCR, ASR ve temporal summary.
- `context_evidence`: author history, event neighbors, time, source graph.
- `relationship_evidence`: text-image similarity, contradiction, complementarity, irony adayi.
- `uncertainty`: modality bazli confidence, missingness ve model version.

Son konu ve fayda skoru early fusion ile ham feature birlestirmek yerine, modality scorer ciktilarinin confidence-aware late fusion'i ile baslar. Veri arttiginda gated fusion veya kucuk multimodal classifier challenger olarak denenir.

## Iliskisiz medyanin ele alinmasi

Text-image dusuk benzerlik otomatik ceza degildir. Sistem uc hipotezi ayirir:

1. Yanlis veya spam medya.
2. Ironi/meme/attention hook olarak bilincli kontrast.
3. Modelin anlayamadigi ama baglamla ilgili medya.

Karar icin author history, benzer format performansi, OCR, quote, event neighbor ve kullanici feedback kullanilir. Kontrast formatlari ayri bir `format_family` olarak izlenir; ayni format tekrarlandikca fatigue uygulanir.

## Ogrenme sinyalleri

Pozitif:

- Onaylandi ve degistirilmeden paylasildi.
- Az revizyonla paylasildi.
- Segment baseline'ina gore yuksek performans.
- Yeni kaynak daha sonra dogru/erken sinyal verdi.

Negatif:

- Reddedildi veya ignore edildi.
- Buyuk edit distance ile revize edildi.
- Risk/telif/dogruluk problemi tespit edildi.
- Segment baseline'ina gore tekrarlanan dusuk performans.
- Kullanici “bu format/tarz tekrarli” gerekcesi verdi.

Feedback tek skora eritilmeden saklanir. Model egitimi hedef bazli yapilir; onay tahmini, risk tahmini ve engagement tahmini farkli hedeflerdir.

## Kendi kendine gelisim sinirlari

- Sistem kendi training verisini otomatik etiketleyebilir ancak pseudo-label confidence ve provenance saklanir.
- Pseudo-label verisi insan etiketinden daha dusuk agirliklidir.
- Yeni model once offline, sonra shadow, sonra sinirli champion olur.
- Minimum ornek ve confidence olmadan model agirligi guncellenmez.
- Drift veya performans dususunde son iyi modele rollback edilir.
- Model kendi policy/risk sinirlarini degistiremez.

## Hata analizi

Her basarisiz oneride asagidaki hata siniflarindan biri veya birkaci kaydedilir:

- Yanlis konu/event.
- Eksik quote/thread baglami.
- Gorsel/OCR/ASR yanlis anladi.
- Kaynak guveni yanlis.
- Zamanlama gec/erken.
- Ton veya format uyumsuz.
- Tekrar/fatigue.
- Iddia/risk/telif.
- Uretim dogal degil.
- Distribution/exposure etkisi; icerik kalitesiyle karistirilmamali.

Haftalik rapor yalniz sayim degil, hata segmenti, trend, confidence ve onerilen deney icerir.

## Model adaylari ve secim kapisi

Model adlari zorunlu bagimlilik degildir. Secim benchmark ve lisans kontrolunden sonra yapilir.

- Text embedding: multilingual sentence-transformer veya BGE-M3 sinifi; CPU/ONNX profili karsilastirilir.
- Image-text: CLIP/SigLIP sinifi; Turkce metin yerine gerekirse local ceviri veya multilingual adapter.
- OCR: Tesseract ilk fallback; EasyOCR kalite challengeri.
- ASR: Whisper tiny/small; yalniz sesli ve degerli videoda.
- Caption/VLM: kucuk quantized model; belirsiz ve yuksek degerli ornekte.
- Ranker: logistic/LightGBM ilk supervised model; derin model veri yeterliligine bagli.

Her model icin model card: lisans, boyut, RAM, latency, dil, kalite, offline durumu, veri gonderimi ve fallback kaydedilir.
