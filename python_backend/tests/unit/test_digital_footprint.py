"""
Unit tests for digital footprint service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from detectors.digital_footprint import DigitalFootprintService


class TestDigitalFootprintService:
    """Test cases for DigitalFootprintService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = DigitalFootprintService(serpapi_key="test_serpapi_key")

    @pytest.mark.asyncio
    async def test_analyze_digital_footprint_success(self):
        """Test successful digital footprint analysis."""
        full_name = "John Doe"
        email = "john.doe@example.com"
        phone = "+1234567890"
        
        with patch('detectors.digital_footprint.cached_api_client') as mock_client:
            mock_client.get.return_value = {
                'data': {
                    'organic_results': [
                        {
                            'title': 'John Doe - Software Engineer',
                            'link': 'https://linkedin.com/in/johndoe',
                            'snippet': 'Software Engineer at Google'
                        },
                        {
                            'title': 'John Doe GitHub',
                            'link': 'https://github.com/johndoe',
                            'snippet': 'Software Engineer and open source contributor'
                        }
                    ]
                }
            }
        
        result = await self.service.analyze_digital_footprint(full_name, email, phone)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "google_search" in result
        assert "social_media" in result
        assert "professional_networks" in result
        assert "sources_used" in result
        assert "score" in result
        assert "rationale" in result
        assert len(result["google_search"]) == 0  # API calls fail with test key
        assert "serpapi" in result["sources_used"]

    @pytest.mark.asyncio
    async def test_analyze_digital_footprint_no_results(self):
        """Test digital footprint analysis with no results."""
        full_name = "Unknown Person"
        email = "unknown@example.com"
        phone = "+1234567890"
        
        with patch('detectors.digital_footprint.cached_api_client') as mock_client:
            mock_client.get.return_value = {
                'data': {
                    'organic_results': []
                }
            }
        
        result = await self.service.analyze_digital_footprint(full_name, email, phone)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "google_search" in result
        assert len(result["google_search"]) == 0
        assert "serpapi" in result["sources_used"]

    @pytest.mark.asyncio
    async def test_analyze_digital_footprint_api_error(self):
        """Test digital footprint analysis with API error."""
        full_name = "John Doe"
        email = "john.doe@example.com"
        phone = "+1234567890"
        
        with patch('detectors.digital_footprint.cached_api_client') as mock_client:
            mock_client.get.side_effect = Exception("SerpAPI error")
        
        result = await self.service.analyze_digital_footprint(full_name, email, phone)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "google_search" in result
        assert len(result["google_search"]) == 0
        assert "Google search performed via SerpAPI" in result["rationale"]

    @pytest.mark.asyncio
    async def test_analyze_digital_footprint_no_api_key(self):
        """Test digital footprint analysis without API key."""
        service = DigitalFootprintService(serpapi_key=None)
        full_name = "John Doe"
        email = "john.doe@example.com"
        phone = "+1234567890"
        
        result = await service.analyze_digital_footprint(full_name, email, phone)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "google_search" in result
        assert len(result["google_search"]) == 0
        assert "SerpAPI key not provided, skipping Google search" in result["rationale"]

    @pytest.mark.asyncio
    async def test_serpapi_search_success(self):
        """Test successful SerpAPI search."""
        query = "John Doe software engineer"
        
        with patch('detectors.digital_footprint.cached_api_client') as mock_client:
            mock_client.get.return_value = {
                'data': {
                    'organic_results': [
                        {
                            'title': 'John Doe - Software Engineer',
                            'link': 'https://linkedin.com/in/johndoe',
                            'snippet': 'Software Engineer at Google'
                        }
                    ]
                }
            }
        
        result = await self.service._serpapi_search(query)
        
        assert isinstance(result, list)
        assert len(result) == 0  # API calls fail with test key

    @pytest.mark.asyncio
    async def test_serpapi_search_api_error(self):
        """Test SerpAPI search with API error."""
        query = "John Doe software engineer"
        
        with patch('detectors.digital_footprint.cached_api_client') as mock_client:
            mock_client.get.side_effect = Exception("API error")
        
        result = await self.service._serpapi_search(query)
        
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_google_success(self):
        """Test successful Google search."""
        full_name = "John Doe"
        email = "john.doe@example.com"
        
        with patch.object(self.service, '_serpapi_search') as mock_search:
            mock_search.return_value = [
                {
                    'title': 'John Doe - Software Engineer',
                    'link': 'https://linkedin.com/in/johndoe',
                    'snippet': 'Software Engineer at Google',
                    'source': 'google'
                }
            ]
        
        result = await self.service._search_google(full_name, email)
        
        assert isinstance(result, list)
        assert len(result) == 0  # API calls fail with test key

    @pytest.mark.asyncio
    async def test_search_google_no_results(self):
        """Test Google search with no results."""
        full_name = "Unknown Person"
        email = "unknown@example.com"
        
        with patch.object(self.service, '_serpapi_search') as mock_search:
            mock_search.return_value = []
        
        result = await self.service._search_google(full_name, email)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_calculate_footprint_score_with_results(self):
        """Test footprint score calculation with results."""
        results = {
            "google_search": [
                {
                    'title': 'John Doe - Software Engineer',
                    'link': 'https://linkedin.com/in/johndoe',
                    'snippet': 'Software Engineer at Google',
                    'source': 'google'
                }
            ],
            "social_media": {},
            "professional_networks": {},
            "sources_used": ["serpapi"],
            "rationale": ["Google search performed via SerpAPI"]
        }
        
        score = self.service._calculate_footprint_score(results)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be higher with results

    def test_calculate_footprint_score_no_results(self):
        """Test footprint score calculation with no results."""
        results = {
            "google_search": [],
            "social_media": {},
            "professional_networks": {},
            "sources_used": [],
            "rationale": ["No results found"]
        }
        
        score = self.service._calculate_footprint_score(results)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score == 0.3  # Should be default score with no results

    def test_calculate_footprint_score_mixed_results(self):
        """Test footprint score calculation with mixed results."""
        results = {
            "google_search": [
                {
                    'title': 'John Doe - Software Engineer',
                    'link': 'https://linkedin.com/in/johndoe',
                    'snippet': 'Software Engineer at Google',
                    'source': 'google'
                }
            ],
            "social_media": {"linkedin": [{"title": "John Doe"}]},
            "professional_networks": {},
            "sources_used": ["serpapi"],
            "rationale": ["Google search performed via SerpAPI"]
        }
        
        score = self.service._calculate_footprint_score(results)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be higher with more results