"""
Rate limiting middleware for FastAPI.
"""

import time
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from utils.rate_limiter import client_rate_limiter, global_rate_limiter, get_client_id
from utils.logging_config import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app, skip_paths: list = None):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI app instance
            skip_paths: List of paths to skip rate limiting
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/docs", "/openapi.json", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Skip rate limiting for non-API paths (except test endpoints)
        if not request.url.path.startswith("/api/") and not request.url.path.startswith("/analyze") and not request.url.path.startswith("/test-"):
            return await call_next(request)
        
        try:
            # Check global rate limit
            if not await global_rate_limiter.is_allowed():
                logger.warning("Global rate limit exceeded")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Global rate limit exceeded",
                        "message": "Too many requests across all clients. Please try again later.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
            
            # Check client rate limit
            client_id = get_client_id(request)
            if not await client_rate_limiter.is_allowed(client_id):
                remaining = await client_rate_limiter.get_remaining_requests(client_id)
                reset_time = await client_rate_limiter.get_reset_time(client_id)
                
                logger.warning(f"Client rate limit exceeded for {client_id}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: 5 requests per minute.",
                        "remaining_requests": remaining,
                        "retry_after": 60,
                        "reset_time": reset_time
                    },
                    headers={"Retry-After": "60"}
                )
            
            # Add rate limit headers to response
            response = await call_next(request)
            remaining = await client_rate_limiter.get_remaining_requests(client_id)
            response.headers["X-RateLimit-Limit"] = "5"
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request to proceed if rate limiting fails
            return await call_next(request)
