from config import settings

import os
import re
from fastapi import UploadFile

from google import genai
from langfuse import get_client, Langfuse
from langfuse.langchain import CallbackHandler
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Neo4jVector
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from llama_index_pipeline.index_builder import (
    build_index_from_bytes,
    get_available_pdfs,
    get_chunks_from_neo4j,
    embed_model,
)

langfuse = get_client()
assert langfuse.auth_check(), "Langfuse authentication failed."

client = genai.Client(api_key=settings.GOOGLE_API_KEY)
embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")


async def save_and_process_pdfs(files: list[UploadFile], project_name: str):
    """
    Save and process uploaded PDFs under a specific project namespace.

    Each file is read in its entirety and indexed into the vector database.

    Args:
        files (list[UploadFile]): List of uploaded PDF files.
        project_name (str): Unique project name for session isolation.

    Returns:
        dict: Confirmation message on successful processing.
    """
    for file in files:
        file_bytes = await file.read()
        build_index_from_bytes(file_bytes, filename=file.filename, project_name=project_name)
    return {"message": f"PDFs processed and indexed under project: {project_name}"}


def get_chunks_for_pdf(pdf_name: str, project_name: str):
    """
    Retrieve chunks for a given PDF within a specific project.

    Args:
        pdf_name (str): PDF file name.
        project_name (str): Project namespace.

    Returns:
        dict: Dictionary with list of extracted text chunks.
    """
    chunks = get_chunks_from_neo4j(pdf_name, project_name=project_name)
    return {"chunks": chunks}


def filter_clean_chunks(chunks: list[str]) -> list[str]:
    """
    Clean and filter text chunks for minimum length/word requirements.

    Removes non-printable characters and filters out short/non-informative chunks.

    Args:
        chunks (list[str]): List of text chunks to process.

    Returns:
        list[str]: Cleaned, filtered list of chunks.
    """
    clean = []
    for chunk in chunks:
        chunk = re.sub(r"[^\x20-\x7E\n]", "", chunk)
        if len(chunk.strip()) > 50 and len(re.findall(r"\w+", chunk)) > 10:
            clean.append(chunk)
    return clean


def count_tokens(client, model_name, text):
    """
    Count tokens for a given text prompt using the specified model.

    Args:
        client: Google Generative AI client instance.
        model_name (str): Model name (e.g., 'gemini-2.5-flash').
        text (str): Text for which to count tokens.

    Returns:
        int: Number of tokens in the text.
    """
    if not isinstance(text, str):
        text = str(text)
    content_obj = genai.types.Content(parts=[genai.types.Part(text=text)])
    token_data = client.models.count_tokens(model=model_name, contents=content_obj)
    return token_data.total_tokens


async def answer_question(question: str, project_name: str, pdf_name: str | None = None):
    """
    Answer a user question by retrieving and using indexed PDF context.

    Retrieves top-k relevant chunks from Neo4j vector store and passes them to a language model.
    Also manages Langfuse tracing for prompt/response usage.

    Args:
        question (str): User's question string.
        project_name (str): Project namespace for isolation.
        pdf_name (str|None): Optional PDF filename to restrict context source.

    Returns:
        dict: Answer, source PDF(s), chunk preview, and token usage.
    """
    langfuse_handler = CallbackHandler()
    clean_chunks = []
    context = ""
    source_pdfs = []

    if pdf_name:
        raw_chunks = get_chunks_from_neo4j(pdf_name, project_name=project_name)
        clean_chunks = filter_clean_chunks(raw_chunks)
        context = "\n\n".join(clean_chunks)
        source_pdfs = [pdf_name]
    else:
        vector_store = Neo4jVector(
            embedding=embed_model,
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
            node_label="Chunk",
            text_node_property="text",
            embedding_node_property="embedding"
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(question)

        docs = [doc for doc in docs if doc.metadata.get('project') == project_name]
        raw_chunks = [doc.page_content for doc in docs]
        clean_chunks = filter_clean_chunks(raw_chunks)
        context = "\n\n".join(clean_chunks)
        source_pdfs = list({doc.metadata.get("source", "unknown") for doc in docs})

    if not clean_chunks:
        return {
            "answer": "No readable content found in the retrieved chunks.",
            "pdf_name": ", ".join(source_pdfs) if source_pdfs else "unknown",
            "context_chunks": [],
        }

    try:
        lf_prompt = langfuse.get_prompt("pdf_qa_prompt", label="production")
        template = PromptTemplate.from_template(
            lf_prompt.get_langchain_prompt(),
            metadata={"langfuse_prompt": lf_prompt}
        )
    except Exception:
        template = PromptTemplate.from_template(
            """You are a helpful assistant. Use the following context to answer the question.

Context:
{context}

Question:
{question}

Answer:"""
        )

    try:
        compiled_prompt = template.invoke(
            {"context": context, "question": question},
            config={"callbacks": [langfuse_handler]}
        )
    except Exception:
        compiled_prompt = template.format(context=context, question=question)

    if not isinstance(compiled_prompt, str):
        compiled_prompt = str(compiled_prompt)

    try:
        model_name = "gemini-2.5-flash"
        prompt_tokens = count_tokens(client, model_name, compiled_prompt)
        response = client.models.generate_content(
            model=model_name,
            contents=compiled_prompt
        )
        response_text = response.candidates[0].content.parts[0].text.strip()

        if not isinstance(response_text, str):
            response_text = str(response_text)

        completion_tokens = count_tokens(client, model_name, response_text)

        if hasattr(langfuse_handler, "update_current_trace"):
            langfuse_handler.update_current_trace(
                usage_details={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                metadata={"model": model_name},
            )

    except Exception:
        response_text = "Sorry, I couldn't generate a response at the moment."
        prompt_tokens = 0
        completion_tokens = 0

    return {
        "answer": response_text,
        "pdf_name": ", ".join(source_pdfs),
        "num_chunks": len(clean_chunks),
        "context_preview": clean_chunks[:2],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def list_available_pdfs(project_name: str):
    """
    List all PDFs indexed under the specified project name.

    Args:
        project_name (str): Project namespace for filtering.

    Returns:
        dict: Dictionary with list of PDF filenames.
    """
    return {"pdfs": get_available_pdfs(project_name=project_name)}
