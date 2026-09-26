import io
import os
import textwrap

import fitz
import pytesseract
import streamlit as st
from PIL import Image

from services.hackathon_api import ask_gemini
from validators.lot_log import validate_lot_log
from validators.qs_f_049 import validate_qs_f_049
from validators.mp_f_023 import validate_mp_f_023
from validators.discard_form import validate_discard_form


# ============================================================
# CONFIG
# ============================================================

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

if "HACKATHON_API_KEY" in st.secrets:
    os.environ["HACKATHON_API_KEY"] = st.secrets["HACKATHON_API_KEY"]


st.set_page_config(
    page_title="RegenMed Internal Document Reviewer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "analysis_result": None,
    "images": None,
    "file_name": None,
    "page_count": 0,
    "file_size_kb": 0.0,
    "last_processed_file": None,

    "all_page_text": [],
    "detected_form_type": None,
    "detection_remaining": None,

    # idle
    # detecting
    # detected
    # analyzing
    # complete
    "review_stage": "idle"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# THEME SWITCHER
# ============================================================

toolbar_left, toolbar_right = st.columns(
    [6, 2],
    vertical_alignment="center"
)

with toolbar_left:
    st.markdown("")

with toolbar_right:
    st.caption("✨ Appearance")

    theme_choice = st.radio(
        "Theme",
        ["🌙 Dark", "☀️ Light"],
        horizontal=True,
        label_visibility="collapsed",
        key="theme_selector"
    )

light_mode = theme_choice == "☀️ Light"


# ============================================================
# THEME COLORS
# ============================================================

if light_mode:

    BG = "#F3F7FC"
    BG_SECONDARY = "#EAF1F8"

    CARD = "#FFFFFF"
    CARD_2 = "#F8FAFC"
    CARD_HOVER = "#F1F5F9"

    TEXT = "#0F172A"
    TEXT_SECONDARY = "#334155"
    MUTED = "#64748B"

    BORDER = "rgba(15,23,42,0.13)"

    PRIMARY = "#2563EB"
    PRIMARY_LIGHT = "#3B82F6"
    ACCENT = "#0284C7"

    HERO_START = "#FFFFFF"
    HERO_MID = "#EFF6FF"
    HERO_END = "#E0ECFF"

    HERO_TEXT = "#0F172A"
    HERO_SUB = "#334155"

    ISSUE_BG = "#FFF7F7"
    SUCCESS_BG = "#F0FDF4"

    INPUT_BG = "#FFFFFF"

    TOOLBAR_BG = "rgba(255,255,255,0.94)"

    OVERLAY_BG = "rgba(241,245,249,0.97)"

else:

    BG = "#101827"
    BG_SECONDARY = "#162033"

    CARD = "#182235"
    CARD_2 = "#131D2E"
    CARD_HOVER = "#202C42"

    TEXT = "#F8FAFC"
    TEXT_SECONDARY = "#D8E2F0"
    MUTED = "#A8B5C7"

    BORDER = "rgba(148,163,184,0.20)"

    PRIMARY = "#60A5FA"
    PRIMARY_LIGHT = "#7DD3FC"
    ACCENT = "#38BDF8"

    HERO_START = "#172554"
    HERO_MID = "#1E3A5F"
    HERO_END = "#1E293B"

    HERO_TEXT = "#F8FAFC"
    HERO_SUB = "#D6E1F0"

    ISSUE_BG = "#251B25"
    SUCCESS_BG = "#142A23"

    INPUT_BG = "#182235"

    TOOLBAR_BG = "rgba(24,34,53,0.95)"

    OVERLAY_BG = "rgba(10,18,32,0.97)"


# ============================================================
# HTML HELPER
# ============================================================

def html(content):

    cleaned = textwrap.dedent(content).strip()

    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(
            cleaned.replace("\n", ""),
            unsafe_allow_html=True
        )


# ============================================================
# CSS
# ============================================================

html(f"""
<style>

.stApp {{
    background:
        linear-gradient(
            145deg,
            {BG} 0%,
            {BG_SECONDARY} 100%
        ) !important;

    color: {TEXT} !important;
}}

.block-container {{
    padding-top: 0.7rem;
    padding-bottom: 3rem;
    max-width: 1850px;
}}


/* ============================================================
   GLOBAL TEXT
============================================================ */

.stApp,
.stApp p,
.stApp span,
.stApp label {{
    color: {TEXT_SECONDARY};
}}

h1,
h2,
h3,
h4,
h5,
h6 {{
    color: {TEXT} !important;
}}

[data-testid="stMarkdownContainer"] p {{
    color: {TEXT_SECONDARY} !important;
}}

[data-testid="stCaptionContainer"] p {{
    color: {MUTED} !important;
}}

[data-testid="stWidgetLabel"] p {{
    color: {TEXT} !important;
    font-weight: 650 !important;
}}


/* ============================================================
   THEME SELECTOR
============================================================ */

div[data-testid="stRadio"] {{
    background: {TOOLBAR_BG} !important;
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 0.35rem 0.5rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    backdrop-filter: blur(14px);
}}

div[role="radiogroup"] {{
    gap: 0.45rem;
}}

div[role="radiogroup"] label {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 999px;
    padding: 0.38rem 0.8rem;
    min-width: 95px;
    justify-content: center;
    transition: all 0.2s ease;
}}

div[role="radiogroup"] label:hover {{
    transform: translateY(-1px);
    border-color: {PRIMARY};
    background: {CARD_HOVER};
}}

div[role="radiogroup"] label span {{
    color: {TEXT} !important;
    font-weight: 750;
}}

div[role="radiogroup"] label:has(input:checked) {{
    background:
        linear-gradient(
            135deg,
            {PRIMARY},
            {ACCENT}
        ) !important;

    border-color: transparent !important;
}}

div[role="radiogroup"] label:has(input:checked) span {{
    color: white !important;
}}


/* ============================================================
   HERO
============================================================ */

.hero-box {{
    padding: 1.8rem 2rem;

    border-radius: 22px;

    background:
        linear-gradient(
            135deg,
            {HERO_START} 0%,
            {HERO_MID} 55%,
            {HERO_END} 100%
        );

    border: 1px solid {BORDER};

    box-shadow:
        0 18px 45px rgba(15,23,42,0.12);

    margin-bottom: 1.7rem;

    position: relative;

    overflow: hidden;
}}

.hero-box::before {{
    content: "";

    position: absolute;

    width: 420px;
    height: 420px;

    border-radius: 50%;

    right: -180px;
    top: -220px;

    background:
        radial-gradient(
            circle,
            rgba(56,189,248,0.22),
            transparent 65%
        );
}}

.app-brand {{
    color: {PRIMARY} !important;

    font-size: 0.72rem;

    font-weight: 900;

    letter-spacing: 0.15rem;

    margin-bottom: 0.55rem;
}}

.hero-title {{
    color: {HERO_TEXT} !important;

    font-size: 2.25rem;

    font-weight: 850;

    line-height: 1.15;

    margin-bottom: 0.65rem;
}}

.hero-subtitle {{
    color: {HERO_SUB} !important;

    font-size: 0.98rem;

    line-height: 1.65;

    max-width: 920px;
}}

.ai-ready {{
    display: inline-flex;

    align-items: center;

    gap: 8px;

    margin-top: 1rem;

    padding: 0.4rem 0.75rem;

    border-radius: 999px;

    background: rgba(37,99,235,0.10);

    border:
        1px solid rgba(37,99,235,0.30);

    color: {PRIMARY} !important;

    font-size: 0.76rem;

    font-weight: 850;
}}

.ai-dot {{
    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: {ACCENT};

    animation: pulse 1.6s infinite;
}}

@keyframes pulse {{

    0% {{
        box-shadow:
            0 0 0 0
            rgba(56,189,248,0.60);
    }}

    70% {{
        box-shadow:
            0 0 0 8px
            rgba(56,189,248,0);
    }}

    100% {{
        box-shadow:
            0 0 0 0
            rgba(56,189,248,0);
    }}
}}


/* ============================================================
   SECTION TITLES
============================================================ */

.section-title {{
    font-size: 1.08rem;

    font-weight: 800;

    color: {TEXT} !important;

    margin-top: 0.6rem;

    margin-bottom: 0.9rem;
}}


/* ============================================================
   CARDS
============================================================ */

.metric-card {{
    background: {CARD};

    border: 1px solid {BORDER};

    padding: 1rem 1.05rem;

    border-radius: 15px;

    margin-bottom: 0.75rem;

    box-shadow:
        0 4px 18px rgba(15,23,42,0.05);
}}

.metric-label {{
    color: {MUTED} !important;

    font-size: 0.68rem;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 0.065rem;

    margin-bottom: 0.35rem;
}}

.metric-value {{
    color: {TEXT} !important;

    font-size: 0.98rem;

    font-weight: 750;

    word-break: break-word;
}}


.kpi-card {{
    background: {CARD};

    border: 1px solid {BORDER};

    border-radius: 15px;

    padding: 1rem;

    min-height: 102px;

    box-shadow:
        0 4px 18px rgba(15,23,42,0.05);
}}

.kpi-title {{
    color: {MUTED} !important;

    font-size: 0.67rem;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 0.06rem;
}}

.kpi-number {{
    color: {TEXT} !important;

    font-size: 1.25rem;

    font-weight: 850;

    margin-top: 0.5rem;
}}


/* ============================================================
   BUTTONS
============================================================ */

.stButton > button {{
    border-radius: 10px !important;

    border:
        1px solid {BORDER} !important;

    font-weight: 750 !important;

    transition:
        all 0.2s ease;
}}

.stButton > button:not([kind="primary"]) {{
    background: {CARD} !important;

    color: {TEXT} !important;
}}

.stButton > button[kind="primary"] {{
    background:
        linear-gradient(
            135deg,
            {PRIMARY},
            {ACCENT}
        ) !important;

    color: white !important;

    border: none !important;

    box-shadow:
        0 8px 20px rgba(37,99,235,0.22);
}}


/* ============================================================
   STATUS
============================================================ */

.pass-chip {{
    display: inline-block;

    background:
        rgba(34,197,94,0.12);

    border:
        1px solid rgba(34,197,94,0.42);

    color:
        #16A34A !important;

    padding:
        0.35rem 0.7rem;

    border-radius: 999px;

    font-size: 0.77rem;

    font-weight: 850;
}}

.review-chip {{
    display: inline-block;

    background:
        rgba(239,68,68,0.12);

    border:
        1px solid rgba(239,68,68,0.42);

    color:
        #EF4444 !important;

    padding:
        0.35rem 0.7rem;

    border-radius: 999px;

    font-size: 0.77rem;

    font-weight: 850;
}}

.status-pass {{
    background: {SUCCESS_BG};

    border:
        1px solid rgba(34,197,94,0.30);

    color:
        #16A34A !important;

    padding: 0.95rem 1rem;

    border-radius: 13px;

    font-weight: 750;

    margin-top: 0.8rem;

    margin-bottom: 1rem;
}}

.status-fail {{
    background: {ISSUE_BG};

    border:
        1px solid rgba(239,68,68,0.30);

    color:
        #EF4444 !important;

    padding: 0.95rem 1rem;

    border-radius: 13px;

    font-weight: 750;

    margin-top: 0.8rem;

    margin-bottom: 1rem;
}}


/* ============================================================
   ISSUES
============================================================ */

.issue-card {{
    background: {ISSUE_BG};

    border:
        1px solid rgba(239,68,68,0.22);

    border-left:
        4px solid #EF4444;

    padding: 0.9rem 1rem;

    border-radius: 12px;

    margin-bottom: 0.65rem;

    color: {TEXT} !important;

    line-height: 1.5;
}}

.issue-number {{
    display: inline-flex;

    width: 24px;
    height: 24px;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background:
        rgba(239,68,68,0.14);

    color:
        #EF4444 !important;

    font-size: 0.74rem;

    font-weight: 850;

    margin-right: 0.45rem;
}}


/* ============================================================
   PREVIEW
============================================================ */

.preview-header {{
    padding: 0.95rem 1.05rem;

    background: {CARD};

    border: 1px solid {BORDER};

    border-radius: 14px;

    margin-bottom: 0.9rem;

    box-shadow:
        0 4px 16px rgba(15,23,42,0.05);
}}

.preview-file {{
    color: {TEXT} !important;

    font-weight: 800;

    font-size: 0.92rem;
}}

.preview-meta {{
    color: {MUTED} !important;

    font-size: 0.77rem;

    margin-top: 0.25rem;
}}

.empty-preview {{
    border: 1px dashed {BORDER};

    border-radius: 17px;

    padding: 6rem 1rem;

    text-align: center;

    color: {TEXT_SECONDARY} !important;

    background: {CARD_2};
}}

.empty-preview strong {{
    color: {TEXT} !important;
}}

.empty-preview-icon {{
    font-size: 2.2rem;

    margin-bottom: 0.7rem;
}}


/* ============================================================
   PREMIUM DOCUMENT UPLOAD
============================================================ */

.upload-shell {{

    background:
        linear-gradient(
            135deg,
            rgba(59,130,246,0.08),
            rgba(56,189,248,0.04)
        );

    border:
        1px solid rgba(59,130,246,0.18);

    border-radius:
        18px;

    padding:
        1.15rem 1.2rem 0.85rem 1.2rem;

    margin-bottom:
        0.55rem;
}}


.upload-header-row {{

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        1rem;
}}


.upload-eyebrow {{

    color:
        {PRIMARY} !important;

    font-size:
        0.66rem;

    font-weight:
        850;

    letter-spacing:
        0.12rem;

    margin-bottom:
        0.28rem;
}}


.upload-title {{

    color:
        {TEXT} !important;

    font-size:
        1rem;

    font-weight:
        850;

    margin-bottom:
        0.22rem;
}}


.upload-subtitle {{

    color:
        {MUTED} !important;

    font-size:
        0.79rem;

    line-height:
        1.45;
}}


.upload-badge {{

    color:
        {PRIMARY} !important;

    background:
        rgba(59,130,246,0.10);

    border:
        1px solid rgba(59,130,246,0.25);

    border-radius:
        999px;

    padding:
        0.33rem 0.62rem;

    font-size:
        0.64rem;

    font-weight:
        850;

    white-space:
        nowrap;
}}


/* Main Streamlit uploader */

[data-testid="stFileUploader"] {{

    background:
        {CARD};

    border:
        1px solid {BORDER};

    border-radius:
        16px;

    padding:
        0.35rem;

    box-shadow:
        0 8px 24px rgba(15,23,42,0.06);

    transition:
        all 0.2s ease;
}}


[data-testid="stFileUploader"]:hover {{

    border-color:
        {PRIMARY};

    box-shadow:
        0 12px 30px rgba(37,99,235,0.12);

    transform:
        translateY(-1px);
}}


/* Drop zone */

[data-testid="stFileUploaderDropzone"] {{

    min-height:
        145px !important;

    background:
        linear-gradient(
            145deg,
            {CARD_2},
            {CARD}
        ) !important;

    border:
        1.5px dashed rgba(59,130,246,0.35) !important;

    border-radius:
        13px !important;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    transition:
        all 0.2s ease;
}}


[data-testid="stFileUploaderDropzone"]:hover {{

    background:
        rgba(59,130,246,0.06) !important;

    border-color:
        {PRIMARY} !important;
}}


/* Drop zone instructions */

[data-testid="stFileUploaderDropzoneInstructions"] {{

    text-align:
        center;
}}


[data-testid="stFileUploaderDropzoneInstructions"] span {{

    color:
        {TEXT} !important;

    font-weight:
        750 !important;
}}


[data-testid="stFileUploaderDropzoneInstructions"] small {{

    color:
        {MUTED} !important;
}}


/* Browse button */

[data-testid="stFileUploaderDropzone"] button {{

    background:
        linear-gradient(
            135deg,
            {PRIMARY},
            {ACCENT}
        ) !important;

    color:
        white !important;

    border:
        none !important;

    border-radius:
        9px !important;

    font-weight:
        750 !important;

    padding:
        0.5rem 0.9rem !important;

    box-shadow:
        0 5px 14px rgba(37,99,235,0.20);
}}


[data-testid="stFileUploaderDropzone"] button:hover {{

    transform:
        translateY(-1px);

    box-shadow:
        0 7px 18px rgba(37,99,235,0.28);
}}


/* Uploaded file */

[data-testid="stFileUploaderFile"] {{

    background:
        {CARD_2} !important;

    border:
        1px solid {BORDER} !important;

    border-radius:
        10px !important;

    margin-top:
        0.4rem !important;
}}


/* Bottom helper */

.upload-helper {{

    display:
        flex;

    align-items:
        center;

    gap:
        0.45rem;

    margin-top:
        0.4rem;

    margin-bottom:
        0.9rem;

    color:
        {MUTED} !important;

    font-size:
        0.70rem;

    padding-left:
        0.15rem;
}}


.upload-helper span {{

    color:
        {MUTED} !important;
}}


/* ============================================================
   TABS
============================================================ */

[data-testid="stTabs"] button {{
    color: {MUTED} !important;

    font-weight: 700 !important;
}}

[data-testid="stTabs"] button[aria-selected="true"] {{
    color: {PRIMARY} !important;
}}


/* ============================================================
   EXPANDER
============================================================ */

[data-testid="stExpander"] {{
    background: {CARD} !important;

    border:
        1px solid {BORDER} !important;

    border-radius: 12px !important;
}}


/* ============================================================
   FULL SCREEN REVIEW EXPERIENCE
============================================================ */

.review-overlay {{
    position: fixed;

    inset: 0;

    width: 100vw;
    height: 100vh;

    z-index: 999999;

    background: {OVERLAY_BG};

    backdrop-filter:
        blur(15px);

    display: flex;

    align-items: center;

    justify-content: center;

    animation:
        overlayFade 0.25s ease;
}}


@keyframes overlayFade {{

    from {{
        opacity: 0;
    }}

    to {{
        opacity: 1;
    }}
}}


.review-loader-card {{
    width: min(620px, 88vw);

    background: {CARD};

    border:
        1px solid {BORDER};

    border-radius: 28px;

    padding:
        3rem 3.2rem;

    box-shadow:
        0 30px 90px rgba(0,0,0,0.25);

    text-align: center;

    animation:
        loaderCardIn 0.35s ease;
}}


@keyframes loaderCardIn {{

    from {{
        opacity: 0;

        transform:
            translateY(18px)
            scale(0.97);
    }}

    to {{
        opacity: 1;

        transform:
            translateY(0)
            scale(1);
    }}
}}


.review-orbit {{
    width: 92px;
    height: 92px;

    margin:
        0 auto 1.6rem auto;

    position: relative;
}}


.review-orbit::before {{

    content: "";

    position: absolute;

    inset: 0;

    border-radius: 50%;

    border:
        4px solid rgba(59,130,246,0.14);

    border-top-color:
        {ACCENT};

    border-right-color:
        {PRIMARY};

    animation:
        spinReview 1.05s linear infinite;
}}


.review-orbit::after {{

    content: "✦";

    position: absolute;

    inset: 14px;

    border-radius: 50%;

    background:
        linear-gradient(
            135deg,
            {PRIMARY},
            {ACCENT}
        );

    display: flex;

    align-items: center;

    justify-content: center;

    color: white;

    font-size: 1.8rem;

    box-shadow:
        0 0 30px rgba(56,189,248,0.25);
}}


@keyframes spinReview {{

    from {{
        transform:
            rotate(0deg);
    }}

    to {{
        transform:
            rotate(360deg);
    }}
}}


.loader-title {{
    color: {TEXT} !important;

    font-size: 1.55rem;

    font-weight: 850;

    margin-bottom: 0.45rem;
}}


.loader-subtitle {{
    color: {MUTED} !important;

    font-size: 0.90rem;

    margin-bottom: 2rem;

    line-height: 1.55;
}}


.review-step {{
    display: flex;

    align-items: center;

    gap: 0.8rem;

    text-align: left;

    padding:
        0.72rem 0;

    color: {MUTED} !important;

    font-size: 0.88rem;

    font-weight: 650;
}}


.review-step-active {{
    color: {TEXT} !important;

    font-weight: 800;
}}


.step-icon {{
    width: 28px;
    height: 28px;

    border-radius: 50%;

    display: inline-flex;

    align-items: center;

    justify-content: center;

    background:
        {CARD_2};

    border:
        1px solid {BORDER};

    flex-shrink: 0;
}}


.step-icon-active {{
    background:
        rgba(37,99,235,0.14);

    color:
        {PRIMARY} !important;

    border-color:
        {PRIMARY};

    animation:
        activePulse 1.3s infinite;
}}


.step-icon-done {{
    background:
        rgba(34,197,94,0.12);

    color:
        #22C55E !important;

    border-color:
        rgba(34,197,94,0.38);
}}


@keyframes activePulse {{

    0% {{
        box-shadow:
            0 0 0 0
            rgba(59,130,246,0.30);
    }}

    70% {{
        box-shadow:
            0 0 0 8px
            rgba(59,130,246,0);
    }}

    100% {{
        box-shadow:
            0 0 0 0
            rgba(59,130,246,0);
    }}
}}


/* ============================================================
   DETECTION CARD
============================================================ */

.detected-wrapper {{
    max-width: 640px;

    margin:
        2rem auto;

    text-align: center;
}}


.detected-card {{
    background: {CARD};

    border:
        1px solid {BORDER};

    border-radius: 28px;

    padding:
        2.8rem 2.5rem;

    box-shadow:
        0 25px 70px rgba(0,0,0,0.15);

    position: relative;

    overflow: hidden;
}}


.detected-card::before {{
    content: "";

    position: absolute;

    width: 300px;
    height: 300px;

    border-radius: 50%;

    top: -220px;
    left: 50%;

    transform:
        translateX(-50%);

    background:
        radial-gradient(
            circle,
            rgba(56,189,248,0.25),
            transparent 70%
        );
}}


.detected-check {{
    width: 72px;
    height: 72px;

    margin:
        0 auto 1.1rem auto;

    border-radius: 50%;

    background:
        rgba(34,197,94,0.12);

    border:
        1px solid rgba(34,197,94,0.35);

    color:
        #22C55E !important;

    font-size:
        2rem;

    font-weight:
        900;

    display: flex;

    align-items: center;

    justify-content: center;

    animation:
        checkPop .35s ease;
}}


@keyframes checkPop {{

    from {{
        transform:
            scale(0.55);

        opacity: 0;
    }}

    to {{
        transform:
            scale(1);

        opacity: 1;
    }}
}}


.detected-label {{
    color:
        {MUTED} !important;

    font-size:
        0.72rem;

    letter-spacing:
        0.13rem;

    font-weight:
        850;

    text-transform:
        uppercase;
}}


.detected-type {{
    color:
        {TEXT} !important;

    font-size:
        2rem;

    font-weight:
        900;

    margin-top:
        0.6rem;
}}


.detected-name {{
    color:
        {TEXT_SECONDARY} !important;

    font-size:
        1rem;

    margin-top:
        0.45rem;
}}


.detected-info {{
    color:
        {MUTED} !important;

    font-size:
        0.84rem;

    margin-top:
        1.25rem;

    line-height:
        1.55;
}}


/* ============================================================
   STREAMLIT
============================================================ */

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

</style>
""")


# ============================================================
# SCHEMAS
# ============================================================

LOT_LOG_SCHEMA = {
    "type": "object",
    "properties": {

        "form_type": {
            "type": "string"
        },

        "page_1_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string"
                    },
                    "lot_number": {
                        "type": "string"
                    },
                    "exp_date": {
                        "type": "string"
                    },
                    "manufacturer": {
                        "type": "string"
                    }
                },
                "required": [
                    "item",
                    "lot_number",
                    "exp_date",
                    "manufacturer"
                ]
            }
        },

        "regenmed_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string"
                    },
                    "lot": {
                        "type": "string"
                    },
                    "qty_used": {
                        "type": "string"
                    }
                },
                "required": [
                    "item",
                    "lot",
                    "qty_used"
                ]
            }
        },

        "page_2_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string"
                    },
                    "load_number": {
                        "type": "string"
                    },
                    "sterilization_date": {
                        "type": "string"
                    }
                },
                "required": [
                    "item",
                    "load_number",
                    "sterilization_date"
                ]
            }
        },

        "packaging": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string"
                    },
                    "lot": {
                        "type": "string"
                    },
                    "qty_used": {
                        "type": "string"
                    }
                },
                "required": [
                    "item",
                    "lot",
                    "qty_used"
                ]
            }
        }
    },

    "required": [
        "form_type",
        "page_1_items",
        "regenmed_items",
        "page_2_items",
        "packaging"
    ]
}


