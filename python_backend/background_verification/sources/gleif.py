"""
GLEIF (Global Legal Entity Identifier Foundation) API integration.
"""

import requests
from typing import List, Dict
from utils.logging_config import get_logger
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

BASE = "https://api.gleif.org/api/v1/lei-records"

async def search_by_name(name: str, limit: int = 3) -> List[Dict]:
    """Search for companies by name in GLEIF database with caching."""
    try:
        params = {"filter[entity.legalName]": name, "page[size]": limit}
        
        # Use cached API client
        response = await cached_api_client.get(
            BASE,
            params=params,
            cache_key_prefix='gleif',
            cache_ttl=3600  # Cache for 1 hour
        )
        
        data = response['data']
        out = []
        for item in data.get("data", [])[:limit]:
            attr = item.get("attributes", {})
            out.append({
                "lei": item.get("id"),
                "legal_name": attr.get("entity", {}).get("legalName", {}).get("name"),
                "status": attr.get("registration", {}).get("status"),
                "country": attr.get("entity", {}).get("legalAddress", {}).get("country"),
            })
        logger.info(f"GLEIF search for '{name}' returned {len(out)} results")
        return out
    except Exception as e:
        logger.error(f"GLEIF search failed for '{name}': {e}")
        return []
