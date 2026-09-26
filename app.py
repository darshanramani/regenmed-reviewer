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
# HTML HELPER
# ============================================================

def html(content):

    cleaned = (
        textwrap
        .dedent(content)
        .strip()
    )

    if hasattr(
        st,
        "html"
    ):
        st.html(
            cleaned
        )

    else:

        st.markdown(
            cleaned.replace(
                "\n",
                ""
            ),
            unsafe_allow_html=True
        )


# ============================================================
# CSS
# ============================================================

html("""
<style>

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1800px;
}

.hero-box {
    padding: 1.5rem 1.7rem;
    border-radius: 18px;
    background:
        linear-gradient(
            135deg,
            #0f172a 0%,
            #172554 50%,
            #1e293b 100%
        );
    border: 1px solid rgba(96,165,250,0.22);
    box-shadow: 0 12px 35px rgba(0,0,0,0.20);
    margin-bottom: 1.5rem;
}

.app-brand {
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.14rem;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 0.45rem;
}

.hero-title {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.4rem;
}

.hero-subtitle {
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.6;
    max-width: 1000px;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 750;
    color: #e2e8f0;
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
}

.metric-card {
    background: #111827;
    border: 1px solid rgba(148,163,184,0.16);
    padding: 0.85rem 1rem;
    border-radius: 13px;
    margin-bottom: 0.65rem;
}

.metric-label {
    font-size: 0.70rem;
    color: #94a3b8;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.05rem;
}

.metric-value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f8fafc;
    word-break: break-word;
}

.kpi-card {
    background:
        linear-gradient(
            145deg,
            rgba(30,41,59,0.98),
            rgba(15,23,42,0.98)
        );
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 14px;
    padding: 1rem;
    min-height: 100px;
}

.kpi-title {
    color: #94a3b8;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05rem;
}

.kpi-number {
    color: #f8fafc;
    font-size: 1.22rem;
    font-weight: 800;
    margin-top: 0.5rem;
}

.pass-chip {
    display: inline-block;
    background: rgba(34,197,94,0.14);
    border: 1px solid rgba(34,197,94,0.42);
    color: #86efac;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
}

.review-chip {
    display: inline-block;
    background: rgba(239,68,68,0.14);
    border: 1px solid rgba(239,68,68,0.42);
    color: #fca5a5;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
}

.status-pass {
    background: rgba(34,197,94,0.10);
    border: 1px solid rgba(34,197,94,0.35);
    color: #86efac;
    padding: 0.9rem 1rem;
    border-radius: 12px;
    font-weight: 700;
    margin-top: 0.8rem;
    margin-bottom: 1rem;
}

.status-fail {
    background: rgba(239,68,68,0.10);
    border: 1px solid rgba(239,68,68,0.35);
    color: #fca5a5;
    padding: 0.9rem 1rem;
    border-radius: 12px;
    font-weight: 700;
    margin-top: 0.8rem;
    margin-bottom: 1rem;
}

.issue-card {
    background: #0f172a;
    border: 1px solid rgba(239,68,68,0.22);
    border-left: 4px solid #ef4444;
    padding: 0.82rem 0.95rem;
    border-radius: 11px;
    margin-bottom: 0.58rem;
    color: #e5e7eb;
    line-height: 1.5;
}

.issue-number {
    display: inline-flex;
    width: 24px;
    height: 24px;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: rgba(239,68,68,0.15);
    color: #fca5a5;
    font-size: 0.75rem;
    font-weight: 800;
    margin-right: 0.45rem;
}

.preview-header {
    padding: 0.75rem 1rem;
    background: #111827;
    border: 1px solid rgba(148,163,184,0.15);
    border-radius: 12px;
    margin-bottom: 0.8rem;
}

.preview-file {
    color: #f8fafc;
    font-weight: 700;
    font-size: 0.90rem;
}

.preview-meta {
    color: #94a3b8;
    font-size: 0.76rem;
    margin-top: 0.2rem;
}

.empty-preview {
    border: 1px dashed rgba(148,163,184,0.35);
    border-radius: 16px;
    padding: 6rem 1rem;
    text-align: center;
    color: #94a3b8;
    background: rgba(15,23,42,0.25);
}

.empty-preview-icon {
    font-size: 2rem;
    margin-bottom: 0.7rem;
}

.divider-space {
    margin-top: 1rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""")


