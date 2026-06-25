# XNative Veri Akisi - Level 1 - 1.0 Capture ve Ingestion

## DFD nasil olmali?

- DFD, verinin sistem icinde nereden gelip nereye gittigini gostermeli.
- DFD'de karar/if mantigi degil veri akisi anlatilir.
- External entity sistem disindaki kaynak/hedefleri gosterir.
- Process veriyi donusturen is adimidir ve numaralandirilir.
- Data store kalici veri kaynagini gosterir.
- Flow oklarinin ustunde akan veri adi yazmalidir.

## Bu ornekteki elemanlar

- External entity sayisi: 4
- Ana surec grubu sayisi: 1
- Process sayisi: 3
- Data store sayisi: 1
- Data flow sayisi: 7

## Renk ve sekil kurallari

- Sari yuvarlatilmis dikdortgen: external entity.
- Renkli elipsler: alt surecler.
- Yesil acik uclu depo: DFD data store. Silindir database icin ayrilir.
- Kirmizi ok: odeme/risk verisi.
- Mor ok: stok/envanter verisi.
- Mavi ok: kargo/teslimat verisi.
- Yesil ok: kalici kayit akisi.

## Uretilen dosyalar

- `xnative_veri_akisi_level_1_g1.mmd`: Mermaid DFD
- `xnative_veri_akisi_level_1_g1.drawio`: draw.io/diagrams.net editable DFD
- `xnative_veri_akisi_level_1_g1.png`: static visual preview
- `xnative_veri_akisi_level_1_g1_overview.png`: compact overview preview
- `xnative_veri_akisi_level_1_g1_group_<id>.png`: per-process-group previews when groups exist
- `xnative_veri_akisi_level_1_g1_report.md`: bu aciklama raporu
