from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from langchain_ollama import ChatOllama
import chromadb

chromadb_client = chromadb.PersistentClient(path="./chromadb")
chromadb_collection = chromadb_client.get_or_create_collection("pdf_collection")
vector_store = ChromaVectorStore(chroma_collection=chromadb_collection)

embed_model = OllamaEmbedding(model_name="gemma:2b")
chat_llm = ChatOllama(model="gemma:2b")

def build_index(DATA_DIR: str):
    documents = SimpleDirectoryReader(input_dir=DATA_DIR).load_data()

    parser = SentenceSplitter()
    nodes = parser.get_nodes_from_documents(documents, chunk_size=500, overlap=50)
    VectorStoreIndex.from_documents(nodes, embed_model=embed_model, vector_store=vector_store)

def get_retriever_and_llm():
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    retriever = index.as_retriever()
    return retriever, chat_llm
