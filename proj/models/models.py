from pydantic import BaseModel
from typing import List, Optional


class UploadResponse(BaseModel):
    """
    Response model for PDF upload endpoint.

    Attributes:
        message (str): Confirmation message after processing uploaded PDFs.
    """
    message: str


class AnswerResponse(BaseModel):
    """
    Response model for the question answering endpoint.

    Attributes:
        answer (str): The text answer generated for the user's question.
        pdf_name (str): The name of the PDF file from which the answer was derived.
        context_chunks (Optional[List[str]]): Optional list of text chunks (context) 
                                             relevant to the answer.
    """
    answer: str
    pdf_name: str
    context_chunks: Optional[List[str]] = None
