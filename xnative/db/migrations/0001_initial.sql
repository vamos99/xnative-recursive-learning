CREATE TABLE IF NOT EXISTS captured_posts (
  id TEXT PRIMARY KEY,
  schema_version INTEGER NOT NULL DEFAULT 1,
  platform TEXT NOT NULL DEFAULT 'x',
  platform_post_id TEXT,
  canonical_url TEXT NOT NULL,
  author_handle TEXT NOT NULL,
  visible_text TEXT NOT NULL DEFAULT '',
  quote_post_json TEXT,
  visible_metrics_json TEXT NOT NULL DEFAULT '{}',
  platform_created_at INTEGER,
  captured_at INTEGER NOT NULL,
  capture_source TEXT NOT NULL,
  selector_version TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  raw_payload_hash TEXT NOT NULL,
  data_class TEXT NOT NULL DEFAULT 'visible_content',
  deleted_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  CHECK (length(id) = 36),
  CHECK (length(visible_text) <= 20000)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_captured_posts_platform_post_id
ON captured_posts(platform, platform_post_id)
WHERE platform_post_id IS NOT NULL AND platform_post_id != '';

CREATE INDEX IF NOT EXISTS idx_captured_posts_author_captured
ON captured_posts(author_handle, captured_at DESC);

CREATE VIRTUAL TABLE IF NOT EXISTS captured_posts_fts
USING fts5(post_id UNINDEXED, visible_text, author_handle, tokenize='unicode61');

CREATE TABLE IF NOT EXISTS post_metrics (
  id TEXT PRIMARY KEY,
  post_id TEXT NOT NULL REFERENCES captured_posts(id) ON DELETE RESTRICT,
  observed_at INTEGER NOT NULL,
  likes INTEGER,
  reposts INTEGER,
  replies INTEGER,
  views INTEGER,
  ingestion_method TEXT NOT NULL DEFAULT 'capture',
  created_at INTEGER NOT NULL,
  UNIQUE(post_id, observed_at)
);

CREATE TABLE IF NOT EXISTS capture_inbox (
  id TEXT PRIMARY KEY,
  post_id TEXT NOT NULL REFERENCES captured_posts(id) ON DELETE RESTRICT,
  raw_payload_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'accepted',
  received_at INTEGER NOT NULL,
  correlation_id TEXT NOT NULL,
  UNIQUE(post_id, raw_payload_hash)
);

CREATE TABLE IF NOT EXISTS media_assets (
  id TEXT PRIMARY KEY,
  post_id TEXT REFERENCES captured_posts(id) ON DELETE RESTRICT,
  kind TEXT NOT NULL DEFAULT 'unknown',
  media_type TEXT DEFAULT 'unknown',
  source_url TEXT,
  alt_text TEXT,
  mime_type TEXT,
  byte_size INTEGER,
  width INTEGER,
  height INTEGER,
  duration_ms INTEGER,
  exact_sha256 TEXT,
  perceptual_hash TEXT,
  phash TEXT,
  storage_policy TEXT NOT NULL DEFAULT 'metadata',
  local_path TEXT,
  availability TEXT NOT NULL DEFAULT 'remote',
  ocr_text TEXT,
  clip_tags_json TEXT NOT NULL DEFAULT '[]',
  risk_label TEXT NOT NULL DEFAULT 'unknown',
  copyright_status TEXT NOT NULL DEFAULT 'unknown',
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_media_assets_post_id ON media_assets(post_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_exact_sha256 ON media_assets(exact_sha256);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload_ref TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  priority INTEGER NOT NULL DEFAULT 100,
  resource_class TEXT NOT NULL DEFAULT 'light',
  dedupe_key TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 5,
  available_at INTEGER NOT NULL,
  lease_owner TEXT,
  lease_expires_at INTEGER,
  last_error_code TEXT,
  last_error_message TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_active_dedupe
ON jobs(dedupe_key)
WHERE status IN ('pending', 'running', 'retry');

CREATE INDEX IF NOT EXISTS idx_jobs_claim
ON jobs(status, resource_class, priority DESC, available_at, created_at);

CREATE TABLE IF NOT EXISTS job_attempts (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
  attempt_number INTEGER NOT NULL,
  owner TEXT NOT NULL,
  started_at INTEGER NOT NULL,
  completed_at INTEGER,
  status TEXT NOT NULL,
  error_code TEXT,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS dead_letters (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
  reason_code TEXT NOT NULL,
  reason_message TEXT,
  payload_snapshot_json TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  value TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE(entity_type, normalized_value)
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL DEFAULT 'other',
  title TEXT NOT NULL,
  summary TEXT,
  status TEXT NOT NULL DEFAULT 'candidate',
  started_at INTEGER,
  last_seen_at INTEGER NOT NULL,
  confidence REAL NOT NULL DEFAULT 0,
  post_count INTEGER NOT NULL DEFAULT 0,
  source_count INTEGER NOT NULL DEFAULT 0,
  entity_ids_json TEXT NOT NULL DEFAULT '[]',
  cluster_version TEXT NOT NULL DEFAULT 'rule-v1',
  merged_into_event_id TEXT REFERENCES events(id) ON DELETE RESTRICT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS event_posts (
  event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  post_id TEXT NOT NULL REFERENCES captured_posts(id) ON DELETE RESTRICT,
  link_reason TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  PRIMARY KEY(event_id, post_id)
);

CREATE TABLE IF NOT EXISTS graph_nodes (
  id TEXT PRIMARY KEY,
  node_type TEXT NOT NULL,
  ref_type TEXT,
  ref_id TEXT,
  label TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_edges (
  id TEXT PRIMARY KEY,
  src_id TEXT NOT NULL REFERENCES graph_nodes(id) ON DELETE RESTRICT,
  edge_type TEXT NOT NULL,
  dst_id TEXT NOT NULL REFERENCES graph_nodes(id) ON DELETE RESTRICT,
  weight REAL NOT NULL DEFAULT 1,
  observed_at INTEGER NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE(src_id, edge_type, dst_id, observed_at)
);

CREATE TABLE IF NOT EXISTS features (
  id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  feature_name TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  value_json TEXT NOT NULL,
  model_version TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  source_ids_json TEXT NOT NULL DEFAULT '[]',
  data_class TEXT NOT NULL DEFAULT 'derived_feature',
  created_at INTEGER NOT NULL,
  UNIQUE(owner_type, owner_id, feature_name, feature_version)
);

CREATE TABLE IF NOT EXISTS embeddings (
  id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  dims INTEGER NOT NULL,
  vector_path TEXT,
  vector_json TEXT,
  config_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE(owner_type, owner_id, model_version)
);

CREATE TABLE IF NOT EXISTS model_outputs (
  id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  model_version TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  output_json TEXT NOT NULL,
  status TEXT NOT NULL,
  latency_ms INTEGER,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
  id TEXT PRIMARY KEY,
  post_id TEXT REFERENCES captured_posts(id) ON DELETE RESTRICT,
  event_id TEXT REFERENCES events(id) ON DELETE RESTRICT,
  feature_version TEXT NOT NULL,
  model_version TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  utility_score REAL NOT NULL DEFAULT 0,
  risk_score REAL NOT NULL DEFAULT 0,
  selector_reason TEXT NOT NULL DEFAULT '',
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id TEXT REFERENCES candidates(id) ON DELETE RESTRICT,
  event_id TEXT,
  suggestion_type TEXT DEFAULT 'tweet',
  text TEXT,
  variant_label TEXT,
  variant_family TEXT,
  draft_text TEXT,
  evidence_ids_json TEXT NOT NULL DEFAULT '[]',
  policy_result TEXT NOT NULL DEFAULT 'pending',
  review_state TEXT NOT NULL DEFAULT 'pending',
  final_score REAL DEFAULT 0,
  quality_score REAL DEFAULT 0,
  risk_score REAL DEFAULT 0,
  status TEXT DEFAULT 'pending',
  model_version TEXT,
  feature_version TEXT,
  config_hash TEXT,
  created_at INTEGER DEFAULT (CAST((julianday('now') - 2440587.5) * 86400000000 AS INTEGER))
);

CREATE TABLE IF NOT EXISTS feedback_events (
  id TEXT PRIMARY KEY,
  suggestion_id TEXT NOT NULL,
  action TEXT NOT NULL,
  reason_codes_json TEXT NOT NULL DEFAULT '[]',
  original_text TEXT,
  edited_text TEXT,
  edit_distance INTEGER,
  actor TEXT NOT NULL DEFAULT 'local_user',
  occurred_at INTEGER NOT NULL,
  model_version TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_events_suggestion_occurred
ON feedback_events(suggestion_id, occurred_at);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  suggestion_id INTEGER,
  action TEXT,
  edited_text TEXT,
  reason TEXT,
  metrics_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id TEXT REFERENCES captured_posts(id) ON DELETE RESTRICT,
  suggestion_id INTEGER,
  observed_at INTEGER,
  snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP,
  minutes_after_publish INTEGER,
  impressions INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  reposts INTEGER DEFAULT 0,
  replies INTEGER DEFAULT 0,
  views INTEGER,
  followers_delta INTEGER DEFAULT 0,
  engagement_rate REAL DEFAULT 0,
  ingestion_method TEXT DEFAULT 'manual',
  created_at INTEGER
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_performance_post_observed
ON performance_snapshots(post_id, observed_at)
WHERE post_id IS NOT NULL AND observed_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  handle TEXT UNIQUE,
  display_name TEXT,
  source_type TEXT DEFAULT 'unknown',
  status TEXT DEFAULT 'candidate',
  reliability_score REAL DEFAULT 30,
  risk_score REAL DEFAULT 0,
  early_signal_score REAL DEFAULT 0,
  language_style_tags TEXT DEFAULT '',
  last_seen_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  handle TEXT,
  candidate_score REAL,
  reason TEXT,
  risk_note TEXT,
  status TEXT DEFAULT 'pending',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_reliability_snapshots (
  id TEXT PRIMARY KEY,
  source_ref TEXT NOT NULL,
  score REAL NOT NULL,
  method_version TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  observed_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS style_examples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_post_id INTEGER,
  text TEXT,
  tone_tags TEXT,
  performance_score REAL DEFAULT 50,
  embedding TEXT,
  approved_for_style_memory INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_registry (
  id TEXT PRIMARY KEY,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  artifact_ref TEXT,
  metrics_json TEXT NOT NULL DEFAULT '{}',
  rollback_ref TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE(model_name, model_version)
);

CREATE TABLE IF NOT EXISTS experiment_runs (
  id TEXT PRIMARY KEY,
  backlog_id TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  dataset_hash TEXT NOT NULL,
  split_policy TEXT NOT NULL,
  metrics_json TEXT NOT NULL DEFAULT '{}',
  decision TEXT NOT NULL,
  started_at INTEGER NOT NULL,
  completed_at INTEGER
);

CREATE TABLE IF NOT EXISTS audit_log (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  details_json TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id, created_at);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT,
  entity_type TEXT,
  entity_id TEXT,
  details_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_weights (
  key TEXT PRIMARY KEY,
  value REAL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  platform_post_id TEXT UNIQUE,
  url TEXT,
  author_handle TEXT,
  text TEXT,
  normalized_text TEXT,
  quoted_post_id TEXT,
  captured_at TEXT DEFAULT CURRENT_TIMESTAMP,
  post_time TEXT,
  visible_metrics_json TEXT DEFAULT '{}',
  raw_json TEXT DEFAULT '{}',
  dedup_hash TEXT UNIQUE
);
