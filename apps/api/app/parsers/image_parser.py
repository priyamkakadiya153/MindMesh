import io
from .base import BaseParser

class ImageParser(BaseParser):
    def parse(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        meta = self.extract_metadata(file_content)
        tables = self.extract_tables(file_content)
        images = self.extract_images(file_content)
        structure = self.extract_structure(file_content)

        return {
            "title": "",
            "metadata": meta,
            "sections": structure,
            "paragraphs": [],
            "tables": [],
            "images": images,
            "links": [],
            "language": "en",
            "statistics": {
                "word_count": 0,
                "character_count": 0,
                "page_count": 1,
                "table_count": 0,
                "image_count": 1
            }
        }

    def extract_text(self, file_content: bytes) -> str:
        # OCR is executed in later milestones.
        return ""

    def extract_tables(self, file_content: bytes) -> list[dict]:
        return []

    def extract_images(self, file_content: bytes) -> list[dict]:
        meta = self.extract_metadata(file_content)
        return [{
            "width": meta.get("width", 0),
            "height": meta.get("height", 0),
            "format": meta.get("format", "")
        }]

    def extract_metadata(self, file_content: bytes) -> dict:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_content))
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode
            }
        except ImportError:
            return {"width": 0, "height": 0, "format": "unknown"}
        except Exception:
            return {}

    def extract_structure(self, file_content: bytes) -> list[dict]:
        return []