QS_SCHEMA = {
    "type": "object",

    "properties": {

        "form_type": {
            "type": "string"
        },

        "review_rows": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "item": {
                        "type": "string"
                    },

                    "technical_initials": {
                        "type": "string"
                    },

                    "technical_date": {
                        "type": "string"
                    },

                    "technical_na": {
                        "type": "boolean"
                    },

                    "quality_initials": {
                        "type": "string"
                    },

                    "quality_date": {
                        "type": "string"
                    },

                    "quality_na": {
                        "type": "boolean"
                    }
                },

                "required": [
                    "item",
                    "technical_initials",
                    "technical_date",
                    "technical_na",
                    "quality_initials",
                    "quality_date",
                    "quality_na"
                ]
            }
        },

        "item_10": {
            "type": "object",

            "properties": {

                "inc_number": {
                    "type": "string"
                },

                "status": {
                    "type": "string"
                }
            },

            "required": [
                "inc_number",
                "status"
            ]
        }
    },

    "required": [
        "form_type",
        "review_rows",
        "item_10"
    ]
}


MP_SCHEMA = {
    "type": "object",

    "properties": {

        "form_type": {
            "type": "string"
        },

        "top_fields": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "field": {
                        "type": "string"
                    },

                    "value": {
                        "type": "string"
                    }
                },

                "required": [
                    "field",
                    "value"
                ]
            }
        },

        "by_date_fields": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "field": {
                        "type": "string"
                    },

                    "initials": {
                        "type": "string"
                    },

                    "date": {
                        "type": "string"
                    }
                },

                "required": [
                    "field",
                    "initials",
                    "date"
                ]
            }
        },

        "operations_manager_review": {
            "type": "object",

            "properties": {

                "initials": {
                    "type": "string"
                },

                "date": {
                    "type": "string"
                }
            },

            "required": [
                "initials",
                "date"
            ]
        },

        "production_rows": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "item": {
                        "type": "string"
                    },

                    "produced": {
                        "type": "string"
                    },

                    "packaged": {
                        "type": "string"
                    },

                    "required_field": {
                        "type": "string"
                    }
                },

                "required": [
                    "item",
                    "produced",
                    "packaged",
                    "required_field"
                ]
            }
        }
    },

    "required": [
        "form_type",
        "top_fields",
        "by_date_fields",
        "operations_manager_review",
        "production_rows"
    ]
}


