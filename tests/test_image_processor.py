import pytest
import io
from PIL import Image
from src.utils.image_processor import ImageProcessor
from src.utils.image_validator import ImageValidationError

class TestImageProcessor:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
    
    def create_test_image(self, width: int, height: int, format: str = 'JPEG') -> bytes:
        """Create a test image with specified dimensions."""
        image = Image.new('RGB', (width, height), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
    
    def test_process_image_within_limits(self):
        """Test processing an image that's already within Instagram limits."""
        # Create a 1000x1000 image (within limits)
        original_data = self.create_test_image(1000, 1000)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that the image was processed
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.size == (1000, 1000)  # Should remain the same
        assert processed_image.mode == 'RGB'
    
    def test_process_image_too_large(self):
        """Test processing an image that's too large."""
        # Create a 2000x2000 image (exceeds max resolution)
        original_data = self.create_test_image(2000, 2000)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that the image was resized
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.size[0] <= self.processor.MAX_RESOLUTION
        assert processed_image.size[1] <= self.processor.MAX_RESOLUTION
        assert processed_image.mode == 'RGB'
    
    def test_process_image_too_small(self):
        """Test processing an image that's too small."""
        # Create a 100x100 image (below minimum resolution)
        original_data = self.create_test_image(100, 100)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that the image was scaled up
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.size[0] >= self.processor.MIN_RESOLUTION
        assert processed_image.size[1] >= self.processor.MIN_RESOLUTION
        assert processed_image.mode == 'RGB'
    
    def test_process_image_wrong_aspect_ratio_tall(self):
        """Test processing an image that's too tall (aspect ratio < 0.8)."""
        # Create a 500x1000 image (aspect ratio 0.5, too tall)
        original_data = self.create_test_image(500, 1000)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that padding was added
        processed_image = Image.open(io.BytesIO(processed_data))
        aspect_ratio = processed_image.size[0] / processed_image.size[1]
        assert aspect_ratio >= self.processor.MIN_ASPECT_RATIO
        assert processed_image.mode == 'RGB'
    
    def test_process_image_wrong_aspect_ratio_wide(self):
        """Test processing an image that's too wide (aspect ratio > 1.91)."""
        # Create a 2000x500 image (aspect ratio 4.0, too wide)
        original_data = self.create_test_image(2000, 500)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that padding was added
        processed_image = Image.open(io.BytesIO(processed_data))
        aspect_ratio = processed_image.size[0] / processed_image.size[1]
        
        # Use tolerance for floating point comparison
        tolerance = 0.01
        assert aspect_ratio <= (self.processor.MAX_ASPECT_RATIO + tolerance), f"Aspect ratio {aspect_ratio:.6f} exceeds limit {self.processor.MAX_ASPECT_RATIO}"
        assert processed_image.mode == 'RGB'
    
    def test_process_image_non_rgb(self):
        """Test processing a non-RGB image."""
        # Create a grayscale image
        image = Image.new('L', (1000, 1000), color=128)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        original_data = buffer.getvalue()
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that it was converted to RGB
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.mode == 'RGB'
    
    def test_process_image_png_format(self):
        """Test processing a PNG image."""
        # Create a PNG image
        image = Image.new('RGB', (1000, 1000), color=(0, 255, 0))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        original_data = buffer.getvalue()
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that it was processed correctly
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.mode == 'RGB'
        assert processed_image.size == (1000, 1000)
    
    def test_process_image_invalid_data(self):
        """Test processing invalid image data."""
        invalid_data = b"not an image"
        
        with pytest.raises(ImageValidationError):
            self.processor.process_image(invalid_data)
    
    def test_file_size_optimization(self):
        """Test that large images are optimized for file size."""
        # Create a large image that might exceed file size limits
        # This is a simplified test - in practice, you'd need a very large image
        original_data = self.create_test_image(1440, 1440)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that the processed image is not empty
        assert len(processed_data) > 0
        
        # Check that file size is reasonable (should be under 8MB)
        file_size_mb = len(processed_data) / (1024 * 1024)
        assert file_size_mb <= self.processor.MAX_FILE_SIZE_MB
    
    def test_preserve_aspect_ratio(self):
        """Test that aspect ratio is preserved when possible."""
        # Create a 1200x800 image (aspect ratio 1.5)
        original_data = self.create_test_image(1200, 800)
        
        processed_data = self.processor.process_image(original_data)
        
        # Check that aspect ratio is preserved
        processed_image = Image.open(io.BytesIO(processed_data))
        original_ratio = 1200 / 800
        processed_ratio = processed_image.size[0] / processed_image.size[1]
        
        # Allow for small rounding differences
        assert abs(original_ratio - processed_ratio) < 0.01 