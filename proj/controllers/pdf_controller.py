from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from services.pdf_service import save_and_process_pdfs, answer_question, list_available_pdfs, get_chunks_for_pdf
from models.models import UploadResponse, AnswerResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse, tags=["PDF"])
async def upload_pdfs(
    project_name: str = Query(..., description="Project namespace for this session"),
    files: list[UploadFile] = File(...)
):
    """
    Upload PDFs scoped to a unique project name.

    Args:
        project_name (str): Unique project name for session isolation.
        files (list[UploadFile]): Uploaded PDF files.

    Returns:
        dict: Confirmation message.
    """
    if len(files) > 2:
        raise HTTPException(status_code=400, detail="Maximum 2 PDFs allowed.")
    return await save_and_process_pdfs(files, project_name=project_name)

@router.get("/ask", response_model=AnswerResponse, tags=["QA"])
async def ask(
    q: str = Query(..., description="User question"),
    project_name: str = Query(..., description="Project to scope the query"),
    pdf_name: str | None = Query(None, description="Optional PDF scope")
):
    """
    Ask a question scoped to a project and optionally a PDF.

    Args:
        q (str): Question string.
        project_name (str): Project namespace.
        pdf_name (str | None): Optional PDF file name.

    Returns:
        dict: Answer and context chunks.
    """
    return await answer_question(q, project_name=project_name, pdf_name=pdf_name)


@router.get("/pdf/list", tags=["PDF"])
def list_pdfs(project_name: str = Query(..., description="Project namespace")):
    """
    List PDFs for the specific project only.

    Args:
        project_name (str): Project namespace.

    Returns:
        dict: Available PDFs.
    """
    return list_available_pdfs(project_name=project_name)


@router.get("/pdf/chunks", tags=["PDF"])
def get_pdf_chunks(
    pdf_name: str = Query(..., description="PDF file name"),
    project_name: str = Query(..., description="Project namespace")
):
    """
    Get chunks for a given PDF under a specific project.

    Args:
        pdf_name (str): PDF file name.
        project_name (str): Project namespace.

    Returns:
        dict: Text chunks list.
    """
    return get_chunks_for_pdf(pdf_name, project_name=project_name)
