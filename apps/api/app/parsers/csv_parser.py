import csv
import io
from .base import BaseParser

class CSVParser(BaseParser):
    def parse(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        meta = self.extract_metadata(file_content)
        tables = self.extract_tables(file_content)
        images = self.extract_images(file_content)
        structure = self.extract_structure(file_content)

        words = len(text.split())
        chars = len(text)
        
        return {
            "title": meta.get("title", ""),
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
                "table_count": len(tables),
                "image_count": len(images)
            }
        }

    def extract_text(self, file_content: bytes) -> str:
        try:
            content_str = file_content.decode("utf-8")
        except Exception:
            content_str = file_content.decode("latin-1", errors="ignore")
            
        reader = csv.reader(io.StringIO(content_str))
        lines = []
        for row in reader:
            row_str = " | ".join(row)
            if row_str.strip():
                lines.append(row_str)
        return "\n\n".join(lines)

    def extract_tables(self, file_content: bytes) -> list[dict]:
        try:
            content_str = file_content.decode("utf-8")
        except Exception:
            content_str = file_content.decode("latin-1", errors="ignore")
            
        reader = csv.reader(io.StringIO(content_str))
        grid = list(reader)
        return [{
            "table_index": 1,
            "data": grid
        }]

    def extract_images(self, file_content: bytes) -> list[dict]:
        return []

    def extract_metadata(self, file_content: bytes) -> dict:
        try:
            content_str = file_content.decode("utf-8")
        except Exception:
            content_str = file_content.decode("latin-1", errors="ignore")
            
        lines = content_str.split("\n")
        return {"row_count": len(lines)}

    def extract_structure(self, file_content: bytes) -> list[dict]:
        return []
