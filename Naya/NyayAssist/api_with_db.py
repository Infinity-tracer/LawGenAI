"""
NyayAssist API with MySQL Database Integration
Legal AI Assistant API for PDF Chat and Indian Kanoon Search
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import os
import re
import requests
import tempfile
import time
import hashlib
import uuid
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Database imports
from database import db_service, init_db
from middleware import AccessLogMiddleware, get_client_ip

load_dotenv()

app = FastAPI(
    title="NyayAssist API",
    description="Legal AI Assistant API for PDF Chat and Indian Kanoon Search with MySQL Database",
    version="2.0.0"
)

# Add access logging middleware
app.add_middleware(AccessLogMiddleware)

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
    session_uuid: Optional[str] = None
    user_uuid: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    success: bool
    message_id: Optional[str] = None

class KanoonSearchRequest(BaseModel):
    query: str
    page: Optional[int] = 0
    session_uuid: Optional[str] = None
    user_uuid: Optional[str] = None

class CaseResult(BaseModel):
    title: str
    doc_id: str
    snippet: str
    case_link: str

class KanoonSearchResponse(BaseModel):
    cases: List[CaseResult]
    total_found: int
    success: bool
    query_id: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    chunks_processed: int
    success: bool
    upload_id: Optional[str] = None

# User-related models
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_uuid: str
    full_name: str
    email: str
    success: bool

class SessionCreate(BaseModel):
    chat_mode: str  # 'PDF_CHAT' or 'KANOON_SEARCH'
    user_uuid: Optional[str] = None
    title: Optional[str] = "New Chat"

class SessionResponse(BaseModel):
    session_uuid: str
    title: str
    success: bool

class FeedbackRequest(BaseModel):
    feedback_type: str  # 'helpful', 'not_helpful', 'incorrect', 'offensive', 'other'
    message_id: Optional[str] = None
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    user_uuid: Optional[str] = None

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

def hash_password(password: str) -> str:
    """Simple password hashing - use bcrypt in production"""
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------- STARTUP EVENT ----------------------

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")

# ---------------------- API ENDPOINTS ----------------------

@app.get("/")
async def root():
    return {"message": "NyayAssist API is running", "version": "2.0.0", "database": "MySQL"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


# ---------------------- USER ENDPOINTS ----------------------

@app.post("/api/users/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing = db_service.get_user_by_email(user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user (returns dict now)
        new_user = db_service.create_user(
            full_name=user.full_name,
            email=user.email,
            password_hash=hash_password(user.password),
            phone=user.phone
        )
        
        return UserResponse(
            user_uuid=new_user["user_uuid"],
            full_name=new_user["full_name"],
            email=new_user["email"],
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users/login", response_model=UserResponse)
async def login_user(credentials: UserLogin):
    """Login user"""
    try:
        user = db_service.get_user_by_email(credentials.email)
        if not user or user["password_hash"] != hash_password(credentials.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login
        db_service.update_last_login(user["id"])
        
        return UserResponse(
            user_uuid=user["user_uuid"],
            full_name=user["full_name"],
            email=user["email"],
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- SESSION ENDPOINTS ----------------------

@app.post("/api/sessions/create", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    """Create a new chat session"""
    try:
        user_id = None
        if session.user_uuid:
            user = db_service.get_user_by_uuid(session.user_uuid)
            user_id = user["id"] if user else None
        
        new_session = db_service.create_chat_session(
            chat_mode=session.chat_mode,
            user_id=user_id,
            title=session.title
        )
        
        return SessionResponse(
            session_uuid=new_session["session_uuid"],
            title=new_session["title"],
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- PDF ENDPOINTS ----------------------

@app.post("/api/pdf/upload", response_model=UploadResponse)
async def upload_pdf(
    files: List[UploadFile] = File(...),
    user_uuid: Optional[str] = None,
    session_uuid: Optional[str] = None
):
    """Upload and process PDF files for chat"""
    try:
        all_text = ""
        total_pages = 0
        file_names = []
        
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            # Read PDF content
            content = await file.read()
            file_size = len(content)
            file_names.append(file.filename)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                pdf_reader = PdfReader(tmp_path)
                pages = len(pdf_reader.pages)
                total_pages += pages
                all_text += get_pdf_text(tmp_path)
                
                # Log PDF upload to database
                upload = db_service.log_pdf_upload(
                    original_filename=file.filename,
                    file_size_bytes=file_size,
                    file_content=content,
                    pages_count=pages,
                    processing_status="processing"
                )
            finally:
                os.unlink(tmp_path)
        
        if not all_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF(s)")
        
        # Create vector store
        text_chunks = get_text_chunks(all_text)
        embeddings = get_embeddings()
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local(FAISS_INDEX_PATH)
        
        # Update PDF upload status
        if upload:
            db_service.update_pdf_processing_status(
                upload_id=upload["id"],
                status="completed",
                chunks_processed=len(text_chunks)
            )
            # Store text chunks
            db_service.add_pdf_chunks(upload["id"], text_chunks)
        
        return UploadResponse(
            message=f"PDFs processed successfully: {', '.join(file_names)}",
            chunks_processed=len(text_chunks),
            success=True,
            upload_id=upload["upload_uuid"] if upload else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pdf/chat", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest):
    """Ask questions about uploaded PDF documents"""
    start_time = time.time()
    
    try:
        if not os.path.exists(FAISS_INDEX_PATH):
            raise HTTPException(status_code=400, detail="No PDF has been uploaded yet. Please upload a PDF first.")
        
        embeddings = get_embeddings()
        vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        docs = vector_store.similarity_search(request.question)
        
        chain = get_conversational_chain()
        context = format_docs(docs)
        response = chain.invoke({"context": context, "question": request.question})
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log LLM output to database
        llm_log = db_service.log_llm_output(
            user_question=request.question,
            llm_response=response,
            context_provided=context[:5000] if context else None,  # Limit context size
            response_time_ms=response_time_ms,
            model_name="gemini-2.5-flash",
            success=True
        )
        
        return ChatResponse(
            answer=response, 
            success=True,
            message_id=llm_log["output_uuid"] if llm_log else None
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        db_service.log_llm_output(
            user_question=request.question,
            llm_response="",
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- KANOON ENDPOINTS ----------------------

@app.post("/api/kanoon/search", response_model=KanoonSearchResponse)
async def search_kanoon(request: KanoonSearchRequest):
    """Search Indian Kanoon for legal cases"""
    start_time = time.time()
    
    try:
        url = f"{BASE_URL}/search/?formInput={request.query}&pagenum={request.page}"
        r = requests.post(url, headers=_kanoon_headers())
        r.raise_for_status()
        data = r.json()
        
        docs = data.get("docs", [])
        cases = []
        case_results_for_db = []
        
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
            
            case_link = f"https://indiankanoon.org/doc/{doc_id}/"
            
            cases.append(CaseResult(
                title=title,
                doc_id=str(doc_id),
                snippet=snippet,
                case_link=case_link
            ))
            
            case_results_for_db.append({
                "title": title,
                "doc_id": str(doc_id),
                "snippet": snippet,
                "case_link": case_link,
                "headline": doc.get("headline", "")
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log Kanoon query to database
        kanoon_log = db_service.log_kanoon_query(
            search_query=request.query,
            page_number=request.page,
            total_results_found=len(docs),
            results_returned=len(cases),
            response_time_ms=response_time_ms,
            success=True,
            raw_api_response=data,
            case_results=case_results_for_db
        )
        
        return KanoonSearchResponse(
            cases=cases,
            total_found=len(docs),
            success=True,
            query_id=kanoon_log["query_uuid"] if kanoon_log else None
        )
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        # Log error
        db_service.log_kanoon_query(
            search_query=request.query,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=502, detail=f"Error connecting to Indian Kanoon: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- FEEDBACK ENDPOINTS ----------------------

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for a response"""
    try:
        user_id = None
        if feedback.user_uuid:
            user = db_service.get_user_by_uuid(feedback.user_uuid)
            user_id = user["id"] if user else None
        
        fb = db_service.add_feedback(
            feedback_type=feedback.feedback_type,
            user_id=user_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text
        )
        
        return {"success": True, "feedback_id": fb["feedback_uuid"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- ANALYTICS ENDPOINTS ----------------------

@app.get("/api/analytics/stats")
async def get_stats():
    """Get usage statistics"""
    try:
        daily_stats = db_service.get_daily_stats(days=30)
        popular_searches = db_service.get_popular_searches(limit=10)
        
        return {
            "success": True,
            "daily_stats": daily_stats,
            "popular_searches": popular_searches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
