import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.logging import log_access, error_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Get client info
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Process request
        try:
            response: Response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log the request
            log_access(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_time=round(response_time * 1000, 2),  # ms
                ip_address=client_ip,
                user_agent=user_agent
            )
            
            return response
            
        except Exception as e:
            # Calculate response time for failed requests
            response_time = time.time() - start_time
            
            # Log the error
            error_logger.error(f"Request failed: {str(e)}", extra={
                'operation': 'request_error',
                'method': request.method,
                'path': str(request.url.path),
                'ip_address': client_ip,
                'response_time': round(response_time * 1000, 2),
                'error_type': type(e).__name__
            })
            
            # Re-raise the exception
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
