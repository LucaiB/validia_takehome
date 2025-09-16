"""
Secrets management utility for secure credential handling.
"""

import os
import boto3
import json
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from utils.logging_config import get_logger

logger = get_logger(__name__)

class SecretsManager:
    """Secure secrets management using AWS Secrets Manager and SSM Parameter Store."""
    
    def __init__(self, aws_region: str = "us-east-1"):
        """Initialize the secrets manager."""
        self.aws_region = aws_region
        self.secrets_client = None
        self.ssm_client = None
        
        try:
            self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
            self.ssm_client = boto3.client('ssm', region_name=aws_region)
        except NoCredentialsError:
            logger.warning("AWS credentials not found, falling back to environment variables")
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            fallback_env_var: Environment variable to fall back to if AWS is unavailable
            
        Returns:
            Secret value or None if not found
        """
        if not self.secrets_client:
            if fallback_env_var:
                return os.getenv(fallback_env_var)
            return None
        
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_value = response['SecretString']
            
            # Try to parse as JSON first
            try:
                return json.loads(secret_value)
            except json.JSONDecodeError:
                return secret_value
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Secret {secret_name} not found in AWS Secrets Manager")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_name}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_name}")
            elif error_code == 'DecryptionFailureException':
                logger.error(f"Decryption failed for secret {secret_name}")
            elif error_code == 'InternalServiceErrorException':
                logger.error(f"AWS internal service error for secret {secret_name}")
            else:
                logger.error(f"Error retrieving secret {secret_name}: {e}")
            
            # Fall back to environment variable
            if fallback_env_var:
                logger.info(f"Falling back to environment variable {fallback_env_var}")
                return os.getenv(fallback_env_var)
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            if fallback_env_var:
                return os.getenv(fallback_env_var)
            return None
    
    def get_parameter(self, parameter_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a parameter from AWS SSM Parameter Store.
        
        Args:
            parameter_name: Name of the parameter in SSM Parameter Store
            fallback_env_var: Environment variable to fall back to if AWS is unavailable
            
        Returns:
            Parameter value or None if not found
        """
        if not self.ssm_client:
            if fallback_env_var:
                return os.getenv(fallback_env_var)
            return None
        
        try:
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            return response['Parameter']['Value']
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                logger.warning(f"Parameter {parameter_name} not found in SSM Parameter Store")
            else:
                logger.error(f"Error retrieving parameter {parameter_name}: {e}")
            
            # Fall back to environment variable
            if fallback_env_var:
                logger.info(f"Falling back to environment variable {fallback_env_var}")
                return os.getenv(fallback_env_var)
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving parameter {parameter_name}: {e}")
            if fallback_env_var:
                return os.getenv(fallback_env_var)
            return None
    
    def get_all_secrets(self, secret_prefix: str = "sentinelhire/") -> Dict[str, Any]:
        """
        Retrieve all secrets with a given prefix.
        
        Args:
            secret_prefix: Prefix to filter secrets
            
        Returns:
            Dictionary of secret names and values
        """
        if not self.secrets_client:
            return {}
        
        try:
            response = self.secrets_client.list_secrets(
                MaxResults=100,
                Filters=[
                    {
                        'Key': 'name',
                        'Values': [secret_prefix]
                    }
                ]
            )
            
            secrets = {}
            for secret in response['SecretList']:
                secret_name = secret['Name']
                secret_value = self.get_secret(secret_name)
                if secret_value:
                    # Remove prefix from key name
                    key_name = secret_name.replace(secret_prefix, '')
                    secrets[key_name] = secret_value
            
            return secrets
            
        except ClientError as e:
            logger.error(f"Error listing secrets with prefix {secret_prefix}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error listing secrets: {e}")
            return {}

