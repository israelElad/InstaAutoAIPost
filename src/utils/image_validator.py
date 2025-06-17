from PIL import Image
import io
from ..config import (
    INSTAGRAM_MIN_ASPECT_RATIO,
    INSTAGRAM_MAX_ASPECT_RATIO,
    INSTAGRAM_MIN_RESOLUTION,
    INSTAGRAM_MAX_RESOLUTION,
    INSTAGRAM_MAX_FILE_SIZE_MB
)

class ImageValidationError(Exception):
    """Custom exception for image validation errors."""
    pass

def validate_image(image_data: bytes) -> bool:
    """
    Validate if the image meets Instagram requirements.
    
    Args:
        image_data (bytes): The image data to validate
        
    Returns:
        bool: True if the image meets all requirements
        
    Raises:
        ImageValidationError: If the image doesn't meet requirements
    """
    try:
        # Check file size
        if len(image_data) > INSTAGRAM_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ImageValidationError(f"Image size exceeds {INSTAGRAM_MAX_FILE_SIZE_MB}MB limit")
        
        # Open image and get dimensions
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        
        # Check minimum resolution
        if width < INSTAGRAM_MIN_RESOLUTION or height < INSTAGRAM_MIN_RESOLUTION:
            raise ImageValidationError(f"Image resolution below minimum {INSTAGRAM_MIN_RESOLUTION}x{INSTAGRAM_MIN_RESOLUTION}")
        
        # Check maximum resolution
        if width > INSTAGRAM_MAX_RESOLUTION or height > INSTAGRAM_MAX_RESOLUTION:
            raise ImageValidationError(f"Image resolution exceeds maximum {INSTAGRAM_MAX_RESOLUTION}x{INSTAGRAM_MAX_RESOLUTION}")
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio < INSTAGRAM_MIN_ASPECT_RATIO or aspect_ratio > INSTAGRAM_MAX_ASPECT_RATIO:
            raise ImageValidationError(
                f"Image aspect ratio {aspect_ratio:.2f} outside allowed range "
                f"[{INSTAGRAM_MIN_ASPECT_RATIO:.2f}, {INSTAGRAM_MAX_ASPECT_RATIO:.2f}]"
            )
        
        return True
        
    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(f"Error validating image: {str(e)}") 