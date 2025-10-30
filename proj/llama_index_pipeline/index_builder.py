import os
from datetime import datetime
from pymongo import MongoClient
from neo4j import GraphDatabase, basic_auth
import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain.docstore.document import Document

from config import settings


embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

mongo_client = MongoClient(settings.MONGO_URI)
meta_db = mongo_client["pdf_metadata"]
meta_collection = meta_db["uploads"]


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF (fitz).
    
    Reads all pages in the PDF and concatenates their text.
    
    Args:
        file_bytes (bytes): PDF file as a byte stream.
        
    Returns:
        str: Combined text from all PDF pages.
    """
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])


def get_neo4j_driver():
    """
    Create and return a Neo4j driver instance using credentials from config.
    
    Returns:
        neo4j.GraphDatabase.driver: Configured Neo4j driver.
    """
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=basic_auth(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )


def build_index_from_bytes(file_bytes: bytes, filename: str, project_name: str = "default"):
    """
    Build vector index for a PDF file using its byte content.
    
    Splits the PDF into text chunks, stores metadata in MongoDB, and embeds 
    chunks into Neo4j.
    
    Args:
        file_bytes (bytes): PDF file content as bytes.
        filename (str): Original filename for metadata.
        project_name (str): Project namespace for chunk isolation.
        
    Returns:
        None
    """
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
    except Exception:
        pass

    try:
        docs = [Document(page_content=chunk, metadata={"source": filename, "project": project_name}) for chunk in chunks]
        Neo4jVector.from_documents(
            documents=docs,
            embedding=embed_model,
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
            node_label="Chunk",
            text_node_property="text",
            embedding_node_property="embedding"
        )
        _link_chunks_to_pdf_and_project(filename, project_name)
    except Exception:
        pass


def _link_chunks_to_pdf_and_project(filename: str, project_name: str):
    """
    Link indexed chunks in Neo4j to their respective PDF and Project nodes.
    
    Ensures data relationships for future querying and retrieval.
    
    Args:
        filename (str): PDF's filename whose chunks to link.
        project_name (str): Project name for namespace.
        
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


def get_chunks_from_neo4j(pdf_name: str, project_name: str = "default") -> list[str]:
    """
    Retrieve text chunks for a given PDF from Neo4j.
    
    Args:
        pdf_name (str): PDF file name.
        project_name (str): Project namespace. Default is "default".
        
    Returns:
        list[str]: List of text chunks for that PDF.
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


def get_available_pdfs(project_name: str = "default") -> list[str]:
    """
    List all distinct PDF filenames indexed within a given project namespace.
    
    Args:
        project_name (str): Project name for filtering. Default is "default".
        
    Returns:
        list[str]: Alphabetical list of unique PDF filenames for the project.
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
