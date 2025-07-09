import os
import boto3
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager that loads credentials from AWS Secrets Manager."""
    
    def __init__(self):
        self.secrets_client = None
        self._credentials = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from AWS Secrets Manager or environment variables."""
        try:
            # Try to load from AWS Secrets Manager first
            self._load_from_secrets_manager()
        except Exception as e:
            logger.warning(f"Failed to load from Secrets Manager: {e}")
            # Fallback to environment variables
            self._load_from_environment()
    
    def _load_from_secrets_manager(self):
        """Load credentials from AWS Secrets Manager."""
        try:
            self.secrets_client = boto3.client('secretsmanager')
            
            # Get the secret
            response = self.secrets_client.get_secret_value(
                SecretId='insta-auto-ai-post-secrets'
            )

            # Parse the secret
            secret_data = json.loads(response['SecretString'])
            
            self._credentials = {
                'INSTAGRAM_USERNAME': secret_data.get('INSTAGRAM_USERNAME'),
                'INSTAGRAM_PASSWORD': secret_data.get('INSTAGRAM_PASSWORD'),
                'AWS_ACCESS_KEY_ID': secret_data.get('AWS_ACCESS_KEY_ID'),
                'AWS_SECRET_ACCESS_KEY': secret_data.get('AWS_SECRET_ACCESS_KEY'),
                'S3_BUCKET_NAME': secret_data.get('S3_BUCKET_NAME')
            }
            
            logger.info("✅ Credentials loaded from AWS Secrets Manager")
            
        except Exception as e:
            logger.error(f"Failed to load from Secrets Manager: {e}")
            raise
    
    def _load_from_environment(self):
        """Load credentials from environment variables (fallback)."""
        self._credentials = {
            'INSTAGRAM_USERNAME': os.getenv('INSTAGRAM_USERNAME'),
            'INSTAGRAM_PASSWORD': os.getenv('INSTAGRAM_PASSWORD'),
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'S3_BUCKET_NAME': os.getenv('S3_BUCKET_NAME')
        }
        
        logger.info("⚠️  Credentials loaded from environment variables (fallback)")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value."""
        return self._credentials.get(key, default) if self._credentials else default
    
    def get_all(self) -> Dict[str, Optional[str]]:
        """Get all configuration values."""
        return self._credentials.copy() if self._credentials else {}
    
    def validate(self) -> bool:
        """Validate that all required credentials are present."""
        required_keys = [
            'INSTAGRAM_USERNAME',
            'INSTAGRAM_PASSWORD',
            'S3_BUCKET_NAME'
        ]
        
        if not self._credentials:
            logger.error("❌ No credentials loaded")
            return False
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"❌ Missing required credentials: {missing_keys}")
            return False
        
        logger.info("✅ All required credentials are present")
        return True
    
    def refresh_credentials(self):
        """Refresh credentials from Secrets Manager."""
        try:
            self._load_from_secrets_manager()
            logger.info("✅ Credentials refreshed from Secrets Manager")
        except Exception as e:
            logger.error(f"❌ Failed to refresh credentials: {e}")

# Global configuration instance
config = Config()

# Convenience functions
def get_instagram_username() -> Optional[str]:
    return config.get('INSTAGRAM_USERNAME')

def get_instagram_password() -> Optional[str]:
    return config.get('INSTAGRAM_PASSWORD')

def get_aws_access_key_id() -> Optional[str]:
    return config.get('AWS_ACCESS_KEY_ID')

def get_aws_secret_access_key() -> Optional[str]:
    return config.get('AWS_SECRET_ACCESS_KEY')

def get_s3_bucket_name() -> Optional[str]:
    return config.get('S3_BUCKET_NAME')

def get_session_file() -> str:
    return os.getenv('INSTAGRAM_SESSION_FILE', '/app/session.json')

# Direct exports for backward compatibility (lazy properties)
class LazyConfig:
    @property
    def INSTAGRAM_USERNAME(self) -> Optional[str]:
        return get_instagram_username()
    
    @property
    def INSTAGRAM_PASSWORD(self) -> Optional[str]:
        return get_instagram_password()
    
    @property
    def AWS_ACCESS_KEY_ID(self) -> Optional[str]:
        return get_aws_access_key_id()
    
    @property
    def AWS_SECRET_ACCESS_KEY(self) -> Optional[str]:
        return get_aws_secret_access_key()
    
    @property
    def S3_BUCKET_NAME(self) -> Optional[str]:
        return get_s3_bucket_name()

# Create a proxy object that provides the lazy properties
_lazy_config = LazyConfig()

# Direct exports for backward compatibility
INSTAGRAM_USERNAME = _lazy_config.INSTAGRAM_USERNAME
INSTAGRAM_PASSWORD = _lazy_config.INSTAGRAM_PASSWORD
AWS_ACCESS_KEY_ID = _lazy_config.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = _lazy_config.AWS_SECRET_ACCESS_KEY
S3_BUCKET_NAME = _lazy_config.S3_BUCKET_NAME

# Instagram image requirements
INSTAGRAM_MIN_ASPECT_RATIO = 0.8
INSTAGRAM_MAX_ASPECT_RATIO = 1.91
INSTAGRAM_MIN_RESOLUTION = 320
INSTAGRAM_MAX_RESOLUTION = 1440
INSTAGRAM_MAX_FILE_SIZE_MB = 8

# Error messages
ERROR_MESSAGES = {
    'missing_credentials': 'Missing required credentials in environment variables',
    'invalid_image': 'Image does not meet Instagram requirements',
    'upload_failed': 'Failed to upload image to Instagram',
    's3_error': 'Error accessing S3 bucket',
    'instagram_error': 'Error with Instagram API',
}