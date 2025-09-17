"""
Scoring logic for background verification.
"""

from typing import Dict

def score_background(company_ok: float, education_ok: float, timeline_ok: float, dev_ok: float) -> Dict[str, float]:
    """
    Calculate background verification scores.
    
    Weights: company 0.4, education 0.2, timeline 0.25, developer 0.15
    Note: Developer score is additive (0.0-0.6) so we normalize it to 0.0-1.0 scale
    """
    # Normalize developer score from 0.0-0.6 range to 0.0-1.0 range
    normalized_dev_ok = min(1.0, dev_ok / 0.6) if dev_ok > 0 else 0.0
    composite = round(0.40 * company_ok + 0.20 * education_ok + 0.25 * timeline_ok + 0.15 * normalized_dev_ok, 2)
    return {
        "company_identity_score": round(company_ok, 2),
        "education_institution_score": round(education_ok, 2),
        "timeline_corroboration_score": round(timeline_ok, 2),
        "developer_footprint_score": round(dev_ok, 2),
        "composite": composite,
    }
