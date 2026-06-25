from __future__ import annotations

from pathlib import Path
from typing import Any

from xnative.core.config import settings
from xnative.db.repositories import UnitOfWork


def load_queue_dashboard(db_path: str | Path | None = None) -> dict[str, list[dict[str, Any]]]:
    with UnitOfWork(db_path) as uow:
        return {
            "queue_summary": uow.jobs.queue_summary(),
            "dead_letters": uow.jobs.list_dead_letters(),
        }


def replay_dead_letter(db_path: str | Path | None, job_id: str) -> dict[str, Any]:
    with UnitOfWork(db_path) as uow:
        result = uow.jobs.replay_dead_letter(job_id)
    return {
        "job_id": result.job_id,
        "source_job_id": result.source_job_id,
        "duplicate": result.duplicate,
    }


def run_app():
    try:
        import streamlit as st
    except Exception:
        print(
            "Streamlit is optional. Install streamlit to use UI, or run sample mode via CLI/tests."
        )
        return
    st.set_page_config(page_title="XNative MVP", layout="wide")
    st.title("XNative Recursive Learning - Local-first MVP")
    st.write("No X API, no mandatory paid LLM. Use fixture/manual import and human approval queue.")
    db_path = settings.database_path
    dashboard = load_queue_dashboard(db_path)

    st.subheader("Worker queue")
    if dashboard["queue_summary"]:
        st.dataframe(dashboard["queue_summary"], use_container_width=True)
    else:
        st.info("No jobs found yet.")

    st.subheader("Dead letters")
    dead_letters = dashboard["dead_letters"]
    if not dead_letters:
        st.success("No dead-letter jobs.")
        return

    st.dataframe(dead_letters, use_container_width=True)
    replay_job_id = st.selectbox(
        "Select a dead job to replay",
        options=[str(item["job_id"]) for item in dead_letters],
    )
    if st.button("Replay selected job"):
        result = replay_dead_letter(db_path, replay_job_id)
        st.success(f"Replay queued: {result['job_id']}")
