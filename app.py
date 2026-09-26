import io
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

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

st.set_page_config(
    page_title="RegenMed Internal Document Reviewer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# DEFAULT SESSION STATE
# ============================================================

defaults = {
    "analysis_result": None,
    "images": None,
    "file_name": None,
    "page_count": 0,
    "file_size_kb": 0.0,
    "last_processed_file": None,
    "all_page_text": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# TOP TOOLBAR - THEME SWITCHER
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
        options=["🌙 Dark", "☀️ Light"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_selector"
    )

light_mode = theme_choice == "☀️ Light"


# ============================================================
# THEME COLORS
# ============================================================

if light_mode:
    BG = "#8bc7f5"
    CARD = "#5d5be3"
    CARD_2 = "#f8fafc"
    TEXT = "#aabde8"
    MUTED = "#010d1d"
    BORDER = "rgba(15,23,42,0.12)"

    HERO_START = "#e0e7ff"
    HERO_MID = "#dbeafe"
    HERO_END = "#eef2ff"

    HERO_TEXT = "#0f172a"
    HERO_SUB = "#031125"

    ISSUE_BG = "#fff7f7"
    TOOLBAR_BG = "#ffffff"

else:
    BG = "#080d16"
    CARD = "#111827"
    CARD_2 = "#0f172a"
    TEXT = "#f8fafc"
    MUTED = "#94a3b8"
    BORDER = "rgba(148,163,184,0.17)"

    HERO_START = "#0f172a"
    HERO_MID = "#172554"
    HERO_END = "#1e293b"

    HERO_TEXT = "#ffffff"
    HERO_SUB = "#cbd5e1"

    ISSUE_BG = "#0f172a"
    TOOLBAR_BG = "#0b1220"


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
    background: {BG};
    color: {TEXT};
}}

.block-container {{
    padding-top: 0.6rem;
    padding-bottom: 3rem;
    max-width: 1850px;
}}

/* ------------------------------------------------
   Top radio / toolbar styling
------------------------------------------------ */

div[data-testid="stRadio"] {{
    background: {TOOLBAR_BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 0.45rem 0.7rem 0.3rem 0.7rem;
}}

div[data-testid="stRadio"] > div {{
    gap: 0.45rem;
}}

div[role="radiogroup"] {{
    gap: 0.5rem;
}}

div[role="radiogroup"] label {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 999px;
    padding: 0.42rem 0.85rem;
    min-width: 102px;
    justify-content: center;
    transition: all 0.2s ease;
}}

div[role="radiogroup"] label:hover {{
    border-color: rgba(59,130,246,0.45);
    transform: translateY(-1px);
}}

div[role="radiogroup"] label span {{
    color: {TEXT} !important;
    font-weight: 700;
    font-size: 0.88rem;
}}

div[role="radiogroup"] label:has(input:checked) {{
    background: rgba(59,130,246,0.14);
    border-color: rgba(59,130,246,0.65);
    box-shadow: 0 0 0 1px rgba(59,130,246,0.18) inset;
}}

div[data-testid="stCaptionContainer"] p {{
    color: {MUTED};
}}

/* ------------------------------------------------
   Header
------------------------------------------------ */

.hero-box {{
    padding: 1.6rem 1.8rem;
    border-radius: 20px;
    background:
        linear-gradient(
            135deg,
            {HERO_START} 0%,
            {HERO_MID} 50%,
            {HERO_END} 100%
        );
    border: 1px solid {BORDER};
    box-shadow: 0 15px 40px rgba(0,0,0,0.14);
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}}

.hero-box::after {{
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background:
        radial-gradient(
            circle,
            rgba(59,130,246,0.16),
            transparent 70%
        );
    right: -90px;
    top: -110px;
}}

.app-brand {{
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.14rem;
    color: #3b82f6;
    margin-bottom: 0.5rem;
}}

.hero-title {{
    font-size: 2.15rem;
    font-weight: 800;
    color: {HERO_TEXT};
    margin-bottom: 0.45rem;
}}

.hero-subtitle {{
    font-size: 0.95rem;
    color: {HERO_SUB};
    line-height: 1.6;
    max-width: 900px;
}}

.ai-ready {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-top: 0.9rem;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    background: rgba(59,130,246,0.10);
    border: 1px solid rgba(59,130,246,0.30);
    color: #60a5fa;
    font-size: 0.75rem;
    font-weight: 700;
}}

.ai-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3b82f6;
    animation: pulse 1.6s infinite;
}}

