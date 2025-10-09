from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pdf_service import save_and_process_pdfs, answer_question
from models.models import UploadResponse, AnswerResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse, tags=["PDF"])
async def upload_pdfs(files: list[UploadFile] = File(...)):
    if len(files) > 2:
        raise HTTPException(status_code=400, detail="Maximum 2 PDFs allowed.")
    return await save_and_process_pdfs(files)

@router.get("/ask", response_model=AnswerResponse, tags=["QA"])
def ask(q: str = Query(..., description="Your question")):
    return answer_question(q)
