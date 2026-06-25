# Dis Servis ve Ucretsiz Kota Politikasi

## Kural

Urunun temel akisi ucretsiz kota veya API anahtarina bagli olamaz. Dis servis yalniz opsiyonel kalite/hizlandirma adapteridir. Kota biterse yerel fallback devreye girer ve is kaybolmaz.

## Degerlendirme kapisi

Bir servis eklenmeden once su alanlar belgelenir:

- Guncel resmi ucretsiz kota ve rate limit.
- Kart/billing zorunlulugu.
- Girilen verinin saklanma ve egitim politikasi.
- Turkce, vision, OCR veya ASR kalitesi.
- Timeout, retry, 429 ve circuit breaker davranisi.
- Ham veri minimizasyonu ve kullanici onayi.
- Yerel fallback ve provider lock-in riski.

## Uygun kullanim

- Yerel modelin confidence'i dusuk oldugunda ikinci gorus.
- Uzun/belirsiz icerikte caption veya metin yeniden yazma.
- Backlog halinde batch enrichment; canli capture'i bloklamaz.
- Kullanici tarafindan acikca etkinlestirilmis adapter.

## Uygun olmayan kullanim

- Tum postlari varsayilan olarak dis servise gondermek.
- Ucretsiz kota etrafinda coklu hesap veya limit asma taktikleri.
- Credential, cookie, 2FA veya gizli X verisi gondermek.
- Provider cevabini kanitsiz gercek kabul etmek.

## 2026-06-22 aday notlari

- Groq resmi dokumani free-plan rate limitleri yayinlar; model bazinda limitler degisir. Uygun kullanim: opsiyonel text generation/ASR, adapter + 429 fallback.
- Hugging Face Hub modelleri yerel cache ve `local_files_only` modu ile calisabilir; her modelin lisansi ayri kontrol edilmelidir.
- Google AI Pro, Gemini uygulamasi ve AI Studio icin yuksek limitler sunabilir. Guncel Google One sayfasi uygun hesaplarda Google Developer Program uzerinden aylik 10 USD Google Cloud kredisi de listeler.
- Google AI Pro'daki aylik 1.000 “AI credit” Flow/Whisk urunleri icindir; Gemini API token bakiyesi olarak kabul edilmez.
- Gemini API free/paid plani ayri bir AI Studio/Cloud Billing projesine baglidir. Proje “Paid” olarak gorunmeden ve kredi ilgili billing hesaba redeem edilmeden abonelik API butcesi sayilmaz.
- Gemini API limitleri model, proje ve billing tier'a gore degisir. Aktif RPM/TPM/RPD degerleri AI Studio'dan okunmali; statik belge degeri runtime konfigurasyonu sayilmamalidir.
- Free Tier'da gonderilen icerik urun gelistirme icin kullanilabilir; resmi fiyatlandirma sayfasi Paid Tier icin bunun yapilmadigini belirtir. Hassas/ozel icerik icin paid proje veya tamamen yerel yol tercih edilir.
- Gemini 2.5 Flash-Lite/Flash sinifi modeller ucuz multimodal enrichment ve caption icin ilk adaydir; Pro yalniz dusuk hacimli zor vakalarda kullanilir.
- Cloudflare Workers AI gibi diger adaylar ancak aktivasyon aninda resmi fiyat/kota ve veri politikalari yeniden dogrulanarak eklenir.

Resmi kaynaklar:

- https://console.groq.com/docs/rate-limits
- https://huggingface.co/docs/huggingface_hub/main/package_reference/file_download
- https://one.google.com/about/google-ai-plans/
- https://developers.google.com/profile/help/benefits
- https://ai.google.dev/gemini-api/docs/billing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/pricing
