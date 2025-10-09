from pydantic import BaseModel

class UploadResponse(BaseModel):
    message: str

class AnswerResponse(BaseModel):
    answer: str
