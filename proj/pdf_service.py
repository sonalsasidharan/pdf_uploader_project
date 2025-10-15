import os
import re
from fastapi import UploadFile
from dotenv import load_dotenv
from google import genai
from langfuse import Langfuse
from langchain_community.vectorstores import Neo4jVector
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

from llama_index_pipeline.index_builder import (
    build_index_from_bytes,
    get_available_pdfs,
    embed_model
)

# === Load Environment Variables ===
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# === Gemini Client Setup ===
client = genai.Client(api_key=GOOGLE_API_KEY)

# === Langfuse Setup ===
langfuse = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)

# === Embedding Model ===
embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# === PDF Upload ===
async def save_and_process_pdfs(files: list[UploadFile]):
    for file in files:
        file_bytes = await file.read()
        build_index_from_bytes(file_bytes, filename=file.filename)
    return {"message": "PDFs processed and indexed in Neo4j"}

# === Chunk Filter ===
def filter_clean_chunks(chunks: list[str]) -> list[str]:
    clean = []
    for chunk in chunks:
        chunk = re.sub(r"[^\x20-\x7E\n]", "", chunk)
        if len(chunk.strip()) > 50 and len(re.findall(r"\w+", chunk)) > 10:
            clean.append(chunk)
    return clean

# === Question Answering ===
async def answer_question(question: str):
    vector_store = Neo4jVector(
        embedding=embed_model,
        url="bolt://127.0.0.1:7687",
        username="neo4j",
        password="Son@l98achu",
        node_label="Chunk",
        text_node_property="text",
        embedding_node_property="embedding"
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(question)

    if not docs:
        return {"answer": "No relevant information found.", "pdf_name": "auto", "context_chunks": []}

    raw_chunks = [doc.page_content for doc in docs]
    clean_chunks = filter_clean_chunks(raw_chunks)
    context = "\n\n".join(clean_chunks)
    source_pdfs = list({doc.metadata.get("source", "unknown") for doc in docs})

    if not clean_chunks:
        return {
            "answer": "No readable content found in the retrieved chunks.",
            "pdf_name": ", ".join(source_pdfs),
            "context_chunks": []
        }

    # === Load Langfuse Prompt ===
    try:
        prompt_text = langfuse.get_prompt("pdf_qa_prompt",label="production")
        formatted_prompt = prompt_text.compile(context=context, question=question)

    except Exception as e:
        print(f"[Langfuse] Error loading prompt: {e}")
        prompt = f"""You are a helpful assistant. Use the following context to answer the question.

Context:
{context}

Question:
{question}

Answer:"""

    # === Gemini Generation ===
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": formatted_prompt}]}]
        )
        response_text = response.candidates[0].content.parts[0].text.strip()
    except Exception as e:
        print(f"[Gemini SDK] Error: {e}")
        response_text = "Sorry, I couldn't generate a response at the moment."

    return {
        "answer": response_text,
        "pdf_name": ", ".join(source_pdfs),
        "num_chunks": len(clean_chunks),
        "context_preview": clean_chunks[:2]
    }

# === PDF Listing ===
def list_available_pdfs():
    return {"pdfs": get_available_pdfs()}
