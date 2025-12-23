from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import re
import requests
import tempfile
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="NyayAssist API",
    description="Legal AI Assistant API for PDF Chat and Indian Kanoon Search",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
KANOON_API_TOKEN = os.getenv("KANOON_API_TOKEN")
BASE_URL = "https://api.indiankanoon.org"
FAISS_INDEX_PATH = "faiss_index"

# ---------------------- PYDANTIC MODELS ----------------------

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    success: bool

class KanoonSearchRequest(BaseModel):
    query: str
    page: Optional[int] = 0

class CaseResult(BaseModel):
    title: str
    doc_id: str
    snippet: str
    case_link: str

class KanoonSearchResponse(BaseModel):
    cases: List[CaseResult]
    total_found: int
    success: bool

class UploadResponse(BaseModel):
    message: str
    chunks_processed: int
    success: bool

# ---------------------- HELPER FUNCTIONS ----------------------

def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text and decode HTML entities"""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return clean.strip()

def _kanoon_headers():
    if not KANOON_API_TOKEN:
        raise HTTPException(status_code=500, detail="KANOON_API_TOKEN missing")
    return {
        "Authorization": f"Token {KANOON_API_TOKEN}",
        "Accept": "application/json"
    }

def get_pdf_text(pdf_file) -> str:
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def get_text_chunks(text: str) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    return text_splitter.split_text(text)

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer

    Context:
    {context}

    Question: {question}

    Answer:
    """
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY
    )
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return prompt | model | StrOutputParser()

# ---------------------- API ENDPOINTS ----------------------

@app.get("/")
async def root():
    return {"message": "NyayAssist API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# PDF Chat Endpoints
@app.post("/api/pdf/upload", response_model=UploadResponse)
async def upload_pdf(files: List[UploadFile] = File(...)):
    """Upload and process PDF files for chat"""
    try:
        all_text = ""
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            # Read PDF content
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                all_text += get_pdf_text(tmp_path)
            finally:
                os.unlink(tmp_path)
        
        if not all_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF(s)")
        
        # Create vector store
        text_chunks = get_text_chunks(all_text)
        embeddings = get_embeddings()
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local(FAISS_INDEX_PATH)
        
        return UploadResponse(
            message="PDFs processed successfully",
            chunks_processed=len(text_chunks),
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pdf/chat", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest):
    """Ask questions about uploaded PDF documents"""
    try:
        if not os.path.exists(FAISS_INDEX_PATH):
            raise HTTPException(status_code=400, detail="No PDF has been uploaded yet. Please upload a PDF first.")
        
        embeddings = get_embeddings()
        vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        docs = vector_store.similarity_search(request.question)
        
        chain = get_conversational_chain()
        context = format_docs(docs)
        response = chain.invoke({"context": context, "question": request.question})
        
        return ChatResponse(answer=response, success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Indian Kanoon Endpoints
@app.post("/api/kanoon/search", response_model=KanoonSearchResponse)
async def search_kanoon(request: KanoonSearchRequest):
    """Search Indian Kanoon for legal cases"""
    try:
        url = f"{BASE_URL}/search/?formInput={request.query}&pagenum={request.page}"
        r = requests.post(url, headers=_kanoon_headers())
        r.raise_for_status()
        data = r.json()
        
        docs = data.get("docs", [])
        cases = []
        
        for doc in docs[:5]:  # Limit to top 5 results
            title = strip_html_tags(doc.get("title", "Untitled Case"))
            doc_id = doc.get("docid") or doc.get("tid") or doc.get("id")
            
            if not doc_id:
                continue
            
            # Try to get headline/snippet
            snippet = strip_html_tags(doc.get("headline", ""))
            
            if not snippet:
                try:
                    frag_url = f"{BASE_URL}/docfragment/{doc_id}/?formInput={request.query}"
                    frag_r = requests.post(frag_url, headers=_kanoon_headers())
                    frag_r.raise_for_status()
                    frag_data = frag_r.json()
                    snippet = strip_html_tags(frag_data.get("fragment", "") or frag_data.get("content", ""))
                except:
                    snippet = ""
            
            if not snippet:
                snippet = "No relevant excerpt available."
            elif len(snippet) > 500:
                snippet = snippet[:500] + "..."
            
            cases.append(CaseResult(
                title=title,
                doc_id=str(doc_id),
                snippet=snippet,
                case_link=f"https://indiankanoon.org/doc/{doc_id}/"
            ))
        
        return KanoonSearchResponse(
            cases=cases,
            total_found=len(docs),
            success=True
        )
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error connecting to Indian Kanoon: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
