from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

STATION_VERNACULAR_MAP = {
    "बांद्रा": ("BA", "Bandra"),
    "बांद्रे": ("BA", "Bandra"),
    "bandra": ("BA", "Bandra"),
    "अंधेरी": ("ADH", "Andheri"),
    "andheri": ("ADH", "Andheri"),
    "बोरीवली": ("BVI", "Borivali"),
    "borivali": ("BVI", "Borivali"),
    "दादर": ("DDR", "Dadar"),
    "dadar": ("DDR", "Dadar"),
    "विरार": ("VR", "Virar"),
    "virar": ("VR", "Virar"),
    "चर्चगेट": ("CCG", "Churchgate"),
    "churchgate": ("CCG", "Churchgate"),
    "मुंबई सेंट्रल": ("BCT", "Mumbai Central"),
    "mumbai central": ("BCT", "Mumbai Central"),
}

CATEGORY_KEYWORDS = {
    "platform_cleanliness": ["कचरा", "स्वच्छता", "गंदगी", "साफ", "गંદકી", "cleanliness", "garbage", "trash", "dirty"],
    "facilities": ["पानी", "पाणी", "लीकेज", "गळती", "નળ", "water", "leak", "tap"],
    "lifts_escalators": ["लिफ्ट", "सरकता जिना", "एस्कलेटर", "escalator", "lift"],
    "safety_security": ["सुरक्षा", "गर्दी", "चोरी", "महिला", "safety", "crowd", "theft", "emergency"],
}


class VoiceAssistantService:
    def detect_language(self, text: str) -> str:
        """Detect vernacular language from script and vocabulary."""
        # Devanagari script regex range: \u0900-\u097F
        if re.search(r"[\u0900-\u097F]", text):
            if any(w in text for w in ["आहे", "नाही", "गळती", "जिना"]):
                return "mr"  # Marathi
            return "hi"  # Hindi
        # Gujarati script regex range: \u0A80-\u0AFF
        if re.search(r"[\u0A80-\u0AFF]", text):
            return "gu"  # Gujarati
        if any(w in text.lower() for w in ["hai", "par", "pe", "bohot", "nahi"]):
            return "hinglish"
        return "en"

    def extract_station(self, text: str) -> tuple[str | None, str | None]:
        """Extract station code and station name from spoken text."""
        lowered = text.lower()
        for kw, (code, name) in STATION_VERNACULAR_MAP.items():
            if kw in lowered or kw in text:
                return code, name
        return None, None

    def predict_category(self, text: str) -> str:
        """Predict issue category from vernacular keywords."""
        lowered = text.lower()
        for cat, kws in CATEGORY_KEYWORDS.items():
            if any(kw in lowered or kw in text for kw in kws):
                return cat
        return "station_infrastructure"

    def generate_translated_summary(self, text: str, lang: str, station_name: str | None) -> str:
        """Generate structured English translation summary of spoken grievance."""
        st_prefix = f"At {station_name}: " if station_name else ""
        if lang in {"hi", "mr", "gu", "hinglish"}:
            return f"{st_prefix}[Voice Report - {lang.upper()}] Spoken grievance: '{text}'"
        return f"{st_prefix}{text}"

    def process_voice_input(self, text: str) -> dict[str, Any]:
        """Process raw spoken transcript into structured grievance payload."""
        cleaned_text = text.strip()
        lang = self.detect_language(cleaned_text)
        code, name = self.extract_station(cleaned_text)
        category_code = self.predict_category(cleaned_text)
        summary = self.generate_translated_summary(cleaned_text, lang, name)

        return {
            "detected_language": lang,
            "station_code": code,
            "station_name": name,
            "category_code": category_code,
            "original_transcript": cleaned_text,
            "translated_summary": summary,
        }


voice_assistant = VoiceAssistantService()
