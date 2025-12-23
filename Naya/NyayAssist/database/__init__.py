"""
NyayAssist Database Package
MySQL Database integration for the Legal AI Assistant
"""

from .db_config import DB_CONFIG, get_database_url, get_async_database_url
from .models import (
    Base, User, UserSession, AccessLog, ChatSession, Message,
    LLMOutput, KanoonQuery, KanoonCaseResult, PDFUpload, PDFTextChunk,
    APIRateLimit, Analytics, Feedback, init_db, get_session
)
from .db_service import DatabaseService, db_service

__all__ = [
    # Config
    'DB_CONFIG',
    'get_database_url',
    'get_async_database_url',
    
    # Models
    'Base',
    'User',
    'UserSession',
    'AccessLog',
    'ChatSession',
    'Message',
    'LLMOutput',
    'KanoonQuery',
    'KanoonCaseResult',
    'PDFUpload',
    'PDFTextChunk',
    'APIRateLimit',
    'Analytics',
    'Feedback',
    
    # Functions
    'init_db',
    'get_session',
    
    # Service
    'DatabaseService',
    'db_service'
]
