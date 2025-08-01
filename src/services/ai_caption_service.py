from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
import os
import threading
import time
from ..config import GEMINI_API_KEY # Import GEMINI_API_KEY from config

print("[Gemini] ai_caption_service.py loaded")
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
print("[Gemini] os imported")
import logging
print("[Gemini] logging imported")
try:
    from google import genai
    print("[Gemini] google.genai imported")
except ImportError:
    genai = None
    print("[Gemini] google.genai import failed")

logger = logging.getLogger(__name__)

class AICaptionService(ABC):
    @abstractmethod
    def generate_caption(self, image_path: str, metadata: Dict) -> Dict:
        """
        Generate captions and hashtags for an Instagram post.
        Returns a dict with keys: 'en', 'he', 'hashtags'.
        """
        pass

class GeminiCaptionService(AICaptionService):
    def __init__(self, api_key: Optional[str] = None):
        # Use API key from config if not provided directly
        self.api_key = api_key or GEMINI_API_KEY
        print(f"[Gemini] Loaded API key: {'FOUND' if self.api_key else 'NOT FOUND'}")
        if not self.api_key:
            logger.warning("Gemini API key not found. Set GEMINI_API_KEY in environment or config.")
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key) if self.api_key else None
            print("[Gemini] Client initialized successfully")
        except ImportError:
            self.client = None
            logger.error("google-genai package not installed. Run 'pip install google-genai'.")
        except Exception as e:
            self.client = None
            logger.error(f"Failed to initialize Gemini client: {e}")
        self.disclaimers = [
            "התמונות צולמו על ידי, בלי פילטרים או AI. התיאור? AI כתב לי! 😉",
            "אלה התמונות שלי מהמצלמה, אמיתיות לגמרי (בלי עזרת AI/פילטרים). התיאור הגיע מהבינה.",
            "התמונות? אני צילמתי, 100% טבעי. את התיאור ה-AI הכין לי.",
            "אני מאחורי העדשה, בלי פילטרים. התיאור? ה-AI עשה את הקסם.",
            "הצילומים צולמו על ידי, בלי התערבות של AI או פילטרים. התיאור זה AI לגמרי.",
            "תמונות שצילמתי כמו פעם, בלי עזרים. התיאור? החבר'ה מה-AI כתבו.",
            "רק אני והמצלמה, בלי AI ובלי פילטרים. התיאור זה כבר סיפור אחר (AI).",
            "מה שרואים צולם על ידי, נאמן למקור. התיאור באדיבות AI."
        ]
        self.disclaimer_index = 0

    def generate_caption(self, image_path: str, metadata: Dict) -> Dict:
        if not self.api_key or not self.client:
            print("[Gemini] API not available, using mock response.")
            logger.warning("Gemini API not available, using mock response.")
            return {
                'en': f"A beautiful nature photo taken at {metadata.get('location', 'an unknown location')}.",
                'he': f"תמונה יפה של טבע שצולמה ב{metadata.get('location', 'מקום לא ידוע')}",
                'hashtags': "#nature #photography #landscape #travel #explore"
            }
        try:
            print(f"[Gemini] Using new google-genai client...")
            print(f"[Gemini] Reading image: {image_path}")
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            import random
            disclaimer = random.choice(self.disclaimers)
            prompt = (
                "You are an expert Instagram content creator. "
                "Write a short, light, and engaging Instagram caption (max 150 characters) for a nature photo taken at the following location. "
                "The caption should be friendly, simple, and relatable (no literary or poetic language). Mention the location naturally. "
                "Try to mention what's special and unique and beautiful about this photo. "
                "Write from a MALE perspective using male Hebrew grammar and pronouns (e.g., 'ממליץ' not 'ממליצה', 'אוהב' not 'אוהבת'). "
                "Include 5-10 relevant hashtags in both Hebrew and English for maximum reach. "
                f"At the end, add this disclaimer in Hebrew: '# {disclaimer}'\n"
                f"Location: {metadata.get('location', 'Unknown')}\n"
                "Output format:\n"
                "Hebrew: ...\n"
                "Hashtags: #tag1 #tag2 #tag3 ...\n"
            )
            print(f"[Gemini] Sending request to Gemini API...")
            result = {}
            def call_gemini():
                try:
                    import PIL.Image
                    import io
                    img = PIL.Image.open(io.BytesIO(image_bytes))
                    response = self.client.models.generate_content(
                        model='gemini-2.5-pro',
                        contents=[prompt, img]
                    )
                    print(f"[Gemini] Received response from Gemini API.")
                    text = response.text if hasattr(response, 'text') else str(response)
                    en, he, hashtags = self._parse_gemini_response(text)
                    result['en'] = en
                    result['he'] = he
                    result['hashtags'] = hashtags
                except Exception as e:
                    print(f"[Gemini] API call failed: {e}")
                    logger.error(f"Gemini API call failed: {e}")
            thread = threading.Thread(target=call_gemini)
            start_time = time.time()
            thread.start()
            thread.join(timeout=30)
            if thread.is_alive():
                print("[Gemini] API call timed out after 30 seconds. Aborting.")
                return {
                    'en': f"A beautiful nature photo taken at {metadata.get('location', 'an unknown location')} (timeout).",
                    'he': f"תמונה יפה של טבע שצולמה ב{metadata.get('location', 'מקום לא ידוע')} (timeout)",
                    'hashtags': "#nature #photography #landscape #travel #explore"
                }
            if not result:
                print("[Gemini] API call failed or returned no result.")
                return {
                    'en': f"A beautiful nature photo taken at {metadata.get('location', 'an unknown location')} (error).",
                    'he': f"תמונה יפה של טבע שצולמה ב{metadata.get('location', 'מקום לא ידוע')} (error)",
                    'hashtags': "#nature #photography #landscape #travel #explore"
                }
            return result
        except Exception as e:
            print(f"[Gemini] API call failed: {e}")
            logger.error(f"Gemini API call failed: {e}")
            return {
                'en': f"A beautiful nature photo taken at {metadata.get('location', 'an unknown location')}.",
                'he': f"תמונה יפה של טבע שצולמה ב{metadata.get('location', 'מקום לא ידוע')}",
                'hashtags': "#nature #photography #landscape #travel #explore"
            }

    def _parse_gemini_response(self, text: str):
        import re
        he = hashtags = ''
        he_match = re.search(r'Hebrew: ?(.*?)(?:\nHashtags:|$)', text, re.DOTALL)
        hashtags_match = re.search(r'Hashtags: ?(.*)', text, re.DOTALL)
        if he_match:
            he = he_match.group(1).strip()
        if hashtags_match:
            hashtags = hashtags_match.group(1).strip()
        return '', he, hashtags
