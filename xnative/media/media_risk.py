def media_risk(
    copyright_status: str = "unknown", source_url: str = "", alt_text: str = ""
) -> tuple[float, str]:
    status = (copyright_status or "unknown").lower()
    if status in {"owned", "permitted"}:
        return 5.0, "media_permitted"
    if status == "risky":
        return 80.0, "media_marked_risky"
    return 55.0, "copyright_unknown_review_required"
