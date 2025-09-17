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
        # Try multiple search variations for better matching
        search_terms = [name]
        
        # Add parent company searches for known subsidiaries
        company_mappings = {
            "amazon web services": ["amazon.com", "amazon"],
            "aws": ["amazon.com", "amazon"],
            "microsoft azure": ["microsoft", "microsoft corporation"],
            "google cloud": ["google", "alphabet"],
            "meta": ["facebook", "meta platforms"],
            "facebook": ["meta platforms", "meta"]
        }
        
        if name.lower() in company_mappings:
            search_terms.extend(company_mappings[name.lower()])
        
        all_results = []
        
        for search_term in search_terms:
            params = {"filter[entity.legalName]": search_term, "page[size]": limit}
            
            # Use cached API client
            response = await cached_api_client.get(
                BASE,
                params=params,
                cache_key_prefix='gleif',
                cache_ttl=3600  # Cache for 1 hour
            )
            
            data = response['data']
            # Handle both direct data array and nested data structure
            items = data if isinstance(data, list) else data.get("data", [])
            for item in items[:limit]:
                if not isinstance(item, dict):
                    continue
                attr = item.get("attributes", {})
                result = {
                    "lei": item.get("id"),
                    "legal_name": attr.get("entity", {}).get("legalName", {}).get("name"),
                    "status": attr.get("registration", {}).get("status"),
                    "country": attr.get("entity", {}).get("legalAddress", {}).get("country"),
                }
                # Avoid duplicates
                if not any(r["lei"] == result["lei"] for r in all_results):
                    all_results.append(result)
        
        logger.info(f"GLEIF search for '{name}' returned {len(all_results)} results")
        return all_results[:limit]
    except Exception as e:
        logger.error(f"GLEIF search failed for '{name}': {e}")
        return []