def get_config_from_secrets() -> Dict[str, Any]:
    """
    Get configuration from AWS Secrets Manager with environment variable fallback.
    
    Returns:
        Configuration dictionary
    """
    secrets_manager = SecretsManager()
    
    config = {
        # AWS Configuration
        'aws_access_key_id': secrets_manager.get_parameter(
            '/sentinelhire/aws/access_key_id',
            'AWS_ACCESS_KEY_ID'
        ),
        'aws_secret_access_key': secrets_manager.get_parameter(
            '/sentinelhire/aws/secret_access_key',
            'AWS_SECRET_ACCESS_KEY'
        ),
        'aws_region': secrets_manager.get_parameter(
            '/sentinelhire/aws/region',
            'AWS_REGION'
        ) or 'us-east-1',
        
        # Supabase Configuration
        'supabase_url': secrets_manager.get_parameter(
            '/sentinelhire/supabase/url',
            'SUPABASE_URL'
        ),
        'supabase_key': secrets_manager.get_parameter(
            '/sentinelhire/supabase/key',
            'SUPABASE_KEY'
        ),
        'supabase_service_role_key': secrets_manager.get_parameter(
            '/sentinelhire/supabase/service_role_key',
            'SUPABASE_SERVICE_ROLE_KEY'
        ),
        
        # External API Keys
        'numverify_api_key': secrets_manager.get_parameter(
            '/sentinelhire/apis/numverify_key',
            'NUMVERIFY_API_KEY'
        ),
        'abstract_api_key': secrets_manager.get_parameter(
            '/sentinelhire/apis/abstract_key',
            'ABSTRACT_API_KEY'
        ),
        'serpapi_key': secrets_manager.get_parameter(
            '/sentinelhire/apis/serpapi_key',
            'SERPAPI_KEY'
        ),
        
        # Background Verification APIs
        'college_scorecard_key': secrets_manager.get_parameter(
            '/sentinelhire/apis/college_scorecard_key',
            'COLLEGE_SCORECARD_KEY'
        ),
        'github_token': secrets_manager.get_parameter(
            '/sentinelhire/apis/github_token',
            'GITHUB_TOKEN'
        ),
        'sec_contact_email': secrets_manager.get_parameter(
            '/sentinelhire/apis/sec_contact_email',
            'SEC_CONTACT_EMAIL'
        ),
        'openalex_contact_email': secrets_manager.get_parameter(
            '/sentinelhire/apis/openalex_contact_email',
            'OPENALEX_CONTACT_EMAIL'
        ),
        
        # Redis Configuration
        'redis_url': secrets_manager.get_parameter(
            '/sentinelhire/redis/url',
            'REDIS_URL'
        ),
        
        # Application Settings
        'debug': secrets_manager.get_parameter(
            '/sentinelhire/app/debug',
            'DEBUG'
        ) == 'true',
        'log_level': secrets_manager.get_parameter(
            '/sentinelhire/app/log_level',
            'LOG_LEVEL'
        ) or 'INFO',
        'rate_limit_per_minute': int(secrets_manager.get_parameter(
            '/sentinelhire/app/rate_limit_per_minute',
            'RATE_LIMIT_PER_MINUTE'
        ) or '60'),
        'max_file_size_mb': int(secrets_manager.get_parameter(
            '/sentinelhire/app/max_file_size_mb',
            'MAX_FILE_SIZE_MB'
        ) or '10'),
    }
    
    # Filter out None values
    return {k: v for k, v in config.items() if v is not None}

def validate_required_secrets(config: Dict[str, Any]) -> bool:
    """
    Validate that all required secrets are present.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if all required secrets are present, False otherwise
    """
    required_secrets = [
        'aws_access_key_id',
        'aws_secret_access_key',
        'supabase_url',
        'supabase_key',
        'supabase_service_role_key'
    ]
    
    missing_secrets = [secret for secret in required_secrets if not config.get(secret)]
    
    if missing_secrets:
        logger.error(f"Missing required secrets: {missing_secrets}")
        return False
    
    return True