# ============================================================
# LOT LOG SCHEMA
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


# ============================================================
# QS SCHEMA
# ============================================================

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


# ============================================================
# MP-F-023 SCHEMA
# ============================================================

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


# ============================================================
# DISCARD FORM SCHEMA
# ============================================================

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
# DETECTION PROMPT
# ============================================================

def detection_prompt(text):

    return f"""
Identify this RegenMed document.

Possible document types:

MP-F-023
QS-F-049
LOT_LOG
DISCARD_FORM


DISCARD_FORM means a Tissue Discard Form.

LOT_LOG means a Processing or Packaging Lot Log.

OCR may contain mistakes.

Use:

- title
- headings
- field labels
- table structure
- footer information


OCR TEXT:

{text}


Return ONLY one exact value:

MP-F-023
QS-F-049
LOT_LOG
DISCARD_FORM
"""


# ============================================================
# LOT LOG PROMPT
# ============================================================

def lot_log_prompt(text):

    return f"""
Extract structured information from this RegenMed Lot Log.

OCR may contain errors.

Do not intentionally invent values.

If clearly blank return "".

If N/A explicitly appears return "N/A".


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


PAGE 2 PACKAGING TABLE:

item
lot
qty_used


Do not intentionally place Packaging rows
inside page_2_items.


OCR TEXT:

{text}
"""


# ============================================================
# QS PROMPT
# ============================================================

def qs_prompt(text):

    return f"""
Extract structured information from RegenMed QS-F-049.

Extract every numbered Technical and Quality review row.

Return:

item

technical_initials
technical_date
technical_na

quality_initials
quality_date
quality_na


technical_na is true only when explicitly N/A.

quality_na is true only when explicitly N/A.


Also extract Item 10:

inc_number
status


Do not intentionally invent missing values.


OCR TEXT:

{text}
"""


# ============================================================
# MP PROMPT
# ============================================================

def mp_prompt(text):

    return f"""
Extract structured information from RegenMed MP-F-023.

TOP SECTION:

Extract fields from Donor # through
Tissue Checked In By/Date.


Normal fields go into:

top_fields


By/Date fields go into:

by_date_fields


OPERATIONS MANAGER REVIEW:

initials
date


PROCESSING TABLE:

Extract relevant rows involving:

# Produced
# Packaged


Return:

item
produced
packaged
required_field


required_field must be:

produced

or

packaged


If information cannot be read return "".

Do not intentionally invent values.


OCR TEXT:

{text}
"""


# ============================================================
# DISCARD FORM PROMPT
# ============================================================

def discard_prompt(text):

    return f"""
Extract structured information from a RegenMed Tissue Discard Form.

OCR may contain handwriting errors.

Do not intentionally invent values.

If information cannot be read, return "".


TOP SECTION

Extract:

donor_number

discard_authorized_by

discard_authorized_date

reason_for_discard


TISSUE STATUS

Determine which checkbox is visibly checked.

Return booleans for:

unprocessed_tissue

in_processing_tissue

unreleased_packaged_tissue

released_packaged_tissue


Only set a value true if the box appears selected.


TISSUE TABLE

Extract only rows that actually contain tissue information.

For each row return:

graft_id

tissue_description

storage_location

confirmed_x


confirmed_x must be true only when the small right-side X box
for that listed tissue appears completed.


BOTTOM SECTION

Extract:

tissue_discarded_by

confirmed_by

discard_date

freezerpro_updated_by

freezerpro_updated_date

donor_chart_updated_by

donor_chart_updated_date


If a field explicitly says N/A, return "N/A".

Do not convert blank fields to N/A.


OCR TEXT:

{text}
"""


