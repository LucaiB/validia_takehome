"""
Background verification models for professional background checking.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any

class PositionClaim(BaseModel):
    """A claimed work position."""
    employer_name: str
    title: Optional[str] = None
    start: Optional[str] = Field(None, description="YYYY or YYYY-MM")
    end: Optional[str] = Field(None, description="YYYY or YYYY-MM or 'present'")
    location: Optional[str] = None
    employer_domain: Optional[str] = None  # e.g., example.com

class EducationClaim(BaseModel):
    """A claimed education."""
    institution_name: str
    degree: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None

class Identifiers(BaseModel):
    """External identifiers for the person."""
    github_username: Optional[str] = None
    orcid_id: Optional[str] = None  # e.g., 0000-0002-1825-0097
    personal_site: Optional[HttpUrl] = None

class BackgroundVerifyRequest(BaseModel):
    """Request for background verification."""
    full_name: str
    positions: List[PositionClaim] = []
    educations: List[EducationClaim] = []
    identifiers: Optional[Identifiers] = None

class BackgroundVerifyResponse(BaseModel):
    """Response from background verification."""
    company_evidence: Dict[str, Any]
    education_evidence: Dict[str, Any]
    developer_evidence: Dict[str, Any]
    timeline_assessment: Dict[str, Any]
    score: Dict[str, float]
    rationale: List[str]
    sources_used: List[str]
