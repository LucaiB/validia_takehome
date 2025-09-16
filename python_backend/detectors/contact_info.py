"""
Contact information verification using external APIs.
"""

import logging
import httpx
import re
from typing import Dict, Any, Optional
import asyncio

from models.schemas import ContactVerificationResult
from utils.logging_config import get_logger
from .contact_verification import ContactVerificationService

logger = get_logger(__name__)

class ContactInfoDetector:
    """Detector for contact information verification."""
    
    def __init__(self, numverify_api_key: Optional[str] = None, abstract_api_key: Optional[str] = None):
        """Initialize the contact info detector."""
        self.numverify_api_key = numverify_api_key
        self.abstract_api_key = abstract_api_key
        
        # Initialize the comprehensive contact verification service
        self.contact_service = ContactVerificationService(
            numverify_api_key=numverify_api_key,
            abstract_api_key=abstract_api_key
        )
    
    async def verify_contact_info(
        self, 
        email: str, 
        phone: Optional[str] = None, 
        location: Optional[str] = None
    ) -> ContactVerificationResult:
        """
        Verify contact information using the comprehensive verification service.
        
        Args:
            email: Email address to verify
            phone: Phone number to verify (optional)
            location: Location for geo consistency check (optional)
            
        Returns:
            ContactVerificationResult with verification details
        """
        try:
            logger.info(f"Starting contact verification for email: {email}")
            
            # Use the comprehensive contact verification service
            result = await self.contact_service.verify_contact(
                email=email,
                phone=phone,
                stated_location=location,
                default_region="US"
            )
            
            # Extract results
            email_data = result.get("email", {})
            phone_data = result.get("phone", {})
            geo_data = result.get("geo_consistency", {})
            scores = result.get("score", {})
            
            # Determine overall verification status
            is_verified = (
                email_data.get('syntax_valid', False) and 
                email_data.get('mx_records_found', False) and
                not email_data.get('is_disposable', False) and
                not email_data.get('is_role', False) and
                (phone_data is None or phone_data.get('valid', False))
            )
            
            # Create details summary
            details_parts = []
            if email_data.get('syntax_valid'):
                details_parts.append("Email syntax valid")
            else:
                details_parts.append("Email syntax invalid")
                
            if email_data.get('mx_records_found'):
                details_parts.append("MX records found")
            else:
                details_parts.append("No MX records")
                
            if email_data.get('is_disposable'):
                details_parts.append("Email is disposable")
                
            if email_data.get('is_role'):
                details_parts.append("Email is role-based")
                
            if phone_data:
                if phone_data.get('valid'):
                    details_parts.append("Phone is valid")
                    if phone_data.get('carrier'):
                        details_parts.append(f"Carrier: {phone_data['carrier']}")
                else:
                    details_parts.append("Phone is invalid")
            
            if geo_data and not geo_data.get('error'):
                if geo_data.get('phone_country_matches'):
                    details_parts.append("Phone country matches location")
                if geo_data.get('phone_region_matches'):
                    details_parts.append("Phone region matches location")
            
            details = "; ".join(details_parts) if details_parts else "No verification details available"
            
            result = ContactVerificationResult(
                email=email,
                phone=phone,
                is_verified=is_verified,
                details=details,
                email_valid=email_data.get('syntax_valid'),
                email_disposable=email_data.get('is_disposable'),
                phone_valid=phone_data.get('valid') if phone_data else None,
                phone_carrier=phone_data.get('carrier') if phone_data else None,
                geo_consistent=geo_data.get('phone_country_matches') if geo_data else None
            )
            
            logger.info(f"Contact verification completed: {is_verified} (score: {scores.get('composite', 0)})")
            return result
            
        except Exception as e:
            logger.error(f"Error in contact verification: {e}")
            return ContactVerificationResult(
                email=email,
                phone=phone,
                is_verified=False,
                details=f"Verification failed: {str(e)}"
            )
    
    async def _verify_email(self, email: str) -> Dict[str, Any]:
        """Verify email address using available APIs."""
        try:
            # Basic email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return {'valid': False, 'disposable': False, 'reason': 'Invalid format'}
            
            # Check if disposable email
            domain = email.split('@')[1].lower()
            is_disposable = domain in self.disposable_domains
            
            # If we have Abstract API key, use it for more detailed verification
            if self.abstract_api_key:
                return await self._verify_email_with_abstract(email)
            
            # Basic validation result
            return {
                'valid': True,
                'disposable': is_disposable,
                'reason': 'Basic validation passed'
            }
            
        except Exception as e:
            logger.error(f"Error verifying email {email}: {e}")
            return {'valid': False, 'disposable': False, 'reason': f'Verification error: {str(e)}'}
    
    async def _verify_email_with_abstract(self, email: str) -> Dict[str, Any]:
        """Verify email using Abstract API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://emailvalidation.abstractapi.com/v1/",
                    params={
                        'api_key': self.abstract_api_key,
                        'email': email
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'valid': data.get('deliverability') == 'DELIVERABLE',
                        'disposable': data.get('is_disposable_email', {}).get('value', False),
                        'reason': data.get('deliverability', 'Unknown')
                    }
                else:
                    logger.warning(f"Abstract API returned status {response.status_code}")
                    return {'valid': False, 'disposable': False, 'reason': 'API error'}
                    
        except Exception as e:
            logger.error(f"Error with Abstract API: {e}")
            return {'valid': False, 'disposable': False, 'reason': f'API error: {str(e)}'}
    
    async def _verify_phone(self, phone: str) -> Dict[str, Any]:
        """Verify phone number using available APIs."""
        try:
            # Clean phone number
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Basic phone validation
            if len(cleaned_phone) < 10:
                return {'valid': False, 'carrier': None, 'reason': 'Too short'}
            
            # If we have Numverify API key, use it
            if self.numverify_api_key:
                return await self._verify_phone_with_numverify(cleaned_phone)
            
            # Basic validation
            return {
                'valid': True,
                'carrier': 'Unknown',
                'reason': 'Basic validation passed'
            }
            
        except Exception as e:
            logger.error(f"Error verifying phone {phone}: {e}")
            return {'valid': False, 'carrier': None, 'reason': f'Verification error: {str(e)}'}
    
    async def _verify_phone_with_numverify(self, phone: str) -> Dict[str, Any]:
        """Verify phone using Numverify API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://apilayer.net/api/validate",
                    params={
                        'access_key': self.numverify_api_key,
                        'number': phone
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'valid': data.get('valid', False),
                        'carrier': data.get('carrier', 'Unknown'),
                        'reason': 'Numverify API'
                    }
                else:
                    logger.warning(f"Numverify API returned status {response.status_code}")
                    return {'valid': False, 'carrier': None, 'reason': 'API error'}
                    
        except Exception as e:
            logger.error(f"Error with Numverify API: {e}")
            return {'valid': False, 'carrier': None, 'reason': f'API error: {str(e)}'}
    
    async def _check_geo_consistency(self, phone: str, location: str) -> bool:
        """Check if phone number and location are geographically consistent."""
        try:
            # This is a simplified check - in a real implementation,
            # you would use phone number geolocation APIs
            logger.info(f"Checking geo consistency for phone: {phone}, location: {location}")
            
            # For now, return True as a placeholder
            # In a real implementation, you would:
            # 1. Extract country/region from phone number
            # 2. Extract country/region from location string
            # 3. Compare them for consistency
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking geo consistency: {e}")
            return False
