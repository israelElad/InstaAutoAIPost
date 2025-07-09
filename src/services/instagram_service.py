from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError, ClientConnectionError
from ..config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
import io
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests
import json
import tempfile
import os
from pathlib import Path
import logging
import time
import random
from .ai_caption_service import GeminiCaptionService
from typing import Optional

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
        self.client.user_agent = self.USER_AGENT  # Set the user agent
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
        logger = logging.getLogger(__name__)
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
                    logger.info("⚠️ No EXIF data found in image")
                    return None
                
                logger.info(f"✅ EXIF data found with {len(exif_data)} tags")
                
                # Extract GPS data
                gps_data = {}
                for tag_id in exif_data:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exif_data[tag_id]
                    
                    if isinstance(tag, str) and tag.startswith('GPS'):
                        gps_data[tag] = data
                        logger.info(f"📍 Found GPS tag: {tag} = {data}")
                
                if not gps_data:
                    logger.info("⚠️ No GPS data found in EXIF")
                    return None
                
                logger.info(f"✅ Found {len(gps_data)} GPS tags")
                
                # Convert GPS coordinates to decimal degrees
                location = self._convert_gps_to_decimal(gps_data)
                if location:
                    logger.info(f"📍 Converted GPS coordinates: {location['lat']:.6f}, {location['lng']:.6f}")
                    return {
                        'lat': location['lat'],
                        'lng': location['lng'],
                        'name': f"GPS Location ({location['lat']:.4f}, {location['lng']:.4f})"
                    }
                else:
                    logger.warning("⚠️ Failed to convert GPS coordinates to decimal degrees")
                
                return None
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
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

    def get_instagram_location_name_and_obj(self, lat, lng):
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"🔍 Searching Instagram locations for coordinates: {lat:.6f}, {lng:.6f}")
            locations = self.client.location_search(lat, lng)
            if locations:
                location = locations[0]
                logger.info(f"✅ Found Instagram location: {location.name} (ID: {location.pk})")
                return location.name, location
            else:
                logger.info("⚠️ No Instagram locations found for these coordinates")
        except Exception as e:
            logger.warning(f"⚠️ Failed to find Instagram location: {e}")
        return None, None

    def _extract_location_for_caption(self, image_data: bytes):
        logger = logging.getLogger(__name__)
        logger.info("🔍 Starting location extraction process...")
        
        location = self._extract_location_from_exif(image_data)
        if location and 'lat' in location and 'lng' in location:
            logger.info(f"📍 GPS coordinates extracted: {location['lat']:.6f}, {location['lng']:.6f}")
            name, loc_obj = self.get_instagram_location_name_and_obj(location['lat'], location['lng'])
            if name:
                location['name'] = name
                logger.info(f"✅ Final location name: {name}")
            else:
                logger.info("⚠️ Could not find Instagram location name, using GPS coordinates")
            location['insta_obj'] = loc_obj
        else:
            logger.info("⚠️ No location data extracted from image")
        return location

    def post_image(self, image_data: bytes, caption: Optional[str] = None) -> bool:
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
            # Extract location from EXIF and Instagram
            location = self._extract_location_for_caption(image_data)
            
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
                    kwargs = {
                        'caption': caption,
                        'extra_data': {
                            "custom_accessibility_caption": "",
                            "like_and_view_counts_disabled": "0",
                            "disable_comments": "0",
                        }
                    }
                    if location and location.get('insta_obj'):
                        kwargs['location'] = location['insta_obj']
                    return self.client.photo_upload(Path(temp_file_path), **kwargs)
                
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

def generate_instagram_caption(image_path: str, metadata: dict) -> str:
    ai_service = GeminiCaptionService()
    result = ai_service.generate_caption(image_path, metadata)
    # Only return Hebrew caption with hashtags
    caption = f"{result['he']}\n{result['hashtags']}"
    return caption

# Example test function for local testing (does not post to Instagram)
def test_generate_captions_for_photos(photo_dir: str, metadata_func=None):
    if not isinstance(photo_dir, str) or not photo_dir:
        print("Invalid photo_dir argument. Must be a non-empty string.")
        return
    photos = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    photos = [f for f in photos if isinstance(f, str) and f]
    if len(photos) > 3:
        photos = random.sample(photos, 3)
    for photo in photos:
        image_path = os.path.join(photo_dir, photo)
        if not isinstance(image_path, str) or not image_path or not os.path.isfile(image_path):
            continue
        # Extract location for caption
        with open(image_path, 'rb') as f:
            image_data = f.read()
        service = InstagramService()
        location = service._extract_location_for_caption(image_data)
        location_name = location['name'] if location and 'name' in location else 'Unknown'
        metadata = metadata_func(photo) if metadata_func else {'location': location_name}
        assert isinstance(image_path, str) and image_path, "image_path must be a non-empty string"
        caption = generate_instagram_caption(image_path, metadata)
        print(f"Photo: {photo}\nLocation: {location_name}\nCaption:\n{caption}\n{'-'*40}") 

