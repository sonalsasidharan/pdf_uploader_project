from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    MONGO_URI = os.getenv("MONGO_URI")
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
    HF_API_KEY = os.getenv("HF_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

settings = Settings()
