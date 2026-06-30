CREATE TABLE IF NOT EXISTS local_media_objects (
  exact_sha256 TEXT PRIMARY KEY,
  relative_path TEXT NOT NULL DEFAULT '',
  byte_size INTEGER NOT NULL DEFAULT 0,
  perceptual_hash TEXT,
  storage_policy TEXT NOT NULL DEFAULT 'metadata',
  availability TEXT NOT NULL DEFAULT 'metadata_only',
  source_url TEXT,
  retention_reason TEXT,
  retention_expires_at INTEGER,
  local_deleted_at INTEGER,
  local_deleted_reason TEXT,
  reference_count INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS local_media_references (
  id TEXT PRIMARY KEY,
  exact_sha256 TEXT NOT NULL REFERENCES local_media_objects(exact_sha256) ON DELETE CASCADE,
  reference_id TEXT NOT NULL,
  owner_type TEXT,
  owner_id TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE(exact_sha256, reference_id)
);

CREATE TABLE IF NOT EXISTS remote_media_snapshots (
  id TEXT PRIMARY KEY,
  source_url TEXT NOT NULL,
  reason TEXT NOT NULL,
  visible_text TEXT NOT NULL DEFAULT '',
  alt_text TEXT NOT NULL DEFAULT '',
  observed_at INTEGER NOT NULL,
  availability TEXT NOT NULL DEFAULT 'remote_unavailable',
  created_at INTEGER NOT NULL,
  UNIQUE(source_url, reason, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_local_media_objects_availability
  ON local_media_objects(availability);
CREATE INDEX IF NOT EXISTS idx_local_media_objects_retention_expires_at
  ON local_media_objects(retention_expires_at);
CREATE INDEX IF NOT EXISTS idx_local_media_references_owner
  ON local_media_references(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_remote_media_snapshots_source_url
  ON remote_media_snapshots(source_url);
