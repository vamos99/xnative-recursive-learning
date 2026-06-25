CREATE TABLE IF NOT EXISTS pipeline_cursors (
  name TEXT PRIMARY KEY,
  cursor_value TEXT NOT NULL,
  high_water_mark TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cache_entries (
  id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  cache_key TEXT NOT NULL,
  version TEXT NOT NULL,
  value_json TEXT NOT NULL,
  source_ids_json TEXT NOT NULL DEFAULT '[]',
  expires_at INTEGER,
  invalidated_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE(namespace, cache_key, version)
);

CREATE INDEX IF NOT EXISTS idx_cache_entries_lookup
ON cache_entries(namespace, cache_key, version, invalidated_at, expires_at);

CREATE INDEX IF NOT EXISTS idx_pipeline_cursors_updated
ON pipeline_cursors(updated_at);
