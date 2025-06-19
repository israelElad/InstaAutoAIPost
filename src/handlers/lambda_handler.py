import json
import logging
import os
from datetime import datetime
from ..services.s3_service import S3Service
from ..services.instagram_service import InstagramService
from ..utils.image_validator import validate_image, ImageValidationError
from ..utils.image_processor import ImageProcessor
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
        image_processor = ImageProcessor()
        
        # Get oldest image from S3
        image_data, image_key = s3_service.get_oldest_image()
        
        if not image_data or not image_key:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No images found in S3 bucket'
                })
            }
        
        # Save original image locally for testing (if running locally)
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("test_output", exist_ok=True)
            original_filename = f"test_output/original_{timestamp}_{os.path.basename(image_key)}"
            with open(original_filename, 'wb') as f:
                f.write(image_data)
            logger.info(f"Saved original image locally: {original_filename}")
        
        # Process image to make it Instagram-compliant
        try:
            logger.info("Processing image to make it Instagram-compliant...")
            processed_image_data = image_processor.process_image(image_data)
            logger.info("Image processing completed successfully")
        except ImageValidationError as e:
            logger.error(f"Image processing failed: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': f'Image processing failed: {str(e)}'
                })
            }
        
        # Save processed image locally for testing (if running locally)
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is None:
            processed_filename = f"test_output/processed_{timestamp}_{os.path.basename(image_key)}"
            with open(processed_filename, 'wb') as f:
                f.write(processed_image_data)
            logger.info(f"Saved processed image locally: {processed_filename}")
            
            # Print comparison
            original_size_mb = len(image_data) / (1024 * 1024)
            processed_size_mb = len(processed_image_data) / (1024 * 1024)
            logger.info(f"Original size: {original_size_mb:.2f} MB")
            logger.info(f"Processed size: {processed_size_mb:.2f} MB")
            logger.info(f"Size change: {((processed_size_mb - original_size_mb) / original_size_mb * 100):+.1f}%")
        
        # Validate processed image
        try:
            validate_image(processed_image_data)
            logger.info("Processed image validation passed")
        except ImageValidationError as e:
            logger.error(f"Processed image validation failed: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': f'Processed image validation failed: {str(e)}'
                })
            }
        
        # Post to Instagram (only if not in test mode)
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None:
            try:
                instagram_service.post_image(processed_image_data)
                logger.info("Successfully posted image to Instagram")
            except Exception as e:
                logger.error(f"Failed to post to Instagram: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'message': f'Failed to post to Instagram: {str(e)}'
                    })
                }
            
            # Delete from S3 (only if posted successfully)
            try:
                s3_service.delete_image(image_key)
                logger.info("Successfully deleted image from S3")
            except Exception as e:
                logger.error(f"Failed to delete image from S3: {str(e)}")
                # Don't return error here as the post was successful
        else:
            logger.info("Running in test mode - skipping Instagram post and S3 deletion")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed image' + (' and posted to Instagram' if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None else ' (test mode)')
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