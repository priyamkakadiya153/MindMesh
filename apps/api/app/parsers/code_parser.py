from .base import BaseParser
import json

class CodeParser(BaseParser):
    def parse(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        lines = text.splitlines()
        return {
            "title": "Source Code Document",
            "sections": [
                {
                    "title": "Code Content",
                    "content": text,
                    "level": 1
                }
            ],
            "metadata": {
                "line_count": len(lines),
                "character_count": len(text)
            }
        }

    def extract_text(self, file_content: bytes) -> str:
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except Exception:
                return str(file_content)

    def extract_tables(self, file_content: bytes) -> list[dict]:
        return []

    def extract_images(self, file_content: bytes) -> list[dict]:
        return []

    def extract_metadata(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        return {
            "line_count": len(text.splitlines()),
            "character_count": len(text)
        }

    def extract_structure(self, file_content: bytes) -> list[dict]:
        text = self.extract_text(file_content)
        return [{"title": "Source Code", "content": text[:500], "level": 1}]
