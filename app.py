import io
import fitz
import pytesseract
import streamlit as st
from PIL import Image
from validators.lot_log import validate_lot_log

from services.hackathon_api import ask_gemini


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


st.set_page_config(
    page_title="RegenMed Document Reviewer",
    page_icon="📄",
    layout="wide"
)


st.title("RegenMed Internal Document Reviewer")
st.write("Upload a RegenMed PDF form for analysis.")


uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    st.success("PDF uploaded successfully.")

    st.write("### File Information")
    st.write(f"File name: {uploaded_file.name}")
    st.write(f"File size: {uploaded_file.size / 1024:.2f} KB")

    pdf_bytes = uploaded_file.read()

    pdf_document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    st.write(f"Number of pages: {len(pdf_document)}")

    all_page_text = []

    st.write("### PDF Preview")

    for page_number in range(len(pdf_document)):

        page = pdf_document.load_page(page_number)

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2)
        )

        image_bytes = pix.tobytes("png")

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        extracted_text = pytesseract.image_to_string(image)

        all_page_text.append(extracted_text)

        st.write(f"Page {page_number + 1}")

        st.image(
            image,
            use_container_width=True
        )


    st.write("### Document Analysis")

    if st.button("Analyze Document"):

        first_page_text = all_page_text[0]

        # -----------------------------
        # STEP 1: Detect form type
        # -----------------------------

        detection_prompt = f"""
You are classifying a RegenMed document.

The document must be exactly one of:

MP-F-023
QS-F-049
LOT_LOG

Important:
- Processing or packaging lot logs should be LOT_LOG.
- OCR may contain mistakes.
- Use the title, headings, and structure.

OCR TEXT:

{first_page_text}

Return only one exact value:

MP-F-023
QS-F-049
LOT_LOG
"""

        with st.spinner("Detecting form type..."):

            form_type, remaining = ask_gemini(
                detection_prompt
            )

        form_type = form_type.strip()

        st.success(
            f"Detected Form Type: {form_type}"
        )


        # -----------------------------
        # STEP 2: Extract Lot Log data
        # -----------------------------

        if form_type == "LOT_LOG":

            full_text = "\n\n".join(all_page_text)

            lot_log_schema = {
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


            extraction_prompt = f"""
You are extracting structured information from a RegenMed Lot Log.

OCR text may contain mistakes because the original form contains handwriting.

Extract only the information requested by the JSON schema.

Important rules:

PAGE 1 ITEMS:
Extract rows from the Item table with:
- item
- lot_number
- exp_date
- manufacturer

REGENMED ITEMS:
Extract:
- item
- lot
- qty_used

PAGE 2 ITEMS:
Extract ONLY rows from the large item tables on Page 2 that contain:
- item
- load_number
- sterilization_date

DO NOT include rows from the Packaging table here.

PACKAGING:
Extract ONLY rows from the bottom-right table titled "Packaging".
These rows usually contain package sizes such as:
- 8x10
- 8x13
- 6.5x17
- 5x12
- 5x17

For Packaging extract:
- item
- lot
- qty_used

Never place Packaging rows inside page_2_items.

If a field appears blank, return an empty string "".

If the form explicitly says N/A, return "N/A".

Do not invent missing values.

OCR TEXT:

{full_text}
"""

            with st.spinner(
                "Extracting document fields..."
            ):

                extracted_data, remaining = ask_gemini(
                    extraction_prompt,
                    response_schema=lot_log_schema
                )


            st.write("### Extracted Structured Data")

            st.json(extracted_data)

            # -----------------------------
            # STEP 3: Validate Lot Log
            # -----------------------------

            issues = validate_lot_log(extracted_data)

            st.write("### Validation Result")

            if not issues:

                st.success(
                    "Document passed all required Lot Log checks."
                )

            else:

                st.error(
                    f"{len(issues)} issue(s) found."
                )

                for number, issue in enumerate(
                    issues,
                    start=1
                ):
                    st.write(
                        f"{number}. {issue}"
                    )

            st.caption(
                f"API requests remaining: {remaining}"
            )