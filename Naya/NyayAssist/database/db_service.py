"""
NyayAssist Database Service
Provides database operations for logging and retrieving data
"""

import uuid
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .db_config import get_database_url
from .models import (
    User, UserSession, AccessLog, ChatSession, Message,
    LLMOutput, KanoonQuery, KanoonCaseResult, PDFUpload,
    PDFTextChunk, APIRateLimit, Analytics, Feedback
)


class DatabaseService:
    """Main database service class for NyayAssist"""
    
    def __init__(self):
        self.engine = create_engine(
            get_database_url(),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # =====================================================
    # USER OPERATIONS
    # =====================================================
    
    def create_user(self, full_name: str, email: str, password_hash: str, 
                    phone: str = None) -> dict:
        """Create a new user and return user data as dict"""
        with self.get_session() as session:
            user = User(
                user_uuid=str(uuid.uuid4()),
                full_name=full_name,
                email=email,
                password_hash=password_hash,
                phone=phone
            )
            session.add(user)
            session.flush()
            session.refresh(user)
            # Return as dict to avoid session detachment issues
            return {
                "id": user.id,
                "user_uuid": user.user_uuid,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "role": user.role,
                "created_at": user.created_at
            }
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        with self.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "id": user.id,
                    "user_uuid": user.user_uuid,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "password_hash": user.password_hash,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "role": user.role,
                    "created_at": user.created_at
                }
            return None
    
    def get_user_by_uuid(self, user_uuid: str) -> Optional[dict]:
        """Get user by UUID"""
        with self.get_session() as session:
            user = session.query(User).filter(User.user_uuid == user_uuid).first()
            if user:
                return {
                    "id": user.id,
                    "user_uuid": user.user_uuid,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_active": user.is_active,
                    "role": user.role
                }
            return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        with self.get_session() as session:
            session.query(User).filter(User.id == user_id).update({
                "last_login_at": datetime.utcnow()
            })
    
    # =====================================================
    # ACCESS LOG OPERATIONS
    # =====================================================
    
    def log_access(self, endpoint: str, http_method: str, 
                   user_id: int = None, user_uuid: str = None,
                   session_id: str = None, ip_address: str = None,
                   user_agent: str = None, request_body: dict = None,
                   response_status_code: int = None, response_time_ms: int = None,
                   error_message: str = None) -> AccessLog:
        """Log an API access"""
        with self.get_session() as session:
            log = AccessLog(
                user_id=user_id,
                user_uuid=user_uuid,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                http_method=http_method,
                request_body=request_body,
                response_status_code=response_status_code,
                response_time_ms=response_time_ms,
                error_message=error_message
            )
            session.add(log)
            session.flush()
            return log
    
    def get_access_logs(self, user_id: int = None, endpoint: str = None,
                        start_date: datetime = None, end_date: datetime = None,
                        limit: int = 100) -> List[AccessLog]:
        """Get access logs with optional filters"""
        with self.get_session() as session:
            query = session.query(AccessLog)
            
            if user_id:
                query = query.filter(AccessLog.user_id == user_id)
            if endpoint:
                query = query.filter(AccessLog.endpoint.like(f"%{endpoint}%"))
            if start_date:
                query = query.filter(AccessLog.created_at >= start_date)
            if end_date:
                query = query.filter(AccessLog.created_at <= end_date)
            
            return query.order_by(AccessLog.created_at.desc()).limit(limit).all()
    
    # =====================================================
    # CHAT SESSION OPERATIONS
    # =====================================================
    
    def create_chat_session(self, chat_mode: str, user_id: int = None,
                            title: str = "New Chat", folder: str = None) -> dict:
        """Create a new chat session"""
        with self.get_session() as session:
            chat_session = ChatSession(
                session_uuid=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                chat_mode=chat_mode,
                folder=folder
            )
            session.add(chat_session)
            session.flush()
            session.refresh(chat_session)
            return {
                "id": chat_session.id,
                "session_uuid": chat_session.session_uuid,
                "title": chat_session.title,
                "chat_mode": chat_session.chat_mode,
                "user_id": chat_session.user_id,
                "created_at": chat_session.created_at
            }
    
    def get_user_chat_sessions(self, user_id: int, limit: int = 50) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        with self.get_session() as session:
            return session.query(ChatSession)\
                .filter(ChatSession.user_id == user_id)\
                .filter(ChatSession.is_archived == False)\
                .order_by(ChatSession.updated_at.desc())\
                .limit(limit).all()
    
    def update_session_title(self, session_id: int, title: str):
        """Update chat session title"""
        with self.get_session() as session:
            session.query(ChatSession).filter(ChatSession.id == session_id).update({
                "title": title
            })
    
    # =====================================================
    # MESSAGE OPERATIONS
    # =====================================================
    
    def add_message(self, session_id: int, role: str, content: str,
                    message_type: str = "text") -> Message:
        """Add a message to a chat session"""
        with self.get_session() as session:
            message = Message(
                message_uuid=str(uuid.uuid4()),
                session_id=session_id,
                role=role,
                content=content,
                message_type=message_type
            )
            session.add(message)
            session.flush()
            session.refresh(message)
            
            # Update session's updated_at timestamp
            session.query(ChatSession).filter(ChatSession.id == session_id).update({
                "updated_at": datetime.utcnow()
            })
            
            return message
    
    def get_session_messages(self, session_id: int) -> List[Message]:
        """Get all messages in a chat session"""
        with self.get_session() as session:
            return session.query(Message)\
                .filter(Message.session_id == session_id)\
                .order_by(Message.created_at.asc()).all()
    
    # =====================================================
    # LLM OUTPUT OPERATIONS
    # =====================================================
    
    def log_llm_output(self, user_question: str, llm_response: str,
                       user_id: int = None, session_id: int = None,
                       message_id: int = None, model_name: str = "gemini-2.5-flash",
                       prompt_template: str = None, context_provided: str = None,
                       tokens_used: int = None, response_time_ms: int = None,
                       temperature: float = 0.3, success: bool = True,
                       error_message: str = None) -> dict:
        """Log an LLM output"""
        with self.get_session() as session:
            output = LLMOutput(
                output_uuid=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                model_name=model_name,
                prompt_template=prompt_template,
                context_provided=context_provided,
                user_question=user_question,
                llm_response=llm_response,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                temperature=temperature,
                success=success,
                error_message=error_message
            )
            session.add(output)
            session.flush()
            session.refresh(output)
            return {
                "id": output.id,
                "output_uuid": output.output_uuid,
                "user_question": output.user_question,
                "llm_response": output.llm_response,
                "model_name": output.model_name,
                "success": output.success,
                "created_at": output.created_at
            }
    
    def get_llm_outputs(self, user_id: int = None, session_id: int = None,
                        start_date: datetime = None, limit: int = 100) -> List[LLMOutput]:
        """Get LLM outputs with optional filters"""
        with self.get_session() as session:
            query = session.query(LLMOutput)
            
            if user_id:
                query = query.filter(LLMOutput.user_id == user_id)
            if session_id:
                query = query.filter(LLMOutput.session_id == session_id)
            if start_date:
                query = query.filter(LLMOutput.created_at >= start_date)
            
            return query.order_by(LLMOutput.created_at.desc()).limit(limit).all()
    
    # =====================================================
    # KANOON QUERY OPERATIONS
    # =====================================================
    
    def log_kanoon_query(self, search_query: str, user_id: int = None,
                         session_id: int = None, message_id: int = None,
                         page_number: int = 0, total_results_found: int = 0,
                         results_returned: int = 0, response_time_ms: int = None,
                         success: bool = True, error_message: str = None,
                         raw_api_response: dict = None,
                         case_results: List[Dict] = None) -> dict:
        """Log a Kanoon search query"""
        with self.get_session() as session:
            query_obj = KanoonQuery(
                query_uuid=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                search_query=search_query,
                page_number=page_number,
                total_results_found=total_results_found,
                results_returned=results_returned,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                raw_api_response=raw_api_response
            )
            session.add(query_obj)
            session.flush()
            
            # Add case results if provided
            if case_results:
                for idx, case in enumerate(case_results):
                    case_result = KanoonCaseResult(
                        query_id=query_obj.id,
                        doc_id=case.get('doc_id', ''),
                        title=case.get('title', ''),
                        snippet=case.get('snippet', ''),
                        case_link=case.get('case_link', ''),
                        headline=case.get('headline', ''),
                        result_rank=idx + 1
                    )
                    session.add(case_result)
            
            session.flush()
            session.refresh(query_obj)
            return {
                "id": query_obj.id,
                "query_uuid": query_obj.query_uuid,
                "search_query": query_obj.search_query,
                "total_results_found": query_obj.total_results_found,
                "results_returned": query_obj.results_returned,
                "success": query_obj.success,
                "created_at": query_obj.created_at
            }
    
    def get_kanoon_queries(self, user_id: int = None, search_term: str = None,
                           start_date: datetime = None, limit: int = 100) -> List[KanoonQuery]:
        """Get Kanoon queries with optional filters"""
        with self.get_session() as session:
            query = session.query(KanoonQuery)
            
            if user_id:
                query = query.filter(KanoonQuery.user_id == user_id)
            if search_term:
                query = query.filter(KanoonQuery.search_query.like(f"%{search_term}%"))
            if start_date:
                query = query.filter(KanoonQuery.created_at >= start_date)
            
            return query.order_by(KanoonQuery.created_at.desc()).limit(limit).all()
    
    # =====================================================
    # PDF UPLOAD OPERATIONS
    # =====================================================
    
    def log_pdf_upload(self, original_filename: str, user_id: int = None,
                       session_id: int = None, file_size_bytes: int = None,
                       file_content: bytes = None, pages_count: int = None,
                       text_extracted: str = None, chunks_processed: int = 0,
                       faiss_index_path: str = None,
                       processing_status: str = "pending") -> dict:
        """Log a PDF upload"""
        file_hash = None
        if file_content:
            file_hash = hashlib.sha256(file_content).hexdigest()
        
        with self.get_session() as session:
            upload = PDFUpload(
                upload_uuid=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                original_filename=original_filename,
                file_size_bytes=file_size_bytes,
                file_hash=file_hash,
                pages_count=pages_count,
                text_extracted=text_extracted,
                chunks_processed=chunks_processed,
                faiss_index_path=faiss_index_path,
                processing_status=processing_status
            )
            session.add(upload)
            session.flush()
            session.refresh(upload)
            return {
                "id": upload.id,
                "upload_uuid": upload.upload_uuid,
                "original_filename": upload.original_filename,
                "file_size_bytes": upload.file_size_bytes,
                "pages_count": upload.pages_count,
                "chunks_processed": upload.chunks_processed,
                "processing_status": upload.processing_status,
                "created_at": upload.created_at
            }
    
    def update_pdf_processing_status(self, upload_id: int, status: str,
                                      chunks_processed: int = None,
                                      error_message: str = None):
        """Update PDF processing status"""
        with self.get_session() as session:
            update_data = {"processing_status": status}
            
            if status == "completed":
                update_data["processed_at"] = datetime.utcnow()
            if chunks_processed is not None:
                update_data["chunks_processed"] = chunks_processed
            if error_message:
                update_data["error_message"] = error_message
            
            session.query(PDFUpload).filter(PDFUpload.id == upload_id).update(update_data)
    
    def add_pdf_chunks(self, upload_id: int, chunks: List[str]):
        """Add text chunks for a PDF upload"""
        with self.get_session() as session:
            for idx, chunk_text in enumerate(chunks):
                chunk = PDFTextChunk(
                    upload_id=upload_id,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    chunk_hash=hashlib.sha256(chunk_text.encode()).hexdigest()
                )
                session.add(chunk)
    
    # =====================================================
    # FEEDBACK OPERATIONS
    # =====================================================
    
    def add_feedback(self, feedback_type: str, user_id: int = None,
                     message_id: int = None, llm_output_id: int = None,
                     kanoon_query_id: int = None, rating: int = None,
                     feedback_text: str = None) -> dict:
        """Add user feedback"""
        with self.get_session() as session:
            feedback = Feedback(
                feedback_uuid=str(uuid.uuid4()),
                user_id=user_id,
                message_id=message_id,
                llm_output_id=llm_output_id,
                kanoon_query_id=kanoon_query_id,
                rating=rating,
                feedback_type=feedback_type,
                feedback_text=feedback_text
            )
            session.add(feedback)
            session.flush()
            session.refresh(feedback)
            return {
                "id": feedback.id,
                "feedback_uuid": feedback.feedback_uuid,
                "feedback_type": feedback.feedback_type,
                "rating": feedback.rating,
                "created_at": feedback.created_at
            }
    
    # =====================================================
    # ANALYTICS OPERATIONS
    # =====================================================
    
    def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Get daily statistics for the last N days"""
        with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            results = session.execute(text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_requests,
                    COUNT(DISTINCT user_id) as unique_users
                FROM access_logs
                WHERE created_at >= :start_date
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """), {"start_date": start_date})
            
            return [{"date": row[0], "total_requests": row[1], "unique_users": row[2]} 
                    for row in results]
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Get most popular Kanoon searches"""
        with self.get_session() as session:
            results = session.query(
                KanoonQuery.search_query,
                text("COUNT(*) as count")
            ).filter(KanoonQuery.success == True)\
             .group_by(KanoonQuery.search_query)\
             .order_by(text("count DESC"))\
             .limit(limit).all()
            
            return [{"query": row[0], "count": row[1]} for row in results]


# Create a global instance
db_service = DatabaseService()
