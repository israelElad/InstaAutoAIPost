from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError, ClientConnectionError
from ..config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
import io
from PIL import Image
from PIL.ExifTags import TAGS
import requests
import json
import tempfile
import os
from pathlib import Path
import logging
import time
import random

class InstagramService:
    SESSION_FILE = os.environ.get("INSTAGRAM_SESSION_FILE", "session.json")
    PROXY = os.environ.get("INSTAGRAM_PROXY")
    DELAY_RANGE = [4, 8]  # Slightly different delays
    MAX_RETRIES = 3
    RETRY_DELAYS = [6, 18, 35]  # Different backoff delays
    
    # Samsung Galaxy S23 - realistic user agent for Israel
    USER_AGENT = "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"

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
                self.client.load_settings(Path(self.SESSION_FILE))
                self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                # Check if session is valid
                try:
                    self.client.get_timeline_feed()
                    session_loaded = True
                    logger.info("✅ Instagram session loaded and valid.")
                except LoginRequired:
                    logger.info("⚠️ Session invalid, re-logging in with username/password.")
                    old_settings = self.client.get_settings()
                    self.client.set_settings({})
                    if "uuids" in old_settings:
                        self.client.set_uuids(old_settings["uuids"])
                    self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    logger.info("✅ Logged in with username/password after session invalid.")
            except Exception as e:
                logger.warning(f"⚠️ Couldn't login using session: {e}")
        if not session_loaded:
            try:
                self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                logger.info("✅ Logged in with username/password.")
            except Exception as e:
                logger.error(f"❌ Failed to login to Instagram: {e}")
                raise Exception(f"Failed to login to Instagram: {str(e)}")
        # Always dump settings after successful login
        try:
            self.client.dump_settings(Path(self.SESSION_FILE))
            logger.info(f"✅ Session saved to: {self.SESSION_FILE}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save Instagram session: {e}")

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        logger = logging.getLogger(__name__)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Add random delay before each attempt
                if attempt > 0:
                    delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                    delay += random.uniform(0, 7)  # Different jitter range
                    logger.info(f"⏳ Retry attempt {attempt + 1}/{self.MAX_RETRIES}, waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                # Note: No user agent rotation - keeping consistent (more realistic)
                
                result = func(*args, **kwargs)
                return result
                
            except (ClientConnectionError, ClientError) as e:
                error_msg = str(e).lower()
                if "blacklist" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
                    logger.warning(f"⚠️ Rate limiting detected on attempt {attempt + 1}: {e}")
                    if attempt == self.MAX_RETRIES - 1:
                        raise Exception(f"Instagram rate limiting after {self.MAX_RETRIES} attempts: {e}")
                else:
                    logger.error(f"❌ Instagram API error on attempt {attempt + 1}: {e}")
                    if attempt == self.MAX_RETRIES - 1:
                        raise
            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    raise
        
        raise Exception(f"Failed after {self.MAX_RETRIES} attempts")

    def _extract_location_from_exif(self, image_data: bytes):
        """
        Extract GPS location from image EXIF data.
        
        Args:
            image_data (bytes): The image data
            
        Returns:
            dict: Location data with lat, lng, and name if available
        """
        try:
            # Create temporary file for PIL
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            try:
                # Open image and extract EXIF
                with Image.open(temp_file_path) as img:
                    # Use proper EXIF extraction method
                    exif_data = img.getexif() if hasattr(img, 'getexif') else None
                
                if not exif_data:
                    return None
                
                # Extract GPS data
                gps_data = {}
                for tag_id in exif_data:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exif_data[tag_id]
                    
                    if isinstance(tag, str) and tag.startswith('GPS'):
                        gps_data[tag] = data
                
                if not gps_data:
                    return None
                
                # Convert GPS coordinates to decimal degrees
                location = self._convert_gps_to_decimal(gps_data)
                if location:
                    return {
                        'lat': location['lat'],
                        'lng': location['lng'],
                        'name': f"GPS Location ({location['lat']:.4f}, {location['lng']:.4f})"
                    }
                
                return None
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ Failed to extract location from EXIF: {e}")
            return None

    def _convert_gps_to_decimal(self, gps_data):
        """Convert GPS coordinates to decimal degrees."""
        try:
            # Extract latitude
            if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                lat = self._convert_dms_to_decimal(gps_data['GPSLatitude'])
                if gps_data['GPSLatitudeRef'] == 'S':
                    lat = -lat
            else:
                return None
            
            # Extract longitude
            if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                lon = self._convert_dms_to_decimal(gps_data['GPSLongitude'])
                if gps_data['GPSLongitudeRef'] == 'W':
                    lon = -lon
            else:
                return None
            
            return {'lat': lat, 'lng': lon}
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to convert GPS coordinates: {e}")
            return None

    def _convert_dms_to_decimal(self, dms):
        """Convert degrees, minutes, seconds to decimal degrees."""
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        
        return degrees + (minutes / 60.0) + (seconds / 3600.0)

    def _generate_caption(self, image_data: bytes, location=None) -> str:
        """
        Generate a caption for the image with different style.
        
        Args:
            image_data (bytes): The image data
            location (dict): Location data if available
            
        Returns:
            str: Generated caption
        """
        # Different caption style to avoid detection patterns
        captions = [
            "Amazing moment captured! 📸✨ #photography #lifestyle",
            "Living life to the fullest! 🌟 #vibes #goodlife",
            "Beautiful memories made today! 💫 #memories #happy",
            "Another day, another adventure! 🚀 #adventure #explore",
            "Life is beautiful when you capture it! 📷 #beautiful #life",
            "Creating memories one photo at a time! 📸 #memories #photography",
            "Every picture tells a story! 📖 #story #photography",
            "Finding beauty in everyday moments! 🌸 #beauty #moments"
        ]
        
        caption = random.choice(captions)
        
        # Add location if available
        if location and isinstance(location, dict) and 'name' in location:
            caption += f"\n📍 {location['name']}"
            caption += " #location #travel"
        
        return caption

    def post_image(self, image_data: bytes, caption: str = None) -> bool:
        """
        Post an image to Instagram (public).
        
        Args:
            image_data (bytes): The image data to post
            caption (str): Optional caption for the post
            
        Returns:
            bool: True if posting was successful
        """
        # Ensure caption is a string
        final_caption = str(caption) if caption is not None else ""
        return self._post_image_internal(image_data, final_caption, is_private=False)

    def _post_image_internal(self, image_data: bytes, caption: str = "", is_private: bool = False) -> bool:
        """
        Internal method to post an image to Instagram.
        
        Args:
            image_data (bytes): The image data to post
            caption (str): Caption for the post (defaults to empty string)
            is_private (bool): Whether to post as private
            
        Returns:
            bool: True if posting was successful
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Extract location from EXIF if not provided
            location = self._extract_location_from_exif(image_data)
            
            # Generate caption if not provided
            if not caption:
                caption = self._generate_caption(image_data, location)
            
            # Ensure caption is a string
            if not isinstance(caption, str):
                caption = "Amazing moment captured! 📸✨ #photography #lifestyle"
            
            # Save image data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            try:
                # Use retry mechanism for posting
                def post_photo():
                    return self.client.photo_upload(
                        Path(temp_file_path),
                        caption=caption,
                        extra_data={
                            "custom_accessibility_caption": "",
                            "like_and_view_counts_disabled": "0",
                            "disable_comments": "0",
                        }
                    )
                
                # Upload photo with retry mechanism
                media = self._retry_with_backoff(post_photo)
                
                # Set privacy if needed
                if is_private:
                    try:
                        # For private posts, we need to handle this differently
                        # Since InstaGrapi doesn't have a direct is_private parameter,
                        # we'll just log that it was posted as public
                        logger.info("✅ Image posted as public (private posting not supported in current version)")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to set private mode: {e}")
                        logger.info("✅ Image posted as public")
                else:
                    logger.info("✅ Image posted as public")
                
                # Add location if available
                if location:
                    try:
                        # Try to find a nearby location on Instagram
                        locations = self.client.location_search(location['lat'], location['lng'])
                        if locations:
                            # Use the first (closest) location
                            closest_location = locations[0]
                            # Note: Location editing might not be supported in current version
                            logger.info(f"ℹ️ Location found: {closest_location.name} (location editing not implemented)")
                        else:
                            logger.info("ℹ️ No Instagram location found for GPS coordinates")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to add location: {e}")
                
                logger.info(f"✅ Successfully posted image to Instagram (ID: {media.id})")
                return True
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except ClientError as e:
            logger.error(f"❌ Instagram API error: {str(e)}")
            raise Exception(f"Instagram API error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error posting to Instagram: {str(e)}")
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

    def get_session_info(self) -> dict:
        """
        Get information about the current session.
        
        Returns:
            dict: Session information
        """
        try:
            session_file = self.SESSION_FILE
            session_exists = os.path.exists(session_file)
            
            info = {
                'session_file': session_file,
                'session_exists': session_exists,
                'user_id': self.client.user_id if hasattr(self.client, 'user_id') else None,
                'username': self.client.username if hasattr(self.client, 'username') else None,
            }
            
            if session_exists:
                file_size = os.path.getsize(session_file)
                file_mtime = os.path.getmtime(session_file)
                info.update({
                    'session_size': file_size,
                    'session_modified': file_mtime,
                })
            
            return info
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get session info: {e}")
            return {'error': str(e)} 