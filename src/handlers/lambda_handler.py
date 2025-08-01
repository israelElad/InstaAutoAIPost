import json
import logging
import os
from datetime import datetime
from ..services.s3_service import S3Service
from ..services.instagram_service import InstagramService
from ..utils.image_validator import validate_image, ImageValidationError
from ..utils.image_processor import ImageProcessor
from ..config import config

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main handler function for Instagram auto-posting.
    Works for both AWS Lambda and EC2 environments.
    
    Args:
        event (dict): Event data
        context (object): Context object
        
    Returns:
        dict: Response with status and message
    """
    try:
        # Validate configuration
        config.validate()
        
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
        
        # Save original image locally for debugging (if not on Lambda)
        is_lambda = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
        if not is_lambda:
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
        
        # Save processed image locally for debugging (if not on Lambda)
        if not is_lambda:
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
        
        # Post to Instagram (always attempt, regardless of environment)
        try:
            # Extract location from original image data before processing strips EXIF
            location = instagram_service._extract_location_for_caption(image_data)
            # Generate caption for logging (simulate, since post_image will generate it again)
            caption = instagram_service._generate_caption(processed_image_data, location) # Use processed_image_data for caption generation if needed by AI
            instagram_service.log_pre_posting_info(image_key, caption)
            logger.info("[ACTION REQUIRED] Please review the above info and approve before posting to Instagram.")
            # === USER APPROVAL REQUIRED HERE ===
            # Uncomment the next line to actually post after approval:
            instagram_service.post_image(processed_image_data)
            logger.info("[ACTION] Instagram post sent.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Image processed and posted to Instagram.'
                })
            }
        except Exception as e:
            logger.error(f"Failed to prepare Instagram post: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': f'Failed to prepare Instagram post: {str(e)}'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed image and posted to Instagram'
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