DISCARD_SCHEMA = {
    "type": "object",

    "properties": {

        "form_type": {
            "type": "string"
        },

        "donor_number": {
            "type": "string"
        },

        "discard_authorized_by": {
            "type": "string"
        },

        "discard_authorized_date": {
            "type": "string"
        },

        "reason_for_discard": {
            "type": "string"
        },

        "tissue_status": {
            "type": "object",

            "properties": {

                "unprocessed_tissue": {
                    "type": "boolean"
                },

                "in_processing_tissue": {
                    "type": "boolean"
                },

                "unreleased_packaged_tissue": {
                    "type": "boolean"
                },

                "released_packaged_tissue": {
                    "type": "boolean"
                }
            },

            "required": [
                "unprocessed_tissue",
                "in_processing_tissue",
                "unreleased_packaged_tissue",
                "released_packaged_tissue"
            ]
        },

        "tissue_rows": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "graft_id": {
                        "type": "string"
                    },

                    "tissue_description": {
                        "type": "string"
                    },

                    "storage_location": {
                        "type": "string"
                    },

                    "confirmed_x": {
                        "type": "boolean"
                    }
                },

                "required": [
                    "graft_id",
                    "tissue_description",
                    "storage_location",
                    "confirmed_x"
                ]
            }
        },

        "bottom_fields": {
            "type": "object",

            "properties": {

                "tissue_discarded_by": {
                    "type": "string"
                },

                "confirmed_by": {
                    "type": "string"
                },

                "discard_date": {
                    "type": "string"
                },

                "freezerpro_updated_by": {
                    "type": "string"
                },

                "freezerpro_updated_date": {
                    "type": "string"
                },

                "donor_chart_updated_by": {
                    "type": "string"
                },

                "donor_chart_updated_date": {
                    "type": "string"
                }
            },

            "required": [
                "tissue_discarded_by",
                "confirmed_by",
                "discard_date",
                "freezerpro_updated_by",
                "freezerpro_updated_date",
                "donor_chart_updated_by",
                "donor_chart_updated_date"
            ]
        }
    },

    "required": [
        "form_type",
        "donor_number",
        "discard_authorized_by",
        "discard_authorized_date",
        "reason_for_discard",
        "tissue_status",
        "tissue_rows",
        "bottom_fields"
    ]
}

