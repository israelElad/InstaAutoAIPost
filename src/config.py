import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Instagram credentials
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# AWS credentials
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

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

def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = [
        'INSTAGRAM_USERNAME',
        'INSTAGRAM_PASSWORD',
        'S3_BUCKET_NAME'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Check if running on Lambda
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        print("Running on AWS Lambda - using execution role credentials")
    else:
        print("Running locally - using explicit credentials if provided") 