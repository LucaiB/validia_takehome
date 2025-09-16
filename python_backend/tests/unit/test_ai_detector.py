"""
Unit tests for AI text detector.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from detectors.ai_text import AITextDetector


class TestAITextDetector:
    """Test cases for AITextDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = AITextDetector(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_region="us-east-1"
        )

    @pytest.mark.asyncio
    async def test_detect_ai_content_human_written(self):
        """Test AI detection for human-written content."""
        human_text = """
        I have been working as a software engineer for the past 5 years.
        My experience includes developing web applications using Python and JavaScript.
        I have a Bachelor's degree in Computer Science from Stanford University.
        I enjoy solving complex problems and working in collaborative teams.
        """
        
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.25, "rationale": "Content shows natural human writing patterns"}'}]
            }
            
            result = await self.detector.detect_ai_content(human_text)
            
            assert result.is_ai_generated is False
            assert result.confidence == 25
            assert "human" in result.rationale.lower()

    @pytest.mark.asyncio
    async def test_detect_ai_content_ai_generated(self):
        """Test AI detection for AI-generated content."""
        ai_text = """
        I am a highly skilled and experienced software engineer with extensive expertise
        in developing cutting-edge solutions using state-of-the-art technologies.
        My comprehensive background encompasses full-stack development, cloud computing,
        and agile methodologies. I am passionate about leveraging innovative approaches
        to deliver exceptional results that exceed expectations.
        """
        
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.85, "rationale": "Content shows typical AI generation patterns"}'}]
            }
            
            result = await self.detector.detect_ai_content(ai_text)
            
            assert result.is_ai_generated is True
            assert result.confidence == 85
            assert "ai" in result.rationale.lower()

    @pytest.mark.asyncio
    async def test_detect_ai_content_empty_text(self):
        """Test AI detection for empty text."""
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.0, "rationale": "No content to analyze"}'}]
            }
            
            result = await self.detector.detect_ai_content("")
            
            assert result.is_ai_generated is False
            assert result.confidence == 0

    @pytest.mark.asyncio
    async def test_detect_ai_content_short_text(self):
        """Test AI detection for very short text."""
        short_text = "John Doe"
        
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.1, "rationale": "Insufficient content for reliable analysis"}'}]
            }
            
            result = await self.detector.detect_ai_content(short_text)
            
            assert result.is_ai_generated is False
            assert result.confidence == 10

    @pytest.mark.asyncio
    async def test_detect_ai_content_with_model_override(self):
        """Test AI detection with custom model."""
        text = "Test content"
        
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.5, "rationale": "Test result"}'}]
            }
            
            result = await self.detector.detect_ai_content(text, model="claude-3-sonnet")
            
            assert result.model == "claude-sonnet-4"  # Actual model used
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_ai_content_bedrock_error(self):
        """Test AI detection when Bedrock call fails."""
        text = "Test content"
        
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.side_effect = Exception("Bedrock API error")
            
            result = await self.detector.detect_ai_content(text)
            
            # Should return fallback result
            assert result.is_ai_generated is False
            assert result.confidence == 50  # Fallback confidence
            assert "failed" in result.rationale.lower()

    @pytest.mark.asyncio
    async def test_call_bedrock_success(self):
        """Test successful Bedrock API call."""
        text = "Test content"
        expected_response = {
            "content": [{"text": '{"ai_likelihood": 0.3, "rationale": "Test rationale"}'}]
        }
        
        with patch.object(self.detector, 'bedrock_client') as mock_client:
            mock_invoke = Mock()
            mock_invoke.return_value = {
                'body': Mock(read=Mock(return_value='{"content": [{"text": "{\\"ai_likelihood\\": 0.3, \\"rationale\\": \\"Test rationale\\"}"}]}'))
            }
            mock_client.invoke_model = mock_invoke
            
            result = await self.detector._call_bedrock(text)
            
            assert result == expected_response

    def test_create_detection_prompt(self):
        """Test prompt creation."""
        text = "This is a test resume content."
        prompt = self.detector._create_detection_prompt(text)
        
        assert isinstance(prompt, str)
        assert text in prompt
        assert "AI-generated" in prompt
        assert "human-written" in prompt

    def test_parse_response_valid(self):
        """Test parsing valid Bedrock response."""
        response = {
            "content": [{"text": '{"ai_likelihood": 0.75, "rationale": "AI patterns detected"}'}]
        }
        result = self.detector._parse_response(response)
        
        assert result.is_ai_generated is True
        assert result.confidence == 75
        assert "AI patterns" in result.rationale

    @pytest.mark.asyncio
    async def test_detect_ai_content_confidence_boundaries(self):
        """Test AI detection with confidence at boundaries."""
        text = "Test content"
        
        # Test high confidence
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.95, "rationale": "Very high confidence AI"}'}]
            }
            
            result = await self.detector.detect_ai_content(text)
            assert result.confidence == 95

        # Test low confidence
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.05, "rationale": "Very low confidence human"}'}]
            }
            
            result = await self.detector.detect_ai_content(text)
            assert result.confidence == 5

    @pytest.mark.asyncio
    async def test_detect_ai_content_unicode_text(self):
        """Test AI detection with Unicode text."""
        unicode_text = "Résumé avec des caractères spéciaux: é, ñ, ü, 中文, العربية"
        
        with patch.object(self.detector, '_call_bedrock') as mock_call:
            mock_call.return_value = {
                "content": [{"text": '{"ai_likelihood": 0.2, "rationale": "Unicode content handled properly"}'}]
            }
            
            result = await self.detector.detect_ai_content(unicode_text)
            
            assert result.is_ai_generated is False
            assert result.confidence == 20
