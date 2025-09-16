"""
Digital footprint analysis using SerpAPI and other sources.
"""

import requests
from typing import List, Dict, Optional, Any
from utils.logging_config import get_logger
from utils.config import get_settings
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

class DigitalFootprintService:
    """Service for analyzing digital footprint and online presence."""
    
    def __init__(self, serpapi_key: Optional[str] = None):
        """Initialize the digital footprint service."""
        self.serpapi_key = serpapi_key
    
    async def analyze_digital_footprint(self, full_name: str, email: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Analyze digital footprint for a person."""
        try:
            results = {
                "google_search": [],
                "social_media": {},
                "professional_networks": {},
                "sources_used": [],
                "score": 0.5,
                "rationale": []
            }
            
            # Google search for the person
            if self.serpapi_key:
                try:
                    google_results = await self._search_google(full_name, email)
                    results["google_search"] = google_results
                    results["sources_used"].append("serpapi")
                    results["rationale"].append("Google search performed via SerpAPI")
                except Exception as e:
                    logger.error(f"Google search failed: {e}")
                    results["rationale"].append("Google search failed")
            else:
                results["rationale"].append("SerpAPI key not provided, skipping Google search")
            
            # Calculate score based on findings
            score = self._calculate_footprint_score(results)
            results["score"] = score
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing digital footprint: {e}")
            return {
                "error": str(e),
                "score": 0.0,
                "sources_used": [],
                "rationale": [f"Analysis failed: {str(e)}"]
            }
    
    async def _search_google(self, full_name: str, email: str) -> List[Dict]:
        """Search Google for information about the person."""
        try:
            # Search for the person's name with professional context
            name_results = await self._serpapi_search(f"\"{full_name}\"")
            
            # Search for name + specific professional terms
            professional_results = await self._serpapi_search(f"\"{full_name}\" linkedin")
            
            # Search for name + company context (if we can extract it)
            company_results = await self._serpapi_search(f"\"{full_name}\" amazon aws")
            
            # Search for email if provided
            email_results = []
            if email:
                email_results = await self._serpapi_search(f"\"{email}\"")
            
            # Combine and deduplicate results
            all_results = name_results + professional_results + company_results + email_results
            unique_results = []
            seen_urls = set()
            
            for result in all_results:
                url = result.get('link', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            return unique_results[:10]  # Limit to top 10 results
            
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    async def _serpapi_search(self, query: str) -> List[Dict]:
        """Perform a search using SerpAPI with caching."""
        try:
            logger.info(f"Searching SerpAPI with query: '{query}'")
            params = {
                'q': query,
                'api_key': self.serpapi_key,
                'engine': 'google',
                'num': 10
            }
            
            # Use cached API client
            response = await cached_api_client.get(
                'https://serpapi.com/search.json',
                params=params,
                cache_key_prefix='serpapi',
                cache_ttl=1800  # Cache for 30 minutes
            )
            
            data = response['data']
            results = []
            
            for result in data.get('organic_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'source': 'google'
                })
            
            logger.info(f"SerpAPI search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI search failed for '{query}': {e}")
            return []
    
    def _calculate_footprint_score(self, results: Dict[str, Any]) -> float:
        """Calculate digital footprint score based on findings."""
        try:
            score = 0.3  # Base score (lower base since we want to reward actual presence)
            
            # Google search results
            google_results = results.get('google_search', [])
            if google_results:
                # More results = higher score (up to 0.4 points)
                result_count = len(google_results)
                if result_count >= 8:
                    score += 0.4
                elif result_count >= 5:
                    score += 0.3
                elif result_count >= 3:
                    score += 0.2
                elif result_count >= 1:
                    score += 0.1
            
            # Check for professional indicators (more weight)
            professional_keywords = ['linkedin', 'github', 'stackoverflow', 'researchgate', 'scholar']
            professional_platforms_found = set()
            
            for result in google_results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                link = result.get('link', '').lower()
                content = f"{title} {snippet} {link}"
                
                for keyword in professional_keywords:
                    if keyword in content:
                        professional_platforms_found.add(keyword)
                        break
            
            # Reward professional platform presence (up to 0.3 points)
            platform_count = len(professional_platforms_found)
            if platform_count >= 3:
                score += 0.3
            elif platform_count >= 2:
                score += 0.2
            elif platform_count >= 1:
                score += 0.1
            
            # Bonus for LinkedIn specifically (strong professional indicator)
            if 'linkedin' in professional_platforms_found:
                score += 0.1
            
            # Cap score at 1.0
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating footprint score: {e}")
            return 0.5