# ============================================================
# PROMPTS
# ============================================================

def detection_prompt(text):

    return f"""
You are identifying a RegenMed quality document from OCR text.

Your task is ONLY to classify the document type.

Possible outputs:

MP-F-023
QS-F-049
LOT_LOG
DISCARD_FORM

Important rules:

1. Return exactly ONE of the four values above.
2. Do not return explanations.
3. Do not guess based on a single OCR word.
4. Use multiple structural signals such as:
   - form title
   - form number
   - section headings
   - column names
   - table structure
   - footer text
5. OCR may contain spelling errors, missing punctuation,
   broken words, or imperfect handwriting recognition.
6. Prefer the overall structure of the form over one
   potentially incorrect OCR token.

Identification hints:

MP-F-023 commonly contains concepts such as:
- Donor #
- Tissue Checked In
- Operations Manager Review
- Produced
- Packaged
- processing / production rows

QS-F-049 commonly contains:
- Reviewed By / Date
- Technical
- Quality
- numbered review items
- INC #
- Status

LOT_LOG commonly contains:
- Lot Number
- Exp. Date
- Manufacturer
- RegenMed Item
- Qty Used
- Load #
- Sterilization Date
- Packaging

DISCARD_FORM commonly contains:
- Tissue Discard
- Discard Authorized By
- Reason for Discard
- Tissue Status
- Graft ID
- Tissue Discarded By
- FreezerPro

OCR TEXT:

{text}

Return ONLY one of:

MP-F-023
QS-F-049
LOT_LOG
DISCARD_FORM
"""


