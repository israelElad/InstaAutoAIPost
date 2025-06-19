import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import io
import os

from src.utils.image_processor import ImageProcessor
from src.config import (
    INSTAGRAM_MIN_ASPECT_RATIO,
    INSTAGRAM_MAX_ASPECT_RATIO,
    INSTAGRAM_MIN_RESOLUTION,
    INSTAGRAM_MAX_RESOLUTION,
    INSTAGRAM_MAX_FILE_SIZE_MB
)

def create_test_image(width: int, height: int, color: str = 'red', quality: int = 95) -> bytes:
    """Create a test image with specified dimensions."""
    image = Image.new('RGB', (width, height), color=color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=quality)
    return img_byte_arr.getvalue()

def save_processed_image(image_data: bytes, filename: str):
    """Save processed image to test_images/after directory for review."""
    os.makedirs('test_images/after', exist_ok=True)
    with open(f'test_images/after/{filename}', 'wb') as f:
        f.write(image_data)

class TestImageProcessor:
    """Test suite for ImageProcessor."""
    
    def test_optimize_valid_image(self):
        """Test optimization of a valid image."""
        original_image = create_test_image(800, 800)
        optimized_image = ImageProcessor.optimize_for_instagram(original_image)
        
        # Save for review
        save_processed_image(optimized_image, 'test_optimize_valid.jpg')
        
        # Check that optimization worked
        assert len(optimized_image) > 0
        assert len(optimized_image) <= len(original_image)
        
        # Verify image can be opened
        processed_img = Image.open(io.BytesIO(optimized_image))
        assert processed_img.mode == 'RGB'

    def test_optimize_oversized_image(self):
        """Test optimization of an oversized image."""
        # Create large image
        original_image = create_test_image(2000, 2000)
        optimized_image = ImageProcessor.optimize_for_instagram(original_image)
        
        # Save for review
        save_processed_image(optimized_image, 'test_optimize_oversized.jpg')
        
        # Check dimensions are within limits
        processed_img = Image.open(io.BytesIO(optimized_image))
        width, height = processed_img.size
        
        assert width <= INSTAGRAM_MAX_RESOLUTION
        assert height <= INSTAGRAM_MAX_RESOLUTION
        assert width >= INSTAGRAM_MIN_RESOLUTION
        assert height >= INSTAGRAM_MIN_RESOLUTION

    def test_optimize_undersized_image(self):
        """Test optimization of an undersized image."""
        # Create small image
        original_image = create_test_image(200, 200)
        optimized_image = ImageProcessor.optimize_for_instagram(original_image)
        
        # Save for review
        save_processed_image(optimized_image, 'test_optimize_undersized.jpg')
        
        # Check dimensions meet minimum requirements
        processed_img = Image.open(io.BytesIO(optimized_image))
        width, height = processed_img.size
        
        assert width >= INSTAGRAM_MIN_RESOLUTION
        assert height >= INSTAGRAM_MIN_RESOLUTION

    def test_optimize_different_formats(self):
        """Test optimization with different image formats."""
        # Test PNG input
        png_image = Image.new('RGBA', (800, 600), (255, 0, 0, 128))
        png_data = io.BytesIO()
        png_image.save(png_data, format='PNG')
        
        optimized_image = ImageProcessor.optimize_for_instagram(png_data.getvalue())
        
        # Save for review
        save_processed_image(optimized_image, 'test_optimize_png_input.jpg')
        
        # Should be converted to JPEG/RGB
        processed_img = Image.open(io.BytesIO(optimized_image))
        assert processed_img.mode == 'RGB'

    def test_crop_to_aspect_ratio_landscape(self):
        """Test cropping to landscape aspect ratio."""
        # Create tall image
        original_image = create_test_image(600, 1000)
        target_ratio = 16/9  # Wide landscape
        
        cropped_image = ImageProcessor.crop_to_aspect_ratio(original_image, target_ratio)
        
        # Save for review
        save_processed_image(cropped_image, 'test_crop_landscape.jpg')
        
        # Check aspect ratio
        processed_img = Image.open(io.BytesIO(cropped_image))
        width, height = processed_img.size
        actual_ratio = width / height
        
        assert abs(actual_ratio - target_ratio) < 0.01

    def test_crop_to_aspect_ratio_portrait(self):
        """Test cropping to portrait aspect ratio."""
        # Create wide image
        original_image = create_test_image(1000, 600)
        target_ratio = 9/16  # Tall portrait
        
        cropped_image = ImageProcessor.crop_to_aspect_ratio(original_image, target_ratio)
        
        # Save for review
        save_processed_image(cropped_image, 'test_crop_portrait.jpg')
        
        # Check aspect ratio
        processed_img = Image.open(io.BytesIO(cropped_image))
        width, height = processed_img.size
        actual_ratio = width / height
        
        assert abs(actual_ratio - target_ratio) < 0.01

    def test_crop_already_correct_ratio(self):
        """Test cropping when aspect ratio is already correct."""
        target_ratio = 1.0  # Square
        original_image = create_test_image(800, 800)  # Already square
        
        cropped_image = ImageProcessor.crop_to_aspect_ratio(original_image, target_ratio)
        
        # Save for review
        save_processed_image(cropped_image, 'test_crop_no_change.jpg')
        
        # Should be very similar size
        assert abs(len(cropped_image) - len(original_image)) < len(original_image) * 0.1

    def test_add_border(self):
        """Test adding border to image."""
        original_image = create_test_image(600, 600)
        
        bordered_image = ImageProcessor.add_border(original_image, border_size=20, border_color='white')
        
        # Save for review
        save_processed_image(bordered_image, 'test_add_border.jpg')
        
        # Check dimensions increased
        original_img = Image.open(io.BytesIO(original_image))
        bordered_img = Image.open(io.BytesIO(bordered_image))
        
        assert bordered_img.width == original_img.width + 40  # 20px on each side
        assert bordered_img.height == original_img.height + 40

    def test_add_colored_border(self):
        """Test adding colored border to image."""
        original_image = create_test_image(600, 600, color='blue')
        
        bordered_image = ImageProcessor.add_border(original_image, border_size=15, border_color='red')
        
        # Save for review
        save_processed_image(bordered_image, 'test_add_colored_border.jpg')
        
        # Should successfully create bordered image
        bordered_img = Image.open(io.BytesIO(bordered_image))
        assert bordered_img.width == 630  # 600 + 15*2
        assert bordered_img.height == 630

    def test_get_image_info(self):
        """Test getting image information."""
        test_image = create_test_image(800, 600)
        info = ImageProcessor.get_image_info(test_image)
        
        assert info['width'] == 800
        assert info['height'] == 600
        assert abs(info['aspect_ratio'] - (800/600)) < 0.01
        assert 'file_size_bytes' in info
        assert 'file_size_mb' in info
        assert 'meets_instagram_requirements' in info

    def test_get_image_info_compliance_check(self):
        """Test image compliance checking in image info."""
        # Valid image
        valid_image = create_test_image(800, 800)
        info = ImageProcessor.get_image_info(valid_image)
        compliance = info['meets_instagram_requirements']
        
        assert compliance['resolution_ok'] is True
        assert compliance['aspect_ratio_ok'] is True
        assert compliance['overall_compliant'] is True

        # Invalid image (too small)
        invalid_image = create_test_image(200, 200)
        info = ImageProcessor.get_image_info(invalid_image)
        compliance = info['meets_instagram_requirements']
        
        assert compliance['resolution_ok'] is False
        assert compliance['overall_compliant'] is False

    def test_file_size_reduction(self):
        """Test file size reduction for large images."""
        # Create a complex image that will be large
        large_image = Image.new('RGB', (1440, 1440))
        # Add random noise to make it less compressible
        import random
        pixels = large_image.load()
        for i in range(large_image.width):
            for j in range(large_image.height):
                pixels[i, j] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
        
        large_data = io.BytesIO()
        large_image.save(large_data, format='JPEG', quality=100)
        large_image_data = large_data.getvalue()
        
        # Process with optimization
        optimized_image = ImageProcessor.optimize_for_instagram(large_image_data, target_quality=60)
        
        # Save for review
        save_processed_image(optimized_image, 'test_file_size_reduction.jpg')
        
        # Should be smaller
        assert len(optimized_image) < len(large_image_data)
        
        # Should still be valid
        processed_img = Image.open(io.BytesIO(optimized_image))
        assert processed_img.mode == 'RGB'

    def test_enhancement_effects(self):
        """Test image enhancement effects."""
        # Create a somewhat dull image
        dull_image = create_test_image(800, 600, color='gray')
        
        enhanced_image = ImageProcessor.optimize_for_instagram(dull_image)
        
        # Save for review
        save_processed_image(enhanced_image, 'test_enhancement.jpg')
        
        # Should produce valid output
        processed_img = Image.open(io.BytesIO(enhanced_image))
        assert processed_img.size == (800, 600) or all(
            dim >= INSTAGRAM_MIN_RESOLUTION for dim in processed_img.size
        )

    def test_various_aspect_ratios(self):
        """Test processing images with various aspect ratios."""
        test_cases = [
            (800, 800, 'square'),
            (800, 600, 'landscape_43'),
            (600, 800, 'portrait_34'),
            (1200, 800, 'landscape_32'),
            (800, 1200, 'portrait_23'),
            (1000, 524, 'max_aspect_ratio'),
            (800, 1000, 'min_aspect_ratio'),
        ]
        
        for width, height, name in test_cases:
            original_image = create_test_image(width, height)
            optimized_image = ImageProcessor.optimize_for_instagram(original_image)
            
            # Save for review
            save_processed_image(optimized_image, f'test_aspect_ratio_{name}.jpg')
            
            # Check it's still a valid image
            processed_img = Image.open(io.BytesIO(optimized_image))
            assert processed_img.mode == 'RGB'
            
            # The processor should adjust aspect ratios to be within Instagram limits
            proc_width, proc_height = processed_img.size
            aspect_ratio = proc_width / proc_height
            # Allow for some tolerance due to processing adjustments
            assert INSTAGRAM_MIN_ASPECT_RATIO <= aspect_ratio <= INSTAGRAM_MAX_ASPECT_RATIO or (
                # Original had valid dimensions and processor may not need to adjust
                abs(aspect_ratio - (width/height)) < 0.01 and 
                INSTAGRAM_MIN_RESOLUTION <= min(proc_width, proc_height) and
                max(proc_width, proc_height) <= INSTAGRAM_MAX_RESOLUTION
            )

    def test_error_handling_invalid_data(self):
        """Test error handling with invalid image data."""
        with pytest.raises(ValueError, match="Error processing image"):
            ImageProcessor.optimize_for_instagram(b'invalid image data')
        
        with pytest.raises(ValueError, match="Error cropping image"):
            ImageProcessor.crop_to_aspect_ratio(b'invalid image data', 1.0)
        
        with pytest.raises(ValueError, match="Error adding border"):
            ImageProcessor.add_border(b'invalid image data')

    def test_error_handling_empty_data(self):
        """Test error handling with empty data."""
        with pytest.raises(ValueError):
            ImageProcessor.optimize_for_instagram(b'')

    def test_get_image_info_invalid_data(self):
        """Test image info with invalid data."""
        info = ImageProcessor.get_image_info(b'invalid')
        assert 'error' in info

    def test_real_world_scenarios(self):
        """Test with real-world image scenarios using generated test images."""
        test_image_dir = 'test_images/before'
        if os.path.exists(test_image_dir):
            for filename in os.listdir(test_image_dir):
                if filename.endswith('.jpg'):
                    filepath = os.path.join(test_image_dir, filename)
                    with open(filepath, 'rb') as f:
                        image_data = f.read()
                    
                    try:
                        # Test optimization
                        optimized = ImageProcessor.optimize_for_instagram(image_data)
                        
                        # Save result
                        save_processed_image(optimized, f'processed_{filename}')
                        
                        # Verify it's valid
                        processed_img = Image.open(io.BytesIO(optimized))
                        assert processed_img.mode == 'RGB'
                        
                        # Test info gathering
                        info = ImageProcessor.get_image_info(optimized)
                        assert 'width' in info
                        assert 'height' in info
                        
                    except Exception as e:
                        # Some test images are intentionally invalid
                        if 'invalid' not in filename.lower():
                            raise e

if __name__ == "__main__":
    pytest.main([__file__, "-v"])