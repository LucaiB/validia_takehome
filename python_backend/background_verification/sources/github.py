"""
GitHub API integration for developer verification.
"""

import requests
from typing import Optional, Dict, Any, List
from utils.logging_config import get_logger
from utils.config import get_settings
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

BASE = "https://api.github.com"

def _get_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests."""
    h = {"Accept": "application/vnd.github+json"}
    settings = get_settings()
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h

async def user_overview(username: str) -> Optional[Dict[str, Any]]:
    """Get GitHub user overview with caching."""
    try:
        response = await cached_api_client.get(
            f"{BASE}/users/{username}",
            headers=_get_headers(),
            cache_key_prefix='github_user',
            cache_ttl=1800  # Cache for 30 minutes
        )
        
        data = response['data']
        logger.info(f"GitHub user {username} found: {data.get('public_repos', 0)} repos")
        return data
    except Exception as e:
        if "404" in str(e):
            logger.info(f"GitHub user {username} not found")
            return None
        logger.error(f"GitHub user fetch failed for {username}: {e}")
        return None

async def repos(username: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get GitHub user repositories with caching."""
    try:
        response = await cached_api_client.get(
            f"{BASE}/users/{username}/repos",
            headers=_get_headers(),
            params={"per_page": limit, "sort": "updated"},
            cache_key_prefix='github_repos',
            cache_ttl=1800  # Cache for 30 minutes
        )
        
        data = response['data']
        logger.info(f"GitHub found {len(data)} repos for {username}")
        return data
    except Exception as e:
        logger.error(f"GitHub repos fetch failed for {username}: {e}")
        return []
