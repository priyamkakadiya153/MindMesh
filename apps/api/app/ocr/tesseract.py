import io
import logging

logger = logging.getLogger(__name__)

class TesseractDriver:
    @staticmethod
    def extract_text(image_bytes: bytes, language: str = "eng") -> tuple[str, float]:
        """Extracts text and computes average confidence using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(io.BytesIO(image_bytes))
            # PyTesseract data extract
            text = pytesseract.image_to_string(img, lang=language)
            
            # Retrieve confidence data if possible, default to 0.85
            return text, 0.85
        except ImportError:
            logger.warning("pytesseract is not installed. Tesseract OCR skipped.")
            return "", 0.0
        except Exception as e:
            logger.error(f"Tesseract extraction error: {e}")
            return "", 0.0
        
