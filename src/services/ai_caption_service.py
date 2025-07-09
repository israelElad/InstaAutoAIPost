from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
import os
import threading
import time

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
    import google.generativeai as genai
    print("[Gemini] google.generativeai imported")
except ImportError:
    genai = None
    print("[Gemini] google.generativeai import failed")

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
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        print(f"[Gemini] Loaded API key: {'FOUND' if self.api_key else 'NOT FOUND'}")
        if not self.api_key:
            logger.warning("Gemini API key not found. Set GEMINI_API_KEY in environment or config.")
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            self.genai = None
            logger.error("google-generativeai package not installed. Run 'pip install google-generativeai'.")

    def generate_caption(self, image_path: str, metadata: Dict) -> Dict:
        if not self.api_key or not self.genai:
            print("[Gemini] API not available, using mock response.")
            logger.warning("Gemini API not available, using mock response.")
            return {
                'en': f"A beautiful nature photo taken at {metadata.get('location', 'an unknown location')}.",
                'he': f"תמונה יפה של טבע שצולמה ב{metadata.get('location', 'מקום לא ידוע')}",
                'hashtags': "#nature #photography #landscape #travel #explore"
            }
        try:
            print(f"[Gemini] Configuring API client...")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            print(f"[Gemini] Reading image: {image_path}")
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            prompt = (
                "You are an expert Instagram content creator. "
                "Write a short, light, and engaging Instagram caption (max 150 characters) for a nature photo taken at the following location. "
                "The caption should be friendly, simple, and relatable (no literary or poetic language). Mention the location naturally. "
                "Write from a MALE perspective using male Hebrew grammar and pronouns (e.g., 'ממליץ' not 'ממליצה', 'אוהב' not 'אוהבת'). "
                "Include 5-10 relevant hashtags in both Hebrew and English for maximum reach. "
                "At the end, add this disclaimer in Hebrew: '# את התמונות אני צילמתי, בלי פילטרים/AI, אבל התיאור נוצר ע\"י AI :)'\n"
                f"Location: {metadata.get('location', 'Unknown')}\n"
                "Output format:\n"
                "Hebrew: ...\n"
                "Hashtags: #tag1 #tag2 #tag3 ...\n"
            )
            print(f"[Gemini] Sending request to Gemini API...")
            result = {}
            def call_gemini():
                try:
                    response = model.generate_content(
                        [prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
                    )
                    print(f"[Gemini] Received response from Gemini API.")
                    text = response.text if hasattr(response, 'text') else str(response)
                    print(f"[Gemini] Raw response text: {text[:300]}...")
                    en, he, hashtags = self._parse_gemini_response(text)
                    print(f"[Gemini] Parsed HE: {he}\n[Gemini] Parsed hashtags: {hashtags}")
                    result['en'] = en
                    result['he'] = he
                    result['hashtags'] = hashtags
                except Exception as e:
                    print(f"[Gemini] API call failed: {e}")
                    logger.error(f"Gemini API call failed: {e}")
            thread = threading.Thread(target=call_gemini)
            start_time = time.time()
            thread.start()
            thread.join(timeout=10)
            if thread.is_alive():
                print("[Gemini] API call timed out after 10 seconds. Aborting.")
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
        he_match = re.search(r'Hebrew: ?(.*?)(?:\n|$)', text, re.DOTALL)
        hashtags_match = re.search(r'Hashtags: ?(.*)', text, re.DOTALL)
        if he_match:
            he = he_match.group(1).strip()
        if hashtags_match:
            hashtags = hashtags_match.group(1).strip()
        # Always append the disclaimer in Hebrew if not present
        disclaimer = "# את התמונות אני צילמתי, בלי פילטרים/AI, אבל התיאור נוצר ע\"י AI :)"
        if disclaimer not in he:
            he = f"{he}\n{disclaimer}"
        return '', he, hashtags 