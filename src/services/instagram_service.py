from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from ..config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
import io
from PIL import Image
import requests
import json

class InstagramService:
    def __init__(self):
        """Initialize Instagram client and login."""
        self.client = Client()
        self._login()

    def _login(self):
        """Login to Instagram."""
        try:
            self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        except LoginRequired as e:
            raise Exception(f"Failed to login to Instagram: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during Instagram login: {str(e)}")

    def _generate_caption(self, image_data: bytes) -> str:
        """
        Generate a caption for the image using a free AI service.
        This is a placeholder that uses a simple template.
        In a real implementation, you would integrate with an AI service.
        
        Args:
            image_data (bytes): The image data
            
        Returns:
            str: Generated caption
        """
        # TODO: Implement AI caption generation
        return "Check out this amazing photo! 📸 #photography #instagood"

    def post_image(self, image_data: bytes) -> bool:
        """
        Post an image to Instagram.
        
        Args:
            image_data (bytes): The image data to post
            
        Returns:
            bool: True if posting was successful
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Generate caption
            caption = self._generate_caption(image_data)
            
            # Upload photo
            media = self.client.photo_upload(
                image,
                caption=caption
            )
            
            return True
            
        except ClientError as e:
            raise Exception(f"Instagram API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error posting to Instagram: {str(e)}")

    def validate_credentials(self) -> bool:
        """
        Validate Instagram credentials.
        
        Returns:
            bool: True if credentials are valid
        """
        try:
            self.client.get_timeline_feed()
            return True
        except Exception:
            return False 