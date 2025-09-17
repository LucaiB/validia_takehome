"""
Main logic for background verification orchestration.
"""

from typing import Dict, Any, List, Optional
from models.background_schemas import BackgroundVerifyRequest, BackgroundVerifyResponse
from background_verification.sources import (
    gleif, sec, openalex, wayback, github, scorecard
)
from background_verification.util import similar, parse_year_month
from background_verification.scoring import score_background
from utils.logging_config import get_logger

logger = get_logger(__name__)

async def _company_evidence(employer_name: str) -> Dict[str, Any]:
    """Gather evidence for a company from various sources."""
    logger.info(f"Gathering company evidence for {employer_name}")
    ev = {"gleif": [], "sec": None}
    
    try:
        logger.info(f"Calling GLEIF for {employer_name}")
        ev["gleif"] = await gleif.search_by_name(employer_name)
        logger.info(f"GLEIF completed for {employer_name}: {len(ev['gleif'])} results")
    except Exception as e:
        logger.error(f"GLEIF search failed for {employer_name}: {e}")
    
    try:
        logger.info(f"Calling SEC for {employer_name}")
        ev["sec"] = await sec.find_company_like(employer_name)
        logger.info(f"SEC completed for {employer_name}: {ev['sec'] is not None}")
    except Exception as e:
        logger.error(f"SEC search failed for {employer_name}: {e}")
    
    logger.info(f"Company evidence gathering completed for {employer_name}")
    return ev

async def _education_evidence(institution_name: str) -> Dict[str, Any]:
    """Gather evidence for an educational institution."""
    logger.info(f"Gathering education evidence for {institution_name}")
    ev = {"scorecard": [], "openalex": []}
    
    try:
        logger.info(f"Calling College Scorecard for {institution_name}")
        sc = await scorecard.search_institution(institution_name)
        if sc:
            ev["scorecard"] = sc
        logger.info(f"College Scorecard completed for {institution_name}: {len(ev['scorecard'])} results")
    except Exception as e:
        logger.error(f"College Scorecard search failed for {institution_name}: {e}")
    
    try:
        logger.info(f"Calling OpenAlex for {institution_name}")
        oa = await openalex.search_institutions(institution_name)
        if oa:
            ev["openalex"] = oa
        logger.info(f"OpenAlex completed for {institution_name}: {len(ev['openalex'])} results")
    except Exception as e:
        logger.error(f"OpenAlex search failed for {institution_name}: {e}")
    
    logger.info(f"Education evidence gathering completed for {institution_name}")
    return ev

async def _developer_evidence(username: Optional[str]) -> Dict[str, Any]:
    """Gather evidence for developer activity."""
    if not username:
        return {}
    
    try:
        u = await github.user_overview(username)
        repos = await github.repos(username, limit=50) if u else []
        return {
            "user": u, 
            "repos": [
                {
                    "name": r.get("name"), 
                    "pushed_at": r.get("pushed_at"), 
                    "language": r.get("language")
                } for r in repos
            ]
        }
    except Exception as e:
        logger.error(f"GitHub search failed for {username}: {e}")
        return {}

def _company_identity_score(ev: Dict[str, Any], employer_name: str) -> float:
    """Calculate company identity verification score."""
    signals = 0
    total = 0
    
    # Check if this is a known major company
    major_companies = {
        "amazon web services", "aws", "amazon", "microsoft", "google", "apple", 
        "meta", "facebook", "tesla", "netflix", "uber", "airbnb", "spotify",
        "twitter", "linkedin", "salesforce", "oracle", "ibm", "intel"
    }
    
    is_major_company = any(major in employer_name.lower() for major in major_companies)
    
    # GLEIF match by name similarity (more lenient for major companies)
    if ev.get("gleif"):
        total += 1
        similarity_threshold = 0.6 if is_major_company else 0.75
        if any(similar(employer_name, x.get("legal_name", "")) > similarity_threshold for x in ev["gleif"]):
            signals += 1
        elif is_major_company and len(ev["gleif"]) > 0:
            # For major companies, any GLEIF result is a positive signal
            signals += 0.5
    
    # SEC ticker presence (public company)
    if ev.get("sec"):
        total += 1
        signals += 1  # presence is strong signal of existence
    
    # For major companies, give partial credit even without perfect matches
    if is_major_company and total == 0:
        return 0.6  # Higher baseline for known major companies
    
    if total == 0:
        return 0.3  # neutral if no sources available
    return min(1.0, max(0.0, signals / total))

async def _timeline_check_position(pos: Dict[str, Any], company_ev: Dict[str, Any]) -> Dict[str, Any]:
    """Check timeline plausibility for a position."""
    start_y, _ = parse_year_month(pos.get("start"))
    end_y, _ = parse_year_month(pos.get("end"))
    timeline = {"plausible": None, "notes": []}
    
    exists_signal = bool(
        company_ev.get("sec") or 
        company_ev.get("gleif")
    )
    
    if exists_signal:
        timeline["plausible"] = True
        timeline["notes"].append("Employer exists in authoritative/open registries.")
    else:
        timeline["plausible"] = None
        timeline["notes"].append("No registry corroboration available; neutral.")

    # If employer_domain provided, attempt Wayback first/last capture
    domain = pos.get("employer_domain")
    if domain:
        try:
            logger.info(f"Checking Wayback for domain: {domain}")
            # Use domain directly instead of wildcard pattern
            wb = await wayback.first_last_capture(domain)
            if wb:
                timeline["wayback"] = wb
                if start_y and wb.get("first"):
                    first_year = int(str(wb["first"])[:4])
                    if start_y < first_year:
                        timeline["notes"].append(
                            "Claimed start precedes earliest public captures of employer domain—may still be ok; informational."
                        )
                logger.info(f"Wayback check completed for {domain}")
            else:
                logger.info(f"No Wayback data found for {domain}")
        except Exception as e:
            logger.error(f"Wayback check failed for {domain}: {e}")
            timeline["notes"].append(f"Wayback check failed: {str(e)}")

    return timeline

