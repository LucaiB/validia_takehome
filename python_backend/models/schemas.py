"""
Pydantic schemas for resume fraud detection API.
Mirrors the TypeScript types from the Next.js frontend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

class CandidateInfo(BaseModel):
    """Candidate information extracted from resume."""
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None

class AiDetectionResult(BaseModel):
    """AI content detection results."""
    is_ai_generated: bool
    confidence: int = Field(..., ge=0, le=100)
    model: str
    rationale: Optional[str] = None

class DocumentAuthenticityResult(BaseModel):
    """Document authenticity analysis results."""
    fileName: str
    fileSize: int
    fileType: str
    creationDate: Optional[str] = None
    modificationDate: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    pdfVersion: Optional[str] = None
    pageCount: Optional[int] = None
    isEncrypted: bool = False
    hasDigitalSignature: bool = False
    softwareUsed: Optional[str] = None
    suspiciousIndicators: List[str] = Field(default_factory=list)
    authenticityScore: int = Field(..., ge=0, le=100)
    rationale: str

class ContactVerificationResult(BaseModel):
    """Contact information verification results."""
    email: str
    phone: Optional[str] = None
    is_verified: bool
    details: str
    email_valid: Optional[bool] = None
    email_disposable: Optional[bool] = None
    phone_valid: Optional[bool] = None
    phone_carrier: Optional[str] = None
    geo_consistent: Optional[bool] = None

class BackgroundVerificationResult(BaseModel):
    """Professional background verification results."""
    linkedin_verified: bool
    company_verified: bool
    education_verified: bool
    timeline_consistent: bool
    details: str
    verification_score: int = Field(..., ge=0, le=100)

class DigitalFootprintResult(BaseModel):
    """Digital footprint analysis results."""
    social_presence: Dict[str, Any] = Field(default_factory=dict)
    search_results: List[str] = Field(default_factory=list)
    consistency_score: int = Field(..., ge=0, le=100)
    details: str

class RiskSlice(BaseModel):
    """Individual risk assessment slice."""
    label: str
    score: int = Field(..., ge=0, le=100)
    description: str

class Evidence(BaseModel):
    """Evidence collected during analysis."""
    contact: Optional[Dict[str, Any]] = None  # Comprehensive contact verification data
    ai: Optional[AiDetectionResult] = None
    document_authenticity: Optional[DocumentAuthenticityResult] = None
    background: Optional[Dict[str, Any]] = None  # Comprehensive background verification data
    digital_footprint: Optional[DigitalFootprintResult] = None
    security: Optional[Dict[str, Any]] = None  # File security scan results

class AggregatedReport(BaseModel):
    """Comprehensive fraud risk assessment report."""
    overall_score: int = Field(..., ge=0, le=100)
    weights_applied: Dict[str, float] = Field(default_factory=dict)
    slices: List[RiskSlice] = Field(default_factory=list)
    evidence: Evidence = Field(default_factory=Evidence)
    rationale: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

class FileAnalysisRequest(BaseModel):
    """Request model for file analysis."""
    candidate_hints: Optional[Dict[str, Any]] = None

class FileAnalysisResponse(BaseModel):
    """Response model for file analysis."""
    extractedText: str
    candidateInfo: CandidateInfo
    aiDetection: AiDetectionResult
    documentAuthenticity: DocumentAuthenticityResult
    contactVerification: Optional[Dict[str, Any]] = None  # Comprehensive contact verification data
    backgroundVerification: Optional[Dict[str, Any]] = None  # Comprehensive background verification data
    digitalFootprint: Optional[DigitalFootprintResult] = None
    aggregatedReport: AggregatedReport
    rationale: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
