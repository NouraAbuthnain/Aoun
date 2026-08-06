"""Aoun dashboard page."""

from __future__ import annotations

from textwrap import dedent

import streamlit as st

from services.repository import list_claim_records

def render_html(content: str) -> None:
    """Render HTML without Markdown treating nested tags as code."""

    cleaned_html = "\n".join(
        line.strip()
        for line in dedent(content).strip().splitlines()
    )

    st.markdown(
        cleaned_html,
        unsafe_allow_html=True,
    )


def load_dashboard_metrics() -> dict[str, object]:
    """Calculate dashboard metrics from the current claim history."""

    history = list_claim_records()

    total_claims = len(history)

    ready_claims = sum(
        1
        for record in history
        if (
            int(record.get("readiness_score", 0)) >= 70
            and not record.get("validation", {}).get(
                "blocking_errors",
                [],
            )
        )
    )

    accepted_claims = sum(
        1
        for record in history
        if record.get("status") == "accepted"
    )

    rejected_claims = sum(
        1
        for record in history
        if record.get("status") == "rejected"
    )

    average_compliance = None

    if total_claims:
        average_compliance = sum(
            int(record.get("readiness_score", 0))
            for record in history
        ) / total_claims

    return {
        "claims": total_claims,
        "ready": ready_claims,
        "accepted": accepted_claims,
        "rejected": rejected_claims,
        "average_compliance": average_compliance,
    }


def render_hero() -> None:
    """Render the dashboard hero section."""

    render_html(
        """
        <div class="aoun-hero">
            <div class="aoun-hero-badge">
                AI-powered claims validation
            </div>
            <h1>
                Submit stronger claims.<br>
                Get them right the first time.
            </h1>
            <p>
                Aoun reviews clinical documentation, claim codes,
                payer requirements, and missing information before
                submission.
            </p>
        </div>
        """
    )


def render_value_cards() -> None:
    """Render Aoun's key benefits."""

    cards = [
        (
            "✓",
            "Complete documentation",
            "Detect missing clinical information before the claim reaches the payer.",
        ),
        (
            "◎",
            "Accurate claim information",
            "Identify coding inconsistencies and unsupported services early.",
        ),
        (
            "⚡",
            "Faster review",
            "Reduce repetitive manual checks and focus on important issues.",
        ),
    ]

    columns = st.columns(3, gap="medium")

    for column, (icon, title, description) in zip(
        columns,
        cards,
        strict=True,
    ):
        with column:
            render_html(
                f"""
                <div class="aoun-value-card">
                    <div class="aoun-value-icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """
            )


def render_process() -> None:
    """Render the simplified claim workflow."""

    render_html(
        """
        <div class="aoun-section-heading">
            <span>How it works</span>
            <h2>From documentation to submission</h2>
            <p>
                Aoun supports the doctor throughout the claim journey
                without replacing clinical judgment.
            </p>
        </div>
        """
    )

    steps = [
        ("1", "Document", "Select the patient and describe the clinical encounter."),
        ("2", "Analyze", "Aoun reviews clinical notes, codes, and payer requirements."),
        ("3", "Resolve", "Potential errors and missing information are highlighted."),
        ("4", "Submit", "The doctor reviews the validated claim and submits it."),
    ]

    columns = st.columns(4, gap="medium")

    for column, (number, title, description) in zip(
        columns,
        steps,
        strict=True,
    ):
        with column:
            render_html(
                f"""
                <div class="aoun-process-card">
                    <div class="aoun-step-number">{number}</div>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """
            )


def render_metrics() -> None:
    """Render live claim metrics from claim history."""

    metrics_data = load_dashboard_metrics()

    average_compliance = metrics_data["average_compliance"]
    average_value = (
        f"{average_compliance:.0f}%"
        if average_compliance is not None
        else "—"
    )

    render_html(
        """
        <div class="aoun-section-heading metrics-heading">
            <span>Current activity</span>
            <h2>Claims overview</h2>
        </div>
        """
    )

    metrics = [
        ("Claims", str(metrics_data["claims"]), "Total reviewed"),
        ("Ready", str(metrics_data["ready"]), "Compliant claims"),
        ("Accepted", str(metrics_data["accepted"]), "Payer accepted"),
        ("Rejected", str(metrics_data["rejected"]), "Payer rejected"),
        ("Avg. compliance", average_value, "Validation score"),
    ]

    columns = st.columns(5, gap="medium")

    for column, (label, value, caption) in zip(
        columns,
        metrics,
        strict=True,
    ):
        with column:
            render_html(
                f"""
                <div class="aoun-metric-card">
                    <p class="aoun-metric-label">{label}</p>
                    <p class="aoun-metric-value">{value}</p>
                    <p class="aoun-metric-caption">{caption}</p>
                </div>
                """
            )


def render_insights() -> None:
    """Render dashboard insight cards."""

    history = st.session_state.get("claim_history", [])

    if history:
        latest = history[-1]
        latest_score = int(latest.get("readiness_score", 0))
        latest_issue = latest.get("primary_issue", "No blocking issue")
    else:
        latest_score = 0
        latest_issue = "No issues detected yet"

    left, right = st.columns(2, gap="medium")

    with left:
        render_html(
            f"""
            <div class="aoun-insight-card">
                <div class="aoun-insight-icon">↗</div>
                <div>
                    <p class="aoun-insight-label">Latest compliance</p>
                    <h3>{latest_score}% compliance score</h3>
                    <p>
                        The latest reviewed claim compliance result
                        appears here.
                    </p>
                </div>
            </div>
            """
        )

    with right:
        render_html(
            f"""
            <div class="aoun-insight-card">
                <div class="aoun-insight-icon">!</div>
                <div>
                    <p class="aoun-insight-label">Latest validation result</p>
                    <h3>{latest_issue}</h3>
                    <p>
                        Blocking issues and frequent validation findings
                        will appear here.
                    </p>
                </div>
            </div>
            """
        )


def render() -> None:
    """Render the complete Aoun dashboard."""

    render_hero()
    render_html("<div class='aoun-space'></div>")
    render_value_cards()
    render_html("<div class='aoun-section-space'></div>")
    render_process()
    render_html("<div class='aoun-section-space'></div>")
    render_metrics()
    render_html("<div class='aoun-small-space'></div>")
    render_insights()
