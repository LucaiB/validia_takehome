"""
Contract tests for API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.main import app


class TestAPIContracts:
    """Contract tests for API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_health_check_contract(self):
        """Test health check endpoint contract."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert data["service"] == "resume-fraud-detection"

    def test_analyze_endpoint_contract(self, sample_pdf_content):
        """Test analyze endpoint contract."""
        with patch('orchestrator.analyzer.ResumeAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_file.return_value = Mock(
                extractedText="John Doe\nSoftware Engineer",
                candidateInfo=Mock(
                    full_name="John Doe",
                    email="john.doe@example.com",
                    phone="+1234567890",
                    location="New York, NY",
                    linkedin=None,
                    github=None,
                    website=None
                ),
                aiDetection=Mock(
                    is_ai_generated=False,
                    confidence=25,
                    model="claude-sonnet-4",
                    rationale="Human-written content"
                ),
                documentAuthenticity=Mock(
                    fileName="test.pdf",
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
                    rationale="Document appears authentic"
                ),
                contactVerification=Mock(
                    email="john.doe@example.com",
                    phone="+1234567890",
                    is_verified=True,
                    details="Contact information verified",
                    email_valid=True,
                    email_disposable=False,
                    phone_valid=True,
                    phone_carrier="Verizon Wireless",
                    geo_consistent=True
                ),
                backgroundVerification=Mock(
                    company_evidence={},
                    education_evidence={},
                    developer_evidence={},
                    timeline_assessment={},
                    score={
                        "company_identity_score": 0.9,
                        "education_institution_score": 1.0,
                        "timeline_corroboration_score": 0.8,
                        "developer_footprint_score": 0.7,
                        "composite": 0.85
                    },
                    rationale=["Background verification completed"],
                    sources_used=["GLEIF", "SEC EDGAR", "OpenAlex", "GitHub"]
                ),
                digitalFootprint=Mock(
                    social_presence={
                        "linkedin": [{"title": "John Doe", "link": "https://linkedin.com/in/johndoe", "snippet": "Software Engineer"}]
                    },
                    search_results=["John Doe Software Engineer"],
                    consistency_score=95,
                    details="Digital footprint analysis completed"
                ),
                aggregatedReport=Mock(
                    overall_score=75,
                    weights_applied={
                        "Contact Info": 0.2,
                        "AI Content": 0.3,
                        "Background": 0.2,
                        "Digital Footprint": 0.1,
                        "Document Authenticity": 0.1,
                        "File Security": 0.1
                    },
                    slices=[
                        {"label": "AI Content", "score": 25, "description": "Human Written (confidence: 25%)"},
                        {"label": "Document Authenticity", "score": 85, "description": "Authenticity score: 85%"},
                        {"label": "Contact Info", "score": 100, "description": "Contact verification score: 100%"},
                        {"label": "Background", "score": 85, "description": "Background verification score: 85%"},
                        {"label": "Digital Footprint", "score": 95, "description": "Digital footprint consistency: 95%"},
                        {"label": "File Security", "score": 100, "description": "File passed security scan"}
                    ],
                    evidence=Mock(
                        contact=Mock(),
                        ai=Mock(),
                        document_authenticity=Mock(),
                        background=Mock(),
                        digital_footprint=Mock(),
                        security=Mock()
                    ),
                    rationale=["AI Content: Low risk (25% confidence)", "Document Authenticity: 85% authentic"],
                    generated_at="2024-01-01T00:00:00Z",
                    version="1.0.0"
                ),
                rationale="Analysis completed successfully",
                usage=None,
                request_id="req_20240101_000000"
            )
            mock_analyzer_class.return_value = mock_analyzer
            
            response = self.client.post(
                "/analyze",
                files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
                data={"candidate_hints": json.dumps({"full_name": "John Doe"})}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields are present
            assert "extractedText" in data
            assert "candidateInfo" in data
            assert "aiDetection" in data
            assert "documentAuthenticity" in data
            assert "contactVerification" in data
            assert "backgroundVerification" in data
            assert "digitalFootprint" in data
            assert "aggregatedReport" in data
            assert "rationale" in data
            assert "usage" in data
            assert "request_id" in data
            
            # Verify candidateInfo structure
            candidate_info = data["candidateInfo"]
            assert "full_name" in candidate_info
            assert "email" in candidate_info
            assert "phone" in candidate_info
            assert "location" in candidate_info
            assert "linkedin" in candidate_info
            assert "github" in candidate_info
            assert "website" in candidate_info
            
            # Verify aiDetection structure
            ai_detection = data["aiDetection"]
            assert "is_ai_generated" in ai_detection
            assert "confidence" in ai_detection
            assert "model" in ai_detection
            assert "rationale" in ai_detection
            
            # Verify documentAuthenticity structure
            doc_auth = data["documentAuthenticity"]
            assert "fileName" in doc_auth
            assert "fileSize" in doc_auth
            assert "fileType" in doc_auth
            assert "creationDate" in doc_auth
            assert "modificationDate" in doc_auth
            assert "author" in doc_auth
            assert "creator" in doc_auth
            assert "producer" in doc_auth
            assert "title" in doc_auth
            assert "subject" in doc_auth
            assert "keywords" in doc_auth
            assert "pdfVersion" in doc_auth
            assert "pageCount" in doc_auth
            assert "isEncrypted" in doc_auth
            assert "hasDigitalSignature" in doc_auth
            assert "softwareUsed" in doc_auth
            assert "suspiciousIndicators" in doc_auth
            assert "authenticityScore" in doc_auth
            assert "rationale" in doc_auth
            
            # Verify contactVerification structure
            contact_ver = data["contactVerification"]
            assert "email" in contact_ver
            assert "phone" in contact_ver
            assert "is_verified" in contact_ver
            assert "details" in contact_ver
            assert "email_valid" in contact_ver
            assert "email_disposable" in contact_ver
            assert "phone_valid" in contact_ver
            assert "phone_carrier" in contact_ver
            assert "geo_consistent" in contact_ver
            
            # Verify backgroundVerification structure
            background_ver = data["backgroundVerification"]
            assert "company_evidence" in background_ver
            assert "education_evidence" in background_ver
            assert "developer_evidence" in background_ver
            assert "timeline_assessment" in background_ver
            assert "score" in background_ver
            assert "rationale" in background_ver
            assert "sources_used" in background_ver
            
            # Verify digitalFootprint structure
            digital_footprint = data["digitalFootprint"]
            assert "social_presence" in digital_footprint
            assert "search_results" in digital_footprint
            assert "consistency_score" in digital_footprint
            assert "details" in digital_footprint
            
            # Verify aggregatedReport structure
            aggregated_report = data["aggregatedReport"]
            assert "overall_score" in aggregated_report
            assert "weights_applied" in aggregated_report
            assert "slices" in aggregated_report
            assert "evidence" in aggregated_report
            assert "rationale" in aggregated_report
            assert "generated_at" in aggregated_report
            assert "version" in aggregated_report

    def test_analyze_endpoint_unsupported_file_type(self):
        """Test analyze endpoint with unsupported file type."""
        response = self.client.post(
            "/analyze",
            files={"file": ("test.exe", b"executable content", "application/x-msdownload")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Unsupported file type" in data["detail"]

    def test_analyze_endpoint_missing_file(self):
        """Test analyze endpoint without file."""
        response = self.client.post("/analyze")
        
        assert response.status_code == 422  # Validation error

    def test_contact_verification_endpoint_contract(self):
        """Test contact verification endpoint contract."""
        with patch('detectors.contact_verification.ContactVerificationService') as mock_service_class:
            mock_service = Mock()
            mock_service.verify_contact_info.return_value = Mock(
                email="john.doe@example.com",
                phone="+1234567890",
                is_verified=True,
                details="Contact information verified",
                email_valid=True,
                email_disposable=False,
                phone_valid=True,
                phone_carrier="Verizon Wireless",
                geo_consistent=True
            )
            mock_service_class.return_value = mock_service
            
            response = self.client.post(
                "/contact/verify",
                json={
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "location": "New York, NY"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields are present
            assert "email" in data
            assert "phone" in data
            assert "is_verified" in data
            assert "details" in data
            assert "email_valid" in data
            assert "email_disposable" in data
            assert "phone_valid" in data
            assert "phone_carrier" in data
            assert "geo_consistent" in data

    def test_background_verification_endpoint_contract(self):
        """Test background verification endpoint contract."""
        with patch('background_verification.logic.run_background_verification') as mock_background:
            mock_background.return_value = Mock(
                company_evidence={
                    "Google": {
                        "gleif": [{"lei": "2138004T8I4HK4Q6X453", "legal_name": "Google LLC", "status": "ACTIVE", "country": "US"}],
                        "sec": {"ticker": "GOOGL", "title": "Alphabet Inc.", "cik_str": "1652044"}
                    }
                },
                education_evidence={
                    "Stanford University": {
                        "scorecard": [{"name": "Stanford University", "city": "Stanford", "state": "CA", "operating": 1}],
                        "openalex": [{"id": "https://openalex.org/I114027114", "display_name": "Stanford University", "country_code": "US", "type": "education", "works_count": 100000, "cited_by_count": 5000000}]
                    }
                },
                developer_evidence={
                    "user": {"login": "johndoe", "public_repos": 50, "followers": 100},
                    "repos": [{"name": "awesome-project", "pushed_at": "2024-01-01T00:00:00Z", "language": "Python"}]
                },
                timeline_assessment={
                    "Google": {
                        "plausible": True,
                        "notes": ["Timeline appears consistent with company history"],
                        "wayback": {"first": "19980101000000", "last": "2024-01-01T00:00:00Z", "captures": 1000}
                    }
                },
                score={
                    "company_identity_score": 0.9,
                    "education_institution_score": 1.0,
                    "timeline_corroboration_score": 0.8,
                    "developer_footprint_score": 0.7,
                    "composite": 0.85
                },
                rationale=[
                    "Company identity checked via GLEIF and SEC EDGAR.",
                    "Education validated via College Scorecard and OpenAlex.",
                    "Timeline plausibility uses registry presence and optional Wayback snapshots.",
                    "Developer evidence from GitHub profile and repo activity."
                ],
                sources_used=["GLEIF", "SEC EDGAR", "OpenAlex", "Wayback CDX", "GitHub", "US College Scorecard"]
            )
            
            response = self.client.post(
                "/background/verify",
                json={
                    "full_name": "John Doe",
                    "positions": [
                        {
                            "employer_name": "Google",
                            "position_title": "Software Engineer",
                            "start": "2020-01",
                            "end": "2023-12",
                            "employer_domain": "google.com"
                        }
                    ],
                    "educations": [
                        {
                            "institution_name": "Stanford University",
                            "degree": "Bachelor of Science",
                            "field_of_study": "Computer Science",
                            "start": "2016-09",
                            "end": "2020-06"
                        }
                    ],
                    "identifiers": {
                        "github_username": "johndoe",
                        "linkedin_url": "https://linkedin.com/in/johndoe"
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields are present
            assert "company_evidence" in data
            assert "education_evidence" in data
            assert "developer_evidence" in data
            assert "timeline_assessment" in data
            assert "score" in data
            assert "rationale" in data
            assert "sources_used" in data
            
            # Verify score structure
            score = data["score"]
            assert "company_identity_score" in score
            assert "education_institution_score" in score
            assert "timeline_corroboration_score" in score
            assert "developer_footprint_score" in score
            assert "composite" in score

    def test_digital_footprint_endpoint_contract(self):
        """Test digital footprint endpoint contract."""
        with patch('detectors.digital_footprint.DigitalFootprintService') as mock_service_class:
            mock_service = Mock()
            mock_service.analyze_digital_footprint.return_value = Mock(
                social_presence={
                    "linkedin": [{"title": "John Doe", "link": "https://linkedin.com/in/johndoe", "snippet": "Software Engineer"}],
                    "github": [{"title": "johndoe", "link": "https://github.com/johndoe", "snippet": "Software Engineer"}]
                },
                search_results=["John Doe Software Engineer", "John Doe GitHub", "John Doe LinkedIn"],
                consistency_score=95,
                details="Found 10 search results. Professional presence on: linkedin, github. Sources used: serpapi"
            )
            mock_service_class.return_value = mock_service
            
            response = self.client.post(
                "/digital-footprint/analyze",
                json={
                    "full_name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields are present
            assert "social_presence" in data
            assert "search_results" in data
            assert "consistency_score" in data
            assert "details" in data
            
            # Verify social_presence structure
            social_presence = data["social_presence"]
            assert "linkedin" in social_presence
            assert "github" in social_presence
            assert isinstance(social_presence["linkedin"], list)
            assert isinstance(social_presence["github"], list)

    def test_cache_stats_endpoint_contract(self):
        """Test cache stats endpoint contract."""
        with patch('utils.cache.api_cache.get_stats') as mock_api_stats:
            mock_api_stats.return_value = {
                "hits": 100,
                "misses": 50,
                "hit_rate": 0.67,
                "total_requests": 150,
                "cache_size": 25
            }
        
        with patch('utils.cache.analysis_cache.get_stats') as mock_analysis_stats:
            mock_analysis_stats.return_value = {
                "hits": 75,
                "misses": 25,
                "hit_rate": 0.75,
                "total_requests": 100,
                "cache_size": 15
            }
        
        response = self.client.get("/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields are present
        assert "api_cache" in data
        assert "analysis_cache" in data
        
        # Verify api_cache structure
        api_cache = data["api_cache"]
        assert "hits" in api_cache
        assert "misses" in api_cache
        assert "hit_rate" in api_cache
        assert "total_requests" in api_cache
        assert "cache_size" in api_cache
        
        # Verify analysis_cache structure
        analysis_cache = data["analysis_cache"]
        assert "hits" in analysis_cache
        assert "misses" in analysis_cache
        assert "hit_rate" in analysis_cache
        assert "total_requests" in analysis_cache
        assert "cache_size" in analysis_cache

    def test_clear_cache_endpoint_contract(self):
        """Test clear cache endpoint contract."""
        with patch('utils.cache.api_cache.clear') as mock_api_clear:
            mock_api_clear.return_value = None
        
        with patch('utils.cache.analysis_cache.clear') as mock_analysis_clear:
            mock_analysis_clear.return_value = None
        
        response = self.client.post("/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields are present
        assert "message" in data
        assert "All caches cleared successfully" in data["message"]

    def test_test_rate_limit_endpoint_contract(self):
        """Test rate limit test endpoint contract."""
        response = self.client.get("/test-rate-limit")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields are present
        assert "message" in data
        assert "timestamp" in data
        assert "This endpoint should be rate limited" in data["message"]
        assert isinstance(data["timestamp"], (int, float))

    def test_analyze_endpoint_error_handling(self, sample_pdf_content):
        """Test analyze endpoint error handling."""
        with patch('orchestrator.analyzer.ResumeAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_file.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer
            
            response = self.client.post(
                "/analyze",
                files={"file": ("test.pdf", sample_pdf_content, "application/pdf")}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Analysis failed" in data["detail"]

    def test_contact_verification_endpoint_error_handling(self):
        """Test contact verification endpoint error handling."""
        with patch('detectors.contact_verification.ContactVerificationService') as mock_service_class:
            mock_service = Mock()
            mock_service.verify_contact_info.side_effect = Exception("Verification failed")
            mock_service_class.return_value = mock_service
            
            response = self.client.post(
                "/contact/verify",
                json={
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "location": "New York, NY"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Contact verification failed" in data["detail"]

    def test_background_verification_endpoint_error_handling(self):
        """Test background verification endpoint error handling."""
        with patch('background_verification.logic.run_background_verification') as mock_background:
            mock_background.side_effect = Exception("Background verification failed")
            
            response = self.client.post(
                "/background/verify",
                json={
                    "full_name": "John Doe",
                    "positions": [],
                    "educations": [],
                    "identifiers": {}
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Background verification failed" in data["detail"]

    def test_digital_footprint_endpoint_error_handling(self):
        """Test digital footprint endpoint error handling."""
        with patch('detectors.digital_footprint.DigitalFootprintService') as mock_service_class:
            mock_service = Mock()
            mock_service.analyze_digital_footprint.side_effect = Exception("Digital footprint analysis failed")
            mock_service_class.return_value = mock_service
            
            response = self.client.post(
                "/digital-footprint/analyze",
                json={
                    "full_name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Digital footprint analysis failed" in data["detail"]
