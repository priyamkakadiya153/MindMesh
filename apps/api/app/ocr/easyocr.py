import io
import logging

logger = logging.getLogger(__name__)

class EasyOCRDriver:
    @staticmethod
    def extract_text(image_bytes: bytes) -> tuple[str, float]:
        """Extracts text using EasyOCR reader."""
        try:
            import easyocr
            import numpy as np
            from PIL import Image
            
            img = Image.open(io.BytesIO(image_bytes))
            img_np = np.array(img)
            
            reader = easyocr.Reader(['en'])
            results = reader.readtext(img_np)
            
            text_blocks = [r[1] for r in results]
            confidences = [r[2] for r in results]
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 1.0
            return " ".join(text_blocks), avg_conf
        except ImportError:
            logger.warning("easyocr is not installed. EasyOCR skipped.")
            return "", 0.0
        except Exception as e:
            logger.error(f"EasyOCR extraction error: {e}")
            return "", 0.0
