from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pdf_service import save_and_process_pdfs, answer_question, list_available_pdfs
from models.models import UploadResponse, AnswerResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse, tags=["PDF"])
async def upload_pdfs(files: list[UploadFile] = File(...)):
    if len(files) > 2:
        raise HTTPException(status_code=400, detail="Maximum 2 PDFs allowed.")
    return await save_and_process_pdfs(files)

@router.get("/ask", response_model=AnswerResponse, tags=["QA"])
async def ask(q: str = Query(..., description="Your question")):
    return await answer_question(q)

@router.get("/pdf/list", tags=["PDF"])
def list_pdfs():
    return list_available_pdfs()
