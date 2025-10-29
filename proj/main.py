from fastapi import FastAPI
from controllers.pdf_controller import router as pdf_router

app = FastAPI(title="PDF Uploader App")
"""
FastAPI application instance for the PDF Uploader Service.

This app includes the PDF API router under the "/pdf" prefix, which provides
endpoints for uploading PDFs, querying questions, listing PDFs, and retrieving
PDF text chunks.

Attributes:
    title (str): The title of the FastAPI application, shown in OpenAPI docs.

Routers:
    pdf_router: Router handling all PDF-related API endpoints.
"""

app.include_router(pdf_router, prefix="/pdf")