@keyframes pulse {{
    0% {{
        box-shadow: 0 0 0 0 rgba(59,130,246,0.6);
    }}
    70% {{
        box-shadow: 0 0 0 8px rgba(59,130,246,0);
    }}
    100% {{
        box-shadow: 0 0 0 0 rgba(59,130,246,0);
    }}
}}

/* ------------------------------------------------
   Sections
------------------------------------------------ */

.section-title {{
    font-size: 1.05rem;
    font-weight: 750;
    color: {TEXT};
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
}}

/* ------------------------------------------------
   Cards
------------------------------------------------ */

.metric-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    padding: 0.9rem 1rem;
    border-radius: 14px;
    margin-bottom: 0.7rem;
    transition: all 0.2s ease;
}}

.metric-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(59,130,246,0.35);
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}}

.metric-label {{
    font-size: 0.68rem;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.06rem;
    margin-bottom: 0.3rem;
}}

.metric-value {{
    font-size: 0.96rem;
    font-weight: 700;
    color: {TEXT};
    word-break: break-word;
}}

.kpi-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 15px;
    padding: 1rem;
    min-height: 100px;
    transition: transform .2s ease;
}}

.kpi-card:hover {{
    transform: translateY(-3px);
}}

.kpi-title {{
    color: {MUTED};
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06rem;
}}

.kpi-number {{
    color: {TEXT};
    font-size: 1.23rem;
    font-weight: 800;
    margin-top: 0.5rem;
}}

/* ------------------------------------------------
   Status
------------------------------------------------ */

.pass-chip {{
    display: inline-block;
    background: rgba(34,197,94,0.13);
    border: 1px solid rgba(34,197,94,0.38);
    color: #22c55e;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    font-size: 0.77rem;
    font-weight: 800;
}}

.review-chip {{
    display: inline-block;
    background: rgba(239,68,68,0.13);
    border: 1px solid rgba(239,68,68,0.38);
    color: #ef4444;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    font-size: 0.77rem;
    font-weight: 800;
}}

.status-pass {{
    background: rgba(34,197,94,0.10);
    border: 1px solid rgba(34,197,94,0.30);
    color: #22c55e;
    padding: 0.9rem 1rem;
    border-radius: 12px;
    font-weight: 700;
    margin-top: 0.8rem;
    margin-bottom: 1rem;
}}

.status-fail {{
    background: rgba(239,68,68,0.10);
    border: 1px solid rgba(239,68,68,0.30);
    color: #ef4444;
    padding: 0.9rem 1rem;
    border-radius: 12px;
    font-weight: 700;
    margin-top: 0.8rem;
    margin-bottom: 1rem;
}}

/* ------------------------------------------------
   Issue cards
------------------------------------------------ */

.issue-card {{
    background: {ISSUE_BG};
    border: 1px solid rgba(239,68,68,0.20);
    border-left: 4px solid #ef4444;
    padding: 0.85rem 0.95rem;
    border-radius: 12px;
    margin-bottom: 0.6rem;
    color: {TEXT};
    line-height: 1.5;
    transition: transform 0.18s ease;
}}

.issue-card:hover {{
    transform: translateX(3px);
}}

.issue-number {{
    display: inline-flex;
    width: 24px;
    height: 24px;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: rgba(239,68,68,0.14);
    color: #ef4444;
    font-size: 0.74rem;
    font-weight: 800;
    margin-right: 0.45rem;
}}

/* ------------------------------------------------
   Preview
------------------------------------------------ */

.preview-header {{
    padding: 0.8rem 1rem;
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 13px;
    margin-bottom: 0.8rem;
}}

.preview-file {{
    color: {TEXT};
    font-weight: 700;
    font-size: 0.90rem;
}}

.preview-meta {{
    color: {MUTED};
    font-size: 0.76rem;
    margin-top: 0.2rem;
}}

.empty-preview {{
    border: 1px dashed {BORDER};
    border-radius: 17px;
    padding: 6rem 1rem;
    text-align: center;
    color: {MUTED};
    background: {CARD_2};
}}

.empty-preview-icon {{
    font-size: 2.2rem;
    margin-bottom: 0.7rem;
}}

/* ------------------------------------------------
   AI Loader
------------------------------------------------ */

.ai-loader {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    padding: 18px;
    margin-top: 8px;
    margin-bottom: 8px;
    border-radius: 12px;
    background: {CARD};
    border: 1px solid {BORDER};
    color: {MUTED};
    font-size: 0.82rem;
    font-weight: 600;
}}

.loader-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3b82f6;
    animation: loader-bounce 1.2s infinite ease-in-out;
}}

.loader-dot:nth-child(2) {{
    animation-delay: 0.15s;
}}

