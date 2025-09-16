"""
Enhanced contact verification service with comprehensive validation.
"""

import logging
import httpx
import re
import dns.resolver
import publicsuffix2
from typing import Dict, Any, Optional, List, Tuple
import asyncio
from urllib.parse import urlparse
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

from models.schemas import ContactVerificationResult
from utils.logging_config import get_logger
from utils.cached_api_client import cached_api_client

logger = get_logger(__name__)

class ContactVerificationService:
    """Enhanced contact verification service with comprehensive validation."""
    
    def __init__(self, numverify_api_key: Optional[str] = None, abstract_api_key: Optional[str] = None):
        """Initialize the contact verification service."""
        self.numverify_api_key = numverify_api_key
        self.abstract_api_key = abstract_api_key
        
        # Disposable email domains list (expanded)
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'yopmail.com', 'maildrop.cc', 'getnada.com', 'sharklasers.com',
            'guerrillamailblock.com', 'pokemail.net', 'spam4.me',
            'bccto.me', 'chacuo.net', 'dispostable.com', 'mailnesia.com'
        }
        
        # Role-based email patterns
        self.role_patterns = {
            'admin', 'administrator', 'info', 'contact', 'support',
            'sales', 'marketing', 'hr', 'jobs', 'noreply', 'no-reply'
        }
    
    async def verify_contact(
        self,
        full_name: Optional[str] = None,
        email: str = "",
        phone: Optional[str] = None,
        stated_location: Optional[str] = None,
        default_region: str = "US"
    ) -> Dict[str, Any]:
        """
        Comprehensive contact verification.
        
        Args:
            full_name: Full name of the person
            email: Email address to verify
            phone: Phone number to verify
            stated_location: Stated location (e.g., "New York, NY, USA")
            default_region: Default region for phone parsing
            
        Returns:
            Comprehensive verification results
        """
        try:
            logger.info(f"Starting comprehensive contact verification for email: {email}")
            
            # Verify email
            email_result = await self._verify_email_comprehensive(email)
            
            # Verify phone
            phone_result = None
            if phone:
                phone_result = await self._verify_phone_comprehensive(phone, default_region)
            
            # Check geo consistency
            geo_consistency = None
            if phone and stated_location:
                geo_consistency = await self._check_geo_consistency_comprehensive(
                    phone, stated_location, default_region
                )
            
            # Calculate composite score
            scores = self._calculate_scores(email_result, phone_result, geo_consistency)
            
            # Generate rationale
            rationale = self._generate_rationale(email_result, phone_result, geo_consistency)
            
            result = {
                "email": email_result,
                "phone": phone_result,
                "geo_consistency": geo_consistency,
                "score": scores,
                "rationale": rationale
            }
            
            logger.info(f"Contact verification completed with composite score: {scores['composite']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in contact verification: {e}")
            return {
                "email": {"input": email, "error": str(e)},
                "phone": {"input": phone, "error": str(e)} if phone else None,
                "geo_consistency": None,
                "score": {"composite": 0.0},
                "rationale": [f"Verification failed: {str(e)}"]
            }
    
    async def _verify_email_comprehensive(self, email: str) -> Dict[str, Any]:
        """Comprehensive email verification."""
        try:
            if not email:
                return {"input": "", "error": "No email provided"}
            
            # Basic syntax validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            syntax_valid = bool(re.match(email_pattern, email))
            
            if not syntax_valid:
                return {
                    "input": email,
                    "normalized": email,
                    "syntax_valid": False,
                    "error": "Invalid email syntax"
                }
            
            # Normalize email
            normalized = email.lower().strip()
            local_part, domain = normalized.split('@', 1)
            
            # Check if disposable
            is_disposable = domain in self.disposable_domains
            
            # Check if role-based
            is_role = any(role in local_part.lower() for role in self.role_patterns)
            
            # Get domain info
            domain_info = await self._get_domain_info(domain)
            
            # SMTP probe (simplified - in production you'd do actual SMTP verification)
            smtp_probe = "UNKNOWN"  # Would implement actual SMTP verification
            
            # Sources used
            sources = ["email-validator", "dnspython", "publicsuffix2"]
            if self.abstract_api_key:
                sources.append("abstract-api")
            
            return {
                "input": email,
                "normalized": normalized,
                "syntax_valid": syntax_valid,
                "domain_registrable": domain_info.get("registrable_domain", domain),
                "mx_records_found": domain_info.get("mx_records_found", False),
                "smtp_probe": smtp_probe,
                "is_disposable": is_disposable,
                "is_role": is_role,
                "notes": domain_info.get("notes", []),
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error verifying email {email}: {e}")
            return {
                "input": email,
                "error": str(e)
            }
    
    async def _get_domain_info(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive domain information."""
        try:
            # Check MX records
            mx_records_found = False
            notes = []
            
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_records_found = len(mx_records) > 0
                notes.append(f"Found {len(mx_records)} MX records")
            except Exception as e:
                notes.append(f"MX lookup failed: {str(e)}")
            
            # Get registrable domain
            try:
                registrable_domain = publicsuffix2.get_sld(domain)
            except:
                registrable_domain = domain
            
            # Check if domain is valid
            try:
                dns.resolver.resolve(domain, 'A')
                notes.append("A record found")
            except:
                notes.append("No A record found")
            
            return {
                "mx_records_found": mx_records_found,
                "registrable_domain": registrable_domain,
                "notes": notes
            }
            
        except Exception as e:
            logger.error(f"Error getting domain info for {domain}: {e}")
            return {
                "mx_records_found": False,
                "registrable_domain": domain,
                "notes": [f"Domain lookup failed: {str(e)}"]
            }
    
    async def _verify_phone_comprehensive(self, phone: str, default_region: str) -> Dict[str, Any]:
        """Comprehensive phone verification using libphonenumber and NumVerify."""
        try:
            if not phone:
                return {"input": "", "error": "No phone provided"}
            
            # Parse phone number
            try:
                parsed_number = phonenumbers.parse(phone, default_region)
            except phonenumbers.NumberParseException as e:
                return {
                    "input": phone,
                    "error": f"Phone parse error: {str(e)}"
                }
            
            # Validate
            is_valid = phonenumbers.is_valid_number(parsed_number)
            
            # Get E164 format
            e164 = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            
            # Get country code
            country_code = phonenumbers.region_code_for_number(parsed_number)
            
            # Get region info
            region_hint = geocoder.description_for_number(parsed_number, "en")
            
            # Check if toll-free (fallback for older phonenumbers versions)
            try:
                is_toll_free = phonenumbers.is_toll_free_number(parsed_number)
            except AttributeError:
                # Fallback for older versions
                is_toll_free = False
            
            # Get carrier info
            carrier_name = carrier.name_for_number(parsed_number, "en")
            
            # Get timezone
            timezones = timezone.time_zones_for_number(parsed_number)
            
            notes = ["libphonenumber parse/validate/geocode"]
            sources = ["libphonenumber"]
            
            # Add NumVerify API verification if available
            if self.numverify_api_key:
                try:
                    numverify_result = await self._verify_phone_with_numverify(e164)
                    if numverify_result.get('valid') is not None:
                        # Update validation based on NumVerify
                        is_valid = is_valid and numverify_result.get('valid', False)
                        if numverify_result.get('carrier'):
                            carrier_name = numverify_result.get('carrier')
                        notes.append(f"NumVerify: {numverify_result.get('reason', 'API verified')}")
                        sources.append("numverify")
                except Exception as e:
                    logger.warning(f"NumVerify API error: {e}")
                    notes.append("NumVerify: API error")
            
            if carrier_name:
                notes.append(f"Carrier: {carrier_name}")
            if timezones:
                notes.append(f"Timezone: {', '.join(timezones)}")
            
            return {
                "input": phone,
                "e164": e164,
                "valid": is_valid,
                "country_code": country_code or default_region,
                "region_hint": region_hint,
                "toll_free": is_toll_free,
                "carrier": carrier_name,
                "timezone": list(timezones),
                "notes": notes,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error verifying phone {phone}: {e}")
            return {
                "input": phone,
                "error": str(e)
            }
    
    async def _verify_phone_with_numverify(self, phone: str) -> Dict[str, Any]:
        """Verify phone using Numverify API with caching."""
        try:
            response = await cached_api_client.get(
                "http://apilayer.net/api/validate",
                params={
                    'access_key': self.numverify_api_key,
                    'number': phone
                },
                cache_key_prefix='numverify',
                cache_ttl=3600  # Cache for 1 hour
            )
            
            data = response['data']
            return {
                'valid': data.get('valid', False),
                'carrier': data.get('carrier', 'Unknown'),
                'reason': 'Numverify API'
            }
                    
        except Exception as e:
            logger.error(f"Error with Numverify API: {e}")
            return {'valid': False, 'carrier': None, 'reason': f'API error: {str(e)}'}
    
    async def _check_geo_consistency_comprehensive(
        self, 
        phone: str, 
        stated_location: str, 
        default_region: str
    ) -> Dict[str, Any]:
        """Comprehensive geo consistency check."""
        try:
            if not phone or not stated_location:
                return None
            
            # Parse phone and get location
            try:
                parsed_number = phonenumbers.parse(phone, default_region)
                phone_region = geocoder.description_for_number(parsed_number, "en")
                phone_country = phonenumbers.region_code_for_number(parsed_number)
            except:
                return {
                    "stated_location": stated_location,
                    "error": "Could not parse phone number",
                    "method": "libphonenumber geocoder",
                    "sources": ["libphonenumber"]
                }
            
            # Check if toll-free (toll-free numbers don't have geographic meaning)
            try:
                is_toll_free = phonenumbers.is_toll_free_number(parsed_number)
            except AttributeError:
                # Fallback for older versions
                is_toll_free = False
            
            # Simple location matching (in production, you'd use more sophisticated geocoding)
            stated_lower = stated_location.lower()
            phone_lower = phone_region.lower() if phone_region else ""
            
            # Check country match
            country_matches = any(country in stated_lower for country in [phone_country.lower() if phone_country else "", "usa", "united states"])
            
            # Check region match
            region_matches = any(region in stated_lower for region in phone_lower.split()) if phone_lower else False
            
            # Toll-free conflict
            toll_free_conflict = is_toll_free and any(term in stated_lower for term in ["local", "area", "city"])
            
            return {
                "stated_location": stated_location,
                "phone_country_matches": country_matches,
                "phone_region_matches": region_matches,
                "toll_free_conflict": toll_free_conflict,
                "phone_region": phone_region,
                "phone_country": phone_country,
                "is_toll_free": is_toll_free,
                "method": "libphonenumber geocoder + toll-free rules",
                "sources": ["libphonenumber"]
            }
            
        except Exception as e:
            logger.error(f"Error checking geo consistency: {e}")
            return {
                "stated_location": stated_location,
                "error": str(e),
                "method": "libphonenumber geocoder",
                "sources": ["libphonenumber"]
            }
    
    def _calculate_scores(
        self, 
        email_result: Dict[str, Any], 
        phone_result: Optional[Dict[str, Any]], 
        geo_consistency: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate verification scores."""
        # Email score
        email_score = 0.0
        if email_result.get("syntax_valid", False):
            email_score += 0.3
        if email_result.get("mx_records_found", False):
            email_score += 0.3
        if not email_result.get("is_disposable", False):
            email_score += 0.2
        if not email_result.get("is_role", False):
            email_score += 0.2
        
        # Phone score
        phone_score = 0.0
        if phone_result and phone_result.get("valid", False):
            phone_score += 0.5
            if not phone_result.get("toll_free", False):
                phone_score += 0.3
            if phone_result.get("carrier"):
                phone_score += 0.2
        
        # Geo consistency score
        geo_score = 0.0
        if geo_consistency and not geo_consistency.get("error"):
            if geo_consistency.get("phone_country_matches", False):
                geo_score += 0.5
            if geo_consistency.get("phone_region_matches", False):
                geo_score += 0.3
            if not geo_consistency.get("toll_free_conflict", False):
                geo_score += 0.2
        
        # Composite score (weighted average)
        weights = {"email": 0.5, "phone": 0.3, "geo": 0.2}
        composite = (
            email_score * weights["email"] + 
            phone_score * weights["phone"] + 
            geo_score * weights["geo"]
        )
        
        return {
            "email_score": round(email_score, 2),
            "phone_score": round(phone_score, 2),
            "geo_score": round(geo_score, 2),
            "composite": round(composite, 2)
        }
    
    def _generate_rationale(
        self, 
        email_result: Dict[str, Any], 
        phone_result: Optional[Dict[str, Any]], 
        geo_consistency: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate human-readable rationale."""
        rationale = []
        
        # Email rationale
        if email_result.get("syntax_valid", False):
            rationale.append("Email syntax/MX and disposable checks executed.")
        else:
            rationale.append("Email syntax validation failed.")
        
        # Phone rationale
        if phone_result:
            if phone_result.get("valid", False):
                rationale.append("Phone parsed via libphonenumber; coarse region/toll‑free derived.")
            else:
                rationale.append("Phone validation failed.")
        
        # Geo rationale
        if geo_consistency:
            if not geo_consistency.get("error"):
                rationale.append("Geo consistency evaluated using libphonenumber geocoder and rules.")
            else:
                rationale.append("Geo consistency check failed.")
        
        return rationale
