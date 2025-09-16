"""
Integration tests for the main analyzer.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from orchestrator.analyzer import ResumeAnalyzer
from utils.config import Settings


class TestAnalyzerIntegration:
    """Integration tests for ResumeAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = Settings(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_region="us-east-1",
            numverify_api_key="test_numverify_key",
            abstract_api_key="test_abstract_key",
            serpapi_key="test_serpapi_key",
            github_token="test_github_token",
            openalex_contact_email="test@example.com",
            college_scorecard_key="test_college_key",
            sec_contact_email="test@example.com"
        )
        self.analyzer = ResumeAnalyzer(self.settings)

    @pytest.mark.asyncio
    async def test_analyze_file_complete_flow(self, sample_pdf_content):
        """Test complete file analysis flow."""
        filename = "test_resume.pdf"
        file_type = "application/pdf"
        candidate_hints = {"full_name": "John Doe", "email": "john.doe@example.com"}
        
        # Mock all the detector methods
        with patch.object(self.analyzer.ai_detector, 'detect_ai_content') as mock_ai:
            mock_ai.return_value = Mock(
                is_ai_generated=False,
                confidence=25,
                model="claude-sonnet-4",
                rationale="Human-written content"
            )
        
        with patch.object(self.analyzer.document_detector, 'analyze_document_authenticity') as mock_doc:
            mock_doc.return_value = Mock(
                fileName=filename,
                fileSize=len(sample_pdf_content),
                fileType=file_type,
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
            )
        
        with patch.object(self.analyzer.contact_detector, 'verify_contact_info') as mock_contact:
            mock_contact.return_value = Mock(
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
        
        with patch.object(self.analyzer, '_verify_background') as mock_background:
            mock_background.return_value = Mock(
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
            )
        
        with patch.object(self.analyzer, '_analyze_digital_footprint') as mock_digital:
            mock_digital.return_value = Mock(
                social_presence={
                    "linkedin": [{"title": "John Doe", "link": "https://linkedin.com/in/johndoe", "snippet": "Software Engineer"}]
                },
                search_results=["John Doe Software Engineer"],
                consistency_score=95,
                details="Digital footprint analysis completed"
            )
        
        with patch.object(self.analyzer.security_scanner, 'scan_file') as mock_security:
            mock_security.return_value = {
                "is_safe": True,
                "threats_detected": [],
                "warnings": [],
                "file_info": {
                    "name": filename,
                    "extension": ".pdf",
                    "size": len(sample_pdf_content),
                    "mime_type": file_type,
                    "sha256": "test_hash"
                },
                "scan_details": {
                    "total_checks": 8,
                    "threats_found": 0,
                    "warnings_found": 0,
                    "file_hash": "test_hash",
                    "scan_timestamp": "2024-01-01T00:00:00Z"
                }
            }
        
        result = await self.analyzer.analyze_file(sample_pdf_content, filename, file_type, candidate_hints)
        
        # Verify the result structure
        assert result.extractedText is not None
        assert result.candidateInfo is not None
        assert result.aiDetection is not None
        assert result.documentAuthenticity is not None
        assert result.contactVerification is not None
        assert result.backgroundVerification is not None
        assert result.digitalFootprint is not None
        assert result.aggregatedReport is not None
        
        # Verify aggregated report
        assert result.aggregatedReport.overall_score is not None
        assert result.aggregatedReport.weights_applied is not None
        assert len(result.aggregatedReport.slices) > 0
        assert result.aggregatedReport.evidence is not None

    @pytest.mark.asyncio
    async def test_analyze_file_security_failure(self, malicious_pdf_content):
        """Test file analysis when security scan fails."""
        filename = "malicious.pdf"
        file_type = "application/pdf"
        
        with patch.object(self.analyzer.security_scanner, 'scan_file') as mock_security:
            mock_security.return_value = {
                "is_safe": False,
                "threats_detected": [
                    {"type": "pdf_javascript", "severity": "high", "message": "PDF contains JavaScript"}
                ],
                "warnings": [],
                "file_info": {
                    "name": filename,
                    "extension": ".pdf",
                    "size": len(malicious_pdf_content),
                    "mime_type": file_type,
                    "sha256": "test_hash"
                },
                "scan_details": {
                    "total_checks": 8,
                    "threats_found": 1,
                    "warnings_found": 0,
                    "file_hash": "test_hash",
                    "scan_timestamp": "2024-01-01T00:00:00Z"
                }
            }
        
        result = await self.analyzer.analyze_file(malicious_pdf_content, filename, file_type)
        
        # Should return early with security warning
        assert result.aggregatedReport.overall_score == 0
        assert result.aggregatedReport.evidence.security is not None
        assert result.aggregatedReport.evidence.security["is_safe"] is False
        assert len(result.aggregatedReport.evidence.security["threats_detected"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_file_detector_failure(self, sample_pdf_content):
        """Test file analysis when individual detectors fail."""
        filename = "test.pdf"
        file_type = "application/pdf"
        
        with patch.object(self.analyzer.security_scanner, 'scan_file') as mock_security:
            mock_security.return_value = {
                "is_safe": True,
                "threats_detected": [],
                "warnings": [],
                "file_info": {
                    "name": filename,
                    "extension": ".pdf",
                    "size": len(sample_pdf_content),
                    "mime_type": file_type,
                    "sha256": "test_hash"
                },
                "scan_details": {
                    "total_checks": 8,
                    "threats_found": 0,
                    "warnings_found": 0,
                    "file_hash": "test_hash",
                    "scan_timestamp": "2024-01-01T00:00:00Z"
                }
            }
        
        # Mock AI detector to fail
        with patch.object(self.analyzer.ai_detector, 'detect_ai_content') as mock_ai:
            mock_ai.side_effect = Exception("AI detection failed")
        
        # Mock document detector to fail
        with patch.object(self.analyzer.document_detector, 'analyze_document_authenticity') as mock_doc:
            mock_doc.side_effect = Exception("Document analysis failed")
        
        # Mock contact detector to fail
        with patch.object(self.analyzer.contact_detector, 'verify_contact_info') as mock_contact:
            mock_contact.side_effect = Exception("Contact verification failed")
        
        # Mock background verification to fail
        with patch.object(self.analyzer, '_verify_background') as mock_background:
            mock_background.side_effect = Exception("Background verification failed")
        
        # Mock digital footprint to fail
        with patch.object(self.analyzer, '_analyze_digital_footprint') as mock_digital:
            mock_digital.side_effect = Exception("Digital footprint analysis failed")
        
        result = await self.analyzer.analyze_file(sample_pdf_content, filename, file_type)
        
        # Should still return a result with fallback values
        assert result is not None
        assert result.aggregatedReport is not None
        assert result.aggregatedReport.evidence is not None

    @pytest.mark.asyncio
    async def test_extract_candidate_info_with_hints(self):
        """Test candidate information extraction with hints."""
        text = "John Doe is a software engineer with 5 years of experience."
        candidate_hints = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        }
        
        with patch.object(self.analyzer.ai_detector, 'extract_candidate_info') as mock_extract:
            mock_extract.return_value = Mock(
                full_name="John Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                location="New York, NY",
                linkedin="https://linkedin.com/in/johndoe",
                github="https://github.com/johndoe",
                website="https://johndoe.com"
            )
        
        result = await self.analyzer._extract_candidate_info(text, candidate_hints)
        
        assert result.full_name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.phone == "+1234567890"

    @pytest.mark.asyncio
    async def test_extract_candidate_info_without_hints(self):
        """Test candidate information extraction without hints."""
        text = "John Doe is a software engineer with 5 years of experience. Contact: john.doe@example.com, +1234567890"
        
        with patch.object(self.analyzer.ai_detector, 'extract_candidate_info') as mock_extract:
            mock_extract.return_value = Mock(
                full_name="John Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                location="New York, NY",
                linkedin=None,
                github=None,
                website=None
            )
        
        result = await self.analyzer._extract_candidate_info(text, None)
        
        assert result.full_name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.phone == "+1234567890"

    @pytest.mark.asyncio
    async def test_verify_background_integration(self):
        """Test background verification integration."""
        candidate_info = Mock(
            full_name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            location="New York, NY",
            linkedin="https://linkedin.com/in/johndoe",
            github="https://github.com/johndoe",
            website="https://johndoe.com"
        )
        
        with patch('background_verification.logic.run_background_verification') as mock_background:
            mock_background.return_value = Mock(
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
            )
            
            result = await self.analyzer._verify_background(candidate_info)
            
            assert result is not None
            assert result.score["composite"] == 0.85

    @pytest.mark.asyncio
    async def test_analyze_digital_footprint_integration(self):
        """Test digital footprint analysis integration."""
        full_name = "John Doe"
        email = "john.doe@example.com"
        phone = "+1234567890"
        
        with patch('detectors.digital_footprint.DigitalFootprintService') as mock_service_class:
            mock_service = Mock()
            mock_service.analyze_digital_footprint.return_value = Mock(
                social_presence={
                    "linkedin": [{"title": "John Doe", "link": "https://linkedin.com/in/johndoe", "snippet": "Software Engineer"}]
                },
                search_results=["John Doe Software Engineer"],
                consistency_score=95,
                details="Digital footprint analysis completed"
            )
            mock_service_class.return_value = mock_service
            
            result = await self.analyzer._analyze_digital_footprint(full_name, email, phone)
            
            assert result is not None
            assert result.consistency_score == 95

    @pytest.mark.asyncio
    async def test_create_aggregated_report(self):
        """Test aggregated report creation."""
        ai_detection = Mock(
            is_ai_generated=False,
            confidence=25,
            model="claude-sonnet-4",
            rationale="Human-written content"
        )
        
        document_authenticity = Mock(
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
        )
        
        contact_verification = Mock(
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
        
        background_verification = Mock(
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
        )
        
        digital_footprint = Mock(
            social_presence={
                "linkedin": [{"title": "John Doe", "link": "https://linkedin.com/in/johndoe", "snippet": "Software Engineer"}]
            },
            search_results=["John Doe Software Engineer"],
            consistency_score=95,
            details="Digital footprint analysis completed"
        )
        
        security_scan = {
            "is_safe": True,
            "threats_detected": [],
            "warnings": [],
            "file_info": {
                "name": "test.pdf",
                "extension": ".pdf",
                "size": 1024,
                "mime_type": "application/pdf",
                "sha256": "test_hash"
            },
            "scan_details": {
                "total_checks": 8,
                "threats_found": 0,
                "warnings_found": 0,
                "file_hash": "test_hash",
                "scan_timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        result = await self.analyzer._create_aggregated_report(
            ai_detection, document_authenticity, contact_verification,
            background_verification, digital_footprint, security_scan
        )
        
        assert result.overall_score is not None
        assert result.weights_applied is not None
        assert len(result.slices) > 0
        assert result.evidence is not None
        assert result.evidence.ai == ai_detection
        assert result.evidence.document_authenticity == document_authenticity
        assert result.evidence.contact == contact_verification
        assert result.evidence.background == background_verification
        assert result.evidence.digital_footprint == digital_footprint
        assert result.evidence.security == security_scan

    @pytest.mark.asyncio
    async def test_extract_text_content_pdf(self, sample_pdf_content):
        """Test text extraction from PDF."""
        filename = "test.pdf"
        file_type = "application/pdf"
        
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pdf = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\njohn.doe@example.com"
            mock_pdf.pages = [mock_page]
            mock_reader.return_value = mock_pdf
            
            result = await self.analyzer._extract_text_content(sample_pdf_content, filename, file_type)
            
            assert "John Doe" in result
            assert "Software Engineer" in result
            assert "john.doe@example.com" in result

    @pytest.mark.asyncio
    async def test_extract_text_content_docx(self):
        """Test text extraction from DOCX."""
        filename = "test.docx"
        file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        docx_content = b'PK\x03\x04'
        
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip_file = Mock()
            mock_zip_file.read.return_value = b'<?xml version="1.0"?><document><body><p>John Doe</p><p>Software Engineer</p></body></document>'
            mock_zip.return_value.__enter__.return_value = mock_zip_file
            
            result = await self.analyzer._extract_text_content(docx_content, filename, file_type)
            
            assert "John Doe" in result
            assert "Software Engineer" in result

    @pytest.mark.asyncio
    async def test_extract_text_content_unsupported(self):
        """Test text extraction from unsupported file type."""
        filename = "test.txt"
        file_type = "text/plain"
        content = b"John Doe\nSoftware Engineer"
        
        result = await self.analyzer._extract_text_content(content, filename, file_type)
        
        assert result == "John Doe\nSoftware Engineer"
