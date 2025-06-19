from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from ..config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
import io
from PIL import Image
import requests
import json
import tempfile
import os
from pathlib import Path

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
            # Save image data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            try:
                # Generate caption
                caption = self._generate_caption(image_data)
                
                # Upload photo using file path
                media = self.client.photo_upload(
                    Path(temp_file_path),
                    caption=caption
                )
                
                return True
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
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