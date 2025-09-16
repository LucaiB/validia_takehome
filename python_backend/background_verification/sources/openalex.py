"""
OpenAlex API integration for academic verification.
"""

import requests
from typing import List, Dict, Optional
from utils.logging_config import get_logger
from utils.config import get_settings
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

BASE = "https://api.openalex.org"

async def search_authors(name: str, institution: Optional[str] = None, limit: int = 3) -> List[Dict]:
    """Search for authors by name in OpenAlex database with caching."""
    try:
        # Use exact search without stemming for better precision
        params = {
            "search": name, 
            "per-page": limit,
            "sort": "cited_by_count:desc"  # Sort by most cited first
        }
        
        if institution:
            # Use exact institution search without stemming
            params["filter"] = f"last_known_institution.display_name.search.no_stem:{institution}"
        
        headers = {"Accept": "application/json"}
        settings = get_settings()
        if settings.openalex_contact_email:
            params["mailto"] = settings.openalex_contact_email
            
        response = await cached_api_client.get(
            f"{BASE}/authors",
            params=params,
            headers=headers,
            cache_key_prefix='openalex_authors',
            cache_ttl=3600  # Cache for 1 hour
        )
        
        data = response['data']
        out = []
        for a in data.get("results", [])[:limit]:
            out.append({
                "id": a.get("id"),
                "display_name": a.get("display_name"),
                "last_known_institution": (a.get("last_known_institution") or {}).get("display_name"),
                "works_count": a.get("works_count"),
                "cited_by_count": a.get("cited_by_count"),
            })
        logger.info(f"OpenAlex search for '{name}' returned {len(out)} results")
        return out
    except Exception as e:
        logger.error(f"OpenAlex search failed for '{name}': {e}")
        return []

async def search_institutions(name: str, limit: int = 3) -> List[Dict]:
    """Search for institutions by name in OpenAlex database with caching."""
    try:
        # Use exact search without stemming for better precision
        params = {
            "search": name,
            "per-page": limit,
            "sort": "display_name"  # Sort alphabetically
        }
        
        headers = {"Accept": "application/json"}
        settings = get_settings()
        if settings.openalex_contact_email:
            params["mailto"] = settings.openalex_contact_email
            
        response = await cached_api_client.get(
            f"{BASE}/institutions",
            params=params,
            headers=headers,
            cache_key_prefix='openalex_institutions',
            cache_ttl=3600  # Cache for 1 hour
        )
        
        data = response['data']
        out = []
        for inst in data.get("results", [])[:limit]:
            out.append({
                "id": inst.get("id"),
                "display_name": inst.get("display_name"),
                "country_code": inst.get("country_code"),
                "type": inst.get("type"),
                "works_count": inst.get("works_count"),
                "cited_by_count": inst.get("cited_by_count"),
            })
        logger.info(f"OpenAlex institution search for '{name}' returned {len(out)} results")
        return out
    except Exception as e:
        logger.error(f"OpenAlex institution search failed for '{name}': {e}")
        return []
