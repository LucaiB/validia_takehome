"""
Unit tests for document authenticity detector.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from detectors.document_auth import DocumentAuthenticityDetector


class TestDocumentAuthenticityDetector:
    """Test cases for DocumentAuthenticityDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            # Set up the mock client to return a proper response structure
            mock_client.invoke_model.return_value = {
                'body': Mock(read=Mock(return_value='{"content": [{"text": "{\\"authenticityScore\\": 50, \\"suspiciousIndicators\\": [\\"Analysis failed\\"], \\"rationale\\": \\"Default test response\\"}"}]}'))
            }
            mock_boto.return_value = mock_client
            self.detector = DocumentAuthenticityDetector(
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                aws_region="us-east-1"
            )

    @pytest.mark.asyncio
    async def test_analyze_document_authenticity_pdf(self, sample_pdf_content):
        """Test document authenticity analysis for PDF."""
        filename = "test_resume.pdf"
        file_type = "application/pdf"
        
        with patch.object(self.detector, '_extract_pdf_metadata') as mock_metadata, \
             patch.object(self.detector, '_analyze_pdf_structure') as mock_structure, \
             patch.object(self.detector, '_analyze_pdf_fonts') as mock_fonts, \
             patch.object(self.detector, '_analyze_pdf_images') as mock_images, \
             patch.object(self.detector, '_analyze_file_integrity') as mock_integrity, \
             patch.object(self.detector, '_create_authenticity_prompt') as mock_prompt:

            mock_metadata.return_value = {
                "creation_date": "2024-01-01T00:00:00Z",
                "modification_date": "2024-01-01T00:00:00Z",
                "author": "John Doe",
                "creator": "Microsoft Word",
                "producer": "Microsoft Word",
                "title": "John Doe Resume",
                "subject": "Software Engineer Resume",
                "keywords": "software, engineer, python, javascript",
                "pdf_version": "1.4",
                "page_count": 1,
                "is_encrypted": False,
                "has_digital_signature": False
            }

            mock_structure.return_value = {"suspicious_indicators": []}
            mock_fonts.return_value = {"suspicious_indicators": []}
            mock_images.return_value = {"suspicious_indicators": []}
            mock_integrity.return_value = {"suspicious_indicators": []}
            mock_prompt.return_value = "Test prompt"

            # Mock the invoke_model method directly on the mock client
            self.detector.bedrock_client.invoke_model.return_value = {
                'body': Mock(read=Mock(return_value='{"content": [{"text": "{\\"authenticityScore\\": 85, \\"suspiciousIndicators\\": [], \\"rationale\\": \\"Document appears authentic\\"}"}]}'))
            }

            result = await self.detector.analyze_document_authenticity(sample_pdf_content, filename, file_type)
        
        assert result.fileName == filename
        assert result.fileSize == len(sample_pdf_content)
        assert result.fileType == file_type
        assert result.authenticityScore == 85
        assert result.author == "John Doe"
        assert result.creator == "Microsoft Word"

    @pytest.mark.asyncio
    async def test_analyze_document_authenticity_docx(self):
        """Test document authenticity analysis for DOCX."""
        filename = "test_resume.docx"
        file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        docx_content = b'PK\x03\x04'  # DOCX header
        
        with patch.object(self.detector, '_extract_docx_metadata') as mock_metadata, \
             patch.object(self.detector, '_analyze_docx_structure') as mock_structure, \
             patch.object(self.detector, '_analyze_docx_fonts') as mock_fonts, \
             patch.object(self.detector, '_analyze_file_integrity') as mock_integrity, \
             patch.object(self.detector, '_create_authenticity_prompt') as mock_prompt:

            mock_metadata.return_value = {
                "creation_date": "2024-01-01T00:00:00Z",
                "modification_date": "2024-01-01T00:00:00Z",
                "author": "John Doe",
                "creator": "Microsoft Word",
                "producer": "Microsoft Word",
                "title": "John Doe Resume",
                "subject": "Software Engineer Resume",
                "keywords": "software, engineer, python, javascript",
                "page_count": 1,
                "is_encrypted": False,
                "has_digital_signature": False
            }

            mock_structure.return_value = {"suspicious_indicators": []}
            mock_fonts.return_value = {"suspicious_indicators": []}
            mock_integrity.return_value = {"suspicious_indicators": []}
            mock_prompt.return_value = "Test prompt"

            # Mock the invoke_model method directly on the mock client
            self.detector.bedrock_client.invoke_model.return_value = {
                'body': Mock(read=Mock(return_value='{"content": [{"text": "{\\"authenticityScore\\": 90, \\"suspiciousIndicators\\": [], \\"rationale\\": \\"Document appears authentic\\"}"}]}'))
            }

            result = await self.detector.analyze_document_authenticity(docx_content, filename, file_type)
        
        assert result.fileName == filename
        assert result.fileSize == len(docx_content)
        assert result.fileType == file_type
        assert result.authenticityScore == 90

    @pytest.mark.asyncio
    async def test_analyze_document_authenticity_suspicious(self, sample_pdf_content):
        """Test document authenticity analysis for suspicious document."""
        filename = "suspicious.pdf"
        file_type = "application/pdf"
        
        with patch.object(self.detector, '_extract_pdf_metadata') as mock_metadata, \
             patch.object(self.detector, '_analyze_pdf_structure') as mock_structure, \
             patch.object(self.detector, '_analyze_pdf_fonts') as mock_fonts, \
             patch.object(self.detector, '_analyze_pdf_images') as mock_images, \
             patch.object(self.detector, '_analyze_file_integrity') as mock_integrity, \
             patch.object(self.detector, '_create_authenticity_prompt') as mock_prompt:

            mock_metadata.return_value = {
                "creation_date": None,
                "modification_date": None,
                "author": None,
                "creator": None,
                "producer": None,
                "title": None,
                "subject": None,
                "keywords": None,
                "pdf_version": None,
                "page_count": 0,
                "is_encrypted": False,
                "has_digital_signature": False
            }

            mock_structure.return_value = {"suspicious_indicators": ["Suspicious structure detected"]}
            mock_fonts.return_value = {"suspicious_indicators": ["No fonts found"]}
            mock_images.return_value = {"suspicious_indicators": ["No images found"]}
            mock_integrity.return_value = {"suspicious_indicators": ["File integrity issues"]}
            mock_prompt.return_value = "Test prompt"

            # Mock the invoke_model method directly on the mock client
            self.detector.bedrock_client.invoke_model.return_value = {
                'body': Mock(read=Mock(return_value='{"content": [{"text": "{\\"authenticityScore\\": 15, \\"suspiciousIndicators\\": [\\"Missing metadata\\", \\"Suspicious structure\\"], \\"rationale\\": \\"Document appears suspicious\\"}"}]}'))
            }

            result = await self.detector.analyze_document_authenticity(sample_pdf_content, filename, file_type)
        
        assert result.authenticityScore == 15
        assert len(result.suspiciousIndicators) > 0
        assert "suspicious" in result.rationale.lower()

    @pytest.mark.asyncio
    async def test_analyze_document_authenticity_bedrock_error(self, sample_pdf_content):
        """Test document authenticity analysis when Bedrock fails."""
        filename = "test.pdf"
        file_type = "application/pdf"
        
        with patch.object(self.detector, '_extract_pdf_metadata') as mock_metadata, \
             patch.object(self.detector, '_analyze_pdf_structure') as mock_structure, \
             patch.object(self.detector, '_analyze_pdf_fonts') as mock_fonts, \
             patch.object(self.detector, '_analyze_pdf_images') as mock_images, \
             patch.object(self.detector, '_analyze_file_integrity') as mock_integrity, \
             patch.object(self.detector, '_create_authenticity_prompt') as mock_prompt:

            mock_metadata.return_value = {
                "creation_date": "2024-01-01T00:00:00Z",
                "modification_date": "2024-01-01T00:00:00Z",
                "author": "John Doe",
                "creator": "Microsoft Word",
                "producer": "Microsoft Word",
                "title": "John Doe Resume",
                "subject": "Software Engineer Resume",
                "keywords": "software, engineer, python, javascript",
                "pdf_version": "1.4",
                "page_count": 1,
                "is_encrypted": False,
                "has_digital_signature": False
            }

            mock_structure.return_value = {"suspicious_indicators": []}
            mock_fonts.return_value = {"suspicious_indicators": []}
            mock_images.return_value = {"suspicious_indicators": []}
            mock_integrity.return_value = {"suspicious_indicators": []}
            mock_prompt.return_value = "Test prompt"

            # Mock the invoke_model method to raise an exception
            self.detector.bedrock_client.invoke_model.side_effect = Exception("Bedrock API error")

            result = await self.detector.analyze_document_authenticity(sample_pdf_content, filename, file_type)
        
        # Should return fallback result
        assert result.authenticityScore == 50  # Default fallback score
        assert "error" in result.rationale.lower()

    @pytest.mark.asyncio
    async def test_extract_pdf_metadata(self, sample_pdf_content):
        """Test PDF metadata extraction."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pdf = Mock()
            mock_pdf.metadata = {
                '/CreationDate': 'D:20240101000000Z',
                '/ModDate': 'D:20240101000000Z',
                '/Author': 'John Doe',
                '/Creator': 'Microsoft Word',
                '/Producer': 'Microsoft Word',
                '/Title': 'John Doe Resume',
                '/Subject': 'Software Engineer Resume',
                '/Keywords': 'software, engineer, python, javascript'
            }
            mock_pdf.pdf_header = b'%PDF-1.4'
            mock_pdf.is_encrypted = False
            mock_pdf.pages = [Mock()]
            mock_reader.return_value = mock_pdf
            
            result = await self.detector._extract_pdf_metadata(sample_pdf_content, "test.pdf", "application/pdf")
            
            assert result["author"] == "John Doe"
            assert result["creator"] == "Microsoft Word"
            assert result["title"] == "John Doe Resume"
            assert result["pdf_version"] is None  # PDF version is not extracted in current implementation
            assert result["page_count"] == 1
            assert result["is_encrypted"] is False

    @pytest.mark.asyncio
    async def test_extract_docx_metadata(self):
        """Test DOCX metadata extraction."""
        docx_content = b'PK\x03\x04'

        with patch('detectors.document_auth.Document') as mock_doc:
            mock_document = Mock()
            mock_props = Mock()
            mock_props.title = "John Doe Resume"
            mock_props.author = "John Doe"
            mock_props.subject = "Software Engineer Resume"
            mock_props.keywords = "software, engineer, python, javascript"
            mock_props.creator = "Microsoft Word"
            mock_props.created = "2024-01-01T00:00:00Z"
            mock_props.modified = "2024-01-01T00:00:00Z"
            mock_document.core_properties = mock_props
            mock_doc.return_value = mock_document

            result = await self.detector._extract_docx_metadata(docx_content, "test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            assert result["author"] == "John Doe"
            assert result["title"] == "John Doe Resume"

    @pytest.mark.asyncio
    async def test_analyze_pdf_structure(self, sample_pdf_content):
        """Test PDF structure analysis."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pdf = Mock()
            mock_pdf.pages = [Mock()]
            mock_reader.return_value = mock_pdf
            
            result = await self.detector._analyze_pdf_structure(sample_pdf_content)
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_pdf_fonts(self, sample_pdf_content):
        """Test PDF font analysis."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pdf = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Test text"
            mock_pdf.pages = [mock_page]
            mock_reader.return_value = mock_pdf
            
            result = await self.detector._analyze_pdf_fonts(sample_pdf_content)
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_pdf_images(self, sample_pdf_content):
        """Test PDF image analysis."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pdf = Mock()
            mock_pdf.pages = [Mock()]
            mock_reader.return_value = mock_pdf
            
            result = await self.detector._analyze_pdf_images(sample_pdf_content)
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_docx_structure(self):
        """Test DOCX structure analysis."""
        docx_content = b'PK\x03\x04'
        
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip_file = Mock()
            mock_zip_file.namelist.return_value = ['word/document.xml']
            mock_zip_file.read.return_value = b'<?xml version="1.0"?><document><body><p>Test content</p></body></document>'
            mock_zip.return_value.__enter__.return_value = mock_zip_file
            
            result = await self.detector._analyze_docx_structure(docx_content)
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_docx_fonts(self):
        """Test DOCX font analysis."""
        docx_content = b'PK\x03\x04'
        
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip_file = Mock()
            mock_zip_file.namelist.return_value = ['word/styles.xml']
            mock_zip_file.read.return_value = b'<?xml version="1.0"?><styles><style><name>Normal</name><font>Times New Roman</font></style></styles>'
            mock_zip.return_value.__enter__.return_value = mock_zip_file
            
            result = await self.detector._analyze_docx_fonts(docx_content)
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_file_integrity(self, sample_pdf_content):
        """Test file integrity analysis."""
        result = await self.detector._analyze_file_integrity(sample_pdf_content, "test.pdf")
        
        assert isinstance(result, dict)

    def test_create_authenticity_prompt(self):
        """Test authenticity prompt creation."""
        metadata = {
            "author": "John Doe",
            "creator": "Microsoft Word",
            "title": "John Doe Resume"
        }
        structure_issues = []
        font_issues = []
        image_issues = []
        integrity_issues = []
        
        prompt = self.detector._create_authenticity_prompt(metadata)
        
        assert isinstance(prompt, str)
        assert "John Doe" in prompt
        assert "authenticity" in prompt.lower()

    @pytest.mark.asyncio
    async def test_analyze_metadata_with_ai_success(self):
        """Test successful AI metadata analysis."""
        metadata = {
            "author": "John Doe",
            "creator": "Microsoft Word",
            "title": "John Doe Resume"
        }
        
        with patch.object(self.detector, 'bedrock_client') as mock_client:
            mock_invoke = Mock()
            mock_invoke.return_value = {
                'body': Mock(read=Mock(return_value='{"content": [{"text": "{\\"authenticityScore\\": 85, \\"suspiciousIndicators\\": [], \\"rationale\\": \\"Document appears authentic\\"}"}]}'))
            }
            mock_client.invoke_model = mock_invoke
            
            result = await self.detector._analyze_metadata_with_ai(metadata)
            
            assert result["authenticityScore"] == 85
            assert result["suspiciousIndicators"] == []
            assert result["rationale"] == "Document appears authentic"

    @pytest.mark.asyncio
    async def test_analyze_document_authenticity_unsupported_type(self):
        """Test document authenticity analysis for unsupported file type."""
        filename = "test.txt"
        file_type = "text/plain"
        content = b"Test content"
        
        result = await self.detector.analyze_document_authenticity(content, filename, file_type)
        
        # Should return fallback result
        assert result.fileName == filename
        assert result.fileSize == len(content)
        assert result.fileType == file_type
        assert result.authenticityScore == 50  # Default fallback score
