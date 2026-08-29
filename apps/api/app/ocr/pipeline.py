from .preprocess import ImagePreprocessor
from .engine import OCREngine

class OCRPipeline:
    @staticmethod
    async def process_image(image_bytes: bytes) -> tuple[str, float]:
        """Runs image cleanup, deskew, and OCR text extraction."""
        # 1. Image Preprocessing (contrast/grayscale)
        clean_bytes = ImagePreprocessor.preprocess(image_bytes)
        
        # 2. Execute OCR Extraction Engine
        text, confidence = OCREngine.run_ocr(clean_bytes)
        
        return text, confidence
