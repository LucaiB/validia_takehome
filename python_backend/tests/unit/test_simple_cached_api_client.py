"""
Simple unit tests for cached API client.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from utils.cached_api_client import cached_api_client


class TestSimpleCachedAPIClient:
    """Simple test cases for CachedAPIClient."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear cache before each test
        import asyncio
        asyncio.run(cached_api_client.clear())

    def test_generate_cache_key(self):
        """Test cache key generation."""
        url = "https://api.example.com/test"
        params = {"key": "value"}
        headers = {"Authorization": "Bearer token"}
        data = {"data": "test"}
        
        # Test GET request
        key1 = cached_api_client._generate_cache_key("GET", url, params=params, headers=headers)
        key2 = cached_api_client._generate_cache_key("GET", url, params=params, headers=headers)
        
        assert key1 == key2  # Same parameters should generate same key
        
        # Test POST request
        key3 = cached_api_client._generate_cache_key("POST", url, data=data, headers=headers)
        key4 = cached_api_client._generate_cache_key("POST", url, data=data, headers=headers)
        
        assert key3 == key4  # Same parameters should generate same key
        assert key1 != key3  # Different methods should generate different keys

    def test_generate_cache_key_different_params(self):
        """Test cache key generation with different parameters."""
        url = "https://api.example.com/test"
        
        key1 = cached_api_client._generate_cache_key("GET", url, params={"key1": "value1"})
        key2 = cached_api_client._generate_cache_key("GET", url, params={"key2": "value2"})
        
        assert key1 != key2  # Different parameters should generate different keys

    def test_generate_cache_key_different_headers(self):
        """Test cache key generation with different headers."""
        url = "https://api.example.com/test"
        
        key1 = cached_api_client._generate_cache_key("GET", url, headers={"Authorization": "Bearer token1"})
        key2 = cached_api_client._generate_cache_key("GET", url, headers={"Authorization": "Bearer token2"})
        
        assert key1 != key2  # Different headers should generate different keys

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test cache clearing."""
        # This should not raise an exception
        await cached_api_client.clear()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test cache statistics."""
        stats = await cached_api_client.get_stats()
        
        assert "max_size" in stats
        assert "size" in stats
        assert "utilization" in stats
        assert isinstance(stats["max_size"], int)
        assert isinstance(stats["size"], int)
        assert isinstance(stats["utilization"], float)