# Safe test function that doesn't initialize InstagramService
def safe_test_generate_captions_for_photos(photo_dir: str, metadata_func=None):
    """
    Safe test function that only tests caption generation and EXIF extraction.
    Does NOT initialize InstagramService to avoid any Instagram API calls.
    """
    if not isinstance(photo_dir, str) or not photo_dir:
        print("Invalid photo_dir argument. Must be a non-empty string.")
        return
    
    if not os.path.exists(photo_dir):
        print(f"Directory {photo_dir} does not exist.")
        return
    
    photos = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    photos = [f for f in photos if isinstance(f, str) and f]
    
    if not photos:
        print(f"No image files found in {photo_dir}")
        return
    
    if len(photos) > 3:
        photos = random.sample(photos, 3)
    
    print(f"Testing {len(photos)} photos from {photo_dir}...")
    print("=" * 60)
    
    for photo in photos:
        image_path = os.path.join(photo_dir, photo)
        if not isinstance(image_path, str) or not image_path or not os.path.isfile(image_path):
            continue
        
        print(f"\n📸 Photo: {photo}")
        print("-" * 40)
        
        # Extract location from EXIF only (no Instagram API calls)
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Extract location from EXIF using standalone function
            location = extract_location_from_exif_standalone(image_data)
            location_name = 'Unknown'
            
            if location and 'lat' in location and 'lng' in location:
                print(f"📍 GPS Coordinates: {location['lat']:.6f}, {location['lng']:.6f}")
                location_name = f"GPS Location ({location['lat']:.4f}, {location['lng']:.4f})"
                print(f"📍 Location Name: {location_name}")
            else:
                print("⚠️ No GPS data found in EXIF")
            
            # Generate caption
            metadata = metadata_func(photo) if metadata_func else {'location': location_name}
            caption_result = generate_instagram_caption(image_path, metadata)
            
            print(f"\n📝 Generated Caption:")
            print(caption_result)
            
        except Exception as e:
            print(f"❌ Error processing {photo}: {e}")
        
        print("=" * 60)

def extract_location_from_exif_standalone(image_data: bytes):
    """
    Standalone function to extract GPS location from image EXIF data.
    Does not require InstagramService initialization.
    """
    logger = logging.getLogger(__name__)
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
                logger.info("No EXIF data found in image")
                return None
            
            logger.info(f"EXIF data found with {len(exif_data)} tags")
            
            # Extract GPS data - handle nested GPSInfo IFD
            gps_data = {}
            
            # Try to get nested GPS info using IFD
            try:
                gps_info = exif_data.get_ifd(0x8825)  # GPSInfo IFD
                if gps_info:
                    logger.info(f"Found GPSInfo IFD with {len(gps_info)} tags")
                    # Store GPS data with tag IDs as keys
                    for tag_id in gps_info:
                        gps_data[tag_id] = gps_info[tag_id]
                        tag_name = GPSTAGS.get(tag_id, f"GPS{tag_id}")
                        logger.info(f"Found GPS tag: {tag_name} ({tag_id}) = {gps_info[tag_id]}")
            except Exception as e:
                logger.warning(f"Failed to access GPSInfo IFD: {e}")
            
            if not gps_data:
                logger.info("No GPS data found in EXIF")
                return None
            
            logger.info(f"Found {len(gps_data)} GPS tags total")
            
            # Convert GPS coordinates to decimal degrees
            location = convert_gps_to_decimal_standalone(gps_data)
            if location:
                logger.info(f"Converted GPS coordinates: {location['lat']:.6f}, {location['lng']:.6f}")
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'name': f"GPS Location ({location['lat']:.4f}, {location['lng']:.4f})"
                }
            else:
                logger.warning("Failed to convert GPS coordinates to decimal degrees")
            
            return None
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.warning(f"Failed to extract location from EXIF: {e}")
        return None

def convert_gps_to_decimal_standalone(gps_data):
    """Convert GPS coordinates to decimal degrees (standalone version)."""
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Processing GPS data: {gps_data}")
        
        # Extract latitude - use tag IDs directly
        gps_lat = gps_data.get(2)  # GPSLatitude
        gps_lat_ref = gps_data.get(1)  # GPSLatitudeRef
        gps_lon = gps_data.get(4)  # GPSLongitude  
        gps_lon_ref = gps_data.get(3)  # GPSLongitudeRef
        
        logger.info(f"Latitude data: {gps_lat}, ref: {gps_lat_ref}")
        logger.info(f"Longitude data: {gps_lon}, ref: {gps_lon_ref}")
        
        if gps_lat and gps_lat_ref:
            lat = convert_dms_to_decimal_standalone(gps_lat)
            if lat is not None and gps_lat_ref == 'S':
                lat = -lat
            logger.info(f"Converted latitude: {lat}")
        else:
            logger.warning("Missing GPSLatitude or GPSLatitudeRef")
            return None
        
        if gps_lon and gps_lon_ref:
            lon = convert_dms_to_decimal_standalone(gps_lon)
            if lon is not None and gps_lon_ref == 'W':
                lon = -lon
            logger.info(f"Converted longitude: {lon}")
        else:
            logger.warning("Missing GPSLongitude or GPSLongitudeRef")
            return None
        
        return {'lat': lat, 'lng': lon}
        
    except Exception as e:
        logger.error(f"Failed to convert GPS coordinates: {e}")
        return None

def convert_dms_to_decimal_standalone(dms):
    """Convert degrees, minutes, seconds to decimal degrees (standalone version)."""
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Converting DMS: {dms} (type: {type(dms)})")
        
        if isinstance(dms, (list, tuple)):
            if len(dms) >= 3:
                degrees = float(dms[0])
                minutes = float(dms[1])
                seconds = float(dms[2])
            else:
                logger.error(f"DMS data too short: {dms}")
                return None
        elif isinstance(dms, str):
            parts = dms.split(',')
            if len(parts) >= 3:
                degrees = float(parts[0].strip())
                minutes = float(parts[1].strip())
                seconds = float(parts[2].strip())
            else:
                logger.error(f"Cannot parse DMS string: {dms}")
                return None
        else:
            logger.error(f"Unsupported DMS data type: {type(dms)}")
            return None
        
        result = degrees + (minutes / 60.0) + (seconds / 3600.0)
        logger.info(f"DMS {dms} -> decimal {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error converting DMS {dms}: {e}")
        return None 