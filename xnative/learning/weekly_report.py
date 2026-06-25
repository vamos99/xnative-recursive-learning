from __future__ import annotations

from xnative.db.database import connect


def generate_weekly_report(db_path=None) -> str:
    conn = connect(db_path)
    rows = conn.execute("SELECT action, COUNT(*) c FROM feedback GROUP BY action").fetchall()
    actions = ", ".join(f"{r['action']}: {r['c']}" for r in rows) or "no feedback yet"
    weights = conn.execute("SELECT key,value FROM learning_weights ORDER BY key").fetchall()
    wtxt = "; ".join(f"{r['key']}={r['value']:.2f}" for r in weights) or "default weights"
    return (
        f"Weekly learning report\nFeedback: {actions}\nWeights: {wtxt}\n"
        "Next action: keep human approval and avoid news-like phrasing."
    )