# ============================================================
# HELPERS
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

    if len(issues) == 0:

        return "PASS"

    return "REVIEW REQUIRED"


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


    lines.extend([

        "",

        "-" * 55,

        "",

        (
            "This report is intended to assist "
            "human document review."
        ),

        (
            "Final quality review remains with "
            "authorized personnel."
        )
    ])


    return "\n".join(
        lines
    )


# ============================================================
# PDF PROCESSING
# ============================================================

def process_pdf(
    pdf_bytes
):

    pdf_document = fitz.open(

        stream=pdf_bytes,

        filetype="pdf"
    )


    images = []

    all_page_text = []


    for page_number in range(
        len(pdf_document)
    ):


        page = (
            pdf_document
            .load_page(
                page_number
            )
        )


        pix = page.get_pixmap(

            matrix=fitz.Matrix(
                2,
                2
            )
        )


        image_bytes = (
            pix.tobytes(
                "png"
            )
        )


        image = Image.open(

            io.BytesIO(
                image_bytes
            )
        )


        images.append(
            image.copy()
        )


        extracted_text = (

            pytesseract
            .image_to_string(
                image
            )
        )


        all_page_text.append(
            extracted_text
        )


    page_count = len(
        pdf_document
    )


    pdf_document.close()


    return (

        page_count,

        images,

        all_page_text
    )


# ============================================================
# ANALYSIS
# ============================================================

def analyze_document(
    all_page_text
):


    if not all_page_text:

        raise ValueError(
            "No document text was extracted."
        )


    full_text = "\n\n".join(
        all_page_text
    )


    # ========================================================
    # FORM DETECTION
    # ========================================================

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


    if (
        "DISCARD"
        in form_type
    ):

        form_type = (
            "DISCARD_FORM"
        )


    elif (
        "LOT"
        in form_type
    ):

        form_type = (
            "LOT_LOG"
        )


    elif (
        "QS-F-049"
        in form_type
    ):

        form_type = (
            "QS-F-049"
        )


    elif (
        "MP-F-023"
        in form_type
    ):

        form_type = (
            "MP-F-023"
        )


    else:

        raise ValueError(
            "Unable to identify document type."
        )


    extracted_data = {}

    issues = []


    # ========================================================
    # LOT LOG
    # ========================================================

    if (
        form_type
        == "LOT_LOG"
    ):


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


    # ========================================================
    # QS
    # ========================================================

    elif (
        form_type
        == "QS-F-049"
    ):


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


    # ========================================================
    # MP-F-023
    # ========================================================

    elif (
        form_type
        == "MP-F-023"
    ):


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


    # ========================================================
    # DISCARD FORM
    # ========================================================

    elif (
        form_type
        == "DISCARD_FORM"
    ):


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


    return {

        "form_type": (
            form_type
        ),

        "extracted_data": (
            extracted_data
        ),

        "issues": (
            issues
        ),

        "remaining": (
            remaining
        ),

        "ocr_text": (
            full_text
        )
    }


# ============================================================
# RESET
# ============================================================

def reset_app():

    keys = [

        "analysis_result",

        "images",

        "file_name",

        "page_count",

        "file_size_kb",

        "last_processed_file",

        "all_page_text"
    ]


    for key in keys:

        if (
            key
            in st.session_state
        ):

            del st.session_state[
                key
            ]


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

    "all_page_text": []
}


for key, value in (
    defaults.items()
):


    if (
        key
        not in st.session_state
    ):

        st.session_state[
            key
        ] = value


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

