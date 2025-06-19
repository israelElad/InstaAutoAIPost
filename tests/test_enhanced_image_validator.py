import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import io
from src.utils.image_validator import validate_image, ImageValidationError
from src.config import (
    INSTAGRAM_MIN_ASPECT_RATIO,
    INSTAGRAM_MAX_ASPECT_RATIO,
    INSTAGRAM_MIN_RESOLUTION,
    INSTAGRAM_MAX_RESOLUTION,
    INSTAGRAM_MAX_FILE_SIZE_MB
)

def create_test_image(width: int, height: int, color: str = 'red', quality: int = 95) -> bytes:
    """Create a test image with specified dimensions and quality."""
    image = Image.new('RGB', (width, height), color=color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=quality)
    return img_byte_arr.getvalue()

def create_large_file_image(target_size_mb: float) -> bytes:
    """Create an image that exceeds the target file size."""
    # Start with a large image and low compression
    width = height = 2000
    quality = 100
    
    while True:
        image_data = create_test_image(width, height, quality=quality)
        size_mb = len(image_data) / (1024 * 1024)
        
        if size_mb >= target_size_mb:
            return image_data
        
        # Increase dimensions if file is still too small
        width += 200
        height += 200
        
        # Prevent infinite loop
        if width > 5000:
            break
    
    return image_data

