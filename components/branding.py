"""Aoun visual identity and global CSS."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"

SIDEBAR_LOGO_PATH = ASSETS_DIR / "Aoun_word_logo.png"
FONT_PATH = ASSETS_DIR / "Agrandir-Regular.woff2"


def _font_css() -> str:
    """Return the Agrandir font declaration when the font file exists."""

    if not FONT_PATH.exists():
        return """
        :root {
            --aoun-font:
                "Agrandir",
                "Segoe UI",
                Arial,
                sans-serif;
        }
        """

    font_uri = FONT_PATH.as_uri()

    return f"""
    @font-face {{
        font-family: "Agrandir";
        src: url("{font_uri}") format("woff2");
        font-weight: 100 900;
        font-style: normal;
        font-display: swap;
    }}

    :root {{
        --aoun-font:
            "Agrandir",
            "Segoe UI",
            Arial,
            sans-serif;
    }}
    """


def apply_branding() -> None:
    """Apply Aoun colors, typography, spacing, and component styling."""

    css = """
    <style>
    __FONT_CSS__

    :root {
        --aoun-blue-50: #E6F1FB;
        --aoun-blue-100: #B5D4F4;
        --aoun-blue-200: #85B7EB;
        --aoun-blue-400: #378ADD;
        --aoun-blue-600: #185FA5;
        --aoun-blue-700: #1D4ED8;
        --aoun-blue-800: #0C447C;
        --aoun-blue-900: #042C53;

        --aoun-card: #F1F5F9;
        --aoun-white: #FFFFFF;
        --aoun-border: #D8E7F5;
        --aoun-muted: #64748B;
    }

    html,
    body,
    [class*="css"],
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"] {
        font-family: var(--aoun-font);
    }

    /* Main page */

    [data-testid="stAppViewContainer"] {
        background: var(--aoun-white);
    }

    .block-container {
        max-width: 1440px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1,
    h2,
    h3,
    h4 {
        color: var(--aoun-blue-900);
        letter-spacing: -0.02em;
    }

    h1 {
        font-weight: 700;
    }

    p,
    label,
    .stCaption {
        color: var(--aoun-blue-900);
    }

    /* Sidebar */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #F8FBFF 0%,
                var(--aoun-blue-50) 100%
            );
        border-right: 1px solid var(--aoun-border);
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1.25rem;
    }

    /* Sidebar page links */

    [data-testid="stPageLink"] a {
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
        transition:
            background-color 150ms ease,
            color 150ms ease,
            transform 150ms ease;
    }

    [data-testid="stPageLink"] a:hover {
        background: var(--aoun-blue-100);
        color: var(--aoun-blue-900);
        transform: translateX(2px);
    }

    /* Buttons */

    .stButton > button {
        min-height: 44px;
        border-radius: 12px;
        border: 1px solid var(--aoun-blue-200);
        font-weight: 600;
        transition:
            background-color 150ms ease,
            border-color 150ms ease,
            transform 150ms ease;
    }

    .stButton > button:hover {
        border-color: var(--aoun-blue-400);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: var(--aoun-blue-700);
        border-color: var(--aoun-blue-700);
        color: white;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--aoun-blue-600);
        border-color: var(--aoun-blue-600);
    }

    /* Form controls */

    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div,
    [data-baseweb="textarea"] {
        background: var(--aoun-card);
        border-color: var(--aoun-border);
        border-radius: 12px;
    }

    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="textarea"]:focus-within {
        border-color: var(--aoun-blue-400);
        box-shadow:
            0 0 0 3px rgba(55, 138, 221, 0.14);
    }

    /* Metrics */

    [data-testid="stMetric"] {
        background: var(--aoun-card);
        border: 1px solid var(--aoun-border);
        border-radius: 16px;
        padding: 1rem;
    }

    [data-testid="stMetricValue"] {
        color: var(--aoun-blue-800);
    }

    /* Alerts */

    [data-testid="stAlert"] {
        border-radius: 14px;
        border-width: 1px;
    }

    /* Progress bar */

    [data-testid="stProgress"] > div > div > div {
        background:
            linear-gradient(
                90deg,
                var(--aoun-blue-700),
                var(--aoun-blue-400)
            );
    }

    /* File uploader */

    [data-testid="stFileUploaderDropzone"] {
        background: var(--aoun-card);
        border: 1.5px dashed var(--aoun-blue-200);
        border-radius: 16px;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        background: var(--aoun-blue-50);
        border-color: var(--aoun-blue-400);
    }

    /* Audio recorder */

    [data-testid="stAudioInput"] {
        background: var(--aoun-card);
        border-radius: 16px;
    }

    /* Expander and containers */

    [data-testid="stExpander"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--aoun-border);
        border-radius: 16px;
    }

    /* Dataframes */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--aoun-border);
        border-radius: 14px;
        overflow: hidden;
    }

    /* Links */

    a {
        color: var(--aoun-blue-600);
    }

    a:hover {
        color: var(--aoun-blue-800);
    }

    /* Keyboard focus */

    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible,
    a:focus-visible {
        outline: 3px solid var(--aoun-blue-200);
        outline-offset: 2px;
    }

    /* Dashboard hero */

    .aoun-hero {
        position: relative;
        overflow: hidden;
        padding: 2.2rem 2.4rem;
        border-radius: 28px;
        background:
            radial-gradient(
                circle at 88% 18%,
                rgba(133, 183, 235, 0.55),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #E6F1FB 0%,
                #F8FBFF 55%,
                #B5D4F4 100%
            );
        border: 1px solid #B5D4F4;
    }

    .aoun-hero::after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -70px;
        bottom: -110px;
        border-radius: 999px;
        border: 45px solid rgba(29, 78, 216, 0.10);
    }

    .aoun-hero-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid #B5D4F4;
        color: #185FA5;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .aoun-hero h1 {
        margin: 1.2rem 0 0.9rem;
        max-width: 820px;
        font-size: clamp(2.2rem, 4vw, 3.4rem);
        line-height: 1.08;
        color: #042C53;
    }

    .aoun-hero p {
        margin: 0;
        color: #47627D;
        max-width: 760px;
        font-size: 1rem;
        line-height: 1.6;
    }

    /* Dashboard value cards */

    .aoun-value-card {
        height: 100%;
        min-height: 205px;
        padding: 1.5rem;
        border-radius: 20px;
        background: #FFFFFF;
        border: 1px solid #D8E7F5;
        box-shadow: 0 10px 28px rgba(12, 68, 124, 0.06);
        transition:
            transform 160ms ease,
            border-color 160ms ease,
            box-shadow 160ms ease;
    }

    .aoun-value-card:hover {
        transform: translateY(-4px);
        border-color: #85B7EB;
        box-shadow: 0 16px 35px rgba(12, 68, 124, 0.10);
    }

    .aoun-value-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        margin-bottom: 1.1rem;
        border-radius: 14px;
        background: #E6F1FB;
        color: #1D4ED8;
    }

    .aoun-value-card h3 {
        margin: 0 0 0.55rem;
        font-size: 1.18rem;
    }

    .aoun-value-card p {
        margin: 0;
        color: #64748B;
        line-height: 1.65;
    }

    /* Section headings */

    .aoun-section-heading {
        margin-bottom: 1.5rem;
    }

    .aoun-section-heading span {
        color: #378ADD;
        font-size: 0.84rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .aoun-section-heading h2 {
        margin: 0.35rem 0 0.35rem;
        font-size: 2rem;
    }

    .aoun-section-heading p {
        max-width: 690px;
        margin: 0;
        color: #64748B;
    }

    .metrics-heading {
        margin-bottom: 1.1rem;
    }

    /* Process cards */

    .aoun-process-card {
        position: relative;
        min-height: 205px;
        padding: 1.4rem;
        border-radius: 20px;
        background: #F8FBFF;
        border: 1px solid #D8E7F5;
    }

    .aoun-step-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        margin-bottom: 1.1rem;
        border-radius: 12px;
        background: #1D4ED8;
        color: white;
        font-weight: 700;
    }

    .aoun-process-card h3 {
        margin: 0 0 0.5rem;
    }

    .aoun-process-card p {
        margin: 0;
        color: #64748B;
        line-height: 1.6;
    }

    /* Metric cards */

    .aoun-metric-card {
        min-height: 155px;
        padding: 1.3rem;
        border-radius: 20px;
        background:
            linear-gradient(
                160deg,
                #F8FBFF,
                #E6F1FB
            );
        border: 1px solid #B5D4F4;
    }

    .aoun-metric-label {
        margin: 0;
        color: #47627D;
        font-size: 0.92rem;
        font-weight: 600;
    }

    .aoun-metric-value {
        margin: 0.45rem 0 0.25rem;
        color: #0C447C;
        font-size: 2.4rem;
        font-weight: 700;
        line-height: 1;
    }

    .aoun-metric-caption {
        margin: 0;
        color: #7A8EA3;
        font-size: 0.8rem;
    }

    /* Insight cards */

    .aoun-insight-card {
        display: flex;
        gap: 1rem;
        min-height: 150px;
        padding: 1.5rem;
        border-radius: 20px;
        background: #FFFFFF;
        border: 1px solid #D8E7F5;
    }
    
    .aoun-insight-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 48px;
        width: 48px;
        height: 48px;
        border-radius: 14px;
        background: #E6F1FB;
        color: #1D4ED8;
        font-size: 1.3rem;
        font-weight: 700;
    }

    .aoun-insight-label {
        margin: 0 0 0.2rem;
        color: #378ADD;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .aoun-insight-card h3 {
        margin: 0 0 0.35rem;
        font-size: 1.1rem;
    }

    .aoun-insight-card p:last-child {
        margin: 0;
        color: #64748B;
        line-height: 1.55;
    }

    /* Layout spacing */

    .aoun-space {
        height: 1.5rem;
    }

    .aoun-section-space {
        height: 3rem;
    }

    .aoun-small-space {
        height: 1rem;
    }

    /* Responsive layout */

    @media (max-width: 900px) {
        .aoun-hero {
            padding: 2rem 1.5rem;
        }

        .aoun-value-card,
        .aoun-process-card,
        .aoun-metric-card {
            margin-bottom: 0.75rem;
        }
    }
    </style>
    """

    css = css.replace("__FONT_CSS__", _font_css())

    st.markdown(
        css,
        unsafe_allow_html=True,
    )

def apply_accessibility(
    language: str = "English",
    high_contrast: bool = False,
    large_fonts: bool = False,
) -> None:
    """Apply language direction and accessibility styles."""

    is_arabic = language.lower() in {
        "arabic",
        "العربية",
        "ar",
    }

    direction = "rtl" if is_arabic else "ltr"
    text_align = "right" if is_arabic else "left"
    font_size = "19px" if large_fonts else "16px"

    contrast_css = ""

    if high_contrast:
        contrast_css = """
        [data-testid="stAppViewContainer"] {
            background: #000000;
            color: #FFFFFF;
        }

        [data-testid="stSidebar"] {
            background: #000000;
            color: #FFFFFF;
        }

        .stButton > button {
            border: 2px solid #FFFFFF;
        }
        """

    st.markdown(
        f"""
        <style>
        html,
        body,
        [data-testid="stAppViewContainer"] {{
            direction: {direction};
            text-align: {text_align};
        }}

        html,
        body,
        [class*="css"],
        button,
        input,
        textarea,
        select {{
            font-size: {font_size};
        }}

        button,
        input,
        textarea,
        select {{
            min-height: 44px;
        }}

        button:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        select:focus-visible,
        a:focus-visible {{
            outline: 3px solid #85B7EB !important;
            outline-offset: 2px;
        }}

        {contrast_css}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_sidebar_brand() -> None:
    """Render the Aoun word logo in the sidebar."""

    if SIDEBAR_LOGO_PATH.exists():
        st.image(
            str(SIDEBAR_LOGO_PATH),
            width=220,
        )
    else:
        st.error("Aoun sidebar logo was not found.")

    st.markdown(
        """
        <div style="
            color: #64748B;
            font-size: 1rem;
            line-height: 1.5;
            margin-top: 0.35rem;
            margin-bottom: 0.75rem;
        ">
            AI-powered claim validation for accurate,
            submission-ready healthcare claims.
        </div>
        """,
        unsafe_allow_html=True,
    )