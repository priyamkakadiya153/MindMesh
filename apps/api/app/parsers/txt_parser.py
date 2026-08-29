from .base import BaseParser

class TXTParser(BaseParser):
    def parse(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        meta = self.extract_metadata(file_content)
        tables = self.extract_tables(file_content)
        images = self.extract_images(file_content)
        structure = self.extract_structure(file_content)

        words = len(text.split())
        chars = len(text)
        
        return {
            "title": "",
            "metadata": meta,
            "sections": structure,
            "paragraphs": [{"text": p.strip()} for p in text.split("\n\n") if p.strip()],
            "tables": tables,
            "images": images,
            "links": [],
            "language": "en",
            "statistics": {
                "word_count": words,
                "character_count": chars,
                "page_count": 1,
                "table_count": 0,
                "image_count": 0
            }
        }

    def extract_text(self, file_content: bytes) -> str:
        try:
            return file_content.decode("utf-8")
        except Exception:
            return file_content.decode("latin-1", errors="ignore")

    def extract_tables(self, file_content: bytes) -> list[dict]:
        return []

    def extract_images(self, file_content: bytes) -> list[dict]:
        return []

    def extract_metadata(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        lines = text.split("\n")
        return {"line_count": len(lines)}

    def extract_structure(self, file_content: bytes) -> list[dict]:
        return []
