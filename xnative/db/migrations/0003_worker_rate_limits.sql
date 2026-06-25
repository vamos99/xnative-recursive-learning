CREATE TABLE IF NOT EXISTS rate_limit_buckets (
  name TEXT PRIMARY KEY,
  capacity REAL NOT NULL,
  refill_per_second REAL NOT NULL,
  tokens REAL NOT NULL,
  updated_at INTEGER NOT NULL
);
