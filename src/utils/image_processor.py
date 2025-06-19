from PIL import Image, ImageEnhance, ImageFilter
import io
from typing import Tuple, Optional
from ..config import (
    INSTAGRAM_MIN_ASPECT_RATIO,
    INSTAGRAM_MAX_ASPECT_RATIO,
    INSTAGRAM_MIN_RESOLUTION,
    INSTAGRAM_MAX_RESOLUTION,
    INSTAGRAM_MAX_FILE_SIZE_MB
)

class ImageProcessor:
    """Image processing utilities for Instagram optimization."""
    
    @staticmethod
    def optimize_for_instagram(image_data: bytes, target_quality: int = 85) -> bytes:
        """
        Optimize an image for Instagram posting requirements.
        
        Args:
            image_data (bytes): Original image data
            target_quality (int): JPEG quality (1-100)
            
        Returns:
            bytes: Optimized image data
            
        Raises:
            ValueError: If image cannot be processed
        """
        try:
            # Open the image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if needed
            image = ImageProcessor._resize_for_instagram(image)
            
            # Apply basic enhancements
            image = ImageProcessor._enhance_image(image)
            
            # Save with optimization
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=target_quality, optimize=True)
            
            # Check file size and reduce quality if needed
            output_data = output.getvalue()
            max_size_bytes = INSTAGRAM_MAX_FILE_SIZE_MB * 1024 * 1024
            
            if len(output_data) > max_size_bytes:
                output_data = ImageProcessor._reduce_file_size(image, max_size_bytes)
            
            return output_data
            
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    
    @staticmethod
    def _resize_for_instagram(image: Image.Image) -> Image.Image:
        """
        Resize image to meet Instagram requirements.
        
        Args:
            image: PIL Image object
            
        Returns:
            Image.Image: Resized image
        """
        width, height = image.size
        aspect_ratio = width / height
        
        # Check if resize is needed
        needs_resize = (
            width > INSTAGRAM_MAX_RESOLUTION or 
            height > INSTAGRAM_MAX_RESOLUTION or
            width < INSTAGRAM_MIN_RESOLUTION or 
            height < INSTAGRAM_MIN_RESOLUTION
        )
        
        if not needs_resize:
            return image
        
        # Calculate new dimensions
        if width > height:  # Landscape
            if width > INSTAGRAM_MAX_RESOLUTION:
                new_width = INSTAGRAM_MAX_RESOLUTION
                new_height = int(new_width / aspect_ratio)
            elif width < INSTAGRAM_MIN_RESOLUTION:
                new_width = INSTAGRAM_MIN_RESOLUTION
                new_height = int(new_width / aspect_ratio)
            else:
                new_width, new_height = width, height
        else:  # Portrait or square
            if height > INSTAGRAM_MAX_RESOLUTION:
                new_height = INSTAGRAM_MAX_RESOLUTION
                new_width = int(new_height * aspect_ratio)
            elif height < INSTAGRAM_MIN_RESOLUTION:
                new_height = INSTAGRAM_MIN_RESOLUTION
                new_width = int(new_height * aspect_ratio)
            else:
                new_width, new_height = width, height
        
        # Ensure minimum dimensions
        new_width = max(new_width, INSTAGRAM_MIN_RESOLUTION)
        new_height = max(new_height, INSTAGRAM_MIN_RESOLUTION)
        
        # Resize with high quality
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def _enhance_image(image: Image.Image) -> Image.Image:
        """
        Apply basic image enhancements.
        
        Args:
            image: PIL Image object
            
        Returns:
            Image.Image: Enhanced image
        """
        # Slightly enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)  # 10% contrast boost
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)  # 10% sharpness boost
        
        return image
    
    @staticmethod
    def _reduce_file_size(image: Image.Image, max_size_bytes: int) -> bytes:
        """
        Reduce image file size by adjusting quality.
        
        Args:
            image: PIL Image object
            max_size_bytes: Maximum file size in bytes
            
        Returns:
            bytes: Compressed image data
        """
        quality = 85
        min_quality = 30
        
        while quality >= min_quality:
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            if len(output.getvalue()) <= max_size_bytes:
                return output.getvalue()
            
            quality -= 5
        
        # If still too large, resize the image
        width, height = image.size
        scale_factor = 0.9
        
        while True:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            if new_width < INSTAGRAM_MIN_RESOLUTION or new_height < INSTAGRAM_MIN_RESOLUTION:
                break
            
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            resized_image.save(output, format='JPEG', quality=min_quality, optimize=True)
            
            if len(output.getvalue()) <= max_size_bytes:
                return output.getvalue()
            
            scale_factor -= 0.1
            if scale_factor <= 0.1:
                break
        
        # Return the smallest possible image
        output = io.BytesIO()
        resized_image.save(output, format='JPEG', quality=min_quality, optimize=True)
        return output.getvalue()
    
    @staticmethod
    def crop_to_aspect_ratio(image_data: bytes, target_ratio: float) -> bytes:
        """
        Crop image to a specific aspect ratio.
        
        Args:
            image_data (bytes): Original image data
            target_ratio (float): Target aspect ratio (width/height)
            
        Returns:
            bytes: Cropped image data
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            current_ratio = width / height
            
            if abs(current_ratio - target_ratio) < 0.01:
                # Already close to target ratio
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=85)
                return output.getvalue()
            
            if current_ratio > target_ratio:
                # Image is too wide, crop horizontally
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                crop_box = (left, 0, left + new_width, height)
            else:
                # Image is too tall, crop vertically
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                crop_box = (0, top, width, top + new_height)
            
            cropped_image = image.crop(crop_box)
            
            output = io.BytesIO()
            cropped_image.save(output, format='JPEG', quality=85)
            return output.getvalue()
            
        except Exception as e:
            raise ValueError(f"Error cropping image: {str(e)}")
    
    @staticmethod
    def add_border(image_data: bytes, border_size: int = 10, border_color: str = 'white') -> bytes:
        """
        Add a border to the image.
        
        Args:
            image_data (bytes): Original image data
            border_size (int): Border size in pixels
            border_color (str): Border color
            
        Returns:
            bytes: Image with border
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Create new image with border
            new_width = image.width + 2 * border_size
            new_height = image.height + 2 * border_size
            
            bordered_image = Image.new('RGB', (new_width, new_height), border_color)
            bordered_image.paste(image, (border_size, border_size))
            
            output = io.BytesIO()
            bordered_image.save(output, format='JPEG', quality=85)
            return output.getvalue()
            
        except Exception as e:
            raise ValueError(f"Error adding border: {str(e)}")
    
    @staticmethod
    def get_image_info(image_data: bytes) -> dict:
        """
        Get information about an image.
        
        Args:
            image_data (bytes): Image data
            
        Returns:
            dict: Image information
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            return {
                'width': width,
                'height': height,
                'aspect_ratio': width / height,
                'format': image.format,
                'mode': image.mode,
                'file_size_bytes': len(image_data),
                'file_size_mb': len(image_data) / (1024 * 1024),
                'meets_instagram_requirements': ImageProcessor._check_instagram_compliance(image_data)
            }
            
        except Exception as e:
            return {'error': f"Error analyzing image: {str(e)}"}
    
    @staticmethod
    def _check_instagram_compliance(image_data: bytes) -> dict:
        """
        Check if image meets Instagram requirements.
        
        Args:
            image_data (bytes): Image data
            
        Returns:
            dict: Compliance status
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            aspect_ratio = width / height
            file_size_mb = len(image_data) / (1024 * 1024)
            
            compliance = {
                'resolution_ok': (
                    width >= INSTAGRAM_MIN_RESOLUTION and 
                    height >= INSTAGRAM_MIN_RESOLUTION and
                    width <= INSTAGRAM_MAX_RESOLUTION and 
                    height <= INSTAGRAM_MAX_RESOLUTION
                ),
                'aspect_ratio_ok': (
                    INSTAGRAM_MIN_ASPECT_RATIO <= aspect_ratio <= INSTAGRAM_MAX_ASPECT_RATIO
                ),
                'file_size_ok': file_size_mb <= INSTAGRAM_MAX_FILE_SIZE_MB,
                'overall_compliant': False
            }
            
            compliance['overall_compliant'] = all([
                compliance['resolution_ok'],
                compliance['aspect_ratio_ok'],
                compliance['file_size_ok']
            ])
            
            return compliance
            
        except Exception:
            return {
                'resolution_ok': False,
                'aspect_ratio_ok': False,
                'file_size_ok': False,
                'overall_compliant': False,
                'error': True
            }