def lot_log_prompt(text):

    return f"""
You are extracting data from a RegenMed Processing / Packaging Lot Log.

This is a transcription task, not an interpretation task.

STRICT EXTRACTION RULES:

1. Never guess or invent a value.
2. Only return a value when it is directly supported by the OCR.
3. If a value is blank, unreadable, ambiguous, or cannot be confidently
   associated with the requested field, return "".
4. Do not repair handwriting by guessing what the writer probably meant.
5. Do not copy nearby values into another field.
6. Do not move data between rows.
7. Do not merge two rows together.
8. Do not create rows that are not present in the document.
9. Preserve visible values as closely as possible.
10. Return "N/A" only when N/A, NA, N / A, or an obviously equivalent
    notation is explicitly present in that specific field.
11. A blank field must remain "".
12. Do not decide whether the form passes or fails.
13. Only extract data.

The form contains SEPARATE sections.

============================================================
PAGE 1 - ITEM TABLE
============================================================

For every listed row in the Page 1 Item table extract:

item
lot_number
exp_date
manufacturer

Important:

- Keep each row separate.
- A value belongs only to the row where it appears.
- If an item is listed but one of the required cells is blank,
  still include that row and return "" for the blank cell.
- Do not exclude a row merely because it contains N/A.

============================================================
PAGE 1 - REGENMED ITEM TABLE
============================================================

For every listed RegenMed Item extract:

item
lot
qty_used

Important:

- This is separate from the normal Page 1 Item table.
- Do not move rows between these two sections.
- Include listed rows even when Lot or Qty Used is blank.

============================================================
PAGE 2 - ITEM / EQUIPMENT TABLE
============================================================

Extract only rows belonging to the Page 2 table whose relevant columns are:

item
load_number
sterilization_date

CRITICAL:

- This table is NOT the Packaging table.
- Packaging material names must NEVER be returned in page_2_items.
- A row belongs here only when it is structurally associated with
  Load # and/or Sterilization Date.
- Do not interpret Lot or Qty Used as Load # or Sterilization Date.
- Include listed rows even when both fields appear blank.

============================================================
PAGE 2 - PACKAGING TABLE
============================================================

Extract only rows from the Packaging section.

For every listed packaging row extract:

item
lot
qty_used

CRITICAL:

- Packaging rows must NEVER appear in page_2_items.
- page_2_items and packaging are separate tables.
- Do not treat packaging Lot values as Load Numbers.
- Do not treat packaging Qty Used values as Sterilization Dates.
- If a packaging row is listed and a value is blank,
  include the row and return "".

============================================================
FINAL CHECK BEFORE RETURNING JSON
============================================================

Before returning:

- Verify that Packaging rows appear only in packaging.
- Verify that Load # / Sterilization Date rows appear only in page_2_items.
- Verify that Page 1 Item rows and RegenMed Item rows remain separate.
- Do not fill missing values using information from another row.
- Do not infer values from expected form patterns.

OCR TEXT:

{text}
"""


def qs_prompt(text):

    return f"""
You are extracting structured information from RegenMed form QS-F-049.

This is a transcription and reconstruction task from noisy OCR.

Your goal is to recover the values that are visibly present in the form,
while avoiding unsupported guesses.

IMPORTANT:

1. OCR may split initials and dates across nearby tokens or lines.
2. OCR may misread separators such as:
   /  -  .  |
3. OCR may split a date into fragments.
4. Use row structure, Technical/Quality column positions, and nearby OCR
   context to reconstruct a value only when the association is clear.
5. Never invent a value that is not supported by OCR evidence.
6. If the value remains ambiguous after using row context, return "".
7. Do not copy values from another numbered row.
8. Do not swap Technical and Quality columns.
9. Do not infer a date just because adjacent rows have similar dates.
10. Do not decide PASS or FAIL.

============================================================
REVIEW ROWS
============================================================

For every numbered review item extract:

item

technical_initials
technical_date
technical_na

quality_initials
quality_date
quality_na

There should normally be one Technical review value
and one Quality review value for each numbered row.

Use the layout and OCR sequence to keep the two columns separate.

============================================================
INITIALS
============================================================

Initials are usually short alphabetic values such as:

MM
LC
AB

If OCR breaks initials slightly but the row/column association is obvious,
return the most directly supported transcription.

If initials cannot be determined confidently, return "".

============================================================
DATES
============================================================

Dates are expected to represent MM/DD/YY.

OCR may render dates as examples such as:

11-27-24
11.27.24
11 27 24
11|27|24
112724

If the OCR clearly contains all three date components and the row/column
association is clear, reconstruct the date into:

MM/DD/YY

Examples:

11-27-24 -> 11/27/24
11.27.24 -> 11/27/24
11 27 24 -> 11/27/24

Do NOT create missing digits.

If OCR contains incomplete or ambiguous digits, return "".

============================================================
N/A
============================================================

technical_na = true only when the Technical field explicitly indicates:

N/A
NA
N / A
NIA when clearly caused by OCR

quality_na = true only when the Quality field explicitly indicates
the same.

If N/A is present:

technical_initials or quality_initials should be ""
technical_date or quality_date should be ""

============================================================
ITEM 10
============================================================

Extract:

inc_number
status

Use only the Item 10 row.

If INC # is visibly present, extract it.

If Status is visibly present next to it, extract it.

Do not infer Status from another part of the form.

============================================================
FINAL CONSISTENCY CHECK
============================================================

Before returning:

- Keep row numbers 1 through 10 separate.
- Do not move dates between rows.
- Do not move Technical values into Quality.
- Do not move Quality values into Technical.
- Reconstruct date punctuation only when all date digits are supported.
- Prefer "" over unsupported guessing.

OCR TEXT:

{text}
"""

    return f"""
You are extracting information from RegenMed form QS-F-049.

This is a transcription task only.

Do NOT determine whether the form passes validation.
Python code will perform validation after extraction.

STRICT RULES:

1. Never invent, infer, or guess a value.
2. Extract only information directly supported by OCR.
3. If handwriting is unclear or ambiguous, return "".
4. Do not move initials or dates between rows.
5. Do not use the value from the row above or below.
6. Keep Technical and Quality columns separate.
7. Preserve dates exactly as read whenever possible.
8. Do NOT automatically change "-", ".", or other separators to "/".
9. Do not manufacture a date because the surrounding dates look similar.
10. Return N/A only when it is explicitly written for that specific review.
11. Blank is not the same as N/A.
12. Include every numbered review row that is visible.

============================================================
REVIEW ROWS
============================================================

For each numbered review item extract:

item

technical_initials
technical_date
technical_na

quality_initials
quality_date
quality_na

Rules for technical_na:

technical_na = true ONLY when the Technical review field explicitly
contains N/A, NA, N / A, or clearly equivalent notation.

Otherwise:

technical_na = false

Rules for quality_na:

quality_na = true ONLY when the Quality review field explicitly
contains N/A, NA, N / A, or clearly equivalent notation.

Otherwise:

quality_na = false

IMPORTANT:

If N/A is explicitly present:

- do not invent initials
- do not invent a date

If initials are visible but the date is blank:

return the initials
return technical_date or quality_date as ""

If the date is visible but initials are blank:

return the date
return initials as ""

If a date appears as:

09-25-24

return:

09-25-24

Do NOT convert it to another format.

If it appears:

09.25.24

return:

09.25.24

Preserve what OCR supports.

============================================================
ITEM 10
============================================================

Extract:

inc_number
status

Rules:

- Extract INC # only when directly visible.
- Extract Status only from the Status field associated with Item 10.
- Do not infer Status from surrounding text.
- If INC # is present and Status is blank, return status as "".
- Do not make a validation decision.

============================================================
FINAL CHECK
============================================================

Before returning:

- Confirm Technical values have not been placed in Quality fields.
- Confirm Quality values have not been placed in Technical fields.
- Confirm dates have not been copied between rows.
- Confirm N/A is true only when explicitly present.
- Preserve uncertain fields as "" rather than guessing.

OCR TEXT:

{text}
"""


