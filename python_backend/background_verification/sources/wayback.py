"""
Wayback Machine CDX API integration for domain history.
"""

import requests
from typing import Optional, Dict, Any
from utils.logging_config import get_logger
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

CDX = "https://web.archive.org/cdx/search/cdx"

async def first_last_capture(url: str) -> Optional[Dict[str, Any]]:
    """Get first and last capture dates for a URL from Wayback Machine with caching."""
    try:
        logger.info(f"Calling Wayback CDX API for {url}")
        
        # Optimized parameters based on best practices
        params = {
            "url": url,
            "output": "json",
            "matchType": "domain",  # Use domain matching instead of wildcard
            "filter": "statuscode:200",  # Only successful captures
            "fl": "timestamp,original,statuscode",  # Minimal fields
            "limit": 10,  # Limit results to avoid large responses
            "collapse": "digest",  # Remove near-identical captures
            "from": "1996",  # Start from when web archiving began
            "to": "2024"  # End at reasonable recent date
        }
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",  # Enable compression
            "User-Agent": "background-verifier/1.0 (contact@example.com)"
        }
        
        response = await cached_api_client.get(
            CDX,
            params=params,
            headers=headers,
            cache_key_prefix='wayback',
            cache_ttl=7200  # Cache for 2 hours
        )
        
        js = response['data']
        if not js or len(js) < 2:
            logger.info(f"Wayback found no captures for {url}")
            return None
            
        # js[0] is header row, get first and last actual captures
        first = js[1][0]  # timestamp (first field)
        last = js[-1][0]  # timestamp (first field)
        result = {"first": first, "last": last, "captures": len(js) - 1}
        logger.info(f"Wayback found {result['captures']} captures for {url} (first: {first}, last: {last})")
        return result
        
    except Exception as e:
        if "timeout" in str(e).lower():
            logger.warning(f"Wayback API timeout for {url} - skipping")
            return None
        logger.error(f"Wayback search failed for {url}: {e}")
        return None
