"""
ORCID API integration for researcher verification.
"""

import requests
from typing import Dict, Any
from utils.logging_config import get_logger

logger = get_logger(__name__)

BASE = "https://pub.orcid.org/v3.0"

def fetch_record(orcid_id: str) -> Dict[str, Any]:
    """Fetch ORCID record by ID."""
    try:
        headers = {"Accept": "application/json"}
        r = requests.get(f"{BASE}/{orcid_id}/record", headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        logger.info(f"ORCID record fetched for {orcid_id}")
        return data
    except Exception as e:
        logger.error(f"ORCID fetch failed for {orcid_id}: {e}")
        return {}
