"""
US College Scorecard API integration for education verification.
"""

import requests
from typing import List, Dict
from utils.logging_config import get_logger
from utils.config import get_settings
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

BASE = "https://api.data.gov/ed/collegescorecard/v1/schools"

async def search_institution(name: str, limit: int = 3) -> List[Dict]:
    """Search for educational institutions in College Scorecard database with caching."""
    try:
        settings = get_settings()
        # Use college_scorecard_key if available, otherwise fall back to datagov_api_key
        api_key = settings.college_scorecard_key or settings.datagov_api_key
        if not api_key or api_key in ["your_college_scorecard_key_here", "your_datagov_key_here"]:
            logger.info("College Scorecard API key not provided, skipping College Scorecard search")
            return []
            
        params = {
            "api_key": api_key, 
            "school.name": name, 
            "per_page": limit,
            "fields": "id,school.name,school.city,school.state,school.operating"
        }
        
        response = await cached_api_client.get(
            BASE,
            params=params,
            cache_key_prefix='college_scorecard',
            cache_ttl=3600  # Cache for 1 hour
        )
        
        data = response['data']
        out = []
        for s in data.get("results", [])[:limit]:
            out.append({
                "name": s.get("school.name"),
                "city": s.get("school.city"),
                "state": s.get("school.state"),
                "zip": s.get("school.zip"),
                "operating": s.get("school.operating")
            })
        logger.info(f"College Scorecard search for '{name}' returned {len(out)} results")
        return out
    except Exception as e:
        logger.error(f"College Scorecard search failed for '{name}': {e}")
        return []