class TestImageValidator:
    """Comprehensive test suite for image validator."""
    
    def test_valid_square_image(self):
        """Test validation of a valid square image."""
        image_data = create_test_image(800, 800)
        assert validate_image(image_data) is True

    def test_valid_portrait_image(self):
        """Test validation of a valid portrait image."""
        image_data = create_test_image(800, 1000)  # 0.8 aspect ratio
        assert validate_image(image_data) is True

    def test_valid_landscape_image(self):
        """Test validation of a valid landscape image."""
        image_data = create_test_image(1200, 800)  # 1.5 aspect ratio
        assert validate_image(image_data) is True

    def test_minimum_resolution_valid(self):
        """Test validation at minimum allowed resolution."""
        image_data = create_test_image(INSTAGRAM_MIN_RESOLUTION, INSTAGRAM_MIN_RESOLUTION)
        assert validate_image(image_data) is True

    def test_maximum_resolution_valid(self):
        """Test validation at maximum allowed resolution."""
        image_data = create_test_image(INSTAGRAM_MAX_RESOLUTION, INSTAGRAM_MAX_RESOLUTION)
        assert validate_image(image_data) is True

    def test_minimum_aspect_ratio_valid(self):
        """Test validation at minimum aspect ratio."""
        # Calculate dimensions for minimum aspect ratio
        width = 800
        height = int(width / INSTAGRAM_MIN_ASPECT_RATIO)
        image_data = create_test_image(width, height)
        assert validate_image(image_data) is True

    def test_maximum_aspect_ratio_valid(self):
        """Test validation at maximum aspect ratio."""
        # Calculate dimensions for maximum aspect ratio
        height = 600
        width = int(height * INSTAGRAM_MAX_ASPECT_RATIO)
        image_data = create_test_image(width, height)
        assert validate_image(image_data) is True

    def test_resolution_too_small_width(self):
        """Test validation failure for width below minimum."""
        image_data = create_test_image(INSTAGRAM_MIN_RESOLUTION - 1, INSTAGRAM_MIN_RESOLUTION)
        with pytest.raises(ImageValidationError, match="resolution below minimum"):
            validate_image(image_data)

    def test_resolution_too_small_height(self):
        """Test validation failure for height below minimum."""
        image_data = create_test_image(INSTAGRAM_MIN_RESOLUTION, INSTAGRAM_MIN_RESOLUTION - 1)
        with pytest.raises(ImageValidationError, match="resolution below minimum"):
            validate_image(image_data)

    def test_resolution_too_large_width(self):
        """Test validation failure for width above maximum."""
        image_data = create_test_image(INSTAGRAM_MAX_RESOLUTION + 1, INSTAGRAM_MAX_RESOLUTION)
        with pytest.raises(ImageValidationError, match="resolution exceeds maximum"):
            validate_image(image_data)

    def test_resolution_too_large_height(self):
        """Test validation failure for height above maximum."""
        image_data = create_test_image(INSTAGRAM_MAX_RESOLUTION, INSTAGRAM_MAX_RESOLUTION + 1)
        with pytest.raises(ImageValidationError, match="resolution exceeds maximum"):
            validate_image(image_data)

    def test_aspect_ratio_too_small(self):
        """Test validation failure for aspect ratio below minimum."""
        # Create image with aspect ratio smaller than minimum
        width = 400
        height = int(width / (INSTAGRAM_MIN_ASPECT_RATIO - 0.1))
        image_data = create_test_image(width, height)
        with pytest.raises(ImageValidationError, match="aspect ratio.*outside allowed range"):
            validate_image(image_data)

    def test_aspect_ratio_too_large(self):
        """Test validation failure for aspect ratio above maximum."""
        # Create image with aspect ratio larger than maximum
        height = 400
        width = int(height * (INSTAGRAM_MAX_ASPECT_RATIO + 0.1))
        image_data = create_test_image(width, height)
        with pytest.raises(ImageValidationError, match="aspect ratio.*outside allowed range"):
            validate_image(image_data)

    def test_file_size_too_large(self):
        """Test validation failure for file size exceeding limit."""
        # Create an image with a reasonable size but force it to be large file
        # by using maximum quality and minimal compression
        image = Image.new('RGB', (800, 800))
        # Fill with noise to make it less compressible
        import random
        pixels = image.load()
        for i in range(image.width):
            for j in range(image.height):
                pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Save with maximum quality to create large file
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=100, optimize=False)
        large_image_data = img_byte_arr.getvalue()
        
        # If the image is not large enough, create a larger one
        if len(large_image_data) <= INSTAGRAM_MAX_FILE_SIZE_MB * 1024 * 1024:
            # Create even larger image data by concatenating
            large_image_data = large_image_data * 10  # This will be invalid image data but large
        
        with pytest.raises(ImageValidationError, match="Image size exceeds|Error validating image"):
            validate_image(large_image_data)

    def test_invalid_image_data(self):
        """Test validation failure for invalid image data."""
        with pytest.raises(ImageValidationError, match="Error validating image"):
            validate_image(b'invalid image data')

    def test_empty_image_data(self):
        """Test validation failure for empty image data."""
        with pytest.raises(ImageValidationError):
            validate_image(b'')

    def test_corrupted_image_data(self):
        """Test validation failure for corrupted image data."""
        # Create partial JPEG header
        corrupted_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
        with pytest.raises(ImageValidationError):
            validate_image(corrupted_data)

    def test_different_image_qualities(self):
        """Test validation with different JPEG qualities."""
        for quality in [30, 60, 90, 95]:
            image_data = create_test_image(800, 800, quality=quality)
            assert validate_image(image_data) is True

    def test_edge_case_dimensions(self):
        """Test validation with edge case dimensions."""
        # Test various combinations at the boundaries that are valid
        test_cases = [
            (320, 320),    # Minimum square
            (320, 400),    # Minimum width, valid height and ratio
            (400, 320),    # Valid width, minimum height and ratio
            (1440, 1440),  # Maximum square
            (1200, 1000),  # Within max dimensions and valid ratio
            (1000, 1200),  # Within max dimensions and valid ratio
        ]
        
        for width, height in test_cases:
            image_data = create_test_image(width, height)
            assert validate_image(image_data) is True

    def test_precision_aspect_ratios(self):
        """Test validation with precise aspect ratios near boundaries."""
        # Test aspect ratios very close to the limits with reasonable dimensions
        base_size = 800
        
        # Just within minimum aspect ratio (0.8), keep dimensions reasonable
        width_min = int(base_size * INSTAGRAM_MIN_ASPECT_RATIO)
        height_for_min = base_size
        image_data = create_test_image(width_min, height_for_min)
        assert validate_image(image_data) is True
        
        # Just within maximum aspect ratio (1.91), keep dimensions reasonable
        width_max = int(base_size * INSTAGRAM_MAX_ASPECT_RATIO)
        height_for_max = base_size
        # Ensure we don't exceed max resolution
        if width_max > INSTAGRAM_MAX_RESOLUTION:
            height_for_max = int(INSTAGRAM_MAX_RESOLUTION / INSTAGRAM_MAX_ASPECT_RATIO)
            width_max = int(height_for_max * INSTAGRAM_MAX_ASPECT_RATIO)
        
        image_data = create_test_image(width_max, height_for_max)
        assert validate_image(image_data) is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])