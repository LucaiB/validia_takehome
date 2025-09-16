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
            logger.info("Falling back to heuristic analysis")
            # Return heuristic fallback result
            return self._heuristic_analysis(text, model)
    
    def _heuristic_analysis(self, text: str, model: str) -> AiDetectionResult:
        """
        Heuristic analysis for AI detection when Bedrock is unavailable.
        
        Args:
            text: Text content to analyze
            model: Model name
            
        Returns:
            AiDetectionResult with heuristic analysis
        """
        try:
            logger.info("Performing heuristic AI content analysis")
            
            # Calculate various heuristics
            text_length = len(text)
            word_count = len(text.split())
            
            # AI-like patterns
            ai_indicators = 0
            rationale_parts = []
            
            # 1. Check for repetitive phrases
            words = text.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only count meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Find overused words
            overused_words = [word for word, count in word_freq.items() if count > 3]
            if overused_words:
                ai_indicators += 1
                rationale_parts.append(f"Repetitive language: {', '.join(overused_words[:3])}")
            
            # 2. Check for buzzword density
            buzzwords = [
                'leverage', 'synergy', 'optimize', 'streamline', 'facilitate',
                'implement', 'utilize', 'enhance', 'maximize', 'minimize',
                'strategic', 'innovative', 'dynamic', 'robust', 'scalable',
                'comprehensive', 'proactive', 'collaborative', 'transformative',
                'cutting-edge', 'state-of-the-art', 'best-in-class', 'world-class'
            ]
            
            buzzword_count = sum(1 for word in words if word in buzzwords)
            buzzword_density = buzzword_count / word_count if word_count > 0 else 0
            
            if buzzword_density > 0.05:  # More than 5% buzzwords
                ai_indicators += 1
                rationale_parts.append(f"High buzzword density: {buzzword_density:.1%}")
            
            # 3. Check for generic phrases
            generic_phrases = [
                'responsible for', 'duties include', 'key responsibilities',
                'proven track record', 'strong background', 'extensive experience',
                'excellent communication skills', 'team player', 'detail-oriented',
                'results-driven', 'goal-oriented', 'self-motivated'
            ]
            
            generic_count = sum(1 for phrase in generic_phrases if phrase in text.lower())
            if generic_count > 2:
                ai_indicators += 1
                rationale_parts.append(f"Generic phrases detected: {generic_count}")
            
            # 4. Check for bullet point consistency (AI often creates very consistent formatting)
            lines = text.split('\n')
            bullet_lines = [line for line in lines if line.strip().startswith(('•', '-', '*'))]
            if len(bullet_lines) > 5:
                # Check if all bullet points start with similar patterns
                bullet_starts = [line.strip().split()[0].lower() for line in bullet_lines if line.strip().split()]
                if len(set(bullet_starts)) < len(bullet_starts) * 0.7:  # Less than 70% unique starts
                    ai_indicators += 1
                    rationale_parts.append("Repetitive bullet point structure")
            
            # 5. Check for lack of specific details
            specific_indicators = ['%', '$', 'million', 'billion', 'thousand', '2019', '2020', '2021', '2022', '2023', '2024']
            specific_count = sum(1 for indicator in specific_indicators if indicator in text)
            if specific_count < 3 and word_count > 200:
                ai_indicators += 1
                rationale_parts.append("Lack of specific metrics and details")
            
            # 6. Check for overly perfect structure
            if len(lines) > 10:
                # Check if lines are very similar in length (AI often creates uniform formatting)
                line_lengths = [len(line.strip()) for line in lines if line.strip()]
                if line_lengths:
                    avg_length = sum(line_lengths) / len(line_lengths)
                    variance = sum((length - avg_length) ** 2 for length in line_lengths) / len(line_lengths)
                    if variance < 100:  # Very low variance in line lengths
                        ai_indicators += 1
                        rationale_parts.append("Overly uniform formatting")
            
            # Calculate confidence based on indicators
            if ai_indicators == 0:
                confidence = 20
                is_ai = False
                rationale = "Heuristic analysis suggests human-written content"
            elif ai_indicators == 1:
                confidence = 40
                is_ai = False
                rationale = "Heuristic analysis suggests likely human-written content"
            elif ai_indicators == 2:
                confidence = 60
                is_ai = True
                rationale = "Heuristic analysis suggests possible AI-generated content"
            else:
                confidence = 80
                is_ai = True
                rationale = "Heuristic analysis suggests likely AI-generated content"
            
            if rationale_parts:
                rationale += f". Indicators: {'; '.join(rationale_parts)}"
            
            return AiDetectionResult(
                is_ai_generated=is_ai,
                confidence=confidence,
                model=f"{model}-heuristic",
                rationale=rationale
            )
            
        except Exception as e:
            logger.error(f"Error in heuristic analysis: {e}")
            return AiDetectionResult(
                is_ai_generated=False,
                confidence=50,
                model=f"{model}-heuristic-failed",
                rationale="Heuristic analysis failed - unable to determine AI content"
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