def mp_prompt(text):

    return f"""
You are extracting structured data from RegenMed form MP-F-023.

This is a transcription task.

Do NOT determine PASS or FAIL.
Do NOT guess missing information.

STRICT RULES:

1. Never invent values.
2. Return only information supported directly by OCR.
3. If a field is blank, unreadable, or ambiguous, return "".
4. Never copy a value from a neighboring field.
5. Never move initials or dates between By/Date fields.
6. Keep each processing-table row separate.
7. Do not create rows that are not visible.
8. Do not remove a listed row merely because it contains blanks.
9. Preserve visible values as closely as possible.
10. N/A may only be returned if explicitly written.

============================================================
TOP SECTION
============================================================

Extract all visible required fields beginning with:

Donor #

and continuing through:

Tissue Checked In By / Date

For ordinary fields return:

top_fields

Each object:

field
value

Important:

- Use the printed field label as "field" where possible.
- If a printed field exists but the handwritten/entered value is blank,
  include the field with value "".

============================================================
BY / DATE FIELDS
============================================================

For every visible field containing a By / Date requirement,
return it inside:

by_date_fields

Each object:

field
initials
date

Rules:

- initials and date must be extracted separately.
- Do not merge them into one value.
- If only initials are visible:
  initials = visible value
  date = ""

- If only date is visible:
  initials = ""
  date = visible value

- Never copy a date from a nearby By/Date field.

============================================================
OPERATIONS MANAGER REVIEW
============================================================

Extract only the Operations Manager Review values:

initials
date

If either value is missing or unreadable, return "".

Do not use another review signature/date as a substitute.

============================================================
PROCESSING / PRODUCTION TABLE
============================================================

For every relevant listed row extract:

item
produced
packaged
required_field

required_field must be exactly one of:

produced
packaged

Use the visual/table structure and OCR evidence to determine
which column is intended for that row.

Important:

- A value in # Produced belongs only to produced.
- A value in # Packaged belongs only to packaged.
- Do not copy between columns.
- Do not fill blank cells using neighboring rows.
- If the required column cannot be determined confidently,
  use the strongest printed table structure available.
- Do not invent numeric quantities.

============================================================
FINAL CHECK
============================================================

Before returning:

- Check that top fields remain separate from By/Date fields.
- Check that Operations Manager Review was not taken from another signature.
- Check that Produced and Packaged values were not swapped.
- Keep unreadable information blank.

OCR TEXT:

{text}
"""


def discard_prompt(text):

    return f"""
You are extracting data from a RegenMed Tissue Discard Form.

This is a transcription task only.

Do NOT determine whether the form passes or fails.
Validation will be performed by deterministic Python rules.

STRICT RULES:

1. Never guess or invent a value.
2. Only return information directly supported by OCR.
3. If handwriting is unreadable, uncertain, or ambiguous, return "".
4. Do not copy information between tissue rows.
5. Do not assume a checkbox is selected unless OCR/layout evidence
   clearly indicates that it is marked.
6. Do not infer Tissue Status from the Graft ID.
7. Do not infer Graft ID from Tissue Status.
8. Return N/A only when explicitly written.
9. Blank and N/A are different.
10. Do not manufacture names, dates, IDs, locations, or X marks.

============================================================
TOP SECTION
============================================================

Extract:

donor_number
discard_authorized_by
discard_authorized_date
reason_for_discard

Rules:

- Each field must come from its own labeled area.
- If the field is present but blank, return "".
- Do not combine Discard Authorized By and Date into one field.

============================================================
TISSUE STATUS
============================================================

Return:

unprocessed_tissue
in_processing_tissue
unreleased_packaged_tissue
released_packaged_tissue

Each must be true or false.

Set a value to true ONLY when its corresponding checkbox appears
explicitly selected/marked.

Do not infer which status should have been selected.

If no checkbox can be confidently identified:

all values should be false.

Do not automatically force exactly one value to true.

============================================================
TISSUE ROWS
============================================================

For every actually listed tissue row extract:

graft_id
tissue_description
storage_location
confirmed_x

Rules:

- Keep rows separate.
- Do not combine multiple tissue descriptions.
- Do not move a Graft ID into another row.
- Do not use a storage location from another row.
- confirmed_x = true ONLY when the small confirmation box/X
  associated with that exact row appears completed.
- If the row contains information but the confirmation mark cannot
  be confidently identified, confirmed_x = false.
- Do not create entirely empty rows.

For Graft ID:

- preserve an actual visible ID
- return "N/A" only if explicitly written
- return "" if blank/unreadable

============================================================
BOTTOM SECTION
============================================================

Extract:

tissue_discarded_by
confirmed_by
discard_date
freezerpro_updated_by
freezerpro_updated_date
donor_chart_updated_by
donor_chart_updated_date

Rules:

- Extract each value only from its labeled field.
- Do not reuse the same name/date across fields unless the OCR
  explicitly shows that value in each field.
- Preserve N/A when explicitly written.
- Return "" when blank or unreadable.

============================================================
FINAL CHECK
============================================================

Before returning:

- Do not infer Tissue Status from business logic.
- Do not infer whether Graft ID should be N/A.
- Do not infer missing X marks.
- Do not fill blank bottom fields using neighboring signatures.
- Keep uncertain values blank.

OCR TEXT:

{text}
"""

# ============================================================
# FORM DISPLAY NAME
# ============================================================

def form_display_name(form_type):

    names = {

        "MP-F-023":
            "Manufacturing / Processing Form",

        "QS-F-049":
            "Quality System Review Form",

        "LOT_LOG":
            "Processing & Packaging Lot Log",

        "DISCARD_FORM":
            "Tissue Discard Form"
    }

    return names.get(
        form_type,
        form_type
    )


# ============================================================
# UI HELPERS
# ============================================================

def render_metric_card(
    label,
    value
):

    html(f"""
    <div class="metric-card">

        <div class="metric-label">
            {label}
        </div>

        <div class="metric-value">
            {value}
        </div>

    </div>
    """)


def render_issue_card(
    number,
    issue
):

    html(f"""
    <div class="issue-card">

        <span class="issue-number">
            {number}
        </span>

        {issue}

    </div>
    """)


def status_label(issues):

    return (
        "PASS"
        if len(issues) == 0
        else "REVIEW REQUIRED"
    )


# ============================================================
# LOADING OVERLAY
# ============================================================

def render_loading_overlay(
    title,
    subtitle,
    active_step
):

    steps = [

        "Preparing document",

        "Detecting form type",

        "Extracting information",

        "Running validation"
    ]


    step_html = ""


    for index, label in enumerate(
        steps,
        start=1
    ):

        if index < active_step:

            icon = "✓"

            icon_class = (
                "step-icon "
                "step-icon-done"
            )

            row_class = (
                "review-step"
            )

        elif index == active_step:

            icon = "●"

            icon_class = (
                "step-icon "
                "step-icon-active"
            )

            row_class = (
                "review-step "
                "review-step-active"
            )

        else:

            icon = "○"

            icon_class = (
                "step-icon"
            )

            row_class = (
                "review-step"
            )


        step_html += f"""

        <div class="{row_class}">

            <div class="{icon_class}">
                {icon}
            </div>

            <div>
                {label}
            </div>

        </div>

        """


    return f"""

    <div class="review-overlay">

        <div class="review-loader-card">

            <div class="review-orbit"></div>

            <div class="loader-title">
                {title}
            </div>

            <div class="loader-subtitle">
                {subtitle}
            </div>

            {step_html}

        </div>

    </div>

    """


