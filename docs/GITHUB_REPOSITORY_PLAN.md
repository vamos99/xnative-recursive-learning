# GitHub Repository Plan

Durum: Hazırlık  
Tarih: 2026-06-25

## 1. Önerilen repo adı

`xnative-recursive-learning`

Gerekçe: Paket adıyla aynı, projenin X-native yerel öğrenme amacını açık taşıyor ve ileride web/API/worker/extension bileşenleri aynı repo altında kalabilir.

## 2. Git'e alınmayacaklar

- `.env`, `.env.*` ve gerçek API key/token dosyaları.
- `.venv/`, cache, `__pycache__`, test/ruff/mypy cache dizinleri.
- `data/*.sqlite3`, media/log runtime çıktıları ve yerel arşiv verisi.
- `docs/archive/`: eski zip/baseline ikili teslim arşivleri.
- `docs/generated/`: Markdown kaynaklardan yeniden üretilebilen DOCX/PDF çıktıları.
- `notes/`, `private_notes/`, `*.local.md`: sadece bize ait notlar.

## 3. İlk GitHub yükleme sırası

1. `main`: kaynak kod, testler, Markdown dokümanlar, extension kaynakları ve config örnekleri.
2. İlk commit: `chore: establish local-first xnative baseline`.
3. Phase 1 commit: `feat(storage): add domain models and sqlite unit of work`.
4. Phase 2 commit: `feat(capture): add local api capture and extension outbox`.
5. Phase 3 commit: `feat(worker): add durable job runtime controls`.

Mevcut worktree zip import olduğu için ilk yüklemede gerçek commit ayrımı ancak dosya geçmişi olmadığı halde mantıksal staging ile yapılabilir. Sonraki geliştirmelerde her faz veya kabul kapısı ayrı branch + PR ile ilerlemelidir.

## 4. GitHub Projects board başlangıcı

Board kolonları:

- `Backlog`
- `Ready`
- `In Progress`
- `Review`
- `Done`
- `Blocked`

Başlangıç kartları:

- `Phase 2 gaps: DOM fixture capture and manual archive`
- `Phase 3 remaining: full pipeline chain and dead-letter UI`
- `Phase 4: media storage, pHash and lifecycle`
- `Phase 5: multimodal understanding baseline`
- `Phase 6: retrieval/event memory`
- `Phase 11: review UI`
- `Phase 12: observability, security and performance gates`

## 5. GitHub'a geçmeden önce kontrol

- `git status --short --ignored` içinde yüklenmeyecek runtime dosyaları `!!` olarak görünmeli.
- Secret taraması gerçek token/key bulmamalı.
- Test/lint/type kapıları yeşil olmalı.
- Remote oluşturulduktan sonra branch koruması ve PR zorunluluğu açılmalı.
