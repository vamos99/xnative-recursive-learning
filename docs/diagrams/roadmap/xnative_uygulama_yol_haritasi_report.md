# XNative Uygulama Yol Haritasi

## Schedule Summary

- Project window: 2026-06-22 to 2026-09-18
- Total calendar days: 89
- Critical path: P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7 -> P8 -> P9 -> P10 -> P11 -> P12 -> P13 -> P14

## Generated Files

- `xnative_uygulama_yol_haritasi_gantt.mmd`: Mermaid Gantt chart
- `xnative_uygulama_yol_haritasi_wbs.mmd`: Mermaid WBS mindmap
- `xnative_uygulama_yol_haritasi_pert.mmd`: Mermaid dependency/PERT diagram
- `xnative_uygulama_yol_haritasi.drawio`: editable diagrams.net file
- `xnative_uygulama_yol_haritasi.excalidraw`: editable Excalidraw scene
- `xnative_uygulama_yol_haritasi_preview.html`: local preview and delivery summary
- `xnative_uygulama_yol_haritasi_tasks.json`: normalized task data
- `xnative_uygulama_yol_haritasi_gantt.png`: static Gantt preview
- `xnative_uygulama_yol_haritasi_wbs.png`: static WBS preview
- `xnative_uygulama_yol_haritasi_pert.png`: static PERT preview

## Assumptions

- P1: Start inferred as 2026-06-25.
- P1: End inferred from 5 day duration.
- P2: Start inferred as 2026-06-30.
- P2: End inferred from 5 day duration.
- P3: Start inferred as 2026-07-05.
- P3: End inferred from 6 day duration.
- P4: Start inferred as 2026-07-11.
- P4: End inferred from 5 day duration.
- P5: Start inferred as 2026-07-16.
- P5: End inferred from 10 day duration.
- P6: Start inferred as 2026-07-26.
- P6: End inferred from 7 day duration.
- P7: Start inferred as 2026-08-02.
- P7: End inferred from 6 day duration.
- P8: Start inferred as 2026-08-08.
- P8: End inferred from 8 day duration.
- P9: Start inferred as 2026-08-16.
- P9: End inferred from 6 day duration.
- P10: Start inferred as 2026-08-22.
- P10: End inferred from 8 day duration.
- P11: Start inferred as 2026-08-30.
- P11: End inferred from 8 day duration.
- P12: Start inferred as 2026-09-07.
- P12: End inferred from 6 day duration.
- P13: Start inferred as 2026-09-13.
- P13: End inferred from 5 day duration.
- P14: Start inferred as 2026-09-18.
- P14: End inferred from 1 day duration.

## Tasks

| ID | Task | Group | Start | End | Duration | Depends | Owner | Critical |
|---|---|---|---|---|---:|---|---|---|
| P0 | Baseline ve yonetisim | Foundation | 2026-06-22 | 2026-06-24 | 3 | - | - | yes |
| P1 | Veri omurgasi | Foundation | 2026-06-25 | 2026-06-29 | 5 | P0 | - | yes |
| P2 | Guvenilir capture | Ingestion | 2026-06-30 | 2026-07-04 | 5 | P1 | - | yes |
| P3 | Queue ve pipeline | Ingestion | 2026-07-05 | 2026-07-10 | 6 | P2 | - | yes |
| P4 | Medya ve arsiv | Intelligence | 2026-07-11 | 2026-07-15 | 5 | P3 | - | yes |
| P5 | Multimodal anlama | Intelligence | 2026-07-16 | 2026-07-25 | 10 | P4 | - | yes |
| P6 | Olay bellegi | Intelligence | 2026-07-26 | 2026-08-01 | 7 | P5 | - | yes |
| P7 | Kaynak ogrenimi | Recommendation | 2026-08-02 | 2026-08-07 | 6 | P6 | - | yes |
| P8 | Cok hedefli ranking | Recommendation | 2026-08-08 | 2026-08-15 | 8 | P6, P7 | - | yes |
| P9 | Taslak ve guvenlik | Recommendation | 2026-08-16 | 2026-08-21 | 6 | P8 | - | yes |
| P10 | Feedback ve learning | Learning | 2026-08-22 | 2026-08-29 | 8 | P9 | - | yes |
| P11 | Review UI | Product | 2026-08-30 | 2026-09-06 | 8 | P10 | - | yes |
| P12 | Performans ve guvenlik | Hardening | 2026-09-07 | 2026-09-12 | 6 | P11 | - | yes |
| P13 | Release testleri | Hardening | 2026-09-13 | 2026-09-17 | 5 | P12 | - | yes |
| P14 | Final belgeler | Delivery | 2026-09-18 | 2026-09-18 | 1 | P13 | - | yes |
