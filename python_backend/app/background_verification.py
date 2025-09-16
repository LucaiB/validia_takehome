"""
Background verification API endpoints.
"""

from fastapi import APIRouter, HTTPException
from models.background_schemas import BackgroundVerifyRequest, BackgroundVerifyResponse
from background_verification.logic import run_background_verification
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/background", tags=["background-verification"])

@router.post("/verify", response_model=BackgroundVerifyResponse)
async def verify_background(payload: BackgroundVerifyRequest):
    """
    Comprehensive background verification endpoint.
    
    Verifies professional background using free APIs:
    - Company verification via GLEIF, SEC EDGAR, OpenCorporates, Companies House
    - Education verification via College Scorecard
    - Developer verification via GitHub
    - Timeline verification via Wayback Machine
    """
    try:
        logger.info(f"Starting background verification for {payload.full_name}")
        result = await run_background_verification(payload)
        logger.info(f"Background verification completed for {payload.full_name}")
        return result
    except Exception as e:
        logger.error(f"Background verification failed for {payload.full_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Background verification failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for background verification service."""
    return {"status": "healthy", "service": "background-verification"}
