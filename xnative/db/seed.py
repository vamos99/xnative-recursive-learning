from __future__ import annotations

from .database import init_db

DEFAULT_WEIGHTS = {
    "tone.reaction": 1.0,
    "tone.dry_humor": 1.0,
    "tone.neutral_short": 1.0,
    "tone.quote_context": 1.0,
}


def seed(path=None):
    conn = init_db(path)
    for k, v in DEFAULT_WEIGHTS.items():
        conn.execute("INSERT OR IGNORE INTO learning_weights(key,value) VALUES (?,?)", (k, v))
    conn.commit()
    return conn
