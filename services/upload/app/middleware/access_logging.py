import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import access_logger

class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        elif "x-real-ip" in request.headers:
            client_ip = request.headers["x-real-ip"]
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Get authentication info
        auth_type = "None"
        user_id = "Anonymous"
        
        # Check for JWT authentication
        if "authorization" in request.headers:
            auth_type = "JWT"
            # We'll update this in the auth functions
        elif "x-service-token" in request.headers:
            auth_type = "Service"
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log the access
            log_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "client_ip": client_ip,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "response_time_ms": round(process_time * 1000, 2),
                "user_agent": user_agent,
                "auth_type": auth_type,
                "user_id": user_id
            }
            
            # Log as JSON for easy parsing
            access_logger.info(json.dumps(log_data))
            
            return response
            
        except Exception as e:
            # Log errors
            process_time = time.time() - start_time
            log_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "client_ip": client_ip,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": 500,
                "response_time_ms": round(process_time * 1000, 2),
                "error": str(e),
                "auth_type": auth_type,
                "user_id": user_id
            }
            
            access_logger.error(json.dumps(log_data))
            raise
