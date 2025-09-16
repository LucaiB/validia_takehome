"""
FastAPI application for resume fraud detection service.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from typing import Optional

from models.schemas import (
    AggregatedReport,
    FileAnalysisRequest,
    FileAnalysisResponse,
    CandidateInfo,
    AiDetectionResult,
    DocumentAuthenticityResult,
    ContactVerificationResult,
    BackgroundVerificationResult,
    DigitalFootprintResult
)
from orchestrator.analyzer import ResumeAnalyzer
from utils.config import get_settings
from utils.logging_config import setup_logging
from app.contact_verification import router as contact_router
from app.background_verification import router as background_router
from app.digital_footprint import router as digital_footprint_router
from utils.cache import api_cache, analysis_cache

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Fraud Detection API",
    description="AI-powered resume fraud detection service with multi-dimensional risk assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
from middleware.rate_limit_middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(contact_router)
app.include_router(background_router)
app.include_router(digital_footprint_router)

# Global analyzer instance
analyzer: Optional[ResumeAnalyzer] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the analyzer on startup."""
    global analyzer
    try:
        settings = get_settings()
        analyzer = ResumeAnalyzer(settings)
        logger.info("Resume analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "resume-fraud-detection"}

@app.get("/test-rate-limit")
async def test_rate_limit():
    """Test endpoint for rate limiting."""
    return {"message": "This endpoint should be rate limited", "timestamp": time.time()}

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    try:
        api_stats = await api_cache.get_stats()
        analysis_stats = await analysis_cache.get_stats()
        return {
            "api_cache": api_stats,
            "analysis_cache": analysis_stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches."""
    try:
        await api_cache.clear()
        await analysis_cache.clear()
        logger.info("All caches cleared")
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear caches")

@app.post("/analyze", response_model=FileAnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    candidate_hints: Optional[str] = None
):
    """
    Analyze a resume file for fraud indicators.
    
    Args:
        file: PDF or DOCX resume file
        candidate_hints: Optional JSON string with candidate information hints
    
    Returns:
        FileAnalysisResponse with comprehensive analysis results
    """
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized")
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.lower().split('.')[-1]
        if file_extension not in ['pdf', 'docx']:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Only PDF and DOCX files are allowed."
            )
        
        # Read file content
        file_content = await file.read()
        
        # Parse candidate hints if provided
        candidate_hints_dict = {}
        if candidate_hints:
            import json
            try:
                candidate_hints_dict = json.loads(candidate_hints)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in candidate_hints, ignoring")
        
        # Perform analysis
        logger.info(f"Starting analysis for file: {file.filename}")
        result = await analyzer.analyze_file(
            file_content=file_content,
            filename=file.filename,
            file_type=file.content_type or f"application/{file_extension}",
            candidate_hints=candidate_hints_dict
        )
        
        logger.info(f"Analysis completed for file: {file.filename}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/ai-detect")
async def detect_ai_content(
    text: str,
    model: str = "claude-sonnet-4"
):
    """
    Detect AI-generated content in text.
    
    Args:
        text: Text content to analyze
        model: AI model to use for detection
    
    Returns:
        AI detection results
    """
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized")
    
    try:
        result = await analyzer.detect_ai_content(text, model)
        return result
    except Exception as e:
        logger.error(f"Error in AI detection: {e}")
        raise HTTPException(status_code=500, detail=f"AI detection failed: {str(e)}")

@app.post("/document-authenticity")
async def analyze_document_authenticity(
    file: UploadFile = File(...)
):
    """
    Analyze document authenticity from metadata.
    
    Args:
        file: PDF or DOCX file to analyze
    
    Returns:
        Document authenticity analysis results
    """
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized")
    
    try:
        file_content = await file.read()
        result = await analyzer.analyze_document_authenticity(
            file_content=file_content,
            filename=file.filename,
            file_type=file.content_type
        )
        return result
    except Exception as e:
        logger.error(f"Error in document authenticity analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")

@app.post("/contact-verify")
async def verify_contact_info(
    email: str,
    phone: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Verify contact information using external APIs.
    
    Args:
        email: Email address to verify
        phone: Phone number to verify (optional)
        location: Location for geo consistency check (optional)
    
    Returns:
        Contact verification results
    """
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized")
    
    try:
        result = await analyzer.verify_contact_info(email, phone, location)
        return result
    except Exception as e:
        logger.error(f"Error in contact verification: {e}")
        raise HTTPException(status_code=500, detail=f"Contact verification failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
