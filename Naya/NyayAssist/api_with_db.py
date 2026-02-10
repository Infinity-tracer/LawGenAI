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

# Law comparison imports
from law_comparison import LawComparisonService

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

# Initialize law comparison service
law_service = LawComparisonService()

# ---------------------- PYDANTIC MODELS ----------------------

class ChatRequest(BaseModel):
    question: str
    session_uuid: Optional[str] = None
    user_uuid: Optional[str] = None

class LawComparison(BaseModel):
    old_law: str
    old_section: str
    old_title: str
    new_law: str
    new_section: str
    new_title: str
    changes: str
    original_text: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    success: bool
    message_id: Optional[str] = None
    law_comparisons: Optional[List[LawComparison]] = None

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
    law_comparisons: Optional[List[LawComparison]] = None

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

# In-memory storage for verification codes (for demo purposes)
# In production, use Redis with expiration
verification_codes = {}

# Email Imports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

def send_email_otp(to_email: str, otp: str):
    """Send OTP via SMTP"""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL")

    if not all([smtp_username, smtp_password, sender_email]):
        print(f"⚠️ SMTP credentials missing. Mocking email to {to_email}: {otp}")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "NyayAssist Verification Code"

    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border_radius: 5px;">
          <h2 style="color: #d4af37;">NyayAssist Verification</h2>
          <p>Hello,</p>
          <p>Your verification code for NyayAssist is:</p>
          <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
            <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #3d2b1f;">{otp}</span>
          </div>
          <p>This code will expire in 10 minutes.</p>
          <p style="font-size: 12px; color: #777; margin-top: 30px;">
            If you did not request this code, please ignore this email.
          </p>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"✅ OTP sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        # Fallback to console for dev
        print(f"Mocking email to {to_email}: {otp}")
        raise e


