from pydantic import BaseModel
from typing import List, Optional

class UploadResponse(BaseModel):
    message: str

class AnswerResponse(BaseModel):
    answer: str
    pdf_name: str
    context_chunks: Optional[List[str]] = None
