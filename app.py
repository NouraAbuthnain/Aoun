"""Main Streamlit entry point for the Aoun application."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from components.branding import (
    apply_accessibility,
    apply_branding,
    render_sidebar_brand,
)
from config.settings import APP_TITLE
from database.session import init_db
from views import claims, dashboard, history


logger = logging.getLogger(__name__)


ASSETS_DIR = Path(__file__).resolve().parent / "assets"

PAGE_ICON_PATH = ASSETS_DIR / "Aoun_logo.png"
SIDEBAR_LOGO_PATH = ASSETS_DIR / "Aoun_word_logo.png"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=(
        str(PAGE_ICON_PATH)
        if PAGE_ICON_PATH.exists()
        else "🛡️"
    ),
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def initialize_database() -> bool:
    """Initialize the application database once per server process."""

    init_db()
    return True


def initialize_session_state() -> None:
    """Create default values for global application preferences."""

    defaults = {
        "language": "English",
        "large_fonts": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def dashboard_page() -> None:
    """Render the dashboard route."""

    dashboard.render()


def claims_page() -> None:
    """Render the unified claims route."""

    claims.render()


def history_page() -> None:
    """Render the history route."""

    history.render()


def render_custom_sidebar(
    dashboard_route: st.Page,
    claims_route: st.Page,
    history_route: st.Page,
) -> None:
    """Render Aoun branding, navigation, and preferences."""

    with st.sidebar:
        render_sidebar_brand()

        st.divider()

        st.page_link(
            dashboard_route,
            label="Dashboard",
            icon=":material/dashboard:",
            use_container_width=True,
        )

        st.page_link(
            claims_route,
            label="Claims",
            icon=":material/add_notes:",
            use_container_width=True,
        )

        st.page_link(
            history_route,
            label="History",
            icon=":material/history:",
            use_container_width=True,
        )

        st.divider()

        st.markdown("#### Preferences")

        language_is_arabic = st.toggle(
            "Arabic language",
            value=st.session_state.language == "العربية",
            key="language_toggle",
            help="Switch the interface between English and Arabic.",
        )

        st.session_state.language = (
            "العربية"
            if language_is_arabic
            else "English"
        )

        st.toggle(
            "Large text",
            key="large_fonts",
        )

        st.divider()

        st.caption(
            "Aoun improves claim quality before submission. "
            "It does not replace NPHIES or payer adjudication."
        )


def main() -> None:
    """Run the Aoun application."""

    initialize_session_state()

    try:
        initialize_database()
    except Exception:
        logger.exception("Database initialization failed.")

        st.error(
            "Aoun could not initialize its database. "
            "Check the terminal logs for more information."
        )

        st.stop()

    apply_branding()

    dashboard_route = st.Page(
        dashboard_page,
        title="Dashboard",
        icon=":material/dashboard:",
        default=True,
    )

    claims_route = st.Page(
        claims_page,
        title="Claims",
        icon=":material/add_notes:",
    )

    history_route = st.Page(
        history_page,
        title="History",
        icon=":material/history:",
    )

    selected_page = st.navigation(
        [
            dashboard_route,
            claims_route,
            history_route,
        ],
        position="hidden",
    )

    render_custom_sidebar(
        dashboard_route=dashboard_route,
        claims_route=claims_route,
        history_route=history_route,
    )

    apply_accessibility(
        language=st.session_state.language,
        high_contrast=False,
        large_fonts=st.session_state.large_fonts,
    )

    selected_page.run()


if __name__ == "__main__":
    main()