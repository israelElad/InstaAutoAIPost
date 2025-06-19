import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from PIL import Image
import io

from src.services.instagram_service import InstagramService

def create_test_image(width: int = 800, height: int = 600) -> bytes:
    """Create a test image for testing purposes."""
    image = Image.new('RGB', (width, height), color='red')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

class TestInstagramService:
    """Test suite for InstagramService."""
    
    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_instagram_service_initialization_success(self, mock_client_class):
        """Test successful Instagram service initialization."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        
        # Verify client was created and login was called
        mock_client_class.assert_called_once()
        mock_client.login.assert_called_once_with('test_user', 'test_pass')
        assert service.client == mock_client

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_instagram_service_login_required_error(self, mock_client_class):
        """Test login failure with LoginRequired exception."""
        from instagrapi.exceptions import LoginRequired
        
        mock_client = MagicMock()
        mock_client.login.side_effect = LoginRequired("Login failed")
        mock_client_class.return_value = mock_client
        
        with pytest.raises(Exception, match="Failed to login to Instagram"):
            InstagramService()

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_instagram_service_unexpected_login_error(self, mock_client_class):
        """Test login failure with unexpected exception."""
        mock_client = MagicMock()
        mock_client.login.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client
        
        with pytest.raises(Exception, match="Unexpected error during Instagram login"):
            InstagramService()

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_generate_caption(self, mock_client_class):
        """Test caption generation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        test_image = create_test_image()
        
        caption = service._generate_caption(test_image)
        
        # Check that caption is generated (currently a static template)
        assert isinstance(caption, str)
        assert len(caption) > 0
        assert "photography" in caption.lower()

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_post_image_success(self, mock_client_class):
        """Test successful image posting."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful photo upload
        mock_media = MagicMock()
        mock_client.photo_upload.return_value = mock_media
        
        service = InstagramService()
        test_image = create_test_image()
        
        result = service.post_image(test_image)
        
        assert result is True
        mock_client.photo_upload.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_client.photo_upload.call_args
        assert 'caption' in call_args[1]
        # First argument should be PIL Image
        posted_image = call_args[0][0]
        assert hasattr(posted_image, 'size')  # PIL Image has size attribute

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_post_image_client_error(self, mock_client_class):
        """Test image posting with Instagram API error."""
        from instagrapi.exceptions import ClientError
        
        mock_client = MagicMock()
        mock_client.photo_upload.side_effect = ClientError("API Error")
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        test_image = create_test_image()
        
        with pytest.raises(Exception, match="Instagram API error"):
            service.post_image(test_image)

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_post_image_unexpected_error(self, mock_client_class):
        """Test image posting with unexpected error."""
        mock_client = MagicMock()
        mock_client.photo_upload.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        test_image = create_test_image()
        
        with pytest.raises(Exception, match="Error posting to Instagram"):
            service.post_image(test_image)

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_post_invalid_image_data(self, mock_client_class):
        """Test posting invalid image data."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        
        with pytest.raises(Exception):
            service.post_image(b'invalid image data')

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_validate_credentials_success(self, mock_client_class):
        """Test successful credential validation."""
        mock_client = MagicMock()
        mock_client.get_timeline_feed.return_value = {}
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        result = service.validate_credentials()
        
        assert result is True
        mock_client.get_timeline_feed.assert_called_once()

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_validate_credentials_failure(self, mock_client_class):
        """Test credential validation failure."""
        mock_client = MagicMock()
        mock_client.get_timeline_feed.side_effect = Exception("Invalid credentials")
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        result = service.validate_credentials()
        
        assert result is False

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_post_different_image_formats(self, mock_client_class):
        """Test posting images in different formats."""
        mock_client = MagicMock()
        mock_client.photo_upload.return_value = MagicMock()
        mock_client_class.return_value = mock_client
        
        service = InstagramService()
        
        # Test different image sizes
        test_cases = [
            (400, 400),    # Small square
            (800, 600),    # Standard landscape
            (600, 800),    # Portrait
            (1200, 1200),  # Large square
        ]
        
        for width, height in test_cases:
            test_image = create_test_image(width, height)
            result = service.post_image(test_image)
            assert result is True

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', None)
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', 'test_pass')
    @patch('src.services.instagram_service.Client')
    def test_missing_username(self, mock_client_class):
        """Test handling of missing username."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # This should still work as the code doesn't validate credentials upfront
        service = InstagramService()
        mock_client.login.assert_called_once_with(None, 'test_pass')

    @patch('src.services.instagram_service.INSTAGRAM_USERNAME', 'test_user')
    @patch('src.services.instagram_service.INSTAGRAM_PASSWORD', None)
    @patch('src.services.instagram_service.Client')
    def test_missing_password(self, mock_client_class):
        """Test handling of missing password."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # This should still work as the code doesn't validate credentials upfront
        service = InstagramService()
        mock_client.login.assert_called_once_with('test_user', None)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])