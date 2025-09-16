"""
Unit tests for file security scanner.
"""

import pytest
from unittest.mock import patch, mock_open
from detectors.file_security import FileSecurityScanner


class TestFileSecurityScanner:
    """Test cases for FileSecurityScanner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = FileSecurityScanner()

    @pytest.mark.asyncio
    async def test_scan_safe_pdf(self, sample_pdf_content):
        """Test scanning a safe PDF file."""
        result = await self.scanner.scan_file("test.pdf", sample_pdf_content)
        
        assert result["is_safe"] is True
        assert len(result["threats_detected"]) == 0
        assert result["file_info"]["mime_type"] == "application/pdf"
        assert result["file_info"]["extension"] == ".pdf"

    @pytest.mark.asyncio
    async def test_scan_malicious_pdf(self, malicious_pdf_content):
        """Test scanning a malicious PDF file."""
        result = await self.scanner.scan_file("malicious.pdf", malicious_pdf_content)
        
        assert result["is_safe"] is False
        assert len(result["threats_detected"]) > 0
        
        # Check for JavaScript threats
        threat_types = [threat["type"] for threat in result["threats_detected"]]
        assert "pdf_javascript" in threat_types

    @pytest.mark.asyncio
    async def test_scan_executable_file(self):
        """Test scanning an executable file."""
        exe_content = b'MZ\x90\x00'  # PE header start
        result = await self.scanner.scan_file("test.exe", exe_content)
        
        assert result["is_safe"] is False
        assert len(result["threats_detected"]) >= 1
        
        threat_types = [threat["type"] for threat in result["threats_detected"]]
        assert "suspicious_extension" in threat_types or "executable_signature" in threat_types

    @pytest.mark.asyncio
    async def test_scan_large_file(self):
        """Test scanning a file that exceeds size limit."""
        large_content = b'A' * (60 * 1024 * 1024)  # 60MB
        result = await self.scanner.scan_file("large.txt", large_content)
        
        assert result["is_safe"] is False
        assert len(result["threats_detected"]) >= 1
        
        threat_types = [threat["type"] for threat in result["threats_detected"]]
        assert "file_size" in threat_types

    @pytest.mark.asyncio
    async def test_scan_suspicious_content(self):
        """Test scanning content with suspicious patterns."""
        suspicious_content = b'<script>alert("XSS")</script>\neval("malicious code")'
        result = await self.scanner.scan_file("test.html", suspicious_content)
        
        assert result["is_safe"] is False
        assert len(result["threats_detected"]) > 0
        
        threat_types = [threat["type"] for threat in result["threats_detected"]]
        assert "suspicious_content" in threat_types or "embedded_script" in threat_types

    def test_detect_mime_type_pdf(self):
        """Test MIME type detection for PDF."""
        pdf_content = b'%PDF-1.4'
        mime_type = self.scanner._detect_mime_type(pdf_content, '.pdf')
        assert mime_type == "application/pdf"

    def test_detect_mime_type_docx(self):
        """Test MIME type detection for DOCX."""
        docx_content = b'PK\x03\x04'
        mime_type = self.scanner._detect_mime_type(docx_content, '.docx')
        assert mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_detect_mime_type_executable(self):
        """Test MIME type detection for executable."""
        exe_content = b'MZ'
        mime_type = self.scanner._detect_mime_type(exe_content, '.exe')
        assert mime_type == "application/x-msdownload"

    def test_check_file_extension_safe(self):
        """Test file extension check for safe files."""
        threat = self.scanner._check_file_extension("test.pdf")
        assert threat is None

    def test_check_file_extension_suspicious(self):
        """Test file extension check for suspicious files."""
        threat = self.scanner._check_file_extension("test.exe")
        assert threat is not None
        assert threat["type"] == "suspicious_extension"
        assert threat["severity"] == "high"

    def test_check_file_signature_safe(self):
        """Test file signature check for safe files."""
        pdf_content = b'%PDF-1.4'
        threat = self.scanner._check_file_signature(pdf_content)
        assert threat is None

    def test_check_file_signature_executable(self):
        """Test file signature check for executable files."""
        exe_content = b'MZ'
        threat = self.scanner._check_file_signature(exe_content)
        assert threat is not None
        assert threat["type"] == "executable_signature"
        assert threat["severity"] == "high"

    @pytest.mark.asyncio
    async def test_analyze_content_safe(self):
        """Test content analysis for safe content."""
        safe_content = b'This is a normal resume with no suspicious content.'
        threats = await self.scanner._analyze_content(safe_content, "test.txt")
        assert len(threats) == 0

    @pytest.mark.asyncio
    async def test_analyze_content_suspicious(self):
        """Test content analysis for suspicious content."""
        suspicious_content = b'<script>alert("XSS")</script>\neval("malicious code")'
        threats = await self.scanner._analyze_content(suspicious_content, "test.html")
        assert len(threats) > 0
        
        threat_types = [threat["type"] for threat in threats]
        assert "suspicious_content" in threat_types or "embedded_script" in threat_types

    def test_scan_pdf_security_safe(self):
        """Test PDF security scanning for safe PDF."""
        safe_pdf = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        threats = self.scanner._scan_pdf_security(safe_pdf)
        assert len(threats) == 0

    def test_scan_pdf_security_malicious(self):
        """Test PDF security scanning for malicious PDF."""
        malicious_pdf = b'%PDF-1.4\n/OpenAction 3 0 R\n/JavaScript (alert("XSS");)'
        threats = self.scanner._scan_pdf_security(malicious_pdf)
        assert len(threats) > 0
        
        threat_types = [threat["type"] for threat in threats]
        assert "pdf_javascript" in threat_types

    def test_scan_zip_security_safe(self):
        """Test ZIP security scanning for safe ZIP."""
        safe_zip = b'PK\x03\x04\x14\x00\x00\x00\x08\x00'
        threats = self.scanner._scan_zip_security(safe_zip)
        # Should not raise exception, may or may not have threats
        assert isinstance(threats, list)

    def test_get_file_info(self, sample_pdf_content):
        """Test file info extraction."""
        file_info = self.scanner._get_file_info("test.pdf", sample_pdf_content)
        
        assert file_info["name"] == "test.pdf"
        assert file_info["extension"] == ".pdf"
        assert file_info["size"] == len(sample_pdf_content)
        assert file_info["mime_type"] == "application/pdf"
        assert "sha256" in file_info
        assert len(file_info["sha256"]) == 64  # SHA256 hash length

    @pytest.mark.asyncio
    async def test_scan_file_error_handling(self):
        """Test error handling in file scanning."""
        # Test with invalid file content
        result = await self.scanner.scan_file("test.txt", b"")
        
        assert result["is_safe"] is True  # Empty file should be safe
        assert "file_info" in result
        assert "scan_details" in result
