from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "XNative Recursive Learning"
    database_path: Path = Path(os.getenv("XNATIVE_DB", "data/xnative.sqlite3"))
    data_dir: Path = Path(os.getenv("XNATIVE_DATA_DIR", "data"))
    media_dir: Path = Path(os.getenv("XNATIVE_MEDIA_DIR", "data/media"))
    logs_dir: Path = Path(os.getenv("XNATIVE_LOGS_DIR", "data/logs"))
    no_api_mode: bool = os.getenv("XNATIVE_NO_API_MODE", "1") != "0"
    optional_llm_provider: str = os.getenv("XNATIVE_LLM_PROVIDER", "none")
    optional_llm_api_key: str = os.getenv("XNATIVE_LLM_API_KEY", "")
    max_capture_posts: int = int(os.getenv("XNATIVE_MAX_CAPTURE_POSTS", "100"))
    max_capture_bytes: int = int(os.getenv("XNATIVE_MAX_CAPTURE_BYTES", "524288"))
    db_busy_timeout_ms: int = int(os.getenv("XNATIVE_DB_BUSY_TIMEOUT_MS", "5000"))
    light_workers: int = int(os.getenv("XNATIVE_LIGHT_WORKERS", "2"))
    heavy_workers: int = int(os.getenv("XNATIVE_HEAVY_WORKERS", "1"))
    io_workers: int = int(os.getenv("XNATIVE_IO_WORKERS", "1"))
    max_pending_jobs_per_resource: int = int(
        os.getenv("XNATIVE_MAX_PENDING_JOBS_PER_RESOURCE", "10000")
    )
    queue_aging_interval_seconds: int = int(os.getenv("XNATIVE_QUEUE_AGING_INTERVAL_SECONDS", "60"))
    queue_aging_max_boost: int = int(os.getenv("XNATIVE_QUEUE_AGING_MAX_BOOST", "50"))
    worker_idle_sleep_seconds: float = float(os.getenv("XNATIVE_WORKER_IDLE_SLEEP_SECONDS", "1"))
    worker_batch_size: int = int(os.getenv("XNATIVE_WORKER_BATCH_SIZE", "4"))
    worker_token_bucket_capacity: float = float(
        os.getenv("XNATIVE_WORKER_TOKEN_BUCKET_CAPACITY", "60")
    )
    worker_token_bucket_refill_per_second: float = float(
        os.getenv("XNATIVE_WORKER_TOKEN_BUCKET_REFILL_PER_SECOND", "10")
    )
    retry_max_attempts: int = int(os.getenv("XNATIVE_RETRY_MAX_ATTEMPTS", "5"))
    risk_review_threshold: float = float(os.getenv("XNATIVE_RISK_REVIEW_THRESHOLD", "0.60"))
    heavy_escalation_confidence: float = float(
        os.getenv("XNATIVE_HEAVY_ESCALATION_CONFIDENCE", "0.55")
    )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
