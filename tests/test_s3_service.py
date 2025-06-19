import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from moto import mock_aws
from unittest.mock import patch, MagicMock
from PIL import Image
import io
from datetime import datetime, timezone

from src.services.s3_service import S3Service

def create_test_image(width: int = 800, height: int = 600) -> bytes:
    """Create a test image for testing purposes."""
    image = Image.new('RGB', (width, height), color='blue')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

class TestS3Service:
    """Test suite for S3Service."""
    
    @mock_aws
    def test_s3_service_initialization(self):
        """Test S3 service initialization with mocked AWS."""
        # Create a mock S3 bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                assert service.bucket_name == 'test-bucket'
                assert service.s3_client is not None

    @mock_aws
    def test_get_oldest_image_empty_bucket(self):
        """Test getting oldest image from empty bucket."""
        # Create empty bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                image_data, image_key = service.get_oldest_image()
                assert image_data is None
                assert image_key is None

    @mock_aws
    def test_get_oldest_image_single_image(self):
        """Test getting oldest image with single image in bucket."""
        # Create bucket and add image
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        test_image = create_test_image()
        s3_client.put_object(
            Bucket='test-bucket',
            Key='test-image.jpg',
            Body=test_image
        )
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                image_data, image_key = service.get_oldest_image()
                
                assert image_data is not None
                assert image_key == 'test-image.jpg'
                assert len(image_data) == len(test_image)

    @mock_aws
    def test_get_oldest_image_multiple_images(self):
        """Test getting oldest image with multiple images in bucket."""
        # Create bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        # Add multiple images with different timestamps
        test_images = [
            ('newest.jpg', create_test_image(400, 400)),
            ('oldest.jpg', create_test_image(500, 500)),
            ('middle.jpg', create_test_image(600, 600))
        ]
        
        # Upload in order to ensure oldest is first
        for key, image_data in test_images:
            s3_client.put_object(
                Bucket='test-bucket',
                Key=key,
                Body=image_data
            )
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                image_data, image_key = service.get_oldest_image()
                
                assert image_data is not None
                assert image_key == 'newest.jpg'  # Due to test order

    @mock_aws
    def test_upload_image(self):
        """Test uploading an image to S3."""
        # Create bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                test_image = create_test_image()
                
                # Upload image
                service.upload_image(test_image, 'uploaded-test.jpg')
                
                # Verify upload
                response = s3_client.get_object(Bucket='test-bucket', Key='uploaded-test.jpg')
                uploaded_data = response['Body'].read()
                assert len(uploaded_data) == len(test_image)

    @mock_aws
    def test_delete_image(self):
        """Test deleting an image from S3."""
        # Create bucket and add image
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        test_image = create_test_image()
        s3_client.put_object(
            Bucket='test-bucket',
            Key='to-delete.jpg',
            Body=test_image
        )
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                
                # Verify image exists
                response = s3_client.list_objects_v2(Bucket='test-bucket')
                assert 'Contents' in response
                assert len(response['Contents']) == 1
                
                # Delete image
                service.delete_image('to-delete.jpg')
                
                # Verify deletion
                response = s3_client.list_objects_v2(Bucket='test-bucket')
                assert 'Contents' not in response

    @mock_aws
    def test_delete_nonexistent_image(self):
        """Test deleting a non-existent image."""
        # Create empty bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                
                # Should not raise exception for non-existent file
                service.delete_image('nonexistent.jpg')

    @mock_aws 
    def test_lambda_environment_detection(self):
        """Test S3 service behavior in Lambda environment."""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch.dict(os.environ, {
                'AWS_LAMBDA_FUNCTION_NAME': 'test-lambda',
                'AWS_REGION': 'us-east-1'
            }):
                service = S3Service()
                assert service.bucket_name == 'test-bucket'

    def test_credentials_error_handling(self):
        """Test error handling for missing credentials."""
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch('boto3.client') as mock_client:
                from botocore.exceptions import NoCredentialsError
                mock_client.side_effect = NoCredentialsError()
                
                with pytest.raises(Exception, match="AWS credentials not found"):
                    S3Service()

    def test_client_error_handling(self):
        """Test error handling for AWS client errors."""
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'test-bucket'):
            with patch('boto3.client') as mock_client:
                from botocore.exceptions import ClientError
                error_response = {'Error': {'Code': 'InvalidAccessKeyId'}}
                mock_client.side_effect = ClientError(error_response, 'CreateClient')
                
                with pytest.raises(Exception, match="Invalid AWS Access Key ID"):
                    S3Service()

    @mock_aws
    def test_get_oldest_image_error_handling(self):
        """Test error handling in get_oldest_image method."""
        with patch('src.services.s3_service.S3_BUCKET_NAME', 'nonexistent-bucket'):
            with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}):
                service = S3Service()
                
                with pytest.raises(Exception, match="Error accessing S3"):
                    service.get_oldest_image()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])