# ============================================================
# REPORT
# ============================================================

def build_text_report(
    result,
    file_name
):

    lines = [

        "REGENMED INTERNAL DOCUMENT REVIEW",

        "=" * 55,

        "",

        f"File: {file_name}",

        f"Detected Form: {result['form_type']}",

        f"Status: {status_label(result['issues'])}",

        f"Issues Found: {len(result['issues'])}",

        "",

        "VALIDATION FINDINGS",

        "-" * 55
    ]


    if not result["issues"]:

        lines.append(
            "No validation issues were detected."
        )

    else:

        for index, issue in enumerate(
            result["issues"],
            start=1
        ):

            lines.append(
                f"{index}. {issue}"
            )


    return "\n".join(
        lines
    )


# ============================================================
# PDF RENDERING
# ============================================================

def render_pdf(
    pdf_bytes
):

    pdf_document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )


    images = []


    for page_number in range(
        len(pdf_document)
    ):

        page = pdf_document.load_page(
            page_number
        )

        pix = page.get_pixmap(
            matrix=fitz.Matrix(
                2,
                2
            )
        )

        image = Image.open(
            io.BytesIO(
                pix.tobytes(
                    "png"
                )
            )
        )

        images.append(
            image.copy()
        )


    page_count = len(
        pdf_document
    )

    pdf_document.close()


    return (
        page_count,
        images
    )


# ============================================================
# OCR
# ============================================================

def extract_ocr(
    images
):

    all_page_text = []


    for image in images:

        text = (
            pytesseract
            .image_to_string(
                image
            )
        )

        all_page_text.append(
            text
        )


    return all_page_text


# ============================================================
# DETECTION ONLY
# ============================================================

def detect_document_type(
    all_page_text
):

    if not all_page_text:

        raise ValueError(
            "No OCR text available."
        )


    form_type, remaining = (
        ask_gemini(

            detection_prompt(
                all_page_text[0]
            )
        )
    )


    form_type = (
        form_type
        .strip()
        .upper()
    )


    if "DISCARD" in form_type:

        form_type = (
            "DISCARD_FORM"
        )

    elif "LOT" in form_type:

        form_type = (
            "LOT_LOG"
        )

    elif "QS-F-049" in form_type:

        form_type = (
            "QS-F-049"
        )

    elif "MP-F-023" in form_type:

        form_type = (
            "MP-F-023"
        )

    else:

        raise ValueError(
            "Unable to identify document type."
        )


    return (
        form_type,
        remaining
    )


# ============================================================
# EXTRACTION + VALIDATION
# ============================================================

def analyze_detected_document(
    all_page_text,
    form_type
):

    full_text = "\n\n".join(
        all_page_text
    )


    if form_type == "LOT_LOG":

        extracted_data, remaining = (
            ask_gemini(

                lot_log_prompt(
                    full_text
                ),

                response_schema=(
                    LOT_LOG_SCHEMA
                )
            )
        )

        issues = (
            validate_lot_log(
                extracted_data
            )
        )


    elif form_type == "QS-F-049":

        extracted_data, remaining = (
            ask_gemini(

                qs_prompt(
                    full_text
                ),

                response_schema=(
                    QS_SCHEMA
                )
            )
        )

        issues = (
            validate_qs_f_049(
                extracted_data
            )
        )


    elif form_type == "MP-F-023":

        extracted_data, remaining = (
            ask_gemini(

                mp_prompt(
                    full_text
                ),

                response_schema=(
                    MP_SCHEMA
                )
            )
        )

        issues = (
            validate_mp_f_023(
                extracted_data
            )
        )


    elif form_type == "DISCARD_FORM":

        extracted_data, remaining = (
            ask_gemini(

                discard_prompt(
                    full_text
                ),

                response_schema=(
                    DISCARD_SCHEMA
                )
            )
        )

        issues = (
            validate_discard_form(
                extracted_data
            )
        )


    else:

        raise ValueError(
            "Unsupported form type."
        )


    return {

        "form_type":
            form_type,

        "extracted_data":
            extracted_data,

        "issues":
            issues,

        "remaining":
            remaining,

        "ocr_text":
            full_text
    }


# ============================================================
# RESET
# ============================================================

def reset_app():

    for key, value in defaults.items():

        st.session_state[key] = value


# ============================================================
# HEADER
# ============================================================

html("""
<div class="hero-box">

    <div class="app-brand">
        REGENMED QUALITY INTELLIGENCE
    </div>

    <div class="hero-title">
        Internal Document Reviewer
    </div>

    <div class="hero-subtitle">

        AI-assisted pre-review of RegenMed processing documentation.
        Upload a scanned form, automatically identify its type,
        and surface incomplete or inconsistent information before
        final human quality review.

    </div>

    <div class="ai-ready">

        <span class="ai-dot"></span>

        AI REVIEW ENGINE READY

    </div>

</div>
""")


# ============================================================
# FORM DETECTED SCREEN
# ============================================================

if (
    st.session_state.review_stage
    == "detected"
):

    detected_type = (
        st.session_state
        .detected_form_type
    )


    html(f"""
    <div class="detected-wrapper">

        <div class="detected-card">

            <div class="detected-check">
                ✓
            </div>

            <div class="detected-label">
                Form Identified
            </div>

            <div class="detected-type">
                {detected_type}
            </div>

            <div class="detected-name">
                {form_display_name(detected_type)}
            </div>

            <div class="detected-info">

                The document type has been identified successfully.
                Continue to extract the form information and apply
                the required validation rules.

            </div>

        </div>

    </div>
    """)


    button_left, button_middle, button_right = (
        st.columns(
            [1.5, 1, 1.5]
        )
    )


    with button_middle:

        if st.button(
            "Continue Review →",
            type="primary",
            use_container_width=True
        ):

            st.session_state.review_stage = (
                "analyzing"
            )

            st.rerun()


    if st.button(
        "← Cancel Review",
        use_container_width=False
    ):

        st.session_state.review_stage = (
            "idle"
        )

        st.session_state.detected_form_type = (
            None
        )

        st.rerun()


    st.stop()


# ============================================================
# SECOND ANALYSIS STAGE
# ============================================================

if (
    st.session_state.review_stage
    == "analyzing"
):

    loading_placeholder = (
        st.empty()
    )


    loading_placeholder.html(
        render_loading_overlay(
            "Completing document review",
            (
                f"{st.session_state.detected_form_type} "
                "identified. Extracting structured information "
                "and applying RegenMed validation rules."
            ),
            active_step=3
        )
    )


    try:

        result = (
            analyze_detected_document(

                st.session_state
                .all_page_text,

                st.session_state
                .detected_form_type
            )
        )


        st.session_state.analysis_result = (
            result
        )

        st.session_state.review_stage = (
            "complete"
        )


    except Exception as error:

        st.session_state.analysis_result = {

            "error": str(
                error
            )
        }

        st.session_state.review_stage = (
            "complete"
        )


    finally:

        loading_placeholder.empty()


    st.rerun()


# ============================================================
# MAIN LAYOUT
# ============================================================

left_col, right_col = st.columns(
    [1, 1.35],
    gap="large"
)


# ============================================================
# LEFT PANEL
# ============================================================

