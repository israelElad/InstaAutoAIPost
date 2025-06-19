import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import json
from PIL import Image
import io

from src.handlers.lambda_handler import lambda_handler

def create_test_image(width: int = 800, height: int = 600) -> bytes:
    """Create a test image for testing purposes."""
    image = Image.new('RGB', (width, height), color='green')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

class TestLambdaHandler:
    """Test suite for Lambda handler integration."""
    
    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    @patch('src.handlers.lambda_handler.validate_image')
    def test_lambda_handler_success_flow(self, mock_validate_image, mock_instagram_service_class, 
                                       mock_s3_service_class, mock_validate_config):
        """Test successful end-to-end Lambda execution."""
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        test_image = create_test_image()
        mock_s3_service.get_oldest_image.return_value = (test_image, 'test-image.jpg')
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service.post_image.return_value = True
        mock_instagram_service_class.return_value = mock_instagram_service
        
        mock_validate_image.return_value = True
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify successful response
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'Successfully posted image to Instagram' in response_body['message']
        
        # Verify workflow steps
        mock_validate_config.assert_called_once()
        mock_s3_service.get_oldest_image.assert_called_once()
        mock_validate_image.assert_called_once_with(test_image)
        mock_instagram_service.post_image.assert_called_once_with(test_image)
        mock_s3_service.delete_image.assert_called_once_with('test-image.jpg')

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    def test_lambda_handler_no_images_in_s3(self, mock_instagram_service_class, 
                                          mock_s3_service_class, mock_validate_config):
        """Test Lambda handler when no images are found in S3."""
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        mock_s3_service.get_oldest_image.return_value = (None, None)
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service_class.return_value = mock_instagram_service
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'No images found in S3 bucket' in response_body['message']
        
        # Verify Instagram service was not called
        mock_instagram_service.post_image.assert_not_called()

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    @patch('src.handlers.lambda_handler.validate_image')
    def test_lambda_handler_image_validation_failure(self, mock_validate_image, 
                                                   mock_instagram_service_class, 
                                                   mock_s3_service_class, 
                                                   mock_validate_config):
        """Test Lambda handler when image validation fails."""
        from src.utils.image_validator import ImageValidationError
        
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        test_image = create_test_image()
        mock_s3_service.get_oldest_image.return_value = (test_image, 'invalid-image.jpg')
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service_class.return_value = mock_instagram_service
        
        mock_validate_image.side_effect = ImageValidationError("Image too small")
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'Image validation failed' in response_body['message']
        assert 'Image too small' in response_body['message']
        
        # Verify Instagram service was not called
        mock_instagram_service.post_image.assert_not_called()

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    @patch('src.handlers.lambda_handler.validate_image')
    def test_lambda_handler_instagram_posting_failure(self, mock_validate_image, 
                                                     mock_instagram_service_class, 
                                                     mock_s3_service_class, 
                                                     mock_validate_config):
        """Test Lambda handler when Instagram posting fails."""
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        test_image = create_test_image()
        mock_s3_service.get_oldest_image.return_value = (test_image, 'test-image.jpg')
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service.post_image.side_effect = Exception("Instagram API error")
        mock_instagram_service_class.return_value = mock_instagram_service
        
        mock_validate_image.return_value = True
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'Failed to post to Instagram' in response_body['message']
        assert 'Instagram API error' in response_body['message']
        
        # Verify S3 deletion was not called since posting failed
        mock_s3_service.delete_image.assert_not_called()

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    @patch('src.handlers.lambda_handler.validate_image')
    def test_lambda_handler_s3_deletion_failure(self, mock_validate_image, 
                                               mock_instagram_service_class, 
                                               mock_s3_service_class, 
                                               mock_validate_config):
        """Test Lambda handler when S3 deletion fails but posting succeeds."""
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        test_image = create_test_image()
        mock_s3_service.get_oldest_image.return_value = (test_image, 'test-image.jpg')
        mock_s3_service.delete_image.side_effect = Exception("S3 deletion failed")
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service.post_image.return_value = True
        mock_instagram_service_class.return_value = mock_instagram_service
        
        mock_validate_image.return_value = True
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response (should still be success since posting worked)
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'Successfully posted image to Instagram' in response_body['message']

    @patch('src.handlers.lambda_handler.validate_config')
    def test_lambda_handler_config_validation_failure(self, mock_validate_config):
        """Test Lambda handler when config validation fails."""
        mock_validate_config.side_effect = ValueError("Missing environment variables")
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'Missing environment variables' in response_body['message']

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    def test_lambda_handler_s3_service_initialization_failure(self, mock_s3_service_class, 
                                                             mock_validate_config):
        """Test Lambda handler when S3 service initialization fails."""
        mock_validate_config.return_value = None
        mock_s3_service_class.side_effect = Exception("S3 credentials error")
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'S3 credentials error' in response_body['message']

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    def test_lambda_handler_instagram_service_initialization_failure(self, mock_instagram_service_class,
                                                                   mock_s3_service_class, 
                                                                   mock_validate_config):
        """Test Lambda handler when Instagram service initialization fails."""
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service_class.side_effect = Exception("Instagram login failed")
        
        # Execute handler
        result = lambda_handler({}, None)
        
        # Verify response
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'Instagram login failed' in response_body['message']

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    @patch('src.handlers.lambda_handler.validate_image')
    def test_lambda_handler_with_event_data(self, mock_validate_image, 
                                          mock_instagram_service_class, 
                                          mock_s3_service_class, 
                                          mock_validate_config):
        """Test Lambda handler with various event data inputs."""
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        test_image = create_test_image()
        mock_s3_service.get_oldest_image.return_value = (test_image, 'test-image.jpg')
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service.post_image.return_value = True
        mock_instagram_service_class.return_value = mock_instagram_service
        
        mock_validate_image.return_value = True
        
        # Test with different event types
        test_events = [
            {},  # Empty event
            {"Records": []},  # S3 event structure
            {"source": "aws.events"},  # CloudWatch event
            {"httpMethod": "POST"},  # API Gateway event
        ]
        
        for event in test_events:
            result = lambda_handler(event, None)
            assert result['statusCode'] == 200

    @patch('src.handlers.lambda_handler.validate_config')
    @patch('src.handlers.lambda_handler.S3Service')
    @patch('src.handlers.lambda_handler.InstagramService')
    @patch('src.handlers.lambda_handler.validate_image')
    def test_lambda_handler_context_handling(self, mock_validate_image, 
                                           mock_instagram_service_class, 
                                           mock_s3_service_class, 
                                           mock_validate_config):
        """Test Lambda handler with different context objects."""
        # Setup mocks
        mock_validate_config.return_value = None
        
        mock_s3_service = MagicMock()
        test_image = create_test_image()
        mock_s3_service.get_oldest_image.return_value = (test_image, 'test-image.jpg')
        mock_s3_service_class.return_value = mock_s3_service
        
        mock_instagram_service = MagicMock()
        mock_instagram_service.post_image.return_value = True
        mock_instagram_service_class.return_value = mock_instagram_service
        
        mock_validate_image.return_value = True
        
        # Test with different context objects
        contexts = [
            None,
            MagicMock(aws_request_id='test-123', log_group_name='test-log-group'),
            MagicMock(function_name='test-function', memory_limit_in_mb=128),
        ]
        
        for context in contexts:
            result = lambda_handler({}, context)
            assert result['statusCode'] == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])