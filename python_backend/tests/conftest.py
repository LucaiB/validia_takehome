"""
Pytest configuration and fixtures for the fraud detection system.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Settings
from models.schemas import (
    CandidateInfo, AiDetectionResult, DocumentAuthenticityResult,
    ContactVerificationResult, BackgroundVerificationResult, DigitalFootprintResult
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings():
    """Create test settings with mock API keys."""
    return Settings(
        aws_access_key_id="test_access_key",
        aws_secret_access_key="test_secret_key",
        aws_region="us-east-1",
        numverify_api_key="test_numverify_key",
        abstract_api_key="test_abstract_key",
        serpapi_key="test_serpapi_key",
        github_token="test_github_token",
        openalex_contact_email="test@example.com",
        college_scorecard_key="test_college_key",
        sec_contact_email="test@example.com"
    )

@pytest.fixture
def mock_candidate_info():
    """Create mock candidate information."""
    return CandidateInfo(
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        location="New York, NY",
        linkedin="https://linkedin.com/in/johndoe",
        github="https://github.com/johndoe",
        website="https://johndoe.com"
    )

@pytest.fixture
def mock_ai_detection():
    """Create mock AI detection result."""
    return AiDetectionResult(
        is_ai_generated=False,
        confidence=25,
        model="claude-sonnet-4",
        rationale="Human-written content with natural patterns"
    )

@pytest.fixture
def mock_document_authenticity():
    """Create mock document authenticity result."""
    return DocumentAuthenticityResult(
        fileName="test_resume.pdf",
        fileSize=1024,
        fileType="application/pdf",
        creationDate="2024-01-01T00:00:00Z",
        modificationDate="2024-01-01T00:00:00Z",
        author="John Doe",
        creator="Microsoft Word",
        producer="Microsoft Word",
        title="John Doe Resume",
        subject="Software Engineer Resume",
        keywords="software, engineer, python, javascript",
        pdfVersion="1.4",
        pageCount=1,
        isEncrypted=False,
        hasDigitalSignature=False,
        softwareUsed="Microsoft Word",
        suspiciousIndicators=[],
        authenticityScore=85,
        rationale="Document appears authentic with standard metadata"
    )

@pytest.fixture
def mock_contact_verification():
    """Create mock contact verification result."""
    return {
        "email": {
            "input": "john.doe@example.com",
            "normalized": "john.doe@example.com",
            "syntax_valid": True,
            "domain_registrable": "example.com",
            "mx_records_found": True,
            "smtp_probe": "UNKNOWN",
            "is_disposable": False,
            "is_role": False,
            "notes": ["Found 5 MX records", "A record found"],
            "sources": ["email-validator", "dnspython", "publicsuffix2", "abstract-api"]
        },
        "phone": {
            "input": "+1234567890",
            "e164": "+1234567890",
            "valid": True,
            "country_code": "US",
            "region_hint": "New York",
            "toll_free": False,
            "carrier": "Verizon Wireless",
            "timezone": ["America/New_York"],
            "notes": ["libphonenumber parse/validate/geocode", "NumVerify: Numverify API"],
            "sources": ["libphonenumber", "numverify"]
        },
        "geo_consistency": {
            "stated_location": "New York, NY",
            "phone_country_matches": True,
            "phone_region_matches": True,
            "toll_free_conflict": False,
            "phone_region": "New York",
            "phone_country": "US",
            "is_toll_free": False,
            "method": "libphonenumber geocoder + toll-free rules",
            "sources": ["libphonenumber"]
        },
        "score": {
            "email_score": 1.0,
            "phone_score": 1.0,
            "geo_score": 1.0,
            "composite": 1.0
        },
        "rationale": [
            "Email syntax/MX and disposable checks executed.",
            "Phone parsed via libphonenumber; coarse region/toll‑free derived.",
            "Geo consistency evaluated using libphonenumber geocoder and rules."
        ]
    }

@pytest.fixture
def mock_background_verification():
    """Create mock background verification result."""
    return {
        "company_evidence": {
            "Google": {
                "gleif": [{"lei": "2138004T8I4HK4Q6X453", "legal_name": "Google LLC", "status": "ACTIVE", "country": "US"}],
                "sec": {"ticker": "GOOGL", "title": "Alphabet Inc.", "cik_str": "1652044"}
            }
        },
        "education_evidence": {
            "Stanford University": {
                "scorecard": [{"name": "Stanford University", "city": "Stanford", "state": "CA", "operating": 1}],
                "openalex": [{"id": "https://openalex.org/I114027114", "display_name": "Stanford University", "country_code": "US", "type": "education", "works_count": 100000, "cited_by_count": 5000000}]
            }
        },
        "developer_evidence": {
            "user": {"login": "johndoe", "public_repos": 50, "followers": 100},
            "repos": [{"name": "awesome-project", "pushed_at": "2024-01-01T00:00:00Z", "language": "Python"}]
        },
        "timeline_assessment": {
            "Google": {
                "plausible": True,
                "notes": ["Timeline appears consistent with company history"],
                "wayback": {"first": "19980101000000", "last": "20240101000000", "captures": 1000}
            }
        },
        "score": {
            "company_identity_score": 0.9,
            "education_institution_score": 1.0,
            "timeline_corroboration_score": 0.8,
            "developer_footprint_score": 0.7,
            "composite": 0.85
        },
        "rationale": [
            "Company identity checked via GLEIF and SEC EDGAR.",
            "Education validated via College Scorecard and OpenAlex.",
            "Timeline plausibility uses registry presence and optional Wayback snapshots.",
            "Developer evidence from GitHub profile and repo activity."
        ],
        "sources_used": ["GLEIF", "SEC EDGAR", "OpenAlex", "Wayback CDX", "GitHub", "US College Scorecard"]
    }

@pytest.fixture
def mock_digital_footprint():
    """Create mock digital footprint result."""
    return DigitalFootprintResult(
        social_presence={
            "linkedin": [{"title": "John Doe - Software Engineer", "link": "https://linkedin.com/in/johndoe", "snippet": "Software Engineer at Google"}],
            "github": [{"title": "johndoe", "link": "https://github.com/johndoe", "snippet": "Software Engineer"}]
        },
        search_results=["John Doe Software Engineer", "John Doe GitHub", "John Doe LinkedIn"],
        consistency_score=95,
        details="Found 10 search results. Professional presence on: linkedin, github. Sources used: serpapi"
    )

@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content for testing."""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(John Doe) Tj
0 -20 Td
(Software Engineer) Tj
0 -20 Td
(Email: john.doe@example.com) Tj
0 -20 Td
(Phone: +1234567890) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
304
%%EOF"""

@pytest.fixture
def malicious_pdf_content():
    """Create malicious PDF content for security testing."""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
/OpenAction 3 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [4 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Action
/S /JavaScript
/JS (alert('XSS Attack!');)
>>
endobj
4 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
5 0 obj
<<
/Length 50
>>
stream
BT
/F1 12 Tf
72 720 Td
(Malicious Resume) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000120 00000 n 
0000000177 00000 n 
0000000234 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
284
%%EOF"""

@pytest.fixture
def mock_http_client():
    """Create mock HTTP client for API testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client

@pytest.fixture
def mock_cached_api_client():
    """Create mock cached API client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client
