"""
Rate limiting utilities for API protection.
"""

import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import hashlib
import json
from utils.logging_config import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiter using sliding window algorithm."""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: Unique identifier for client (IP, user ID, etc.)
            
        Returns:
            True if request is allowed, False otherwise
        """
        async with self._lock:
            now = time.time()
            client_requests = self.requests[client_id]
            
            # Remove old requests outside the window
            while client_requests and client_requests[0] <= now - self.window_seconds:
                client_requests.popleft()
            
            # Check if we're under the limit
            if len(client_requests) < self.max_requests:
                client_requests.append(now)
                logger.info(f"Rate limit check passed for {client_id}: {len(client_requests)}/{self.max_requests} requests")
                return True
            else:
                logger.warning(f"Rate limit exceeded for {client_id}: {len(client_requests)}/{self.max_requests} requests")
                return False
    
    async def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client."""
        async with self._lock:
            now = time.time()
            client_requests = self.requests[client_id]
            
            # Remove old requests
            while client_requests and client_requests[0] <= now - self.window_seconds:
                client_requests.popleft()
            
            return max(0, self.max_requests - len(client_requests))
    
    async def get_reset_time(self, client_id: str) -> Optional[float]:
        """Get time when rate limit resets for client."""
        async with self._lock:
            client_requests = self.requests[client_id]
            if not client_requests:
                return None
            return client_requests[0] + self.window_seconds

class GlobalRateLimiter:
    """Global rate limiter for system-wide protection."""
    
    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        """
        Initialize global rate limiter.
        
        Args:
            max_requests: Maximum total requests across all clients
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def is_allowed(self) -> bool:
        """Check if global request is allowed."""
        async with self._lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()
            
            # Check if we're under the limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                logger.info(f"Global rate limit check passed: {len(self.requests)}/{self.max_requests} requests")
                return True
            else:
                logger.warning(f"Global rate limit exceeded: {len(self.requests)}/{self.max_requests} requests")
                return False

# Global instances
client_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5 requests per minute per client
global_rate_limiter = GlobalRateLimiter(max_requests=50, window_seconds=60)  # 50 total requests per minute

def get_client_id(request) -> str:
    """Extract client ID from request."""
    # Try to get real IP from headers (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"
