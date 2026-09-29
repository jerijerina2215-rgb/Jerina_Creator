from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from fpdf import FPDF
import re
import os
from pathlib import Path
from typing import Optional


PROJECT_DIR = Path(__file__).resolve().parent.parent


def to_txt(markdown_text: str) -> bytes:
    return markdown_text.encode("utf-8")


def _logo_path() -> Optional[str]:
    for candidate in (
        PROJECT_DIR / "assets" / "logo.png",
        PROJECT_DIR / "assets" / "logo.jpg",
        PROJECT_DIR / "logo.png",
        PROJECT_DIR / "logo.jpg",
    ):
        if candidate.exists():
            return str(candidate)
    return None


def _md_to_paragraphs(md: str):
    # very small markdown -> paragraphs helper
    lines = [l.rstrip() for l in md.splitlines()]
    paras = []
    buf = []
    for ln in lines:
        if ln.strip() == "":
            if buf:
                paras.append(" ".join(buf))
                buf = []
        else:
            buf.append(ln)
    if buf:
        paras.append(" ".join(buf))
    return paras


def _pdf_text(value: str) -> str:
    value = re.sub(r"[*`_]", "", value)
    value = value.replace("---", "")
    value = value.encode("latin-1", errors="replace").decode("latin-1")
    return re.sub(r"(\S{80})(?=\S)", r"\1 ", value)


def to_docx(markdown_text: str, payload: dict = None) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    section = doc.sections[0]
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.LEFT
    logo_path = _logo_path()
    if logo_path:
        header.add_run().add_picture(logo_path, width=Inches(1.35))

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("LegalEase Inc. | contact@legalease.com | All Rights Reserved.").font.size = Pt(8)

    # Title if present
    m = re.match(r"^#\s*(.+)$", markdown_text.strip())
    if m:
        title = doc.add_heading(m.group(1), level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].font.color.rgb = RGBColor(31, 78, 121)

    for line in markdown_text.splitlines():
        line = line.strip()
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif re.match(r"^\d+\.\s+", line):
            doc.add_paragraph(re.sub(r"^\d+\.\s+", "", line), style="List Number")
        else:
            doc.add_paragraph(line)

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()


class _PDF(FPDF):
    def __init__(self, logo_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_path = logo_path

    def header(self):
        # draw logo if available, otherwise title text
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # place logo centered at top
                self.image(self.logo_path, x=80, y=6, w=50)
                self.ln(30)
            except Exception:
                self.set_font("Arial", "B", 14)
                self.cell(0, 10, "LegalEase", ln=True, align="C")
        else:
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, "LegalEase", ln=True, align="C")

    def footer(self):
        # page number and small footer text
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")
        self.ln(3)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, "LegalEase - Confidential", align="C")


def to_pdf(markdown_text: str, payload: dict = None) -> bytes:
    payload = payload or {}
    # determine logo path: payload override -> common asset locations
    logo_path = payload.get("logo_path") or _logo_path()

    pdf = _PDF(logo_path=logo_path)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title: use first markdown H1 if present
    title = None
    for line in markdown_text.splitlines():
        m = re.match(r"^#\s*(.+)", line)
        if m:
            title = m.group(1).strip()
            break

    def _safe(s: str) -> str:
        if s is None:
            return ""
        if not isinstance(s, str):
            s = str(s)
        return s.encode("latin-1", errors="replace").decode("latin-1")

    if title:
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, _pdf_text(title), ln=True, align="C")
        pdf.ln(4)

    pdf.set_font("Arial", size=11)

    # Render a Summary Terms table if provided
    terms = payload.get("key_terms") or {}
    if isinstance(terms, dict) and terms:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, _pdf_text("Summary Terms"), ln=True)
        pdf.set_font("Arial", size=10)
        # simple key: value rows
        for k, v in terms.items():
            pdf.multi_cell(0, 6, _pdf_text(f"{k}: {v}"))
        pdf.ln(4)

    # Render markdown blocks while preserving headings and list formatting.
    for line in markdown_text.splitlines():
        line = line.strip()
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 7, _pdf_text(line[3:]))
            pdf.ln(1)
            pdf.set_font("Arial", size=11)
        elif line.startswith("- "):
            pdf.multi_cell(0, 6, _pdf_text("- " + line[2:]))
            pdf.ln(1)
        elif re.match(r"^\d+\.\s+", line):
            pdf.multi_cell(0, 6, _pdf_text(line))
            pdf.ln(1)
        else:
            pdf.multi_cell(0, 6, _pdf_text(line))
            pdf.ln(1)

    # ensure footer text is latin-safe
    pdf.footer = lambda self=pdf: None  # temporarily disable default footer
    # reattach footer using latin-safe strings
    def _footer():
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, _safe(f"Page {pdf.page_no()}"), align="R")
        pdf.ln(3)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, _safe("LegalEase - Confidential"), align="C")

    # monkeypatch footer method
    _PDF.footer = lambda self: _footer()

    return pdf.output(dest="S").encode("latin-1", errors="replace")
