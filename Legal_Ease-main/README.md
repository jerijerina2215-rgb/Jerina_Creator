# LegalEase

>A prototype for generating professional legal documents using a FastAPI backend, Gemini AI generator (with mock fallback), and a Streamlit frontend. Exports supported: PDF (branded), DOCX, TXT.

## Features
- FastAPI backend with `/generate` and `/export/{format}` endpoints
- `ai_core.GeminiDocumentGenerator` with real API call + robust mock fallback
- Streamlit frontend for drafting, editing and previewing generated documents
- Multi-format exports: `.pdf` (logo, title, table, footer/page numbers), `.docx`, `.txt`

## Prerequisites
- Python 3.10+ (project tested with 3.11/3.13)
- Git (optional)

## Setup (Windows PowerShell)
1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the repo root (copy `.env.example` if present) and set:

- `GEMINI_API_KEY` — your Gemini API key (optional; a mock is used when missing)
- `GEMINI_PROJECT` — optional project name
- `FASTAPI_HOST` — default `127.0.0.1`
- `FASTAPI_PORT` — default `8000`
- `DEBUG` — `true` or `false`

Security note: do NOT commit real API keys to the repository. Rotate any keys that were accidentally committed.

## Running locally

Start the backend (FastAPI + Uvicorn):

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the Streamlit frontend (in a separate terminal with the venv active):

```powershell
python -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```

Open the Streamlit UI at `http://127.0.0.1:8501` and the FastAPI docs at `http://127.0.0.1:8000/docs`.

## Using the Web UI

1. Open `http://127.0.0.1:8501` in your browser after starting the Streamlit app.
2. At the top you'll see a logo and the app title. Fill the form fields on the left or main panel:
  - **Document type**: select the template type (e.g., employment agreement).
  - **Parties**: add one or more parties (names and optional roles).
  - **Effective date / Jurisdiction**: fill as needed.
  - **Custom clauses**: add additional clauses to include in the draft.
  - **Key terms**: add short key-terms and definitions that will be shown in the PDF Summary Terms table.
3. Click the **Generate** button. The app will call the backend `/generate` endpoint and return a Markdown draft.
4. The generated draft appears in the editable preview area. Edit text directly in the preview to tweak language.
5. When ready, use the export buttons to download the document in your desired format:
  - **Download PDF**: Sends the current Markdown and payload to `POST /export/pdf`. To embed a logo in the PDF, place an image at `assets/logo.png` or provide an absolute `logo_path` in the payload.
  - **Download DOCX**: Produces a `.docx` with Times New Roman formatting.
  - **Download TXT**: Simple plaintext export.
6. If you want to regenerate after editing, press **Generate** again or paste a new prompt into the preview and export.

Tips:
- Use the editable preview to ensure exact phrasing before exporting—exports use the preview text as-is.
- For multi-page PDFs, the footer will include page numbers and a confidentiality label automatically.
- If the UI seems unresponsive, confirm the backend is running at `http://127.0.0.1:8000` and check browser dev tools for network errors.


## API usage

1) Generate a document (returns Markdown):

```bash
curl -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "employment_agreement",
    "parties": [{"name":"Alice"},{"name":"Bob"}],
    "effective_date": "2026-01-01",
    "jurisdiction": "CA",
    "custom_clauses": ["Non-compete for 12 months"],
    "key_terms": {"Term A":"Definition A","Term B":"Definition B"}
  }'
```

2) Export the generated markdown as PDF (server-side):

```bash
curl -X POST "http://127.0.0.1:8000/export/pdf" \
  -H "Content-Type: application/json" \
  -d '{ "markdown": "# Title\n\nBody...", "key_terms": {"Term":"Def"}, "logo_path": "assets/logo.png" }' --output exported.pdf
```

Supported formats: `txt`, `docx`, `pdf` — use the matching endpoint `POST /export/{format}`.

Notes:
- If you want a logo embedded in the PDF, place an image at `assets/logo.png` or pass an absolute `logo_path` in the payload.
- The PDF exporter extracts the H1 as the title, adds a Summary Terms table (from `key_terms`), and prints a footer with page numbers and a confidentiality label.

## Tests

Run unit tests with `pytest` (ensure venv active):

```powershell
pytest -q
```

There is also `tests/manual_test.py` for scripted API/manual checks — use it after starting the backend.

## Docker (optional)

Build and run using the included `Dockerfile` (image pins Python 3.11):

```bash
docker build -t legalease:latest .
docker run -p 8000:8000 --env-file .env legalease:latest
```

## Troubleshooting
- If a dependency fails to install on your Python version, create the venv with Python 3.11 (docker image uses 3.11).
- If Streamlit or Uvicorn fails to start, check the venv activation and `pip list` for installed packages.

## Next steps / Customization
- Hook a real Gemini API key into `.env` to use live model generation.
- Improve document styling templates for DOCX/PDF per your branding.
- Add richer unit and integration tests that verify exported document contents visually or via text assertions.

## Files of interest
- [app/exporter.py](app/exporter.py)
- [app/routes.py](app/routes.py)
- [ai_core/gemini_generator.py](ai_core/gemini_generator.py)
- [streamlit_app.py](streamlit_app.py)
- [tests/manual_test.py](tests/manual_test.py)

---
If you want, I can: add a sample `assets/logo.png`, run the manual export test, or update the README with deployment steps for a specific platform. Which would you like next?
# LegalEase — Generative AI Legal Document Generator

Minimal scaffold for LegalEase: a FastAPI backend that integrates with Google Gemini (placeholder), document export utilities, and a Streamlit frontend for interactive previews and downloads.

Getting started

1. Create a Python 3.10+ virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` if available.

4. Run the FastAPI backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Run the Streamlit UI:

```bash
streamlit run streamlit_app.py
```

Notes
- The Gemini integration in `app/generator.py` is a thin wrapper. If you provide a `GEMINI_API_KEY` and the `google-generativeai` package, the wrapper will try to call Gemini; otherwise it returns a deterministic mocked contract for development and testing.
