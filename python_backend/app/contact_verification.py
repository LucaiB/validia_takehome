"""
Contact verification API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from detectors.contact_verification import ContactVerificationService
from utils.logging_config import get_logger
from utils.config import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/contact", tags=["contact-verification"])

class ContactVerifyRequest(BaseModel):
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    stated_location: Optional[str] = None
    default_region: str = "US"

class ContactVerifyResponse(BaseModel):
    email: dict
    phone: Optional[dict] = None
    geo_consistency: Optional[dict] = None
    score: dict
    rationale: list

@router.post("/verify", response_model=ContactVerifyResponse)
async def verify_contact(request: ContactVerifyRequest):
    """
    Comprehensive contact verification endpoint.
    
    Verifies email syntax, MX records, disposable status, role-based patterns.
    Validates phone numbers using libphonenumber with geocoding.
    Checks geo consistency between phone and stated location.
    """
    try:
        settings = get_settings()
        
        # Initialize contact verification service
        contact_service = ContactVerificationService(
            numverify_api_key=settings.numverify_api_key,
            abstract_api_key=settings.abstract_api_key
        )
        
        # Perform verification
        result = await contact_service.verify_contact(
            full_name=request.full_name,
            email=request.email,
            phone=request.phone,
            stated_location=request.stated_location,
            default_region=request.default_region
        )
        
        logger.info(f"Contact verification completed for {request.email}")
        return ContactVerifyResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in contact verification: {e}")
        raise HTTPException(status_code=500, detail=f"Contact verification failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for contact verification service."""
    return {"status": "healthy", "service": "contact-verification"}