</div>
""")


# ============================================================
# TWO COLUMN UI
# ============================================================

left_col, right_col = (
    st.columns(
        [1, 1.35],
        gap="large"
    )
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


    uploaded_file = (
        st.file_uploader(

            "Upload RegenMed PDF",

            type=[
                "pdf"
            ]
        )
    )


    control_col1, control_col2 = (
        st.columns(
            [1, 2]
        )
    )


    with control_col1:


        if st.button(

            "Clear Review",

            use_container_width=True
        ):


            reset_app()

            st.rerun()


    with control_col2:


        st.caption(

            "Supported: MP-F-023 • QS-F-049 • Lot Logs • Discard Forms"
        )


    # ========================================================
    # PROCESS UPLOAD
    # ========================================================

    if (
        uploaded_file
        is not None
    ):


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
                "Preparing document..."
            ):


                (

                    page_count,

                    images,

                    all_page_text

                ) = process_pdf(
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


            st.session_state.all_page_text = (
                all_page_text
            )


            st.session_state.analysis_result = (
                None
            )


            st.session_state.last_processed_file = (
                current_file_id
            )


        # ====================================================
        # DOCUMENT INFORMATION
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


        meta_col1, meta_col2 = (

            st.columns(
                2
            )
        )


        with meta_col1:


            render_metric_card(

                "Pages",

                st.session_state.page_count
            )


        with meta_col2:


            render_metric_card(

                "File Size",

                f"{st.session_state.file_size_kb:.2f} KB"
            )


        # ====================================================
        # ANALYZE
        # ====================================================

        if st.button(

            "Analyze Document",

            type="primary",

            use_container_width=True
        ):


            try:


                with st.spinner(
                    "Analyzing document..."
                ):


                    result = (
                        analyze_document(

                            st.session_state
                            .all_page_text
                        )
                    )


                st.session_state.analysis_result = (
                    result
                )


            except Exception as error:


                st.session_state.analysis_result = {

                    "error": str(
                        error
                    )
                }


    else:


        st.info(

            "Upload a RegenMed PDF to begin the review."
        )


    # ========================================================
    # RESULTS
    # ========================================================

    result = (
        st.session_state
        .analysis_result
    )


    if (
        result
        is not None
    ):


        html("""
        <div class="divider-space"></div>
        """)


        if (
            "error"
            in result
        ):


            st.error(

                f"Analysis failed: {result['error']}"
            )


        else:


            html("""
            <div class="section-title">
                Review Summary
            </div>
            """)


            kpi1, kpi2, kpi3 = (

                st.columns(
                    3
                )
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


                if (
                    len(
                        result["issues"]
                    )
                    == 0
                ):


                    status_html = (
                        '<span class="pass-chip">'
                        'PASS'
                        '</span>'
                    )


                else:


                    status_html = (
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
                        {status_html}
                    </div>

                </div>
                """)


            # =================================================
            # STATUS
            # =================================================

            if (
                len(
                    result["issues"]
                )
                == 0
            ):


                html("""
                <div class="status-pass">

                    ✓ Document passed all required
                    validation checks.

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


            if (
                len(
                    result["issues"]
                )
                == 0
            ):


                st.success(

                    "No validation issues detected."
                )


            else:


                st.caption(

                    "Compare each finding with the source document shown on the right."
                )


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

            report_text = (
                build_text_report(

                    result,

                    st.session_state
                    .file_name
                )
            )


            st.download_button(

                label=(
                    "Download Review Report"
                ),

                data=(
                    report_text
                ),

                file_name=(
                    "regenmed_review_report.txt"
                ),

                mime=(
                    "text/plain"
                ),

                use_container_width=True
            )


            # =================================================
            # AUDIT
            # =================================================

            with st.expander(

                "Developer / Audit Details"
            ):


                audit_tab1, audit_tab2 = (

                    st.tabs(
                        [
                            "Structured Extraction",
                            "Raw OCR"
                        ]
                    )
                )


                with audit_tab1:


                    st.json(

                        result[
                            "extracted_data"
                        ]
                    )


                with audit_tab2:


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


    if (
        st.session_state
        .images
    ):


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

                    st.session_state.images[
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
                No document loaded
            </strong>

            <br><br>

            Upload a RegenMed PDF from the
            review workspace to preview it here.

        </div>
        """)