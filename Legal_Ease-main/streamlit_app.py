import os
import re
from datetime import date
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError


DEFAULT_API_URL = "http://localhost:8000"
PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


def get_api_url():
    api_url = os.getenv("API_URL")
    if api_url:
        return api_url

    try:
        return st.secrets.get("API_URL", DEFAULT_API_URL)
    except StreamlitSecretNotFoundError:
        return DEFAULT_API_URL


API_URL = get_api_url()

st.set_page_config(page_title="LegalEase", page_icon="L", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background: #0d0f16; color: #f4f4f5; }
    [data-testid="stHeader"] { background: #0d0f16; }
    .block-container { max-width: 720px; padding-top: 2rem; padding-bottom: 4rem; }
    .brand { text-align: center; margin: 1rem 0 2rem; }
    .brand img { width: 120px; height: auto; margin-bottom: .5rem; }
    .brand h1 { font-size: 1.45rem; margin: 0; color: #f4f4f5; }
    label, .stMarkdown p { color: #e5e7eb !important; }
    input, textarea { background: #262631 !important; color: #f4f4f5 !important; }
    .stButton button, .stDownloadButton button { border-color: #414452; color: #f4f4f5; }
    .preview { background: #111827; border-radius: 6px; padding: 1rem 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = PROJECT_DIR / "assets" / "logo.png"
if logo_path.exists():
    logo = str(logo_path)
else:
    logo = None

st.markdown('<div class="brand">', unsafe_allow_html=True)
if logo:
    st.image(logo, width=120)
st.markdown("<h1>AI Legal Document Generator</h1></div>", unsafe_allow_html=True)

with st.form("document_form"):
    document_type = st.text_input(
        "Document Type (Ex: Agreement, Contract, NDA)",
        placeholder="Freelance Work Contract",
    )
    parties = st.text_area(
        "Parties Involved",
        placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)",
        height=84,
    )
    terms = st.text_area(
        "Terms & Conditions (Use semicolons for bullet points)",
        placeholder="Payment within 30 days; Confidentiality must be maintained",
        height=100,
    )
    effective_date = st.date_input("Effective Date", value=date.today())
    submitted = st.form_submit_button("Generate Document")

if submitted:
    party_entries = [item.strip() for item in parties.split(",") if item.strip()]

    def parse_party(entry, fallback_name, fallback_role):
        match = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", entry)
        if match:
            return {"name": match.group(1).strip(), "role": match.group(2).strip()}
        return {"name": entry or fallback_name, "role": fallback_role}

    party_a = parse_party(
        party_entries[0] if party_entries else "", "Party A", "Party A"
    )
    party_b = parse_party(
        party_entries[1] if len(party_entries) > 1 else "", "Party B", "Party B"
    )
    payload = {
        "document_type": document_type.strip() or "Agreement",
        "party_a": party_a,
        "party_b": party_b,
        "effective_date": effective_date.isoformat(),
        "jurisdiction": "",
        "custom_clauses": terms.strip(),
    }
    with st.spinner("Generating document..."):
        try:
            response = requests.post(f"{API_URL}/generate", json=payload, timeout=30)
            if response.status_code == 422:
                st.error(f"Invalid document details: {response.text}")
                st.stop()
            response.raise_for_status()
        except requests.RequestException as error:
            st.error(f"Could not reach the LegalEase API at {API_URL}: {error}")
            st.stop()
    st.session_state["payload"] = payload
    st.session_state["document"] = response.json().get("markdown", "")
    st.session_state["editing"] = False

document = st.session_state.get("document")
if document:
    st.success("Document Generated Successfully!")
    st.markdown('<div class="preview">', unsafe_allow_html=True)
    st.markdown(document)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Click to Edit Document"):
        st.session_state["editing"] = True

    if st.session_state.get("editing"):
        edited_document = st.text_area(
            "Edit Document Below:",
            value=document,
            height=360,
            key="edited_document",
        )
        if st.button("Apply Changes"):
            st.session_state["document"] = edited_document
            st.session_state["editing"] = False
            st.rerun()

    export_payload = {**st.session_state["payload"], "markdown": st.session_state["document"]}
    columns = st.columns(3)
    export_details = (
        ("txt", "Download as .TXT", "text/plain"),
        ("docx", "Download as .DOCX", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("pdf", "Download as .PDF", "application/pdf"),
    )
    for column, (extension, label, mime) in zip(columns, export_details):
        with column:
            try:
                export_response = requests.post(
                    f"{API_URL}/export/{extension}",
                    json=export_payload,
                    timeout=60,
                )
                export_response.raise_for_status()
                st.download_button(
                    label,
                    data=export_response.content,
                    file_name=f"legalease_document.{extension}",
                    mime=mime,
                    key=f"download_{extension}",
                )
            except requests.RequestException as error:
                st.error(f"{extension.upper()} export failed: {error}")
