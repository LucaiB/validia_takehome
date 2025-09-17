"""
SEC EDGAR API integration for company verification.
"""

import requests
from typing import Dict, Any, Optional
from utils.logging_config import get_logger
from utils.config import get_settings
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

_TICKERS_CACHE: Optional[Dict[str, Any]] = None

def _get_headers() -> Dict[str, str]:
    """Get headers for SEC API requests."""
    settings = get_settings()
    return {
        "User-Agent": f"background-verifier/1.0 ({settings.sec_contact_email})",
        "Accept": "application/json"
    }

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

async def _load_tickers() -> Dict[str, Any]:
    """Load SEC company tickers data with caching."""
    global _TICKERS_CACHE
    if _TICKERS_CACHE is not None:
        return _TICKERS_CACHE
    try:
        response = await cached_api_client.get(
            TICKERS_URL,
            headers=_get_headers(),
            cache_key_prefix='sec_tickers',
            cache_ttl=86400  # Cache for 24 hours
        )
        _TICKERS_CACHE = response['data']
        logger.info(f"Loaded {len(_TICKERS_CACHE)} SEC tickers")
        return _TICKERS_CACHE
    except Exception as e:
        logger.error(f"Failed to load SEC tickers: {e}")
        return {}

async def find_company_like(name: str) -> Optional[Dict[str, Any]]:
    """Find a company similar to the given name in SEC database."""
    try:
        data = await _load_tickers()
        if not data:
            return None
            
        name_low = name.lower()
        best = None
        best_sim = 0.0
        
        # Known company mappings for better matching
        company_mappings = {
            "amazon web services": "amazon",
            "aws": "amazon",
            "microsoft azure": "microsoft",
            "google cloud": "google",
            "alphabet": "google",
            "meta": "facebook",
            "facebook": "meta"
        }
        
        # Check for direct mappings first
        search_name = company_mappings.get(name_low, name_low)
        
        for _, rec in data.items():
            comp = rec.get("title", "").lower()
            
            # Check for exact word matches (more lenient)
            comp_words = set(comp.split())
            name_words = set(search_name.split())
            
            if comp_words and name_words:
                # Calculate similarity based on word overlap
                overlap = len(comp_words & name_words)
                total_words = len(comp_words | name_words)
                sim = overlap / max(1, total_words) if total_words > 0 else 0
                
                # Boost score for major company name matches
                if any(major in comp for major in ["amazon", "microsoft", "google", "apple", "meta", "tesla", "netflix"]):
                    if any(major in search_name for major in ["amazon", "microsoft", "google", "apple", "meta", "tesla", "netflix"]):
                        sim = max(sim, 0.8)  # High confidence for major companies
                
                if sim > best_sim:
                    best, best_sim = rec, sim
        
        if best and best_sim > 0.2:  # Lowered threshold for better matching
            logger.info(f"SEC found company '{best.get('title')}' for '{name}' (similarity: {best_sim:.2f})")
            return best
        return None
    except Exception as e:
        logger.error(f"SEC company search failed for '{name}': {e}")
        return None
