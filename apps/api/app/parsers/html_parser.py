from .base import BaseParser

class HTMLParser(BaseParser):
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
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(file_content, "html.parser")
            return soup.get_text(separator="\n\n")
        except ImportError:
            return "BeautifulSoup not installed."
        except Exception as e:
            return f"Error parsing HTML: {str(e)}"

    def extract_tables(self, file_content: bytes) -> list[dict]:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(file_content, "html.parser")
            tables_list = []
            for idx, table in enumerate(soup.find_all("table")):
                grid = []
                for row in table.find_all("tr"):
                    grid.append([cell.get_text().strip() for cell in row.find_all(["td", "th"])])
                tables_list.append({
                    "table_index": idx + 1,
                    "data": grid
                })
            return tables_list
        except Exception:
            return []

    def extract_images(self, file_content: bytes) -> list[dict]:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(file_content, "html.parser")
            images_list = []
            for idx, img in enumerate(soup.find_all("img")):
                images_list.append({
                    "image_index": idx + 1,
                    "src": img.get("src", ""),
                    "alt": img.get("alt", "")
                })
            return images_list
        except Exception:
            return []

    def extract_metadata(self, file_content: bytes) -> dict:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(file_content, "html.parser")
            title = soup.title.string if soup.title else ""
            return {"title": title}
        except Exception:
            return {}

    def extract_structure(self, file_content: bytes) -> list[dict]:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(file_content, "html.parser")
            structure = []
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                structure.append({
                    "level": tag.name.replace("h", ""),
                    "title": tag.get_text().strip()
                })
            return structure
        except Exception:
            return []
