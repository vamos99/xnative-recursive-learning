from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from xnative.db.database import connect

from .online_weights import update_weight

REWARD = {"approved": 1.0, "posted_manually": 1.2, "edited": 0.4, "ignored": -0.2, "rejected": -1.0}


def record_feedback(
    suggestion_id: int,
    action: str,
    edited_text: str = "",
    reason: str = "",
    metrics: dict[str, Any] | None = None,
    db_path: str | Path | None = None,
) -> None:
    conn = connect(db_path)
    conn.execute(
        "INSERT INTO feedback(suggestion_id, action, edited_text, reason, metrics_json) "
        "VALUES (?,?,?,?,?)",
        (suggestion_id, action, edited_text, reason, json.dumps(metrics or {}, ensure_ascii=False)),
    )
    reward = REWARD.get(action, 0.0)
    row = conn.execute(
        "SELECT variant_label FROM suggestions WHERE id=?", (suggestion_id,)
    ).fetchone()
    if row:
        key = f"tone.{row['variant_label']}"
        old = conn.execute("SELECT value FROM learning_weights WHERE key=?", (key,)).fetchone()
        old_val = float(old["value"]) if old else 1.0
        new_val = update_weight(old_val, reward)
        conn.execute(
            "INSERT OR REPLACE INTO learning_weights(key,value,updated_at) "
            "VALUES (?,?,CURRENT_TIMESTAMP)",
            (key, new_val),
        )
    if edited_text:
        conn.execute(
            "INSERT INTO style_examples("
            "text,tone_tags,performance_score,approved_for_style_memory"
            ") VALUES (?,?,?,?)",
            (edited_text, action, 65, 1),
        )
    conn.commit()
