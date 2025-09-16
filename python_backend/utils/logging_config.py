"""
Logging configuration for the resume fraud detection service.
"""

import logging
import structlog
from typing import Any, Dict
import sys
import re

def redact_pii(data: Any) -> Any:
    """
    Redact PII from log data.
    
    Args:
        data: Data to redact PII from
        
    Returns:
        Data with PII redacted
    """
    if isinstance(data, str):
        # Email addresses
        data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', data)
        
        # Phone numbers (various formats)
        data = re.sub(r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', '[PHONE_REDACTED]', data)
        
        # Social Security Numbers
        data = re.sub(r'\b\d{3}-?\d{2}-?\d{4}\b', '[SSN_REDACTED]', data)
        
        # Credit card numbers
        data = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CC_REDACTED]', data)
        
        # Names (basic pattern - could be improved)
        data = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME_REDACTED]', data)
        
    elif isinstance(data, dict):
        # Recursively redact PII in dictionaries
        return {k: redact_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Recursively redact PII in lists
        return [redact_pii(item) for item in data]
    
    return data

def pii_redaction_processor(logger, method_name, event_dict):
    """Structlog processor to redact PII from log events."""
    return redact_pii(event_dict)

def setup_logging() -> None:
    """Setup structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            pii_redaction_processor,  # Redact PII before JSON rendering
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        stream=sys.stdout
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