def _education_score(ev: Dict[str, Any], claim: Dict[str, Any]) -> float:
    """Calculate education verification score."""
    inst = claim.get("institution_name")
    scorecard_matches = 0
    openalex_matches = 0
    
    # Check College Scorecard results
    if ev.get("scorecard"):
        scorecard_matches = sum(1 for x in ev["scorecard"] if similar(inst, x.get("name", "")) > 0.8)
    
    # Check OpenAlex results
    if ev.get("openalex"):
        openalex_matches = sum(1 for x in ev["openalex"] if similar(inst, x.get("display_name", "")) > 0.8)
    
    # If we have matches from either source, return high score
    if scorecard_matches > 0 or openalex_matches > 0:
        return 1.0
    
    # If we have data from either source but no matches, return medium score
    if ev.get("scorecard") or ev.get("openalex"):
        return 0.6
    
    # If no data sources available, return neutral score
    return 0.5

async def run_background_verification(req: BackgroundVerifyRequest) -> BackgroundVerifyResponse:
    """Run comprehensive background verification."""
    logger.info(f"Starting background verification for {req.full_name}")
    
    company_evidence: Dict[str, Any] = {}
    education_evidence: Dict[str, Any] = {}
    timeline_assessment: Dict[str, Any] = {}

    # Companies
    logger.info(f"Processing {len(req.positions)} company positions")
    for i, pos in enumerate(req.positions):
        logger.info(f"Processing position {i+1}/{len(req.positions)}: {pos.employer_name}")
        comp_ev = await _company_evidence(pos.employer_name)
        logger.info(f"Company evidence gathered for {pos.employer_name}: {len(comp_ev)} sources")
        company_evidence[pos.employer_name] = comp_ev
        logger.info(f"Checking timeline for {pos.employer_name}")
        timeline_assessment[pos.employer_name] = await _timeline_check_position(pos.dict(), comp_ev)
        logger.info(f"Timeline check completed for {pos.employer_name}")

    # Education
    logger.info(f"Processing {len(req.educations)} education records")
    for i, ed in enumerate(req.educations):
        logger.info(f"Processing education {i+1}/{len(req.educations)}: {ed.institution_name}")
        education_evidence[ed.institution_name] = await _education_evidence(ed.institution_name)
        logger.info(f"Education evidence gathered for {ed.institution_name}")

    # Developer footprint (optional)
    logger.info("Processing developer evidence")
    dev_ev = await _developer_evidence(
        req.identifiers.github_username if req.identifiers else None
    )
    logger.info(f"Developer evidence gathered: {len(dev_ev)} fields")

    # Scoring
    logger.info("Starting scoring calculations")
    
    # company score averaged across positions
    comp_scores: List[float] = []
    for pos in req.positions:
        logger.info(f"Calculating company score for {pos.employer_name}")
        comp_scores.append(_company_identity_score(company_evidence[pos.employer_name], pos.employer_name))
    company_ok = round(sum(comp_scores)/len(comp_scores), 2) if comp_scores else 0.5
    logger.info(f"Company score calculated: {company_ok}")

    edu_scores: List[float] = []
    for ed in req.educations:
        logger.info(f"Calculating education score for {ed.institution_name}")
        edu_scores.append(_education_score(education_evidence[ed.institution_name], ed.dict()))
    education_ok = round(sum(edu_scores)/len(edu_scores), 2) if edu_scores else 0.5
    logger.info(f"Education score calculated: {education_ok}")

    # timeline: count positions marked plausible
    logger.info("Calculating timeline scores")
    tl_flags = [
        1.0 if (timeline_assessment[p.employer_name].get("plausible") is True) else 0.5 
        for p in req.positions
    ]
    timeline_ok = round(sum(tl_flags)/len(tl_flags), 2) if tl_flags else 0.5
    logger.info(f"Timeline score calculated: {timeline_ok}")

    # Developer score is purely additive - starts at 0 and only adds points for positive evidence
    dev_ok = 0.0
    if dev_ev.get("user"):
        # Add points for having a public GitHub profile
        dev_ok += 0.3
        if len(dev_ev.get("repos", [])) >= 5:
            # Add more points for having multiple repositories
            dev_ok += 0.2
        if dev_ev.get("user", {}).get("public_repos", 0) > 10:
            # Add points for high activity
            dev_ok += 0.1
    logger.info(f"Developer score calculated: {dev_ok}")

    logger.info("Calculating final composite score")
    score = score_background(company_ok, education_ok, timeline_ok, dev_ok)
    logger.info(f"Final composite score: {score}")

    rationale = [
        "Company identity checked via GLEIF and SEC EDGAR.",
        "Education validated via College Scorecard and OpenAlex.",
        "Timeline plausibility uses registry presence and optional Wayback snapshots (if employer_domain supplied).",
        "Developer evidence from GitHub profile and repo activity (optional).",
    ]

    sources_used = [
        "GLEIF", "SEC EDGAR", "OpenAlex", "Wayback CDX", "GitHub", "US College Scorecard"
    ]

    logger.info(f"Background verification completed for {req.full_name} with composite score: {score['composite']}")
    
    return BackgroundVerifyResponse(
        company_evidence=company_evidence,
        education_evidence=education_evidence,
        developer_evidence=dev_ev,
        timeline_assessment=timeline_assessment,
        score=score,
        rationale=rationale,
        sources_used=sources_used,
    )
