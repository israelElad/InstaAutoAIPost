import io
from PIL import Image, ImageOps
import logging
from typing import Tuple, Optional
from .image_validator import ImageValidationError

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image processing to make images Instagram-compliant."""
    
    # Instagram requirements
    MAX_RESOLUTION = 1440
    MIN_RESOLUTION = 320
    MAX_ASPECT_RATIO = 1.91
    MIN_ASPECT_RATIO = 0.8
    MAX_FILE_SIZE_MB = 8
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_image(self, image_data: bytes) -> bytes:
        """
        Process an image to make it Instagram-compliant.
        
        Args:
            image_data (bytes): Raw image data
            
        Returns:
            bytes: Processed image data that meets Instagram requirements
            
        Raises:
            ImageValidationError: If image cannot be processed to meet requirements
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            self.logger.info(f"Processing image: {image.format} {image.size} {image.mode}")
            
            # Convert to RGB if necessary (Instagram requires RGB)
            if image.mode != 'RGB':
                self.logger.info(f"Converting image from {image.mode} to RGB")
                image = image.convert('RGB')
            
            # Process the image
            processed_image = self._resize_image(image)
            
            # Save to bytes with maximum quality (we have plenty of room within 8MB limit)
            output_buffer = io.BytesIO()
            processed_image.save(output_buffer, format='JPEG', quality=100, optimize=True)
            processed_data = output_buffer.getvalue()
            
            # Check file size
            file_size_mb = len(processed_data) / (1024 * 1024)
            self.logger.info(f"Processed image size: {file_size_mb:.2f} MB")
            
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                # Try with lower quality
                self.logger.info("File too large, reducing quality...")
                processed_data = self._reduce_quality(processed_image)
            
            self.logger.info("Image processing completed successfully")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            raise ImageValidationError(f"Failed to process image: {str(e)}")
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image to meet Instagram requirements while preserving aspect ratio.
        
        Args:
            image (Image.Image): PIL Image object
            
        Returns:
            Image.Image: Resized image
        """
        width, height = image.size
        aspect_ratio = width / height
        
        self.logger.info(f"Original dimensions: {width}x{height}, aspect ratio: {aspect_ratio:.3f}")
        
        # Calculate target dimensions
        target_width, target_height = self._calculate_target_dimensions(width, height, aspect_ratio)
        
        self.logger.info(f"Target dimensions: {target_width}x{target_height}")
        
        # Resize image
        resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Add white padding if aspect ratio is too extreme
        final_image = self._add_padding_if_needed(resized_image)
        
        return final_image
    
    def _calculate_target_dimensions(self, width: int, height: int, aspect_ratio: float) -> Tuple[int, int]:
        """
        Calculate optimal dimensions that meet Instagram requirements.
        
        Args:
            width (int): Original width
            height (int): Original height
            aspect_ratio (float): Original aspect ratio
            
        Returns:
            Tuple[int, int]: Target width and height
        """
        self.logger.info(f"Calculating target dimensions for {width}x{height} (aspect ratio: {aspect_ratio:.3f})")
        
        # Start with original dimensions
        new_width, new_height = width, height
        
        # If image is too large, scale down to fit within max resolution
        if width > self.MAX_RESOLUTION or height > self.MAX_RESOLUTION:
            scale_factor = min(self.MAX_RESOLUTION / width, self.MAX_RESOLUTION / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            self.logger.info(f"Scaled down to {new_width}x{new_height} (scale factor: {scale_factor:.3f})")
        
        # If image is too small, scale up to meet minimum resolution
        if new_width < self.MIN_RESOLUTION or new_height < self.MIN_RESOLUTION:
            min_scale = max(self.MIN_RESOLUTION / new_width, self.MIN_RESOLUTION / new_height)
            new_width = int(new_width * min_scale)
            new_height = int(new_height * min_scale)
            self.logger.info(f"Scaled up to {new_width}x{new_height} (min scale factor: {min_scale:.3f})")
        
        # Check if final dimensions are within Instagram limits
        if (new_width <= self.MAX_RESOLUTION and new_height <= self.MAX_RESOLUTION and 
            self.MIN_ASPECT_RATIO <= (new_width / new_height) <= self.MAX_ASPECT_RATIO):
            self.logger.info("Final dimensions are within Instagram limits")
        else:
            self.logger.info("Final dimensions need padding (will be handled by _add_padding_if_needed)")
        
        self.logger.info(f"Final target dimensions: {new_width}x{new_height}")
        return new_width, new_height
    
    def _add_padding_if_needed(self, image: Image.Image) -> Image.Image:
        """
        Add white padding if aspect ratio is too extreme.
        
        Args:
            image (Image.Image): Image to process
            
        Returns:
            Image.Image: Image with padding if needed
        """
        width, height = image.size
        aspect_ratio = width / height
        
        # Use a small tolerance for aspect ratio comparison
        tolerance = 0.02
        if (self.MIN_ASPECT_RATIO - tolerance) <= aspect_ratio <= (self.MAX_ASPECT_RATIO + tolerance):
            return image
        
        self.logger.info(f"Aspect ratio {aspect_ratio:.3f} outside Instagram limits, adding padding")
        
        # Calculate padding needed
        if aspect_ratio < self.MIN_ASPECT_RATIO:
            # Too tall, add horizontal padding
            target_width = int(height * self.MIN_ASPECT_RATIO)
            padding_left = (target_width - width) // 2
            padding_right = target_width - width - padding_left
            padding_top = padding_bottom = 0
        else:
            # Too wide, add vertical padding
            target_height = int(width / self.MAX_ASPECT_RATIO)
            padding_top = (target_height - height) // 2
            padding_bottom = target_height - height - padding_top
            padding_left = padding_right = 0
        
        # Create new image with white background
        new_size = (width + padding_left + padding_right, height + padding_top + padding_bottom)
        new_image = Image.new('RGB', new_size, (255, 255, 255))
        
        # Paste original image
        new_image.paste(image, (padding_left, padding_top))
        
        # Verify the final aspect ratio
        final_aspect_ratio = new_image.size[0] / new_image.size[1]
        self.logger.info(f"Final aspect ratio after padding: {final_aspect_ratio:.3f}")
        
        # If still outside limits, adjust padding
        if final_aspect_ratio > self.MAX_ASPECT_RATIO:
            # Need more vertical padding
            target_height = int(new_image.size[0] / self.MAX_ASPECT_RATIO)
            additional_padding = target_height - new_image.size[1]
            padding_top += additional_padding // 2
            padding_bottom += additional_padding - (additional_padding // 2)
            
            # Create new image with adjusted padding
            new_size = (width + padding_left + padding_right, height + padding_top + padding_bottom)
            new_image = Image.new('RGB', new_size, (255, 255, 255))
            new_image.paste(image, (padding_left, padding_top))
        
        self.logger.info(f"Added padding: {padding_left},{padding_top},{padding_right},{padding_bottom}")
        return new_image
    
    def _reduce_quality(self, image: Image.Image) -> bytes:
        """
        Reduce image quality to meet file size requirements.
        
        Args:
            image (Image.Image): Image to compress
            
        Returns:
            bytes: Compressed image data
        """
        quality = 95
        while quality > 60:  # Don't go below 60% quality
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            data = output_buffer.getvalue()
            
            file_size_mb = len(data) / (1024 * 1024)
            self.logger.info(f"Quality {quality}%: {file_size_mb:.2f} MB")
            
            if file_size_mb <= self.MAX_FILE_SIZE_MB:
                return data
            
            quality -= 5
        
        # If still too large, resize further
        self.logger.warning("Quality reduction not sufficient, resizing further")
        width, height = image.size
        scale_factor = 0.9
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return self._reduce_quality(resized_image) 