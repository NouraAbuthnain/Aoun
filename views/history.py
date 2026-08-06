"""Aoun claim history page."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from services.repository import list_claim_records

def format_datetime(value: str | None) -> str:
    """Format an ISO datetime for display."""

    if not value:
        return "—"

    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return value


def format_status(status: str | None) -> str:
    """Convert an internal status into a display label."""

    labels = {
        "needs_correction": "Needs correction",
        "ready": "Ready",
        "submitted": "Submitted",
        "accepted": "Accepted",
        "rejected": "Rejected",
        "information_requested": "Information requested",
        "pending": "Pending",
        "failed": "Failed",
    }

    return labels.get(
        status or "",
        (status or "Unknown").replace("_", " ").title(),
    )


def create_history_rows(
    history: list[dict[str, Any]],
) -> list[dict[str, object]]:
    """Create one compact table row per claim."""

    rows: list[dict[str, object]] = []

    for record in reversed(history):
        claim = record.get("claim", {})

        patient_name = record.get(
            "patient_name",
            record.get(
                "patient_id",
                claim.get("patient_id", "—"),
            ),
        )

        patient_id = record.get(
            "patient_id",
            claim.get("patient_id", "—"),
        )

        rows.append(
            {
                "Claim ID": record.get("claim_id", "—"),
                "Patient": f"{patient_name} · {patient_id}",
                "Status": format_status(record.get("status")),
                "Compliance": (
                    f"{int(record.get('readiness_score', 0))}%"
                ),
                "Estimated acceptance": (
                    f"{int(record.get('acceptance_probability', 0))}%"
                ),
                "Validation result": record.get(
                    "primary_issue",
                    "No blocking issue",
                ),
                "Last updated": format_datetime(
                    record.get("submitted_at")
                    or record.get("updated_at")
                ),
            }
        )

    return rows


def render() -> None:
    """Render a simple, single-table claim history."""

    st.title("History")

    st.caption(
        "View validated claims, compliance results, submissions, "
        "and payer responses."
    )

    history = list_claim_records()

    if not history:
        st.info("No claims have been reviewed or submitted yet.")
        return

    dataframe = pd.DataFrame(
        create_history_rows(history)
    )

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True,
        column_config={
            "Claim ID": st.column_config.TextColumn(
                "Claim ID",
                width="large",
            ),
            "Patient": st.column_config.TextColumn(
                "Patient",
                width="large",
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                width="medium",
            ),
            "Compliance": st.column_config.TextColumn(
                "Compliance",
                width="small",
            ),
            "Estimated acceptance": st.column_config.TextColumn(
                "Acceptance",
                width="small",
            ),
            "Validation result": st.column_config.TextColumn(
                "Validation result",
                width="large",
            ),
            "Last updated": st.column_config.TextColumn(
                "Last updated",
                width="medium",
            ),
        },
    )
