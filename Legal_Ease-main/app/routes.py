from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from .schemas import DocumentRequest
from .generator import generate_document
from .exporter import to_pdf, to_docx, to_txt
from io import BytesIO

router = APIRouter()


def request_payload(req: DocumentRequest):
    return req.model_dump() if hasattr(req, "model_dump") else req.dict()


@router.post("/generate")
async def generate(req: DocumentRequest):
    try:
        payload = request_payload(req)
        md = generate_document(payload)
        return JSONResponse({"markdown": md})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{format}")
async def export(req: DocumentRequest, format: str):
    payload = request_payload(req)
    md = payload.get("markdown") or generate_document(payload)
    if format.lower() == "txt":
        data = to_txt(md)
        return StreamingResponse(BytesIO(data), media_type="text/plain", headers={"Content-Disposition": "attachment; filename=document.txt"})
    if format.lower() == "docx":
        data = to_docx(md, payload)
        return StreamingResponse(BytesIO(data), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=document.docx"})
    if format.lower() == "pdf":
        data = to_pdf(md, payload)
        return StreamingResponse(BytesIO(data), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=document.pdf"})
    raise HTTPException(status_code=400, detail="Unsupported format")