.loader-dot:nth-child(3) {{
    animation-delay: 0.30s;
}}

@keyframes loader-bounce {{
    0%, 80%, 100% {{
        transform: scale(0.6);
        opacity: 0.4;
    }}
    40% {{
        transform: scale(1);
        opacity: 1;
    }}
}}

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
        "form_type": {"type": "string"},
        "page_1_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "lot_number": {"type": "string"},
                    "exp_date": {"type": "string"},
                    "manufacturer": {"type": "string"}
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
                    "item": {"type": "string"},
                    "lot": {"type": "string"},
                    "qty_used": {"type": "string"}
                },
                "required": ["item", "lot", "qty_used"]
            }
        },
        "page_2_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "load_number": {"type": "string"},
                    "sterilization_date": {"type": "string"}
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
                    "item": {"type": "string"},
                    "lot": {"type": "string"},
                    "qty_used": {"type": "string"}
                },
                "required": ["item", "lot", "qty_used"]
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
        "form_type": {"type": "string"},
        "review_rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "technical_initials": {"type": "string"},
                    "technical_date": {"type": "string"},
                    "technical_na": {"type": "boolean"},
                    "quality_initials": {"type": "string"},
                    "quality_date": {"type": "string"},
                    "quality_na": {"type": "boolean"}
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
                "inc_number": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["inc_number", "status"]
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
        "form_type": {"type": "string"},
        "top_fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["field", "value"]
            }
        },
        "by_date_fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "initials": {"type": "string"},
                    "date": {"type": "string"}
                },
                "required": ["field", "initials", "date"]
            }
        },
        "operations_manager_review": {
            "type": "object",
            "properties": {
                "initials": {"type": "string"},
                "date": {"type": "string"}
            },
            "required": ["initials", "date"]
        },
        "production_rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "produced": {"type": "string"},
                    "packaged": {"type": "string"},
                    "required_field": {"type": "string"}
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
        "form_type": {"type": "string"},
        "donor_number": {"type": "string"},
        "discard_authorized_by": {"type": "string"},
        "discard_authorized_date": {"type": "string"},
        "reason_for_discard": {"type": "string"},
        "tissue_status": {
            "type": "object",
            "properties": {
                "unprocessed_tissue": {"type": "boolean"},
                "in_processing_tissue": {"type": "boolean"},
                "unreleased_packaged_tissue": {"type": "boolean"},
                "released_packaged_tissue": {"type": "boolean"}
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
                    "graft_id": {"type": "string"},
                    "tissue_description": {"type": "string"},
                    "storage_location": {"type": "string"},
                    "confirmed_x": {"type": "boolean"}
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
                "tissue_discarded_by": {"type": "string"},
                "confirmed_by": {"type": "string"},
                "discard_date": {"type": "string"},
                "freezerpro_updated_by": {"type": "string"},
                "freezerpro_updated_date": {"type": "string"},
                "donor_chart_updated_by": {"type": "string"},
                "donor_chart_updated_date": {"type": "string"}
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
Identify this RegenMed document.

Possible types:

MP-F-023
QS-F-049
LOT_LOG
DISCARD_FORM

DISCARD_FORM means Tissue Discard Form.
LOT_LOG means Processing / Packaging Lot Log.

OCR may contain mistakes.

Use title, headings, labels,
table structure and footer.

OCR:

{text}

Return ONLY:

MP-F-023
QS-F-049
LOT_LOG
DISCARD_FORM
"""


def lot_log_prompt(text):
    return f"""
Extract structured information from this RegenMed Lot Log.

Never intentionally invent values.

If blank return "".
Return N/A only when explicitly written.

PAGE 1 ITEM TABLE:
item
lot_number
exp_date
manufacturer

REGENMED ITEM TABLE:
item
lot
qty_used

PAGE 2 ITEM TABLE:
item
load_number
sterilization_date

PAGE 2 PACKAGING:
item
lot
qty_used

Do not mix Packaging rows
with page_2_items.

OCR:
{text}
"""


def qs_prompt(text):
    return f"""
Extract structured information from RegenMed QS-F-049.

Extract all numbered Technical and Quality review rows.

Return:

item
technical_initials
technical_date
technical_na
quality_initials
quality_date
quality_na

technical_na = true only when explicitly N/A.
quality_na = true only when explicitly N/A.

Also extract Item 10:
inc_number
status

If unreadable return "".
Do not intentionally invent values.

OCR:
{text}
"""


def mp_prompt(text):
    return f"""
Extract structured information from RegenMed MP-F-023.

TOP SECTION:
Extract fields from Donor #
through Tissue Checked In By/Date.

Normal fields:
top_fields

By/Date fields:
by_date_fields

OPERATIONS MANAGER REVIEW:
initials
date

PROCESSING TABLE:
item
produced
packaged
required_field

required_field must be:
produced
or
packaged

If unreadable return "".
Do not intentionally invent values.

OCR:
{text}
"""


def discard_prompt(text):
    return f"""
Extract structured information from a RegenMed Tissue Discard Form.

Never intentionally invent values.

TOP:
donor_number
discard_authorized_by
discard_authorized_date
reason_for_discard

TISSUE STATUS:
unprocessed_tissue
in_processing_tissue
unreleased_packaged_tissue
released_packaged_tissue

Set true only for visibly selected boxes.

TISSUE ROWS:
graft_id
tissue_description
storage_location
confirmed_x

confirmed_x is true only when the small X box
for the listed tissue is visibly completed.

BOTTOM:
tissue_discarded_by
confirmed_by
discard_date
freezerpro_updated_by
freezerpro_updated_date
donor_chart_updated_by
donor_chart_updated_date

Return N/A only when explicitly written.

OCR:
{text}
"""


# ============================================================
# UI HELPERS
# ============================================================

def render_metric_card(label, value):
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


def render_issue_card(number, issue):
    html(f"""
    <div class="issue-card">
        <span class="issue-number">
            {number}
        </span>
        {issue}
    </div>
    """)


def status_label(issues):
    return "PASS" if len(issues) == 0 else "REVIEW REQUIRED"


# ============================================================
# REPORT
# ============================================================

def build_text_report(result, file_name):
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
        lines.append("No validation issues were detected.")
    else:
        for index, issue in enumerate(result["issues"], start=1):
            lines.append(f"{index}. {issue}")

    return "\n".join(lines)


# ============================================================
# PDF PROCESSING
# ============================================================

def process_pdf(pdf_bytes, progress_bar=None, progress_text=None):
    pdf_document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    images = []
    all_page_text = []
    total_pages = len(pdf_document)

    for page_number in range(total_pages):
        if progress_text:
            progress_text.write(
                f"Reading page {page_number + 1} of {total_pages}..."
            )

        page = pdf_document.load_page(page_number)

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2)
        )

        image = Image.open(
            io.BytesIO(pix.tobytes("png"))
        )

        images.append(image.copy())

        extracted_text = pytesseract.image_to_string(image)
        all_page_text.append(extracted_text)

        if progress_bar:
            progress_bar.progress((page_number + 1) / total_pages)

    page_count = len(pdf_document)
    pdf_document.close()

    return page_count, images, all_page_text


# ============================================================
# ANALYSIS
# ============================================================

def analyze_document(all_page_text, status_box=None):
    full_text = "\n\n".join(all_page_text)

    if status_box:
        status_box.write("1. Identifying document type...")

    form_type, remaining = ask_gemini(
        detection_prompt(all_page_text[0])
    )

    form_type = form_type.strip().upper()

    if "DISCARD" in form_type:
        form_type = "DISCARD_FORM"
    elif "LOT" in form_type:
        form_type = "LOT_LOG"
    elif "QS-F-049" in form_type:
        form_type = "QS-F-049"
    elif "MP-F-023" in form_type:
        form_type = "MP-F-023"
    else:
        raise ValueError("Unable to identify document type.")

    if status_box:
        status_box.write(f"2. Detected {form_type}")
        status_box.write("3. Extracting structured fields...")

    if form_type == "LOT_LOG":
        extracted_data, remaining = ask_gemini(
            lot_log_prompt(full_text),
            response_schema=LOT_LOG_SCHEMA
        )
        issues = validate_lot_log(extracted_data)

    elif form_type == "QS-F-049":
        extracted_data, remaining = ask_gemini(
            qs_prompt(full_text),
            response_schema=QS_SCHEMA
        )
        issues = validate_qs_f_049(extracted_data)

    elif form_type == "MP-F-023":
        extracted_data, remaining = ask_gemini(
            mp_prompt(full_text),
            response_schema=MP_SCHEMA
        )
        issues = validate_mp_f_023(extracted_data)

    else:
        extracted_data, remaining = ask_gemini(
            discard_prompt(full_text),
            response_schema=DISCARD_SCHEMA
        )
        issues = validate_discard_form(extracted_data)

    if status_box:
        status_box.write("4. Applying validation rules...")
        status_box.write("5. Review complete.")

    return {
        "form_type": form_type,
        "extracted_data": extracted_data,
        "issues": issues,
        "remaining": remaining,
        "ocr_text": full_text
    }


# ============================================================
# RESET
# ============================================================

def reset_app():
    for key in defaults:
        if key in st.session_state:
            del st.session_state[key]


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

    uploaded_file = st.file_uploader(
        "Upload RegenMed PDF",
        type=["pdf"]
    )

    control_left, control_right = st.columns([1, 2])

    with control_left:
        if st.button(
            "Clear Review",
            use_container_width=True
        ):
            reset_app()
            st.rerun()

    with control_right:
        st.caption(
            "MP-F-023 • QS-F-049 • Lot Logs • Discard Forms"
        )

    if uploaded_file is not None:

        current_file_id = f"{uploaded_file.name}-{uploaded_file.size}"

        if st.session_state.last_processed_file != current_file_id:
            pdf_bytes = uploaded_file.getvalue()

            with st.status(
                "Preparing document...",
                expanded=True
            ) as prep_status:

                progress_text = st.empty()
                progress_bar = st.progress(0)

                page_count, images, all_page_text = process_pdf(
                    pdf_bytes,
                    progress_bar,
                    progress_text
                )

                progress_text.write("OCR processing complete.")
                progress_bar.progress(1.0)

                prep_status.update(
                    label="Document ready",
                    state="complete",
                    expanded=False
                )

            st.session_state.images = images
            st.session_state.file_name = uploaded_file.name
            st.session_state.page_count = page_count
            st.session_state.file_size_kb = uploaded_file.size / 1024
            st.session_state.all_page_text = all_page_text
            st.session_state.analysis_result = None
            st.session_state.last_processed_file = current_file_id

        html("""
        <div class="section-title">
            Document Information
        </div>
        """)

        render_metric_card(
            "File Name",
            st.session_state.file_name
        )

        info1, info2 = st.columns(2)

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

        if st.button(
            "Analyze Document",
            type="primary",
            use_container_width=True
        ):

            loader_placeholder = st.empty()

            loader_placeholder.markdown(
                """
                <div class="ai-loader">
                    <span class="loader-dot"></span>
                    <span class="loader-dot"></span>
                    <span class="loader-dot"></span>
                    &nbsp; AI reviewing document...
                </div>
                """.replace("\n", ""),
                unsafe_allow_html=True
            )

            try:
                with st.status(
                    "AI review in progress...",
                    expanded=True
                ) as analysis_status:

                    result = analyze_document(
                        st.session_state.all_page_text,
                        analysis_status
                    )

                    analysis_status.update(
                        label="Analysis complete",
                        state="complete",
                        expanded=False
                    )

                st.session_state.analysis_result = result

            except Exception as error:
                st.session_state.analysis_result = {
                    "error": str(error)
                }

            finally:
                loader_placeholder.empty()

    else:
        st.info("Upload a RegenMed PDF to begin.")

    result = st.session_state.analysis_result

    if result is not None:
        if "error" in result:
            st.error(f"Analysis failed: {result['error']}")

        else:
            html("""
            <div class="section-title">
                Review Summary
            </div>
            """)

            kpi1, kpi2, kpi3 = st.columns(3)

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
                chip = (
                    '<span class="pass-chip">PASS</span>'
                    if not result["issues"]
                    else '<span class="review-chip">REVIEW</span>'
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

            html("""
            <div class="section-title">
                Validation Findings
            </div>
            """)

            if not result["issues"]:
                st.success("No validation issues detected.")
            else:
                for index, issue in enumerate(result["issues"], start=1):
                    render_issue_card(index, issue)

            report = build_text_report(
                result,
                st.session_state.file_name
            )

            st.download_button(
                "Download Review Report",
                report,
                file_name="regenmed_review_report.txt",
                mime="text/plain",
                use_container_width=True
            )

            with st.expander("Developer / Audit Details"):
                tab1, tab2 = st.tabs(
                    ["Structured Extraction", "Raw OCR"]
                )

                with tab1:
                    st.json(result["extracted_data"])

                with tab2:
                    st.text(result["ocr_text"])

            st.caption(
                f"API requests remaining: {result['remaining']}"
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
                {st.session_state.page_count} page(s)
                &nbsp; • &nbsp;
                {st.session_state.file_size_kb:.2f} KB
            </div>
        </div>
        """)

        page_tabs = st.tabs(
            [
                f"Page {index + 1}"
                for index in range(
                    len(st.session_state.images)
                )
            ]
        )

        for index, tab in enumerate(page_tabs):
            with tab:
                st.image(
                    st.session_state.images[index],
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