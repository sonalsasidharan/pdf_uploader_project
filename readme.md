# WizVault: PDF Question Answering Web App

**WizVault** is a Harry Potter–themed PDF Question Answering Assistant.  
Upload PDFs, ask document-grounded questions, get live answers powered by AI and vectors.

---

## Features

- Beautiful themed Streamlit frontend
- Upload/index up to 2 PDFs per project
- AI answers to your document questions, with context preview
- Gemini/Google Generative AI, HuggingFace, LangChain
- Vector search with Neo4j; metadata in MongoDB
- Modular backend with FastAPI, organized services/controllers

---

## Architecture

Streamlit UI (frontend) <-> FastAPI backend <-> MongoDB + Neo4j + Embeddings

- `frontend/app.py` — Streamlit H.P. themed uploader & QA UI
- `backend/main.py` or `backend/app.py` — FastAPI backend entry point
- `backend/config.py` — Central project config/env loader
- `backend/controllers/pdf_controller.py` — FastAPI PDF API router/controller
- `backend/services/pdf_service.py` — PDF upload, chunking, QA logic
- `backend/llama_index_pipeline/index_builder.py` — chunking/embedding pipeline

---

## Installation & Setup

### 1. Clone repo
git clone https://github.com/yourusername/wizvault.git
cd wizvault

### 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Prepare `.env` for backend
Set your credentials for MongoDB, Neo4j, Google API, Langfuse, etc.

Example:
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/dbname?retryWrites=true&w=majority
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=yourpassword
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
OLLAMA_MODEL=gemma:2b
HF_API_KEY=hf_yyy
GOOGLE_API_KEY=AIzaSyD...

---

## Running the App

### 1. Start FastAPI backend
cd backend
uvicorn main:app --reload
# or (depending on filename)
uvicorn app:app --reload

### 2. Start Streamlit frontend
cd frontend
streamlit run app.py
# Open browser to the provided local URL.

---

## Folder Structure

wizvault/
│
├── backend/
│   ├── config.py                     # Loads .env and settings
│   ├── requirements.txt
│   ├── .env                          # (private, backend env keys)
│   ├── main.py or app.py             # FastAPI backend entry
│   ├── controllers/
│   │   └── pdf_controller.py         # FastAPI controller/router for PDFs
│   ├── services/
│   │   └── pdf_service.py            # PDF upload, chunking, QA logic
│   └── llama_index_pipeline/
│       └── index_builder.py          # Indexing/embedding pipeline code
│
├── frontend/
│   └── app.py                        # Streamlit HP-themed UI
│
└── README.md                         # Project documentation

---

## Usage Guide

1. Open the site in your browser.
2. Enter a Project Name to separate uploads/queries.
3. Upload up to 2 PDFs ("Sorting your PDFs..." spinner).
4. Select a PDF, type a question, and hit Enter.
5. Answers appear with context chunk preview!

---

## Troubleshooting

- Database errors? Check .env and that MongoDB/Neo4j are running.
- MongoDB Atlas DNS errors? Verify your connection string & cluster.
- API key errors? Confirm your quotas/secrets are correct in .env.

---

## Contributing

- PRs welcome—focus on docstring coverage and robust error handling.
- Follow PEP8/PEP257.
- Always use settings from backend/config.py.

---

## Credits

- Harry Potter inspiration, Python-powered
- Built with FastAPI, Streamlit, HuggingFace, LangChain, Gemini, Neo4j, MongoDB

---

## License

