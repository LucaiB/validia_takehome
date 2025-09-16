"""
Utility functions for background verification.
"""

from difflib import SequenceMatcher
from dateutil import parser
from typing import Optional, Tuple


def similar(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


def parse_year_month(s: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """Parse a year-month string into year and month integers."""
    if not s or s.lower() == "present":
        return None, None
    try:
        dt = parser.parse(s)
        return dt.year, dt.month
    except Exception:
        try:
            # Try just the year
            y = int(s)
            return y, None
        except Exception:
            return None, None
