import re

class LanguageService:
    @staticmethod
    def detect_language(text: str) -> tuple[str, float]:
        """Detects primary language of text using Unicode range scanning."""
        if not text or not text.strip():
            return "en", 1.0

        # unicode checks
        hindi_guj_count = len(re.findall(r'[\u0900-\u097F\u0A80-\u0AFF]', text))
        cjk_count = len(re.findall(r'[\u4e00-\u9fff\u3040-\u30ff]', text))
        
        total = len(text)
        
        if hindi_guj_count > total * 0.1:
            # Check for Gujarati specific range
            guj_count = len(re.findall(r'[\u0A80-\u0AFF]', text))
            if guj_count > hindi_guj_count * 0.5:
                return "gu", 0.90
            return "hi", 0.92
            
        if cjk_count > total * 0.1:
            # Check Hiragana/Katakana for Japanese
            jp_count = len(re.findall(r'[\u3040-\u30ff]', text))
            if jp_count > 0:
                return "ja", 0.95
            return "zh", 0.94

        # Check for European languages (accents checks, otherwise default English)
        french_german_accents = len(re.findall(r'[éèàùçäöüßëïœæ]', text, re.IGNORECASE))
        if french_german_accents > 0:
            if len(re.findall(r'[äöüß]', text, re.IGNORECASE)) > french_german_accents * 0.5:
                return "de", 0.88
            return "fr", 0.85
            
        return "en", 0.99
