from fastapi import FastAPI
from controllers.pdf_controller import router as pdf_router

app = FastAPI(title="PDF Uploader App")

app.include_router(pdf_router, prefix="/pdf")
