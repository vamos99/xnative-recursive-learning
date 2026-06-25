# Zero Cost Strategy

Default MVP mode is $0:

- X API: not used.
- Gemini/OpenAI/Claude: not required.
- Database: SQLite local file.
- Hosting: local machine.
- UI/API: optional local services.
- OCR: optional local Tesseract if installed.
- Embedding: TF-IDF fallback by default.
- Media: local metadata and hash, no unlimited download.

Optional future additions can use free-tier LLMs or local lightweight models, but the application must continue to run without keys.

Operational rule: free tier is a best-effort optional accelerator, not a capacity or availability guarantee. Activation-time quota, billing, privacy and fallback checks are defined in `EXTERNAL_SERVICES_POLICY.md`.