with left_col:

    html("""
    <div class="section-title">
        Review Workspace
    </div>
    """)


    html("""
    <div class="upload-shell">

        <div class="upload-header-row">

            <div>
                <div class="upload-eyebrow">
                    DOCUMENT INTAKE
                </div>

                <div class="upload-title">
                    Upload RegenMed PDF
                </div>

                <div class="upload-subtitle">
                    Add one scanned RegenMed form for automated review.
                </div>
            </div>

            <div class="upload-badge">
                PDF ONLY
            </div>

        </div>

    </div>
    """)

    uploaded_file = st.file_uploader(
        "Upload RegenMed PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )

    html("""
    <div class="upload-helper">
        <span>Maximum file size: 200 MB</span>
        <span>•</span>
        <span>Single PDF per review</span>
    </div>
    """)


    control_left, control_right = (
        st.columns(
            [1, 2]
        )
    )


    with control_left:

        if st.button(
            "Clear Review",
            use_container_width=True
        ):

            reset_app()

            st.rerun()


    with control_right:

        st.caption(
            "MP-F-023 • QS-F-049 • "
            "Lot Logs • Discard Forms"
        )


    # ========================================================
    # NEW UPLOAD
    # ========================================================

    if uploaded_file is not None:

        current_file_id = (

            f"{uploaded_file.name}-"
            f"{uploaded_file.size}"
        )


        if (
            st.session_state
            .last_processed_file
            != current_file_id
        ):

            pdf_bytes = (
                uploaded_file
                .getvalue()
            )


            with st.spinner(
                "Preparing document preview..."
            ):

                (
                    page_count,
                    images
                ) = render_pdf(
                    pdf_bytes
                )


            st.session_state.images = (
                images
            )

            st.session_state.file_name = (
                uploaded_file.name
            )

            st.session_state.page_count = (
                page_count
            )

            st.session_state.file_size_kb = (
                uploaded_file.size
                / 1024
            )

            st.session_state.all_page_text = []

            st.session_state.analysis_result = (
                None
            )

            st.session_state.detected_form_type = (
                None
            )

            st.session_state.detection_remaining = (
                None
            )

            st.session_state.review_stage = (
                "idle"
            )

            st.session_state.last_processed_file = (
                current_file_id
            )


        # ====================================================
        # DOCUMENT INFO
        # ====================================================

        html("""
        <div class="section-title">
            Document Information
        </div>
        """)


        render_metric_card(
            "File Name",
            st.session_state.file_name
        )


        info1, info2 = (
            st.columns(2)
        )


        with info1:

            render_metric_card(
                "Pages",
                st.session_state.page_count
            )


        with info2:

            render_metric_card(
                "File Size",
                f"{st.session_state.file_size_kb:.2f} KB"
            )


        # ====================================================
        # START ANALYSIS
        # ====================================================

        if st.button(
            "✦ Analyze Document",
            type="primary",
            use_container_width=True
        ):

            overlay = (
                st.empty()
            )


            overlay.html(
            render_loading_overlay(
                "Reviewing your document",
                (
                    "Reading the uploaded PDF and identifying "
                    "the RegenMed form type."
                ),
                active_step=2
            )
        )


            try:

                # OCR

                all_page_text = (
                    extract_ocr(

                        st.session_state
                        .images
                    )
                )


                st.session_state.all_page_text = (
                    all_page_text
                )


                # FORM DETECTION

                (
                    detected_form_type,
                    remaining
                ) = detect_document_type(
                    all_page_text
                )


                st.session_state.detected_form_type = (
                    detected_form_type
                )

                st.session_state.detection_remaining = (
                    remaining
                )

                st.session_state.review_stage = (
                    "detected"
                )


            except Exception as error:

                st.session_state.analysis_result = {

                    "error": str(
                        error
                    )
                }

                st.session_state.review_stage = (
                    "complete"
                )


            finally:

                overlay.empty()


            st.rerun()


    else:

        st.info(
            "Upload a RegenMed PDF to begin."
        )


    # ========================================================
    # RESULTS
    # ========================================================

    result = (
        st.session_state
        .analysis_result
    )


    if (
        result is not None
        and
        st.session_state.review_stage
        == "complete"
    ):

        if "error" in result:

            st.error(
                f"Analysis failed: "
                f"{result['error']}"
            )


        else:

            html("""
            <div class="section-title">
                Review Summary
            </div>
            """)


            kpi1, kpi2, kpi3 = (
                st.columns(3)
            )


            with kpi1:

                html(f"""
                <div class="kpi-card">

                    <div class="kpi-title">
                        Form Type
                    </div>

                    <div class="kpi-number">
                        {result["form_type"]}
                    </div>

                </div>
                """)


            with kpi2:

                html(f"""
                <div class="kpi-card">

                    <div class="kpi-title">
                        Issues
                    </div>

                    <div class="kpi-number">
                        {len(result["issues"])}
                    </div>

                </div>
                """)


            with kpi3:

                if not result["issues"]:

                    chip = (
                        '<span class="pass-chip">'
                        'PASS'
                        '</span>'
                    )

                else:

                    chip = (
                        '<span class="review-chip">'
                        'REVIEW'
                        '</span>'
                    )


                html(f"""
                <div class="kpi-card">

                    <div class="kpi-title">
                        Status
                    </div>

                    <div class="kpi-number">
                        {chip}
                    </div>

                </div>
                """)


            if not result["issues"]:

                html("""
                <div class="status-pass">
                    ✓ Document passed all required checks.
                </div>
                """)

            else:

                html(f"""
                <div class="status-fail">

                    {len(result["issues"])}
                    issue(s) require human review.

                </div>
                """)


            # =================================================
            # FINDINGS
            # =================================================

            html("""
            <div class="section-title">
                Validation Findings
            </div>
            """)


            if not result["issues"]:

                st.success(
                    "No validation issues detected."
                )

            else:

                for index, issue in enumerate(
                    result["issues"],
                    start=1
                ):

                    render_issue_card(
                        index,
                        issue
                    )


            # =================================================
            # REPORT
            # =================================================

            report = (
                build_text_report(

                    result,

                    st.session_state
                    .file_name
                )
            )


            st.download_button(

                "Download Review Report",

                report,

                file_name=(
                    "regenmed_review_report.txt"
                ),

                mime="text/plain",

                use_container_width=True
            )


            # =================================================
            # AUDIT
            # =================================================

            with st.expander(
                "Developer / Audit Details"
            ):

                tab1, tab2 = (
                    st.tabs(
                        [
                            "Structured Extraction",
                            "Raw OCR"
                        ]
                    )
                )


                with tab1:

                    st.json(
                        result[
                            "extracted_data"
                        ]
                    )


                with tab2:

                    st.text(
                        result[
                            "ocr_text"
                        ]
                    )


            st.caption(
                f"API requests remaining: "
                f"{result['remaining']}"
            )


# ============================================================
# RIGHT PANEL
# ============================================================

with right_col:

    html("""
    <div class="section-title">
        Document Preview
    </div>
    """)


    if st.session_state.images:

        html(f"""
        <div class="preview-header">

            <div class="preview-file">
                {st.session_state.file_name}
            </div>

            <div class="preview-meta">

                {st.session_state.page_count}
                page(s)

                &nbsp; • &nbsp;

                {st.session_state.file_size_kb:.2f}
                KB

            </div>

        </div>
        """)


        page_tabs = (
            st.tabs(
                [
                    f"Page {index + 1}"

                    for index in range(
                        len(
                            st.session_state
                            .images
                        )
                    )
                ]
            )
        )


        for index, tab in enumerate(
            page_tabs
        ):

            with tab:

                st.image(

                    st.session_state
                    .images[
                        index
                    ],

                    use_container_width=True
                )


    else:

        html("""
        <div class="empty-preview">

            <div class="empty-preview-icon">
                📄
            </div>

            <strong>
                Document Preview
            </strong>

            <br><br>

            Upload a RegenMed PDF to display
            the source document here.

        </div>
        """)