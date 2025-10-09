import os
from pathlib import Path
from langchain_ollama import ChatOllama
from llama_index_pipeline.index_builder import build_index, get_retriever_and_llm
from langfuse import Langfuse
langfuse = Langfuse(
    public_key="pk-lf-43a39e54-e3ac-4aa8-8057-738724b52eea",
    secret_key="sk-lf-48bff15f-5f4a-4c85-a707-baa5f315e111",
    host="http://localhost:3000"
)
chat_llm = ChatOllama(model="gemma:2b")
DATA_DIR = "C:\Users\FCI\Desktop\new_project\proj\data"
DATA_DIR.mkdir(exist_ok=True)

async def save_and_process_pdfs(files):
    for f in DATA_DIR.glob("*.pdf"):
        f.unlink()

    for file in files:
        if file.content_type != "application/pdf":
            raise ValueError(f"{file.filename} is not a PDF.")
        file_path = DATA_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

    build_index(str(DATA_DIR))
    return {"message": "PDFs saved and indexed."}

def answer_question(question: str):
    retriever, _ = get_retriever_and_llm()
    nodes = retriever.retrieve(question)

    if not nodes:
        return {"answer": "Sorry, I couldn't find relevant information in the uploaded documents."}

    context = "\n\n".join([node.node.text for node in nodes])

    trace = langfuse.trace(name="pdf_qa_trace", input={"question": question, "context": context})
    span = trace.span(name="llm_call", input={"prompt_name": "pdf_qa_prompt", "variables": {"context": context, "question": question}})

    prompt = langfuse.prompts.resolve("pdf_qa_prompt", {"context": context, "question": question})

    response = chat_llm.invoke(prompt)
    span.output = response.content

    return {"answer": response.content}