@app.post("/api/users/send-otp")
async def send_otp(request: SendOTPRequest):
    """Send verification OTP to email"""
    try:
        # Check if email already registered
        existing = db_service.get_user_by_email(request.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate 6-digit OTP
        otp = str(uuid.uuid4().int)[:6]
        
        # Store OTP
        verification_codes[request.email] = otp
        
        # Send Email
        try:
            send_email_otp(request.email, otp)
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        
        return {"success": True, "message": "Verification code sent to email"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UserRegisterWithOTP(UserCreate):
    otp: str

@app.post("/api/users/register", response_model=UserResponse)
async def register_user(user: UserRegisterWithOTP):
    """Register a new user with OTP verification"""
    try:
        # Verify OTP
        stored_otp = verification_codes.get(user.email)
        if not stored_otp or stored_otp != user.otp:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
            
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
        
        # Clear used OTP
        del verification_codes[user.email]
        
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
        
        # Detect law sections and get comparisons
        augmented_response, comparisons = law_service.augment_answer(response, request.question)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log LLM output to database
        llm_log = db_service.log_llm_output(
            user_question=request.question,
            llm_response=augmented_response,  # Log the augmented response
            context_provided=context[:5000] if context else None,  # Limit context size
            response_time_ms=response_time_ms,
            model_name="gemini-2.5-flash",
            success=True
        )
        
        # Convert comparisons to LawComparison objects
        law_comparisons = None
        if comparisons:
            law_comparisons = [
                LawComparison(
                    old_law=comp['old_law'],
                    old_section=comp['old_section'],
                    old_title=comp['old_title'],
                    new_law=comp['new_law'],
                    new_section=comp['new_section'],
                    new_title=comp['new_title'],
                    changes=comp['changes'],
                    original_text=comp.get('original_text')
                )
                for comp in comparisons
            ]
        
        return ChatResponse(
            answer=augmented_response,
            success=True,
            message_id=llm_log["output_uuid"] if llm_log else None,
            law_comparisons=law_comparisons
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
        
        # Detect law sections in query and get comparisons
        detected_sections = law_service.detect_law_sections(request.query)
        law_comparisons_list = None
        
        if detected_sections:
            comparisons = law_service.get_all_comparisons(detected_sections)
            if comparisons:
                law_comparisons_list = [
                    LawComparison(
                        old_law=comp['old_law'],
                        old_section=comp['old_section'],
                        old_title=comp['old_title'],
                        new_law=comp['new_law'],
                        new_section=comp['new_section'],
                        new_title=comp['new_title'],
                        changes=comp['changes'],
                        original_text=comp.get('original_text')
                    )
                    for comp in comparisons
                ]
        
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
            query_id=kanoon_log["query_uuid"] if kanoon_log else None,
            law_comparisons=law_comparisons_list
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


# ---------------------- LAW COMPARISON ENDPOINT ----------------------

class LawCompareRequest(BaseModel):
    law_type: str  # 'IPC', 'CRPC', or 'IEA'
    section: str   # Section number like '302', '304A'

class LawCompareResponse(BaseModel):
    success: bool
    comparison: Optional[LawComparison] = None
    error: Optional[str] = None

@app.post("/api/law/compare", response_model=LawCompareResponse)
async def compare_law_section(request: LawCompareRequest):
    """
    Get comparison between old law section and new equivalent
    
    Example request:
    {
        "law_type": "IPC",
        "section": "302"
    }
    
    Returns BNS equivalent and changes summary
    """
    try:
        law_type = request.law_type.upper()
        if law_type not in ['IPC', 'CRPC', 'IEA']:
            return LawCompareResponse(
                success=False,
                error=f"Invalid law_type. Must be one of: IPC, CRPC, IEA"
            )
        
        # Get comparison data
        comparison_data = law_service.get_comparison_data(law_type, request.section)
        
        if not comparison_data:
            return LawCompareResponse(
                success=False,
                error=f"No comparison data found for {law_type} Section {request.section}"
            )
        
        # Convert to LawComparison object
        comparison = LawComparison(
            old_law=comparison_data['old_law'],
            old_section=comparison_data['old_section'],
            old_title=comparison_data['old_title'],
            new_law=comparison_data['new_law'],
            new_section=comparison_data['new_section'],
            new_title=comparison_data['new_title'],
            changes=comparison_data['changes']
        )
        
        return LawCompareResponse(
            success=True,
            comparison=comparison
        )
    except Exception as e:
        return LawCompareResponse(
            success=False,
            error=str(e)
        )


class LawSectionRequest(BaseModel):
    law_type: str
    section: str

class BulkCompareRequest(BaseModel):
    sections: List[LawSectionRequest]

class BulkCompareResponse(BaseModel):
    success: bool
    comparisons: List[LawComparison]
    not_found: Optional[List[dict]] = None

@app.post("/api/law/compare/bulk", response_model=BulkCompareResponse)
async def compare_law_sections_bulk(request: BulkCompareRequest):
    """
    Get comparisons for multiple law sections at once
    
    Example request:
    {
        "sections": [
            {"law_type": "IPC", "section": "302"},
            {"law_type": "IPC", "section": "376"},
            {"law_type": "CRPC", "section": "154"}
        ]
    }
    """
    try:
        comparisons = []
        not_found = []
        
        for section_req in request.sections:
            law_type = section_req.law_type.upper()
            if law_type not in ['IPC', 'CRPC', 'IEA']:
                not_found.append({
                    "law_type": section_req.law_type,
                    "section": section_req.section,
                    "reason": "Invalid law_type"
                })
                continue
            
            comparison_data = law_service.get_comparison_data(law_type, section_req.section)
            
            if comparison_data:
                comparisons.append(LawComparison(
                    old_law=comparison_data['old_law'],
                    old_section=comparison_data['old_section'],
                    old_title=comparison_data['old_title'],
                    new_law=comparison_data['new_law'],
                    new_section=comparison_data['new_section'],
                    new_title=comparison_data['new_title'],
                    changes=comparison_data['changes']
                ))
            else:
                not_found.append({
                    "law_type": section_req.law_type,
                    "section": section_req.section,
                    "reason": "Not found in database"
                })
        
        return BulkCompareResponse(
            success=True,
            comparisons=comparisons,
            not_found=not_found if not_found else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/law/sections/{law_type}")
async def get_law_sections(law_type: str):
    """
    Get all available sections for a specific law type
    
    Example: /api/law/sections/IPC
    Returns: List of all IPC sections available in the database
    """
    try:
        law_type = law_type.upper()
        if law_type not in ['IPC', 'CRPC', 'IEA']:
            raise HTTPException(status_code=400, detail="Invalid law_type. Must be IPC, CRPC, or IEA")
        
        # Map law type to mapping key
        mapping_key = {
            'IPC': 'IPC_TO_BNS',
            'CRPC': 'CRPC_TO_BNSS',
            'IEA': 'IEA_TO_BEA'
        }.get(law_type)
        
        sections_data = law_service.mapping_data.get(mapping_key, {})
        
        # Format sections with basic info
        sections = []
        for section_num, data in sections_data.items():
            sections.append({
                "section": section_num,
                "title": data.get("old_title", ""),
                "new_section": data.get("new_section", ""),
                "new_law": {
                    'IPC': 'BNS',
                    'CRPC': 'BNSS',
                    'IEA': 'BEA'
                }.get(law_type, '')
            })
        
        # Sort by section number
        sections.sort(key=lambda x: (
            int(''.join(filter(str.isdigit, x['section'])) or '0'),
            x['section']
        ))
        
        return {
            "success": True,
            "law_type": law_type,
            "total_sections": len(sections),
            "sections": sections
        }
    except HTTPException:
        raise
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
