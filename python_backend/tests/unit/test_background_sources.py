"""
Unit tests for background verification sources.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from background_verification.sources import gleif, sec, openalex, github, wayback, scorecard


class TestGLEIFSource:
    """Test cases for GLEIF source."""

    @pytest.mark.asyncio
    async def test_search_by_name_success(self):
        """Test successful GLEIF search."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    'data': [
                        {
                            'id': '2138004T8I4HK4Q6X453',
                            'attributes': {
                                'entity': {
                                    'legalName': {'name': 'Google LLC'},
                                    'legalAddress': {'country': 'US'}
                                },
                                'registration': {'status': 'ACTIVE'}
                            }
                        }
                    ]
                }
            }
            
            result = await gleif.search_by_name("Google")
            
            assert len(result) == 1
            assert result[0]['lei'] == '2138004T8I4HK4Q6X453'
            assert result[0]['legal_name'] == 'Google LLC'
            assert result[0]['status'] == 'ACTIVE'
            assert result[0]['country'] == 'US'

    @pytest.mark.asyncio
    async def test_search_by_name_no_results(self):
        """Test GLEIF search with no results."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {'data': {'data': []}}
            
            result = await gleif.search_by_name("Nonexistent Company")
            
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_by_name_api_error(self):
        """Test GLEIF search with API error."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await gleif.search_by_name("Google")
            
            assert len(result) == 0


class TestSECSource:
    """Test cases for SEC source."""

    @pytest.mark.asyncio
    async def test_find_company_like_success(self):
        """Test successful SEC company search."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    '0': {'title': 'Apple Inc.', 'ticker': 'AAPL', 'cik_str': '320193'},
                    '1': {'title': 'Microsoft Corporation', 'ticker': 'MSFT', 'cik_str': '789019'}
                }
            }
            
            result = await sec.find_company_like("Apple")
            
            assert result is not None
            assert result['title'] == 'Apple Inc.'
            assert result['ticker'] == 'AAPL'

    @pytest.mark.asyncio
    async def test_find_company_like_no_match(self):
        """Test SEC search with no matching company."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    '0': {'title': 'Apple Inc.', 'ticker': 'AAPL', 'cik_str': '320193'},
                    '1': {'title': 'Microsoft Corporation', 'ticker': 'MSFT', 'cik_str': '789019'}
                }
            }
            
            result = await sec.find_company_like("Nonexistent Company")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_find_company_like_api_error(self):
        """Test SEC search with API error."""
        # Clear the global tickers cache to ensure fresh test
        import background_verification.sources.sec as sec_module
        sec_module._TICKERS_CACHE = None
        
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await sec.find_company_like("Apple")
            
            assert result is None


