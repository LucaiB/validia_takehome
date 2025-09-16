"""
Main orchestrator for resume fraud detection analysis.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import json
import re
from datetime import datetime

from models.schemas import (
    FileAnalysisResponse, AggregatedReport, RiskSlice, Evidence,
    CandidateInfo, AiDetectionResult, DocumentAuthenticityResult,
    ContactVerificationResult, BackgroundVerificationResult, DigitalFootprintResult
)
from models.background_schemas import PositionClaim, EducationClaim
from detectors.ai_text import AITextDetector
from detectors.document_auth import DocumentAuthenticityDetector
from detectors.contact_info import ContactInfoDetector
from detectors.file_security import FileSecurityScanner
from utils.logging_config import get_logger
from utils.config import Settings

logger = get_logger(__name__)

class ResumeAnalyzer:
    """Main analyzer that orchestrates all fraud detection components."""
    
    def __init__(self, settings: Settings):
        """Initialize the resume analyzer."""
        self.settings = settings
        
        # Initialize detectors
        self.ai_detector = AITextDetector(
            settings.aws_access_key_id,
            settings.aws_secret_access_key,
            settings.aws_region
        )
        
        self.document_detector = DocumentAuthenticityDetector(
            settings.aws_access_key_id,
            settings.aws_secret_access_key,
            settings.aws_region
        )
        
        self.contact_detector = ContactInfoDetector(
            settings.numverify_api_key,
            settings.abstract_api_key
        )
        
        self.security_scanner = FileSecurityScanner()
        
        # Default risk weights
        self.risk_weights = {
            "Contact Info": 0.20,
            "AI Content": 0.30,
            "Background": 0.20,
            "Digital Footprint": 0.10,
            "Document Authenticity": 0.10,
            "File Security": 0.10,
        }
    
    async def analyze_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        candidate_hints: Optional[Dict[str, Any]] = None
    ) -> FileAnalysisResponse:
        """
        Perform comprehensive analysis of a resume file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            file_type: MIME type of the file
            candidate_hints: Optional candidate information hints
            
        Returns:
            FileAnalysisResponse with complete analysis
        """
        try:
            logger.info(f"Starting comprehensive analysis for {filename}")
            
            # Extract text content
            extracted_text = await self._extract_text_content(file_content, filename, file_type)
            
            # Perform file security scan
            security_scan = await self.security_scanner.scan_file(filename, file_content)
            
            # Check if file is safe to process
            if not security_scan["is_safe"]:
                logger.warning(f"File {filename} failed security scan: {security_scan['threats_detected']}")
                # Extract basic candidate info for security response
                candidate_info = await self._extract_candidate_info(extracted_text, candidate_hints)
                # Return early with security warning
                return FileAnalysisResponse(
                    extractedText=extracted_text,
                    candidateInfo=candidate_info,
                    aiDetection=AiDetectionResult(
                        is_ai_generated=False,
                        confidence=0,
                        model="security-scanner",
                        rationale="File failed security scan and was not processed"
                    ),
                    documentAuthenticity=DocumentAuthenticityResult(
                        fileName=filename,
                        fileSize=len(file_content),
                        fileType=file_type,
                        creationDate=None,
                        modificationDate=None,
                        author=None,
                        creator=None,
                        producer=None,
                        title=None,
                        subject=None,
                        keywords=None,
                        pdfVersion=None,
                        pageCount=0,
                        isEncrypted=False,
                        hasDigitalSignature=False,
                        softwareUsed=None,
                        suspiciousIndicators=[threat["message"] for threat in security_scan["threats_detected"]],
                        authenticityScore=0,
                        rationale="File failed security scan"
                    ),
                    contactVerification=None,
                    backgroundVerification=None,
                    digitalFootprint=None,
                    aggregatedReport=AggregatedReport(
                        overall_score=0,
                        weights_applied=self.risk_weights,
                        slices=[],
                        evidence=Evidence(
                            contact=None,
                            ai=AiDetectionResult(
                                is_ai_generated=False,
                                confidence=0,
                                model="security-scanner",
                                rationale="File failed security scan"
                            ),
                            document_authenticity=DocumentAuthenticityResult(
                                fileName=filename,
                                fileSize=len(file_content),
                                fileType=file_type,
                                creationDate=None,
                                modificationDate=None,
                                author=None,
                                creator=None,
                                producer=None,
                                title=None,
                                subject=None,
                                keywords=None,
                                pdfVersion=None,
                                pageCount=0,
                                isEncrypted=False,
                                hasDigitalSignature=False,
                                softwareUsed=None,
                                suspiciousIndicators=[threat["message"] for threat in security_scan["threats_detected"]],
                                authenticityScore=0,
                                rationale="File failed security scan"
                            ),
                            background=None,
                            digital_footprint=None
                        ),
                        rationale=["File failed security scan and was not processed"],
                        generated_at=datetime.now().isoformat(),
                        version="1.0.0"
                    ),
                    rationale="File failed security scan and was not processed",
                    usage=None,
                    request_id=f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            # Extract candidate information
            candidate_info = await self._extract_candidate_info(extracted_text, candidate_hints)
            
            # Run all detectors in parallel
            tasks = [
                self.ai_detector.detect_ai_content(extracted_text),
                self.document_detector.analyze_document_authenticity(file_content, filename, file_type),
                self._verify_contact_info(candidate_info),
                self._verify_background(candidate_info, extracted_text),
                self._analyze_digital_footprint(candidate_info)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract results
            ai_detection = results[0] if not isinstance(results[0], Exception) else self._create_fallback_ai_result()
            document_authenticity = results[1] if not isinstance(results[1], Exception) else self._create_fallback_document_result(filename, file_type, len(file_content))
            contact_verification = results[2] if not isinstance(results[2], Exception) else None
            background_verification = results[3] if not isinstance(results[3], Exception) else None
            digital_footprint = results[4] if not isinstance(results[4], Exception) else None
            
            # Create aggregated report
            aggregated_report = await self._create_aggregated_report(
                ai_detection, document_authenticity, contact_verification,
                background_verification, digital_footprint, security_scan
            )
            
            # Create response
            response = FileAnalysisResponse(
                extractedText=extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""),
                candidateInfo=candidate_info,
                aiDetection=ai_detection,
                documentAuthenticity=document_authenticity,
                contactVerification=contact_verification,
                backgroundVerification=background_verification,
                digitalFootprint=digital_footprint,
                aggregatedReport=aggregated_report,
                rationale=ai_detection.rationale,
                request_id=f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            )
            
            logger.info(f"Analysis completed for {filename}")
            return response
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise
    
    async def detect_ai_content(self, text: str, model: str = "claude-sonnet-4") -> AiDetectionResult:
        """Detect AI-generated content in text."""
        return await self.ai_detector.detect_ai_content(text, model)
    
    async def analyze_document_authenticity(
        self, 
        file_content: bytes, 
        filename: str, 
        file_type: str
    ) -> DocumentAuthenticityResult:
        """Analyze document authenticity."""
        return await self.document_detector.analyze_document_authenticity(file_content, filename, file_type)
    
    async def verify_contact_info(
        self, 
        email: str, 
        phone: Optional[str] = None, 
        location: Optional[str] = None
    ) -> ContactVerificationResult:
        """Verify contact information."""
        return await self.contact_detector.verify_contact_info(email, phone, location)
    
    async def _extract_text_content(self, file_content: bytes, filename: str, file_type: str) -> str:
        """Extract text content from file."""
        try:
            if filename.lower().endswith('.pdf'):
                return await self._extract_pdf_text(file_content)
            elif filename.lower().endswith('.docx'):
                return await self._extract_docx_text(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF."""
        try:
            import PyPDF2
            import io
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            import io
            
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    async def _extract_candidate_info(self, text: str, hints: Optional[Dict[str, Any]] = None) -> CandidateInfo:
        """Extract candidate information from text using AI."""
        try:
            # Use hints if provided
            if hints:
                return CandidateInfo(
                    full_name=hints.get('full_name', 'Unknown Candidate'),
                    email=hints.get('email'),
                    phone=hints.get('phone'),
                    location=hints.get('location'),
                    linkedin=hints.get('linkedin'),
                    github=hints.get('github'),
                    website=hints.get('website')
                )
            
            # Use AI to extract candidate information
            prompt = f"""Extract candidate information from this resume. Use the <extract> tags to structure your response.

<extract>
{{
  "full_name": "First Last",
  "email": "email@example.com",
  "phone": "+1234567890",
  "location": "City, State/Country",
  "linkedin": "https://linkedin.com/in/username",
  "github": "https://github.com/username",
  "website": "https://website.com"
}}
</extract>

Extract the person's full name, email, phone, location, and any social media profiles. If a field is not found, use null.

Resume text:
{text[:2000]}"""

            # Call Bedrock for candidate extraction
            result = await self._call_bedrock_for_extraction(prompt)
            
            # Parse the response from XML tags
            import json
            try:
                response_text = result.get('rationale', '')
                if '<extract>' in response_text and '</extract>' in response_text:
                    extract_start = response_text.find('<extract>') + len('<extract>')
                    extract_end = response_text.find('</extract>')
                    json_str = response_text[extract_start:extract_end].strip()
                    data = json.loads(json_str)
                    
                    return CandidateInfo(
                        full_name=data.get('full_name', 'Unknown Candidate'),
                        email=data.get('email'),
                        phone=data.get('phone'),
                        location=data.get('location'),
                        linkedin=data.get('linkedin'),
                        github=data.get('github'),
                        website=data.get('website')
                    )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse candidate info from AI response: {e}")
            
            # Fallback to regex extraction
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
            linkedin_pattern = r'linkedin\.com/in/[\w-]+'
            github_pattern = r'github\.com/[\w-]+'
            website_pattern = r'https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,})+(?:/[^\\s]*)?'
            
            # Extract matches
            email_match = re.search(email_pattern, text)
            phone_match = re.search(phone_pattern, text)
            linkedin_match = re.search(linkedin_pattern, text)
            github_match = re.search(github_pattern, text)
            website_match = re.search(website_pattern, text)
            
            # Extract name (first line that looks like a name)
            lines = text.split('\n')
            name = 'Unknown Candidate'
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if len(line) > 3 and len(line) < 50 and not any(word in line.lower() for word in ['email', 'phone', 'address', 'experience', 'education']):
                    name = line
                    break
            
            return CandidateInfo(
                full_name=name,
                email=email_match.group(0) if email_match else None,
                phone=phone_match.group(0) if phone_match else None,
                location=None,  # Would need more sophisticated extraction
                linkedin=f"https://{linkedin_match.group(0)}" if linkedin_match else None,
                github=f"https://{github_match.group(0)}" if github_match else None,
                website=website_match.group(0) if website_match else None
            )
            
        except Exception as e:
            logger.error(f"Error extracting candidate info: {e}")
            return CandidateInfo(full_name="Unknown Candidate")
    
    async def _verify_contact_info(self, candidate_info: CandidateInfo) -> Optional[Dict[str, Any]]:
        """Verify contact information using comprehensive verification service."""
        if not candidate_info.email:
            return None
        
        # Use the comprehensive contact verification service
        return await self.contact_detector.contact_service.verify_contact(
            full_name=candidate_info.full_name,
            email=candidate_info.email,
            phone=candidate_info.phone,
            stated_location=candidate_info.location,
            default_region="US"
        )
    
    async def _verify_background(self, candidate_info: CandidateInfo, extracted_text: str) -> Optional[Dict[str, Any]]:
        """Verify professional background using comprehensive verification service."""
        try:
            logger.info(f"Starting background verification for {candidate_info.full_name}")
            
            # Extract positions and education from resume text using AI
            logger.info(f"Extracting positions and education for {candidate_info.full_name}")
            positions = await self._extract_positions_from_text(extracted_text)
            educations = await self._extract_educations_from_text(extracted_text)
            logger.info(f"Extracted {len(positions)} positions and {len(educations)} educations")
            
            # Debug: Print extracted companies
            for i, pos in enumerate(positions):
                logger.info(f"Position {i+1}: {pos.employer_name} - {pos.title} ({pos.start} to {pos.end})")
            
            # Debug: Print extracted education
            for i, edu in enumerate(educations):
                logger.info(f"Education {i+1}: {edu.institution_name} - {edu.degree} ({edu.start_year}-{edu.end_year})")
            
            # Extract GitHub username from GitHub URL if available
            github_username = None
            if candidate_info.github:
                import re
                match = re.search(r'github\.com/([^/]+)', candidate_info.github)
                if match:
                    github_username = match.group(1)
            
            # Create background verification request
            from models.background_schemas import BackgroundVerifyRequest, Identifiers
            
            background_request = BackgroundVerifyRequest(
                full_name=candidate_info.full_name,
                positions=positions,
                educations=educations,
                identifiers=Identifiers(
                    github_username=github_username,
                    orcid_id=None,
                    personal_site=candidate_info.website
                )
            )
            
            # Call background verification service with timeout
            logger.info(f"Calling background verification with {len(positions)} positions and {len(educations)} educations")
            from background_verification.logic import run_background_verification
            
            # Add timeout protection
            import asyncio
            result = await asyncio.wait_for(
                run_background_verification(background_request),
                timeout=30.0
            )
            
            # Convert to dictionary for consistency
            result_dict = result.dict() if hasattr(result, 'dict') else result
            logger.info(f"Background verification completed with score: {result_dict.get('score', {}).get('composite', 'unknown')}")
            return result_dict
            
        except asyncio.TimeoutError:
            logger.error("Background verification timed out after 30 seconds")
            return None
        except Exception as e:
            logger.error(f"Background verification failed: {e}")
            import traceback
            logger.error(f"Background verification traceback: {traceback.format_exc()}")
            return None
    
    async def _extract_positions_from_text(self, text: str) -> List[PositionClaim]:
        """Extract work positions from resume text using AI."""
        try:
            
            # Use Bedrock to extract work experience with XML tags
            prompt = f"""Extract work experience from this resume. Use the <extract> tags to structure your response.

IMPORTANT: 
- Extract each work position separately, even if the formatting is poor
- Look for company names that appear at the start of lines or after job descriptions
- Company names are usually followed by job titles and dates
- If you see multiple company names, create separate positions for each
- For company names, use the main company name without abbreviations in parentheses
  - "Amazon Web Services (AWS)" → "Amazon Web Services"
  - "Microsoft (MSFT)" → "Microsoft"
  - "Google (GOOGL)" → "Google"

<extract>
{{
  "positions": [
    {{
      "employer_name": "Company Name",
      "title": "Job Title", 
      "start": "YYYY-MM",
      "end": "YYYY-MM or 'present'",
      "location": "City, State/Country",
      "employer_domain": "company.com"
    }}
  ]
}}
</extract>

If no work experience found, return an empty positions array. Be specific with company names and job titles.

Resume text:
{text[:4000]}"""

            # Call Bedrock directly for text extraction
            result = await self._call_bedrock_for_extraction(prompt)
            
            # Debug: Log the raw AI response
            logger.info(f"Raw AI response for positions: {result.get('rationale', '')[:500]}...")
            
            # Parse the response from XML tags
            import json
            try:
                # Extract JSON from the <extract> tags
                response_text = result.get('rationale', '')
                if '<extract>' in response_text and '</extract>' in response_text:
                    extract_start = response_text.find('<extract>') + len('<extract>')
                    extract_end = response_text.find('</extract>')
                    json_str = response_text[extract_start:extract_end].strip()
                    logger.info(f"Extracted JSON for positions: {json_str}")
                    data = json.loads(json_str)
                    
                    positions = []
                    for pos in data.get('positions', []):
                        if isinstance(pos, dict) and 'employer_name' in pos:
                            positions.append(PositionClaim(
                                employer_name=pos.get('employer_name', ''),
                                title=pos.get('title'),
                                start=pos.get('start'),
                                end=pos.get('end'),
                                location=pos.get('location'),
                                employer_domain=pos.get('employer_domain')
                            ))
                    logger.info(f"Parsed {len(positions)} positions from AI response")
                    return positions
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse positions from AI response: {e}")
                logger.warning(f"Raw response was: {result.get('rationale', '')}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting positions: {e}")
            return []
    
    async def _extract_educations_from_text(self, text: str) -> List[EducationClaim]:
        """Extract education from resume text using AI."""
        try:
            
            # Use Bedrock to extract education with XML tags
            prompt = f"""Extract education from this resume. Use the <extract> tags to structure your response.

IMPORTANT: For institution_name, extract ONLY the parent university/college name, NOT the specific school or department.

Examples:
- "University of Virginia, School of Engineering and Applied Sciences" → "University of Virginia"
- "MIT, Computer Science Department" → "Massachusetts Institute of Technology"
- "Stanford University, School of Medicine" → "Stanford University"
- "Harvard Business School" → "Harvard University"

<extract>
{{
  "educations": [
    {{
      "institution_name": "University Name (parent institution only)",
      "degree": "Degree Type",
      "start_year": YYYY,
      "end_year": YYYY
    }}
  ]
}}
</extract>

If no education found, return an empty educations array. Extract only the main university/college name, not departments or schools.

Resume text:
{text[:4000]}"""

            # Call Bedrock directly for text extraction
            result = await self._call_bedrock_for_extraction(prompt)
            
            # Parse the response from XML tags
            import json
            try:
                # Extract JSON from the <extract> tags
                response_text = result.get('rationale', '')
                if '<extract>' in response_text and '</extract>' in response_text:
                    extract_start = response_text.find('<extract>') + len('<extract>')
                    extract_end = response_text.find('</extract>')
                    json_str = response_text[extract_start:extract_end].strip()
                    data = json.loads(json_str)
                    
                    educations = []
                    for edu in data.get('educations', []):
                        if isinstance(edu, dict) and 'institution_name' in edu:
                            educations.append(EducationClaim(
                                institution_name=edu.get('institution_name', ''),
                                degree=edu.get('degree'),
                                start_year=edu.get('start_year'),
                                end_year=edu.get('end_year')
                            ))
                    return educations
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse education from AI response: {e}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting education: {e}")
            return []
    
    async def _call_bedrock_for_extraction(self, prompt: str) -> Dict[str, Any]:
        """Call Bedrock directly for text extraction tasks."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Initialize Bedrock client
            bedrock_client = boto3.client(
                'bedrock-runtime',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
            
            # Prepare the request
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = bedrock_client.invoke_model(
                modelId="us.anthropic.claude-sonnet-4-20250514-v1:0",
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [{}])[0].get('text', '')
            
            return {
                'rationale': content,
                'usage': response_body.get('usage', {}),
                'model': 'claude-sonnet-4'
            }
            
        except Exception as e:
            logger.error(f"Error calling Bedrock for extraction: {e}")
            return {'rationale': '', 'usage': {}, 'model': 'claude-sonnet-4'}
    
    async def _analyze_digital_footprint(self, candidate_info: CandidateInfo) -> Optional[DigitalFootprintResult]:
        """Analyze digital footprint using SerpAPI and other sources."""
        try:
            logger.info(f"Starting digital footprint analysis for {candidate_info.full_name}")
            
            # Initialize digital footprint service
            from detectors.digital_footprint import DigitalFootprintService
            from utils.config import get_settings
            
            settings = get_settings()
            footprint_service = DigitalFootprintService(serpapi_key=settings.serpapi_key)
            
            # Analyze digital footprint
            result = await footprint_service.analyze_digital_footprint(
                full_name=candidate_info.full_name,
                email=candidate_info.email,
                phone=candidate_info.phone
            )
            
            # Convert to DigitalFootprintResult format
            search_results = [r.get('title', '') for r in result.get('google_search', [])]
            
            # Extract social media presence from search results
            social_presence = {}
            professional_keywords = ['linkedin', 'github', 'stackoverflow', 'researchgate', 'scholar']
            
            for result_item in result.get('google_search', []):
                title = result_item.get('title', '').lower()
                link = result_item.get('link', '').lower()
                snippet = result_item.get('snippet', '').lower()
                
                for keyword in professional_keywords:
                    if keyword in title or keyword in link:
                        if keyword not in social_presence:
                            social_presence[keyword] = []
                        social_presence[keyword].append({
                            'title': result_item.get('title', ''),
                            'link': result_item.get('link', ''),
                            'snippet': result_item.get('snippet', '')
                        })
                        break
            
            # Calculate consistency score (convert from 0-1 to 0-100)
            consistency_score = int(result.get('score', 0.5) * 100)
            
            # Create details string
            details = f"Found {len(search_results)} search results. "
            if social_presence:
                platforms = list(social_presence.keys())
                details += f"Professional presence on: {', '.join(platforms)}. "
            details += f"Sources used: {', '.join(result.get('sources_used', []))}"
            
            logger.info(f"Digital footprint analysis completed with score: {consistency_score}")
            
            return DigitalFootprintResult(
                social_presence=social_presence,
                search_results=search_results,
                consistency_score=consistency_score,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Digital footprint analysis failed: {e}")
            return DigitalFootprintResult(
                social_presence={},
                search_results=[],
                consistency_score=0,
                details=f"Analysis failed: {str(e)}"
            )
    
    async def _create_aggregated_report(
        self,
        ai_detection: AiDetectionResult,
        document_authenticity: DocumentAuthenticityResult,
        contact_verification: Optional[Dict[str, Any]],
        background_verification: Optional[Dict[str, Any]],
        digital_footprint: Optional[DigitalFootprintResult],
        security_scan: Optional[Dict[str, Any]]
    ) -> AggregatedReport:
        """Create aggregated risk assessment report."""
        
        # Calculate risk slices
        slices = []
        
        # AI Content slice
        ai_score = 100 - ai_detection.confidence if ai_detection.is_ai_generated else ai_detection.confidence
        slices.append(RiskSlice(
            label="AI Content",
            score=ai_score,
            description=f"{'AI Generated' if ai_detection.is_ai_generated else 'Human Written'} (confidence: {ai_detection.confidence}%)"
        ))
        
        # Document Authenticity slice
        slices.append(RiskSlice(
            label="Document Authenticity",
            score=document_authenticity.authenticityScore,
            description=f"Authenticity score: {document_authenticity.authenticityScore}%"
        ))
        
        # Contact Info slice
        if contact_verification:
            # Extract score from comprehensive contact verification data
            contact_score = int(contact_verification.get('score', {}).get('composite', 0.5) * 100)
            is_verified = contact_score >= 70  # Consider 70%+ as verified
            slices.append(RiskSlice(
                label="Contact Info",
                score=contact_score,
                description=f"Contact verification score: {contact_score}%" if is_verified else f"Contact verification score: {contact_score}% (needs review)"
            ))
        else:
            slices.append(RiskSlice(
                label="Contact Info",
                score=50,
                description="Contact verification not performed"
            ))
        
        # Background slice
        if background_verification:
            background_score = int(background_verification.get('score', {}).get('composite', 0.5) * 100)
            slices.append(RiskSlice(
                label="Background",
                score=background_score,
                description=f"Background verification score: {background_score}%"
            ))
        else:
            slices.append(RiskSlice(
                label="Background",
                score=50,
                description="Background verification not performed"
            ))
        
        # Digital Footprint slice
        if digital_footprint:
            slices.append(RiskSlice(
                label="Digital Footprint",
                score=digital_footprint.consistency_score,
                description=f"Digital footprint consistency: {digital_footprint.consistency_score}%"
            ))
        else:
            slices.append(RiskSlice(
                label="Digital Footprint",
                score=50,
                description="Digital footprint analysis not performed"
            ))
        
        # Security slice
        if security_scan:
            if security_scan.get("is_safe", True):
                security_score = 100
                security_desc = "File passed security scan"
            else:
                high_threats = [t for t in security_scan.get("threats_detected", []) if t.get("severity") == "high"]
                if high_threats:
                    security_score = 0
                    security_desc = f"File failed security scan: {len(high_threats)} high-severity threats"
                else:
                    security_score = 50
                    security_desc = f"File has {len(security_scan.get('threats_detected', []))} security warnings"
            
            slices.append(RiskSlice(
                label="File Security",
                score=security_score,
                description=security_desc
            ))
        else:
            slices.append(RiskSlice(
                label="File Security",
                score=50,
                description="Security scan not performed"
            ))
        
        # Calculate overall score
        overall_score = sum(slice.score * self.risk_weights.get(slice.label, 0.1) for slice in slices)
        overall_score = int(overall_score)
        
        # Create evidence
        evidence = Evidence(
            contact=contact_verification,
            ai=ai_detection,
            document_authenticity=document_authenticity,
            background=background_verification,
            digital_footprint=digital_footprint,
            security=security_scan
        )
        
        # Create rationale
        rationale = [
            f"AI Content: {'High risk' if ai_detection.is_ai_generated else 'Low risk'} ({ai_detection.confidence}% confidence)",
            f"Document Authenticity: {document_authenticity.authenticityScore}% authentic",
            f"Contact Verification: {contact_verification.get('score', {}).get('composite', 0) * 100:.0f}% score" if contact_verification else "Contact Verification: Not performed",
            f"Background Verification: {background_verification.get('score', {}).get('composite', 0) * 100:.0f}% score" if background_verification else "Background Verification: Not performed"
        ]
        
        return AggregatedReport(
            overall_score=overall_score,
            weights_applied=self.risk_weights,
            slices=slices,
            evidence=evidence,
            rationale=rationale,
            generated_at=datetime.utcnow(),
            version="1.0.0"
        )
    
    def _create_fallback_ai_result(self) -> AiDetectionResult:
        """Create fallback AI detection result."""
        return AiDetectionResult(
            is_ai_generated=False,
            confidence=50,
            model="claude-sonnet-4",
            rationale="AI detection failed - using fallback"
        )
    
    def _create_fallback_document_result(self, filename: str, file_type: str, file_size: int) -> DocumentAuthenticityResult:
        """Create fallback document authenticity result."""
        return DocumentAuthenticityResult(
            fileName=filename,
            fileSize=file_size,
            fileType=file_type,
            suspiciousIndicators=["Analysis failed"],
            authenticityScore=50,
            rationale="Document authenticity analysis failed"
        )
