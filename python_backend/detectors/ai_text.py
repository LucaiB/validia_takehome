"""
AI text detection using Amazon Bedrock.
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

from models.schemas import AiDetectionResult
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AITextDetector:
    """Detector for AI-generated text using Amazon Bedrock."""
    
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, aws_region: str):
        """Initialize the AI text detector."""
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        self.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    
    async def detect_ai_content(self, text: str, model: str = "claude-sonnet-4") -> AiDetectionResult:
        """
        Detect AI-generated content in the given text.
        
        Args:
            text: Text content to analyze
            model: Model name to use for detection
            
        Returns:
            AiDetectionResult with detection results
        """
        try:
            logger.info(f"Starting AI content detection for text of length {len(text)}")
            
            # Truncate text if too long
            max_text_length = 6000
            if len(text) > max_text_length:
                text = text[:max_text_length]
                logger.warning(f"Text truncated to {max_text_length} characters")
            
            # Create the prompt
            prompt = self._create_detection_prompt(text)
            
            # Call Bedrock
            response = await self._call_bedrock(prompt)
            
            # Parse response
            result = self._parse_response(response)
            
            logger.info(f"AI detection completed: {result.is_ai_generated} (confidence: {result.confidence}%)")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI content detection: {e}")
            # Return fallback result
            return AiDetectionResult(
                is_ai_generated=False,
                confidence=50,
                model=model,
                rationale="Analysis failed - unable to determine AI content"
            )
    
    def _create_detection_prompt(self, text: str) -> str:
        """Create the prompt for AI detection."""
        return f"""You are a writing forensics assistant. Analyze the following resume content and determine if it was likely AI-generated.

Consider these factors:
- Repetitiveness and generic phrasing
- Overuse of power verbs and buzzwords
- Unnatural consistency in tone
- Lack of concrete, specific details
- Overly perfect formatting or structure
- Generic job descriptions without specific achievements
- Unusual patterns in language or structure

Resume content:
{text}

Please respond with ONLY a JSON object in this exact format:
{{
  "ai_likelihood": 0.75,
  "rationale": "Brief explanation of your analysis"
}}

Where ai_likelihood is a number between 0 and 1 (0 = definitely human-written, 1 = definitely AI-generated)."""
    
    async def _call_bedrock(self, prompt: str) -> Dict[str, Any]:
        """Call Amazon Bedrock with the given prompt."""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            return response_body
            
        except ClientError as e:
            logger.error(f"Bedrock client error: {e}")
            raise Exception(f"Failed to call Bedrock: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling Bedrock: {e}")
            raise
    
    def _parse_response(self, response: Dict[str, Any]) -> AiDetectionResult:
        """Parse the Bedrock response into an AiDetectionResult."""
        try:
            content = response.get('content', [{}])[0].get('text', '{}')
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group(0))
                ai_likelihood = parsed.get('ai_likelihood', 0.5)
                rationale = parsed.get('rationale', 'No rationale provided')
            else:
                logger.warning("No JSON found in Bedrock response")
                ai_likelihood = 0.5
                rationale = "Unable to parse AI detection response"
            
            # Convert likelihood to confidence and boolean
            confidence = int(ai_likelihood * 100)
            is_ai_generated = ai_likelihood >= 0.6
            
            return AiDetectionResult(
                is_ai_generated=is_ai_generated,
                confidence=confidence,
                model="claude-sonnet-4",
                rationale=rationale
            )
            
        except Exception as e:
            logger.error(f"Error parsing Bedrock response: {e}")
            return AiDetectionResult(
                is_ai_generated=False,
                confidence=50,
                model="claude-sonnet-4",
                rationale="Failed to parse AI detection response"
            )
