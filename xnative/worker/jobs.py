from __future__ import annotations

from xnative.db.repositories import ClaimedJob, UnitOfWork
from xnative.domain import FeatureRecord
from xnative.learning.weekly_report import generate_weekly_report


def weekly_report_job() -> str:
    return generate_weekly_report()


def normalize_capture_job(job: ClaimedJob, uow: UnitOfWork) -> str:
    row = uow.connection.execute(
        "SELECT id, visible_text, author_handle FROM captured_posts WHERE id=?",
        (job.payload_ref,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Captured post not found: {job.payload_ref}")
    feature_id = uow.features.record_feature(
        FeatureRecord(
            owner_type="post",
            owner_id=str(row["id"]),
            feature_name="normalized_capture",
            feature_version="normalize-v1",
            value={
                "text_length": len(str(row["visible_text"] or "")),
                "author_handle": str(row["author_handle"]),
            },
            model_version="rules-v1",
            config_hash="normalize-v1",
            source_ids=[str(row["id"])],
        )
    )
    return feature_id
