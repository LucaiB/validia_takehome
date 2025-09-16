"""
Caching utilities for API responses and analysis results.
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio
from utils.logging_config import get_logger

logger = get_logger(__name__)

class CacheEntry:
    """Cache entry with expiration."""
    
    def __init__(self, value: Any, ttl_seconds: int = 3600):
        """
        Initialize cache entry.
        
        Args:
            value: Cached value
            ttl_seconds: Time to live in seconds
        """
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def get_value(self) -> Optional[Any]:
        """Get value if not expired."""
        if self.is_expired():
            return None
        return self.value

class MemoryCache:
    """In-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            entry = self.cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self.cache[key]
                logger.debug(f"Cache entry expired for key: {key}")
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return entry.get_value()
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in cache."""
        async with self._lock:
            # Remove expired entries if cache is full
            if len(self.cache) >= self.max_size:
                await self._cleanup_expired()
                
                # If still full, remove oldest entry
                if len(self.cache) >= self.max_size:
                    oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
                    del self.cache[oldest_key]
                    logger.debug(f"Removed oldest cache entry: {oldest_key}")
            
            self.cache[key] = CacheEntry(value, ttl_seconds)
            logger.debug(f"Cached value for key: {key} (TTL: {ttl_seconds}s)")
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Deleted cache entry: {key}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            await self._cleanup_expired()
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size * 100
            }

def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from prefix and parameters."""
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    key_data = f"{prefix}:{json.dumps(sorted_kwargs, sort_keys=True)}"
    return hashlib.md5(key_data.encode()).hexdigest()

# Global cache instances
api_cache = MemoryCache(max_size=500)  # For API responses
analysis_cache = MemoryCache(max_size=200)  # For analysis results
