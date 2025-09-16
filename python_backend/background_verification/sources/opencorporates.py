"""
OpenCorporates API integration for company verification.
"""

import requests
from typing import List, Dict
from utils.logging_config import get_logger
from utils.config import get_settings

logger = get_logger(__name__)

BASE = "https://api.opencorporates.com/companies/search"

def search_company(name: str, limit: int = 3) -> List[Dict]:
    """Search for companies in OpenCorporates database - DISABLED."""
    logger.info("OpenCorporates API disabled, skipping search")
    return []
