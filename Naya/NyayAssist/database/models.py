"""
NyayAssist SQLAlchemy Models
ORM Models for MySQL Database
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, Enum, ForeignKey, JSON, DECIMAL, LargeBinary,
    Index, UniqueConstraint, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.mysql import LONGTEXT
import uuid

from .db_config import get_database_url

Base = declarative_base()


# =====================================================
# USER MODELS
# =====================================================

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    profile_picture_url = Column(String(500))
    role = Column(Enum('user', 'admin', 'moderator'), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="user")
    llm_outputs = relationship("LLMOutput", back_populates="user")
    kanoon_queries = relationship("KanoonQuery", back_populates="user")
    pdf_uploads = relationship("PDFUpload", back_populates="user")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user")


class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_token = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")


# =====================================================
# ACCESS LOG MODELS
# =====================================================

class AccessLog(Base):
    __tablename__ = 'access_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    user_uuid = Column(String(36))
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    endpoint = Column(String(255), nullable=False)
    http_method = Column(String(10), nullable=False)
    request_body = Column(JSON)
    response_status_code = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="access_logs")


# =====================================================
# CHAT MODELS
# =====================================================

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    title = Column(String(255), default='New Chat')
    chat_mode = Column(Enum('PDF_CHAT', 'KANOON_SEARCH'), nullable=False)
    folder = Column(String(100))
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    llm_outputs = relationship("LLMOutput", back_populates="session")
    kanoon_queries = relationship("KanoonQuery", back_populates="session")
    pdf_uploads = relationship("PDFUpload", back_populates="session")


class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum('user', 'assistant', 'system'), nullable=False)
    content = Column(LONGTEXT, nullable=False)
    message_type = Column(Enum('text', 'cases', 'error', 'system'), default='text')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    llm_outputs = relationship("LLMOutput", back_populates="message")
    kanoon_queries = relationship("KanoonQuery", back_populates="message")
    feedbacks = relationship("Feedback", back_populates="message")


# =====================================================
# LLM OUTPUT MODELS
# =====================================================

class LLMOutput(Base):
    __tablename__ = 'llm_outputs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    output_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete='SET NULL'))
    message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='SET NULL'))
    
    # Request details
    model_name = Column(String(100), default='gemini-2.5-flash')
    prompt_template = Column(Text)
    context_provided = Column(LONGTEXT)
    user_question = Column(Text, nullable=False)
    
    # Response details
    llm_response = Column(LONGTEXT, nullable=False)
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    temperature = Column(DECIMAL(3, 2), default=0.30)
    
    # Status and metadata
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="llm_outputs")
    session = relationship("ChatSession", back_populates="llm_outputs")
    message = relationship("Message", back_populates="llm_outputs")
    feedbacks = relationship("Feedback", back_populates="llm_output")


# =====================================================
# KANOON MODELS
# =====================================================

class KanoonQuery(Base):
    __tablename__ = 'kanoon_queries'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    query_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete='SET NULL'))
    message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='SET NULL'))
    
    # Query details
    search_query = Column(Text, nullable=False)
    page_number = Column(Integer, default=0)
    
    # Response details
    total_results_found = Column(Integer, default=0)
    results_returned = Column(Integer, default=0)
    response_time_ms = Column(Integer)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    raw_api_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="kanoon_queries")
    session = relationship("ChatSession", back_populates="kanoon_queries")
    message = relationship("Message", back_populates="kanoon_queries")
    case_results = relationship("KanoonCaseResult", back_populates="query", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="kanoon_query")


class KanoonCaseResult(Base):
    __tablename__ = 'kanoon_case_results'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    query_id = Column(BigInteger, ForeignKey('kanoon_queries.id', ondelete='CASCADE'), nullable=False)
    doc_id = Column(String(50), nullable=False)
    title = Column(String(500))
    snippet = Column(Text)
    case_link = Column(String(500))
    headline = Column(Text)
    result_rank = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    query = relationship("KanoonQuery", back_populates="case_results")


# =====================================================
# PDF MODELS
# =====================================================

class PDFUpload(Base):
    __tablename__ = 'pdf_uploads'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete='SET NULL'))
    
    # File details
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger)
    file_hash = Column(String(64))
    mime_type = Column(String(100), default='application/pdf')
    
    # Processing details
    pages_count = Column(Integer)
    text_extracted = Column(LONGTEXT)
    chunks_processed = Column(Integer, default=0)
    chunk_size = Column(Integer, default=10000)
    chunk_overlap = Column(Integer, default=1000)
    
    # Vector store info
    faiss_index_path = Column(String(500))
    embedding_model = Column(String(100), default='sentence-transformers/all-MiniLM-L6-v2')
    
    # Status
    processing_status = Column(Enum('pending', 'processing', 'completed', 'failed'), default='pending')
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="pdf_uploads")
    session = relationship("ChatSession", back_populates="pdf_uploads")
    text_chunks = relationship("PDFTextChunk", back_populates="upload", cascade="all, delete-orphan")


class PDFTextChunk(Base):
    __tablename__ = 'pdf_text_chunks'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey('pdf_uploads.id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(LONGTEXT, nullable=False)
    chunk_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    upload = relationship("PDFUpload", back_populates="text_chunks")
    
    __table_args__ = (
        UniqueConstraint('upload_id', 'chunk_index', name='uk_upload_chunk'),
    )


# =====================================================
# ANALYTICS & FEEDBACK MODELS
# =====================================================

class APIRateLimit(Base):
    __tablename__ = 'api_rate_limits'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    ip_address = Column(String(45))
    endpoint = Column(String(255), nullable=False)
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime, default=datetime.utcnow)
    window_end = Column(DateTime, nullable=False)


class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    metric_type = Column(Enum('daily_users', 'daily_queries', 'pdf_uploads', 'kanoon_searches', 'llm_calls'), nullable=False)
    metric_value = Column(Integer, default=0)
    additional_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('date', 'metric_type', name='uk_date_metric'),
    )


class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='SET NULL'))
    llm_output_id = Column(BigInteger, ForeignKey('llm_outputs.id', ondelete='SET NULL'))
    kanoon_query_id = Column(BigInteger, ForeignKey('kanoon_queries.id', ondelete='SET NULL'))
    
    rating = Column(Integer)  # 1-5
    feedback_type = Column(Enum('helpful', 'not_helpful', 'incorrect', 'offensive', 'other'), nullable=False)
    feedback_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feedbacks")
    message = relationship("Message", back_populates="feedbacks")
    llm_output = relationship("LLMOutput", back_populates="feedbacks")
    kanoon_query = relationship("KanoonQuery", back_populates="feedbacks")


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

def init_db():
    """Initialize the database and create all tables"""
    engine = create_engine(get_database_url(), echo=True)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get a database session"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()
