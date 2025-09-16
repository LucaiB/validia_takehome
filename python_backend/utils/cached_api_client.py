"""
Cached API client for external API calls.
"""

import asyncio
import httpx
import json
from typing import Any, Dict, Optional
from utils.cache import api_cache, generate_cache_key
from utils.logging_config import get_logger

logger = get_logger(__name__)

class CachedAPIClient:
    """HTTP client with caching for external API calls."""
    
    def __init__(self, timeout: int = 10, cache_ttl: int = 3600):
        """
        Initialize cached API client.
        
        Args:
            timeout: Request timeout in seconds
            cache_ttl: Cache TTL in seconds
        """
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, 
                  cache_key_prefix: str = "api", cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Make cached GET request.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            cache_key_prefix: Prefix for cache key
            cache_ttl: Override default cache TTL
            
        Returns:
            Response data
        """
        # Generate cache key
        cache_key = generate_cache_key(
            cache_key_prefix,
            url=url,
            params=params or {},
            headers=headers or {}
        )
        
        # Try to get from cache
        cached_result = await api_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for API call: {url}")
            return cached_result
        
        # Make API call
        try:
            logger.info(f"Making API call: {url}")
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            result = {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
            
            # Cache the result
            ttl = cache_ttl or self.cache_ttl
            await api_cache.set(cache_key, result, ttl)
            logger.info(f"Cached API response for: {url}")
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"API call failed: {url} - {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API call: {url} - {e}")
            raise
    
    async def post(self, url: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None,
                   headers: Optional[Dict] = None, cache_key_prefix: str = "api_post", 
                   cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Make cached POST request.
        
        Args:
            url: Request URL
            data: Form data
            json_data: JSON data
            headers: Request headers
            cache_key_prefix: Prefix for cache key
            cache_ttl: Override default cache TTL
            
        Returns:
            Response data
        """
        # Generate cache key
        cache_key = generate_cache_key(
            cache_key_prefix,
            url=url,
            data=data or {},
            json_data=json_data or {},
            headers=headers or {}
        )
        
        # Try to get from cache
        cached_result = await api_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for API POST call: {url}")
            return cached_result
        
        # Make API call
        try:
            logger.info(f"Making API POST call: {url}")
            response = await self.client.post(
                url, 
                data=data, 
                json=json_data, 
                headers=headers
            )
            response.raise_for_status()
            
            result = {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
            
            # Cache the result
            ttl = cache_ttl or self.cache_ttl
            await api_cache.set(cache_key, result, ttl)
            logger.info(f"Cached API POST response for: {url}")
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"API POST call failed: {url} - {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API POST call: {url} - {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def clear(self):
        """Clear the cache."""
        await api_cache.clear()
    
    async def get_stats(self):
        """Get cache statistics."""
        return await api_cache.get_stats()
    
    def _generate_cache_key(self, method: str, url: str, **kwargs) -> str:
        """Generate cache key for request."""
        return generate_cache_key(
            f"{method}_{url}",
            **kwargs
        )

# Global cached API client
cached_api_client = CachedAPIClient(timeout=10, cache_ttl=3600)
