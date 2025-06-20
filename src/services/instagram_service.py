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
import logging

class InstagramService:
    SESSION_FILE = os.environ.get("INSTAGRAM_SESSION_FILE", "session.json")
    PROXY = os.environ.get("INSTAGRAM_PROXY")
    DELAY_RANGE = [1, 3]

    def __init__(self):
        """Initialize Instagram client and login with best practices."""
        self.client = Client()
        self.client.delay_range = self.DELAY_RANGE
        if self.PROXY:
            self.client.set_proxy(self.PROXY)
        self._login()

    def _login(self):
        """Login to Instagram using persistent session if available."""
        logger = logging.getLogger(__name__)
        session_loaded = False
        # Try to load session settings if available
        if os.path.exists(self.SESSION_FILE):
            try:
                self.client.load_settings(self.SESSION_FILE)
                self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                # Check if session is valid
                try:
                    self.client.get_timeline_feed()
                    session_loaded = True
                    logger.info("Instagram session loaded and valid.")
                except LoginRequired:
                    logger.info("Session invalid, re-logging in with username/password.")
                    old_settings = self.client.get_settings()
                    self.client.set_settings({})
                    if "uuids" in old_settings:
                        self.client.set_uuids(old_settings["uuids"])
                    self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    logger.info("Logged in with username/password after session invalid.")
            except Exception as e:
                logger.warning(f"Couldn't login using session: {e}")
        if not session_loaded:
            try:
                self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                logger.info("Logged in with username/password.")
            except Exception as e:
                logger.error(f"Failed to login to Instagram: {e}")
                raise Exception(f"Failed to login to Instagram: {str(e)}")
        # Always dump settings after successful login
        try:
            self.client.dump_settings(self.SESSION_FILE)
        except Exception as e:
            logger.warning(f"Failed to save Instagram session: {e}")

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