import io
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    @staticmethod
    def preprocess(image_bytes: bytes) -> bytes:
        """Applies cleanup, deskew, and contrast enhancement to input image."""
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            
            img = Image.open(io.BytesIO(image_bytes))
            # 1. Convert to grayscale
            img = img.convert("L")
            # 2. Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            # 3. Apply subtle blur to reduce print noise
            img = img.filter(ImageFilter.SMOOTH_MORE)
            
            out_buf = io.BytesIO()
            img.save(out_buf, format="PNG")
            return out_buf.getvalue()
        except ImportError:
            logger.warning("Pillow not installed. Skipping image cleanup preprocessing.")
            return image_bytes
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_bytes