class TestOpenAlexSource:
    """Test cases for OpenAlex source."""

    @pytest.mark.asyncio
    async def test_search_authors_success(self):
        """Test successful OpenAlex author search."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    'results': [
                        {
                            'id': 'https://openalex.org/A123456789',
                            'display_name': 'John Doe',
                            'last_known_institution': {'display_name': 'Stanford University'},
                            'works_count': 50,
                            'cited_by_count': 1000
                        }
                    ]
                }
            }
            
            result = await openalex.search_authors("John Doe")
            
            assert len(result) == 1
            assert result[0]['id'] == 'https://openalex.org/A123456789'
            assert result[0]['display_name'] == 'John Doe'
            assert result[0]['last_known_institution'] == 'Stanford University'
            assert result[0]['works_count'] == 50
            assert result[0]['cited_by_count'] == 1000

    @pytest.mark.asyncio
    async def test_search_authors_with_institution(self):
        """Test OpenAlex author search with institution filter."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {'data': {'results': []}}
            
            result = await openalex.search_authors("John Doe", "Stanford University")
            
            assert len(result) == 0
            # Verify the filter parameter was passed
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert 'filter' in call_args[1]['params']
            assert 'Stanford University' in call_args[1]['params']['filter']

    @pytest.mark.asyncio
    async def test_search_institutions_success(self):
        """Test successful OpenAlex institution search."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    'results': [
                        {
                            'id': 'https://openalex.org/I114027114',
                            'display_name': 'Stanford University',
                            'country_code': 'US',
                            'type': 'education',
                            'works_count': 100000,
                            'cited_by_count': 5000000
                        }
                    ]
                }
            }
            
            result = await openalex.search_institutions("Stanford University")
            
            assert len(result) == 1
            assert result[0]['id'] == 'https://openalex.org/I114027114'
            assert result[0]['display_name'] == 'Stanford University'
            assert result[0]['country_code'] == 'US'
            assert result[0]['type'] == 'education'

    @pytest.mark.asyncio
    async def test_search_authors_api_error(self):
        """Test OpenAlex author search with API error."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await openalex.search_authors("John Doe")
            
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_institutions_api_error(self):
        """Test OpenAlex institution search with API error."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await openalex.search_institutions("Stanford University")
            
            assert len(result) == 0


class TestGitHubSource:
    """Test cases for GitHub source."""

    @pytest.mark.asyncio
    async def test_user_overview_success(self):
        """Test successful GitHub user overview."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    'login': 'johndoe',
                    'public_repos': 50,
                    'followers': 100,
                    'following': 25,
                    'created_at': '2020-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                }
            }
            
            result = await github.user_overview("johndoe")
            
            assert result is not None
            assert result['login'] == 'johndoe'
            assert result['public_repos'] == 50
            assert result['followers'] == 100

    @pytest.mark.asyncio
    async def test_user_overview_not_found(self):
        """Test GitHub user overview for non-existent user."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("404 Not Found")
            
            result = await github.user_overview("nonexistentuser")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_repos_success(self):
        """Test successful GitHub repos fetch."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': [
                    {
                        'name': 'awesome-project',
                        'pushed_at': '2024-01-01T00:00:00Z',
                        'language': 'Python',
                        'stargazers_count': 10,
                        'forks_count': 5
                    },
                    {
                        'name': 'another-project',
                        'pushed_at': '2023-12-01T00:00:00Z',
                        'language': 'JavaScript',
                        'stargazers_count': 5,
                        'forks_count': 2
                    }
                ]
            }
            
            result = await github.repos("johndoe", limit=50)
            
            assert len(result) == 2
            assert result[0]['name'] == 'awesome-project'
            assert result[0]['language'] == 'Python'
            assert result[1]['name'] == 'another-project'
            assert result[1]['language'] == 'JavaScript'

    @pytest.mark.asyncio
    async def test_repos_api_error(self):
        """Test GitHub repos fetch with API error."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await github.repos("johndoe")
            
            assert len(result) == 0


class TestWaybackSource:
    """Test cases for Wayback source."""

    @pytest.mark.asyncio
    async def test_first_last_capture_success(self):
        """Test successful Wayback capture search."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': [
                    ['timestamp', 'original', 'statuscode'],  # Header row
                    ['19980101000000', 'https://example.com', '200'],
                    ['20240101000000', 'https://example.com', '200']
                ]
            }
            
            result = await wayback.first_last_capture("https://example.com")
            
            assert result is not None
            assert result['first'] == '19980101000000'
            assert result['last'] == '20240101000000'
            assert result['captures'] == 2

    @pytest.mark.asyncio
    async def test_first_last_capture_no_results(self):
        """Test Wayback search with no results."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {'data': []}
            
            result = await wayback.first_last_capture("https://nonexistent.com")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_first_last_capture_api_error(self):
        """Test Wayback search with API error."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await wayback.first_last_capture("https://example.com")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_first_last_capture_timeout(self):
        """Test Wayback search with timeout."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("timeout")
            
            result = await wayback.first_last_capture("https://example.com")
            
            assert result is None


class TestScorecardSource:
    """Test cases for College Scorecard source."""

    @pytest.mark.asyncio
    async def test_search_institution_success(self):
        """Test successful College Scorecard search."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {
                'data': {
                    'results': [
                        {
                            'school.name': 'Stanford University',
                            'school.city': 'Stanford',
                            'school.state': 'CA',
                            'school.zip': '94305',
                            'school.operating': 1
                        }
                    ]
                }
            }
            
            result = await scorecard.search_institution("Stanford University")
            
            assert len(result) == 1
            assert result[0]['name'] == 'Stanford University'
            assert result[0]['city'] == 'Stanford'
            assert result[0]['state'] == 'CA'
            assert result[0]['operating'] == 1

    @pytest.mark.asyncio
    async def test_search_institution_no_api_key(self):
        """Test College Scorecard search without API key."""
        # Clear cache to ensure fresh test
        from utils.cached_api_client import cached_api_client
        await cached_api_client.clear()
        
        with patch('background_verification.sources.scorecard.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                college_scorecard_key=None,
                datagov_api_key=None
            )
            
            result = await scorecard.search_institution("Stanford University")
            
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_institution_api_error(self):
        """Test College Scorecard search with API error."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await scorecard.search_institution("Stanford University")
            
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_institution_no_results(self):
        """Test College Scorecard search with no results."""
        with patch('utils.cached_api_client.cached_api_client.get') as mock_get:
            mock_get.return_value = {'data': {'results': []}}
            
            result = await scorecard.search_institution("Nonexistent University")
            
            assert len(result) == 0
