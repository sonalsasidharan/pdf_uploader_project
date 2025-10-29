import os
from datetime import datetime
from pymongo import MongoClient
from neo4j import GraphDatabase, basic_auth
import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain.docstore.document import Document
from dotenv import load_dotenv


load_dotenv()
hf_token = os.getenv("HF_API_KEY")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Son@l98achu")


NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
PROJECT_NAME = "default"


embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")


mongo_client = MongoClient("mongodb://127.0.0.1:27017")
meta_db = mongo_client["pdf_metadata"]
meta_collection = meta_db["uploads"]


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF.

    Parameters:
        file_bytes (bytes): The PDF file content as bytes.

    Returns:
        str: Extracted text concatenated from all pages.
    """
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])


def get_neo4j_driver():
    """
    Create and return a Neo4j driver instance.

    Returns:
        neo4j.GraphDatabase.driver: Neo4j driver configured with URI and authentication.
    """
    return GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))


def build_index_from_bytes(file_bytes: bytes, filename: str, project_name: str = "default"):
    raw_text = extract_text_from_pdf_bytes(file_bytes)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)[:10]

    if not chunks:
        meta_collection.insert_one({
            "project": project_name,
            "filename": filename,
            "timestamp": datetime.utcnow(),
            "num_chunks": 0,
            "status": "failed"
        })
        return

    try:
        meta_collection.insert_one({
            "project": project_name,
            "filename": filename,
            "timestamp": datetime.utcnow(),
            "num_chunks": len(chunks),
            "status": "indexed"
        })
    except Exception as e:
        print(f"[MongoDB] Error storing metadata: {e}")

    try:
        docs = [Document(page_content=chunk, metadata={"source": filename, "project": project_name}) for chunk in chunks]

        Neo4jVector.from_documents(
            documents=docs,
            embedding=embed_model,
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD,
            node_label="Chunk",
            text_node_property="text",
            embedding_node_property="embedding"
        )
        _link_chunks_to_pdf_and_project(filename, project_name)
    except Exception as e:
        print(f"[Neo4j] Error storing embeddings: {e}")


def _link_chunks_to_pdf_and_project(filename: str, project_name: str):
    """
    Link the indexed chunks in Neo4j to their corresponding PDF and project nodes.

    Parameters:
        filename (str): PDF filename whose chunks to link.
        project_name (str): Project name of the PDF.

    Returns:
        None
    """
    query = """
    MERGE (proj:Project {name: $project_name})
    MERGE (pdf:PDF {name: $filename})
    MERGE (proj)-[:HAS_PDF]->(pdf)
    WITH pdf
    MATCH (chunk:Chunk)
    WHERE chunk.source = $filename AND chunk.project = $project_name
    MERGE (pdf)-[:HAS_CHUNK]->(chunk)
    """
    with get_neo4j_driver().session() as session:
        session.run(query, filename=filename, project_name=project_name)


def get_chunks_from_neo4j(pdf_name: str, project_name: str = PROJECT_NAME) -> list[str]:
    """
    Retrieve text chunks for a specific PDF in a given project from Neo4j.

    Parameters:
        pdf_name (str): Name of the PDF file.
        project_name (str): Project name (default: 'default').

    Returns:
        list[str]: List of text chunks extracted from the PDF.
    """
    query = """
    MATCH (chunk:Chunk)
    WHERE chunk.source = $pdf_name AND chunk.project = $project_name
    RETURN chunk.text AS text
    ORDER BY chunk.index ASC
    """
    with get_neo4j_driver().session() as session:
        result = session.run(query, pdf_name=pdf_name, project_name=project_name)
        return [record["text"] for record in result]


def get_available_pdfs(project_name: str = PROJECT_NAME) -> list[str]:
    """
    List all distinct PDF filenames indexed under a given project.

    Parameters:
        project_name (str): Project name to filter PDFs (default: 'default').

    Returns:
        list[str]: Sorted list of unique PDF filenames.
    """
    query = """
    MATCH (chunk:Chunk)
    WHERE chunk.project = $project_name
    RETURN DISTINCT chunk.source AS name
    ORDER BY name
    """
    with get_neo4j_driver().session() as session:
        result = session.run(query, project_name=project_name)
        return [record["name"] for record in result]
