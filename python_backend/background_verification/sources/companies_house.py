"""
UK Companies House API integration for company verification.
"""

import requests
from typing import List, Dict
from utils.logging_config import get_logger
from utils.config import get_settings

logger = get_logger(__name__)

BASE = "https://api.company-information.service.gov.uk"

def search_company(name: str, limit: int = 3) -> List[Dict]:
    """Search for companies in UK Companies House database - DISABLED."""
    logger.info("Companies House API disabled, skipping search")
    return []
