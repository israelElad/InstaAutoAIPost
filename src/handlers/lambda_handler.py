import json
import logging
from ..services.s3_service import S3Service
from ..services.instagram_service import InstagramService
from ..utils.image_validator import validate_image, ImageValidationError
from ..config import validate_config

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event (dict): Lambda event data
        context (object): Lambda context
        
    Returns:
        dict: Response with status and message
    """
    try:
        # Validate configuration
        validate_config()
        
        # Initialize services
        s3_service = S3Service()
        instagram_service = InstagramService()
        
        # Get oldest image from S3
        image_data, image_key = s3_service.get_oldest_image()
        
        if not image_data or not image_key:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No images found in S3 bucket'
                })
            }
        
        # Validate image
        try:
            validate_image(image_data)
        except ImageValidationError as e:
            logger.error(f"Image validation failed: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': f'Image validation failed: {str(e)}'
                })
            }
        
        # Post to Instagram
        try:
            instagram_service.post_image(image_data)
        except Exception as e:
            logger.error(f"Failed to post to Instagram: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': f'Failed to post to Instagram: {str(e)}'
                })
            }
        
        # Delete from S3
        try:
            s3_service.delete_image(image_key)
        except Exception as e:
            logger.error(f"Failed to delete image from S3: {str(e)}")
            # Don't return error here as the post was successful
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully posted image to Instagram and deleted from S3'
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Unexpected error: {str(e)}'
            })
        }

if __name__ == "__main__":
    print("[Local Test] Running lambda_handler with dummy event...")
    response = lambda_handler({}, None)
    print("[Local Test] Handler response:")
    print(json.dumps(response, indent=2)) 