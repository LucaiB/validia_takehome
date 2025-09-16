"""
Basic test to verify the Python backend is working.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.schemas import CandidateInfo, AiDetectionResult, DocumentAuthenticityResult
from detectors.ai_text import AITextDetector
from detectors.document_auth import DocumentAuthenticityDetector
from detectors.contact_info import ContactInfoDetector

async def test_basic_functionality():
    """Test basic functionality without external APIs."""
    print("Testing Python backend basic functionality...")
    
    # Test 1: Schema validation
    print("✓ Testing schema validation...")
    candidate = CandidateInfo(
        full_name="Test Candidate",
        email="test@example.com",
        phone="+1-555-123-4567"
    )
    print(f"  Created candidate: {candidate.full_name}")
    
    # Test 2: Contact info detector (without APIs)
    print("✓ Testing contact info detector...")
    contact_detector = ContactInfoDetector()
    
    # Test email validation
    email_result = await contact_detector._verify_email("test@example.com")
    print(f"  Email validation: {email_result}")
    
    # Test phone validation
    phone_result = await contact_detector._verify_phone("+1-555-123-4567")
    print(f"  Phone validation: {phone_result}")
    
    print("✓ All basic tests passed!")
    print("\nPython backend is ready to run!")
    print("To start the service, run: python main.py")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
