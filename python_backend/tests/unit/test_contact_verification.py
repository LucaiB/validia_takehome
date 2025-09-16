"""
Unit tests for contact verification service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from detectors.contact_verification import ContactVerificationService


class TestContactVerificationService:
    """Test cases for ContactVerificationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ContactVerificationService(
            numverify_api_key="test_numverify_key",
            abstract_api_key="test_abstract_key"
        )

    @pytest.mark.asyncio
    async def test_verify_contact_valid(self):
        """Test contact verification with valid information."""
        email = "john.doe@example.com"
        phone = "+1234567890"
        location = "New York, NY"
        
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email:
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": True,
                "domain_registrable": "example.com",
                "mx_records_found": True,
                "smtp_probe": "UNKNOWN",
                "is_disposable": False,
                "is_role": False,
                "notes": ["Found 5 MX records", "A record found"],
                "sources": ["email-validator", "dnspython", "publicsuffix2", "abstract-api"]
            }
        
        with patch.object(self.service, '_verify_phone_comprehensive') as mock_phone:
            mock_phone.return_value = {
                "input": phone,
                "e164": phone,
                "valid": True,
                "country_code": "US",
                "region_hint": "New York",
                "toll_free": False,
                "carrier": "Verizon Wireless",
                "timezone": ["America/New_York"],
                "notes": ["libphonenumber parse/validate/geocode", "NumVerify: Numverify API"],
                "sources": ["libphonenumber", "numverify"]
            }
        
        with patch.object(self.service, '_check_geo_consistency_comprehensive') as mock_geo:
            mock_geo.return_value = {
                "stated_location": location,
                "phone_country_matches": True,
                "phone_region_matches": True,
                "toll_free_conflict": False,
                "phone_region": "New York",
                "phone_country": "US",
                "is_toll_free": False,
                "method": "libphonenumber geocoder + toll-free rules",
                "sources": ["libphonenumber"]
            }
        
        result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
        
        assert result["email"]["input"] == email
        assert result["phone"]["input"] == phone
        assert result["score"]["composite"] >= 0.5

    @pytest.mark.asyncio
    async def test_verify_contact_invalid_email(self):
        """Test contact verification with invalid email."""
        email = "invalid-email"
        phone = "+1234567890"
        location = "New York, NY"
        
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email:
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": False,
                "domain_registrable": None,
                "mx_records_found": False,
                "smtp_probe": "UNKNOWN",
                "is_disposable": False,
                "is_role": False,
                "notes": ["Invalid email format"],
                "sources": ["email-validator"]
            }
        
        with patch.object(self.service, '_verify_phone_comprehensive') as mock_phone:
            mock_phone.return_value = {
                "input": phone,
                "e164": phone,
                "valid": True,
                "country_code": "US",
                "region_hint": "New York",
                "toll_free": False,
                "carrier": "Verizon Wireless",
                "timezone": ["America/New_York"],
                "notes": ["libphonenumber parse/validate/geocode"],
                "sources": ["libphonenumber"]
            }
        
        with patch.object(self.service, '_check_geo_consistency_comprehensive') as mock_geo:
            mock_geo.return_value = {
                "stated_location": location,
                "phone_country_matches": True,
                "phone_region_matches": True,
                "toll_free_conflict": False,
                "phone_region": "New York",
                "phone_country": "US",
                "is_toll_free": False,
                "method": "libphonenumber geocoder + toll-free rules",
                "sources": ["libphonenumber"]
            }
        
        result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
        
        assert result["email"]["input"] == email
        assert result["phone"]["input"] == phone
        assert result["score"]["composite"] <= 0.5

    @pytest.mark.asyncio
    async def test_verify_contact_invalid_phone(self):
        """Test contact verification with invalid phone."""
        email = "john.doe@example.com"
        phone = "invalid-phone"
        location = "New York, NY"
        
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email:
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": True,
                "domain_registrable": "example.com",
                "mx_records_found": True,
                "smtp_probe": "UNKNOWN",
                "is_disposable": False,
                "is_role": False,
                "notes": ["Found 5 MX records", "A record found"],
                "sources": ["email-validator", "dnspython", "publicsuffix2", "abstract-api"]
            }
        
        with patch.object(self.service, '_verify_phone_comprehensive') as mock_phone:
            mock_phone.return_value = {
                "input": phone,
                "e164": None,
                "valid": False,
                "country_code": None,
                "region_hint": None,
                "toll_free": False,
                "carrier": None,
                "timezone": [],
                "notes": ["Invalid phone number format"],
                "sources": ["libphonenumber"]
            }
        
        with patch.object(self.service, '_check_geo_consistency_comprehensive') as mock_geo:
            mock_geo.return_value = None  # No geo consistency check for invalid phone
        
        result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
        
        assert result["email"]["input"] == email
        assert result["phone"]["input"] == phone
        assert result["score"]["composite"] <= 0.5

    @pytest.mark.asyncio
    async def test_verify_contact_disposable_email(self):
        """Test contact verification with disposable email."""
        email = "test@10minutemail.com"
        phone = "+1234567890"
        location = "New York, NY"
        
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email:
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": True,
                "domain_registrable": "10minutemail.com",
                "mx_records_found": True,
                "smtp_probe": "UNKNOWN",
                "is_disposable": True,
                "is_role": False,
                "notes": ["Disposable email detected"],
                "sources": ["email-validator", "abstract-api"]
            }
        
        with patch.object(self.service, '_verify_phone_comprehensive') as mock_phone:
            mock_phone.return_value = {
                "input": phone,
                "e164": phone,
                "valid": True,
                "country_code": "US",
                "region_hint": "New York",
                "toll_free": False,
                "carrier": "Verizon Wireless",
                "timezone": ["America/New_York"],
                "notes": ["libphonenumber parse/validate/geocode"],
                "sources": ["libphonenumber"]
            }
        
        with patch.object(self.service, '_check_geo_consistency_comprehensive') as mock_geo:
            mock_geo.return_value = {
                "stated_location": location,
                "phone_country_matches": True,
                "phone_region_matches": True,
                "toll_free_conflict": False,
                "phone_region": "New York",
                "phone_country": "US",
                "is_toll_free": False,
                "method": "libphonenumber geocoder + toll-free rules",
                "sources": ["libphonenumber"]
            }
        
        result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
        
        assert result["email"]["input"] == email
        assert result["phone"]["input"] == phone
        assert result["score"]["composite"] <= 0.5
        assert result["email"]["is_disposable"] is True

    @pytest.mark.asyncio
    async def test_verify_contact_geo_inconsistency(self):
        """Test contact verification with geo inconsistency."""
        email = "john.doe@example.com"
        phone = "+1234567890"  # US phone
        location = "London, UK"  # UK location
        
        # Clear cache first
        from utils.cached_api_client import cached_api_client
        await cached_api_client.clear()
        
        # Mock all the methods at once
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email, \
             patch.object(self.service, '_verify_phone_comprehensive') as mock_phone, \
             patch.object(self.service, '_check_geo_consistency_comprehensive') as mock_geo:
            
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": True,
                "domain_registrable": "example.com",
                "mx_records_found": False,  # Lower email score
                "smtp_probe": "UNKNOWN",
                "is_disposable": True,  # Lower email score (disposable)
                "is_role": False,
                "notes": ["No MX records found"],
                "sources": ["email-validator", "dnspython", "publicsuffix2", "abstract-api"]
            }
            
            mock_phone.return_value = {
                "input": phone,
                "e164": phone,
                "valid": True,
                "country_code": "US",
                "region_hint": "New York",
                "toll_free": True,  # Lower phone score (toll-free)
                "carrier": "Unknown",  # Lower phone score (no carrier)
                "timezone": ["America/New_York"],
                "notes": ["libphonenumber parse/validate/geocode"],
                "sources": ["libphonenumber"]
            }
            
            mock_geo.return_value = {
                "stated_location": location,
                "phone_country_matches": False,
                "phone_region_matches": False,
                "toll_free_conflict": False,
                "phone_region": "New York",
                "phone_country": "US",
                "is_toll_free": False,
                "method": "libphonenumber geocoder + toll-free rules",
                "sources": ["libphonenumber"]
            }
            
            result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
            
            assert result["email"]["input"] == email
            assert result["phone"]["input"] == phone
            assert result["score"]["composite"] <= 0.5
            assert result["geo_consistency"]["phone_country_matches"] is False

    @pytest.mark.asyncio
    async def test_verify_contact_no_phone(self):
        """Test contact verification with no phone number."""
        email = "john.doe@example.com"
        phone = None
        location = "New York, NY"
        
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email:
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": True,
                "domain_registrable": "example.com",
                "mx_records_found": True,
                "smtp_probe": "UNKNOWN",
                "is_disposable": False,
                "is_role": False,
                "notes": ["Found 5 MX records", "A record found"],
                "sources": ["email-validator", "dnspython", "publicsuffix2", "abstract-api"]
            }
        
        result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
        
        assert result["email"]["input"] == email
        assert result["phone"] is None
        assert result["score"]["composite"] > 0.3  # Should still be verified with just email

    @pytest.mark.asyncio
    async def test_verify_contact_no_location(self):
        """Test contact verification with no location."""
        email = "john.doe@example.com"
        phone = "+1234567890"
        location = None
        
        with patch.object(self.service, '_verify_email_comprehensive') as mock_email:
            mock_email.return_value = {
                "input": email,
                "normalized": email,
                "syntax_valid": True,
                "domain_registrable": "example.com",
                "mx_records_found": True,
                "smtp_probe": "UNKNOWN",
                "is_disposable": False,
                "is_role": False,
                "notes": ["Found 5 MX records", "A record found"],
                "sources": ["email-validator", "dnspython", "publicsuffix2", "abstract-api"]
            }
        
        with patch.object(self.service, '_verify_phone_comprehensive') as mock_phone:
            mock_phone.return_value = {
                "input": phone,
                "e164": phone,
                "valid": True,
                "country_code": "US",
                "region_hint": "New York",
                "toll_free": False,
                "carrier": "Verizon Wireless",
                "timezone": ["America/New_York"],
                "notes": ["libphonenumber parse/validate/geocode"],
                "sources": ["libphonenumber"]
            }
        
        result = await self.service.verify_contact(email=email, phone=phone, stated_location=location)
        
        assert result["email"]["input"] == email
        assert result["phone"]["input"] == phone
        assert result["score"]["composite"] >= 0.5
        assert result["geo_consistency"] is None  # No location to check

    @pytest.mark.asyncio
    async def test_verify_email_comprehensive_valid(self):
        """Test email verification for valid email."""
        email = "john.doe@example.com"
        
        with patch('dns.resolver.resolve') as mock_resolve:
            mock_resolve.return_value = [Mock(rdata=['mx1.example.com', 'mx2.example.com'])]
        
        with patch('publicsuffix2.get_sld') as mock_sld:
            mock_sld.return_value = "example.com"
        
        # Mock the domain info method instead
        with patch.object(self.service, '_get_domain_info') as mock_domain:
            mock_domain.return_value = {
                "mx_records_found": True,
                "registrable_domain": "example.com",
                "notes": ["Found 5 MX records", "A record found"]
            }
        
        result = await self.service._verify_email_comprehensive(email)
        
        assert result["input"] == email
        assert result["syntax_valid"] is True
        assert result["mx_records_found"] is True
        assert result["is_disposable"] is False

    @pytest.mark.asyncio
    async def test_verify_phone_comprehensive_valid(self):
        """Test phone verification for valid phone."""
        phone = "+1234567890"

        # Create a service without NumVerify API key to avoid real API calls
        test_service = ContactVerificationService(
            numverify_api_key=None,  # No API key
            abstract_api_key="test_abstract_key"
        )

        # Mock phonenumbers functions
        with patch('phonenumbers.parse') as mock_parse, \
             patch('phonenumbers.is_valid_number') as mock_valid, \
             patch('phonenumbers.format_number') as mock_format, \
             patch('phonenumbers.region_code_for_number') as mock_region, \
             patch('phonenumbers.geocoder.description_for_number') as mock_geocoder, \
             patch('phonenumbers.carrier.name_for_number') as mock_carrier, \
             patch('phonenumbers.timezone.time_zones_for_number') as mock_timezone:

            mock_number = Mock()
            mock_parse.return_value = mock_number
            mock_valid.return_value = True
            mock_format.return_value = "+1234567890"
            mock_region.return_value = "US"
            mock_geocoder.return_value = "New York"
            mock_carrier.return_value = "Verizon Wireless"
            mock_timezone.return_value = ["America/New_York"]

            result = await test_service._verify_phone_comprehensive(phone, "US")

            assert result["input"] == phone
            # The phone should be valid since phonenumbers.is_valid_number returns True
            assert result["valid"] is True
            assert result["country_code"] == "US"
            assert result["carrier"] == "Verizon Wireless"

    @pytest.mark.asyncio
    async def test_verify_phone_with_numverify_success(self):
        """Test NumVerify API integration."""
        phone = "+1234567890"
        
        # Clear cache first
        from utils.cached_api_client import cached_api_client
        await cached_api_client.clear()
        
        with patch.object(cached_api_client, 'get') as mock_get:
            mock_get.return_value = {
                "data": {
                    "valid": True,
                    "carrier": "Verizon Wireless",
                    "country_code": "US"
                }
            }
            
            result = await self.service._verify_phone_with_numverify(phone)
            
            assert result["valid"] is True
            assert result["carrier"] == "Verizon Wireless"
            assert result["reason"] == "Numverify API"

    @pytest.mark.asyncio
    async def test_verify_phone_with_numverify_failure(self):
        """Test NumVerify API failure handling."""
        phone = "+1234567890"
        
        # Clear cache first
        from utils.cached_api_client import cached_api_client
        await cached_api_client.clear()
        
        with patch.object(cached_api_client, 'get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await self.service._verify_phone_with_numverify(phone)
            
            assert result["valid"] is False
            assert result["carrier"] is None
            assert "API error" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_geo_consistency_matching(self):
        """Test geo consistency check with matching data."""
        phone = "+1234567890"
        stated_location = "New York, NY, USA"
        
        with patch('phonenumbers.parse') as mock_parse, \
             patch('phonenumbers.geocoder.description_for_number') as mock_geocoder, \
             patch('phonenumbers.region_code_for_number') as mock_region:
            
            mock_number = Mock()
            mock_parse.return_value = mock_number
            mock_geocoder.return_value = "New York"
            mock_region.return_value = "US"
            
            result = await self.service._check_geo_consistency_comprehensive(phone, stated_location, "US")
            
            assert result["phone_country_matches"] is True
            assert result["phone_region_matches"] is True

    @pytest.mark.asyncio
    async def test_check_geo_consistency_mismatch(self):
        """Test geo consistency check with mismatched data."""
        phone = "+1234567890"  # US phone
        stated_location = "London, UK"  # UK location
        
        with patch('phonenumbers.parse') as mock_parse, \
             patch('phonenumbers.geocoder.description_for_number') as mock_geocoder, \
             patch('phonenumbers.region_code_for_number') as mock_region:
            
            mock_number = Mock()
            mock_parse.return_value = mock_number
            mock_geocoder.return_value = "New York"
            mock_region.return_value = "US"
            
            result = await self.service._check_geo_consistency_comprehensive(phone, stated_location, "US")
            
            assert result["phone_country_matches"] is False
            assert result["phone_region_matches"] is False
