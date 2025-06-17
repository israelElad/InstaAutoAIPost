import pytest
from PIL import Image
import io
from src.utils.image_validator import validate_image, ImageValidationError

def create_test_image(width: int, height: int) -> bytes:
    """Create a test image with specified dimensions."""
    image = Image.new('RGB', (width, height), color='red')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_valid_image():
    """Test validation of a valid image."""
    # Create a valid image (800x800)
    image_data = create_test_image(800, 800)
    assert validate_image(image_data) is True

def test_invalid_resolution():
    """Test validation of an image with invalid resolution."""
    # Create an image that's too small
    image_data = create_test_image(200, 200)
    with pytest.raises(ImageValidationError):
        validate_image(image_data)

def test_invalid_aspect_ratio():
    """Test validation of an image with invalid aspect ratio."""
    # Create an image with invalid aspect ratio
    image_data = create_test_image(1000, 100)
    with pytest.raises(ImageValidationError):
        validate_image(image_data)

def test_large_file():
    """Test validation of an image that's too large."""
    # Create a large image (2000x2000)
    image_data = create_test_image(2000, 2000)
    with pytest.raises(ImageValidationError):
        validate_image(image_data)

def test_invalid_image_data():
    """Test validation of invalid image data."""
    with pytest.raises(ImageValidationError):
        validate_image(b'invalid image data') 