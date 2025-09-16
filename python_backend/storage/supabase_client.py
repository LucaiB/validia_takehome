"""
Supabase client for data persistence.
"""

import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from models.schemas import AggregatedReport, CandidateInfo
from utils.logging_config import get_logger

logger = get_logger(__name__)

class SupabaseStorage:
    """Supabase storage client for persisting analysis results."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase client."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    async def save_analysis(
        self,
        candidate_info: CandidateInfo,
        report: AggregatedReport
    ) -> Dict[str, Any]:
        """
        Save analysis results to Supabase.
        
        Args:
            candidate_info: Candidate information
            report: Aggregated analysis report
            
        Returns:
            Dictionary with saved record IDs
        """
        try:
            logger.info(f"Saving analysis for candidate: {candidate_info.full_name}")
            
            # Upsert candidate
            candidate_data = {
                "full_name": candidate_info.full_name,
                "email": candidate_info.email,
                "phone": candidate_info.phone,
                "location": candidate_info.location,
                "links": {
                    "linkedin": candidate_info.linkedin,
                    "github": candidate_info.github,
                    "website": candidate_info.website
                }
            }
            
            candidate_result = self.supabase.table("candidates").upsert(
                candidate_data,
                on_conflict="email"
            ).execute()
            
            if not candidate_result.data:
                raise Exception("Failed to save candidate")
            
            candidate_id = candidate_result.data[0]["id"]
            
            # Save analysis
            analysis_data = {
                "candidate_id": candidate_id,
                "overall_score": report.overall_score,
                "report": report.dict(),
                "ai_detection": report.evidence.ai.dict() if report.evidence.ai else None,
                "contact_verification": report.evidence.contact.dict() if report.evidence.contact else None,
                "created_at": report.generated_at.isoformat()
            }
            
            analysis_result = self.supabase.table("analyses").insert(analysis_data).execute()
            
            if not analysis_result.data:
                raise Exception("Failed to save analysis")
            
            analysis_id = analysis_result.data[0]["id"]
            
            # Save review history
            history_data = {
                "analysis_id": analysis_id,
                "reviewer_id": "system",
                "review_notes": f"Automated analysis completed with {report.overall_score}% risk score",
                "created_at": report.generated_at.isoformat()
            }
            
            history_result = self.supabase.table("review_history").insert(history_data).execute()
            
            logger.info(f"Analysis saved successfully - Candidate: {candidate_id}, Analysis: {analysis_id}")
            
            return {
                "candidate_id": candidate_id,
                "analysis_id": analysis_id,
                "history_id": history_result.data[0]["id"] if history_result.data else None
            }
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise
