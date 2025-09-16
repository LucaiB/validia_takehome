"""
Digital footprint analysis API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from detectors.digital_footprint import DigitalFootprintService
from utils.logging_config import get_logger
from utils.config import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/digital-footprint", tags=["digital-footprint"])

class DigitalFootprintRequest(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None

class DigitalFootprintResponse(BaseModel):
    google_search: list
    social_media: dict
    professional_networks: dict
    sources_used: list
    score: float
    rationale: list

@router.post("/analyze", response_model=DigitalFootprintResponse)
async def analyze_digital_footprint(request: DigitalFootprintRequest):
    """
    Analyze digital footprint and online presence.
    
    Searches Google for information about the person using SerpAPI.
    Analyzes professional networks and social media presence.
    """
    try:
        settings = get_settings()
        
        # Initialize digital footprint service
        footprint_service = DigitalFootprintService(
            serpapi_key=settings.serpapi_key
        )
        
        # Perform analysis
        result = await footprint_service.analyze_digital_footprint(
            full_name=request.full_name,
            email=request.email,
            phone=request.phone
        )
        
        logger.info(f"Digital footprint analysis completed for {request.full_name}")
        return DigitalFootprintResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in digital footprint analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Digital footprint analysis failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for digital footprint service."""
    return {"status": "healthy", "service": "digital-footprint"}
