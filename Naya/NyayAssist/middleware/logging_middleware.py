"""
FastAPI Middleware for Database Logging
Logs all API requests and responses to MySQL database
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from database.db_service import db_service


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API access to database"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Get request details
        endpoint = str(request.url.path)
        http_method = request.method
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Get user info from headers/session if available
        user_id = None
        user_uuid = request.headers.get("X-User-UUID")
        session_id = request.headers.get("X-Session-ID")
        
        # Try to get request body (for POST requests)
        request_body = None
        if http_method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode())
                    # Don't log sensitive fields
                    if "password" in request_body:
                        request_body["password"] = "[REDACTED]"
                    if "password_hash" in request_body:
                        request_body["password_hash"] = "[REDACTED]"
            except:
                pass
        
        # Process request
        response = None
        error_message = None
        
        try:
            response = await call_next(request)
            response_status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            response_status_code = 500
            raise
        finally:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log to database (non-blocking, ignore errors)
            try:
                # Skip logging for health checks and static files
                if endpoint not in ["/health", "/", "/docs", "/openapi.json", "/favicon.ico"]:
                    db_service.log_access(
                        endpoint=endpoint,
                        http_method=http_method,
                        user_id=user_id,
                        user_uuid=user_uuid,
                        session_id=session_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_body=request_body,
                        response_status_code=response_status_code,
                        response_time_ms=response_time_ms,
                        error_message=error_message
                    )
            except Exception as log_error:
                # Don't let logging errors affect the response
                print(f"Failed to log access: {log_error}")
        
        return response


def get_client_ip(request: Request) -> str:
    """Get the real client IP, considering proxies"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
