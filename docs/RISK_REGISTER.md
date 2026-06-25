# XNative Risk Kaydı

Durum: Aktif ve bağlayıcı  
Tarih: 2026-06-22

Skala: Olasılık ve etki `1-5`; skor çarpımlarıdır. `15+ kritik`, `8-14 yüksek`, `4-7 orta`, `1-3 düşük`.

| ID | Risk | O | E | Skor | Azaltım | Kanıt/faz |
|---|---|---:|---:|---:|---|---|
| R-001 | X DOM değişimi capture'ı bozar | 4 | 4 | 16 | Selector version, parse metric, fixture contract, circuit ve manual import | P2 |
| R-002 | Extension retry sırasında veri kaybı | 3 | 5 | 15 | Disk outbox, DB commit sonrası ack, jitter ve E2E restart testi | P2/P3 |
| R-003 | Yanlış iddia veya kriz taslağı | 3 | 5 | 15 | High-recall policy, evidence requirement, abstention ve human review | P8/P9 |
| R-004 | 8 GB RAM'de OOM/swap | 4 | 4 | 16 | 5.5 GB soft limit, heavy semaphore=1, lazy unload, CPU fallback | P5/P12 |
| R-005 | Tek viral post source güvenini bozar | 4 | 3 | 12 | Beta shrinkage, minimum sample, time decay ve credible interval | P7/P10 |
| R-006 | Feedback loop confirmation bias | 3 | 4 | 12 | Exploration kotası, time split, segment report, champion gate | P8/P10 |
| R-007 | Duplicate leakage metrikleri şişirir | 4 | 4 | 16 | Event/thread/pHash group time split ve leakage audit | P5/P13 |
| R-008 | Provider quota/429 işi durdurur | 4 | 3 | 12 | Provider optional, token bucket, timeout, local fallback | P9/P12 |
| R-009 | Free-tier verisi gizlilik riski | 3 | 5 | 15 | Default local, explicit enable, minimization, policy verification | P9/P12 |
| R-010 | Link silinince öğrenme kanıtı kaybolur | 4 | 3 | 12 | Metadata/visible snapshot, optional thumbnail, availability state | P4 |
| R-011 | Yerel medya telif/gizlilik riski | 3 | 5 | 15 | Metadata-first, original opt-in, reason/TTL/quota/delete | P4 |
| R-012 | SQLite contention veya corruption | 2 | 5 | 10 | WAL, short transaction, busy timeout, integrity/backup/restore | P1/P12 |
| R-013 | Model confidence yanlış kalibre | 4 | 4 | 16 | Brier/log-loss/ECE, sigmoid calibration, abstention, shadow | P8/P13 |
| R-014 | GNN/CLIP/Milvus over-engineering | 4 | 3 | 12 | Technology radar, data/resource gate, ADR ve benchmark-first | P5/P6 |
| R-015 | Otomatik public action eklenmesi | 2 | 5 | 10 | Mimari invariant, security test, UI yalnız manual deep-link | Tüm fazlar |
| R-016 | Secret/log sızıntısı | 3 | 5 | 15 | Local token file, structured redaction, diagnostics audit | P11/P12 |
| R-017 | Drift sessiz kalite düşürür | 4 | 4 | 16 | PSI/JS/rolling loss, segment alarm, freeze ve rollback | P10/P12 |
| R-018 | Disk kotası capture'ı durdurur | 3 | 4 | 12 | Metadata devamı, high watermark, GC, usage dashboard | P4/P12 |
| R-019 | UI eski/partial veriyi güncel gösterir | 3 | 3 | 9 | live/stale/offline/partial state sözleşmesi | P11 |
| R-020 | Belgeler koddan sapar | 3 | 4 | 12 | Backlog ID, traceability, generated master, release cross-check | P14 |

## Risk kabul kuralı

- Kritik risk açık owner/backlog ve test olmadan release edilemez.
- Yüksek risk residual açıklaması ve rollback/fallback olmadan kapatılamaz.
- Risk skoru düşürüldüğünde kanıt linki ve tarih eklenir.
- Güvenlik, privacy ve public-action sınırı “kabul edildi” diyerek kapatılamaz; hard gate'tir.

