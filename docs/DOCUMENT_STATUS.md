# XNative Belge Durum ve Okuma Haritası

Durum: Final uygulama dokümantasyonu v1.0  
Tarih: 2026-06-22

## 1. Kodlamaya başlama sırası

1. `PROJECT_DOCUMENT.md`: ürün amacı, kapsam ve başarı tanımı.
2. `MASTER_IMPLEMENTATION_BACKLOG.md`: değiştirilemez faz sırası.
3. `IMPLEMENTATION_SPECIFICATION.md`: exact kod, veri, API, job ve config sözleşmesi.
4. `ARCHITECTURE_DECISIONS.md`: mimari kararlar ve yeniden değerlendirme koşulları.
5. `TEST_PLAN.md`: test ID'leri ve faz kabul kapıları.
6. `REQUIREMENTS_TRACEABILITY.md`: gereksinim, mevcut durum ve zorunlu kanıt.

## 2. Bağlayıcı uzmanlık belgeleri

- `TARGET_ARCHITECTURE.md`: mantıksal katmanlar ve deployment.
- `ALGORITHM_AND_PERFORMANCE_PLAN.md`: complexity, SLO ve benchmark.
- `ALGORITHM_SELECTION_AND_EXPERIMENT_PLAN.md`: model merdiveni ve promotion.
- `ALGORITHM_TECHNOLOGY_RADAR.md`: algoritma aileleri; şimdi/dene/eşikte/red.
- `ML_MULTIMODAL_LEARNING_STRATEGY.md`: modality, reward ve hata analizi.
- `DATA_LIFECYCLE_AND_ARCHIVING.md`: retention, quota, silme ve yeniden üretme.
- `EXTERNAL_SERVICES_POLICY.md`: provider ve free-tier sınırları.
- `UX_PRODUCT_BRIEF.md`: ürün/interaction sözleşmesi ve P11 visual gate.
- `RISK_REGISTER.md`: risk skoru, mitigation ve faz sahibi.
- `OPERATIONS_RUNBOOK.md`: incident, queue, OOM, backup/restore ve rollback.
- `MODEL_AND_DATA_CARD_TEMPLATE.md`: her model ve dataset release kaydı.
- `GITHUB_REPOSITORY_PLAN.md`: repo adı, Git'e alınmayacak dosyalar, commit/PR sırası ve Projects board başlangıcı.

## 3. Teslim belgeleri

- `generated/XNative_Master_Architecture_And_Implementation_Plan.docx`
- `generated/XNative_Master_Architecture_And_Implementation_Plan.pdf`
- `TECHNICAL_DOCUMENT.md`: implementer için kısa giriş ve compatibility özeti.
- `USER_GUIDE.md`: mevcut baseline ile hedef kullanıcı akışını ayırır.

## 4. Diyagram kaynakları

- `diagrams/architecture_overview.mmd`
- `diagrams/capture_sequence.mmd`
- `diagrams/learning_loop.mmd`
- `diagrams/domain_erd.mmd`
- `diagrams/job_state.mmd`

Mermaid dosyaları düzenlenebilir doğruluk kaynağıdır. DOCX/PDF'deki görseller özet sunumdur.

## 5. Durum/kanıt belgeleri

- `ENGINEERING_BASELINE.md`: doğrulanmış geliştirme ortamı ve belge QA.
- `FINAL_QA_REPORT.md`: mevcut kodun release-ready olmadığını gösteren baseline denetimidir; final ürün onayı değildir.
- `AGENT_IMPLEMENTATION_REPORT.md`: ilk import/remediation çalışmasının tarihsel özetidir; bağlayıcı değildir.
- `ZERO_COST_STRATEGY.md`: kısa maliyet özeti; detaylı politika `EXTERNAL_SERVICES_POLICY.md` içindedir.

## 6. Final belgenin anlamı

Dokümanlar uygulamaya hazır ve kararları kapalıdır; uygulamanın tamamlandığı anlamına gelmez. Kod durumu yalnız backlog, traceability ve güncel QA kanıtıyla belirlenir. Yeni karar önce ADR/backlog/spec'e, sonra koda işlenir.
