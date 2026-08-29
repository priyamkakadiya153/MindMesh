from .base import BaseParser

class MarkdownParser(BaseParser):
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
            return file_content.decode("utf-8")
        except Exception:
            return file_content.decode("latin-1", errors="ignore")

    def extract_tables(self, file_content: bytes) -> list[dict]:
        # Simple regex table line matching for markdown
        text = self.extract_text(file_content)
        tables_list = []
        lines = text.split("\n")
        
        current_table = []
        for line in lines:
            if line.strip().startswith("|") and line.strip().endswith("|"):
                row = [cell.strip() for cell in line.split("|")[1:-1]]
                current_table.append(row)
            else:
                if current_table:
                    # Filter out line dividers like |---|---|
                    clean_table = [r for r in current_table if not all(c.replace("-", "").strip() == "" for c in r)]
                    if clean_table:
                        tables_list.append({
                            "table_index": len(tables_list) + 1,
                            "data": clean_table
                        })
                    current_table = []
        return tables_list

    def extract_images(self, file_content: bytes) -> list[dict]:
        # Parse markdown format: ![alt](url)
        import re
        text = self.extract_text(file_content)
        pattern = r"!\[(.*?)\]\((.*?)\)"
        matches = re.findall(pattern, text)
        return [{"alt": m[0], "url": m[1]} for m in matches]

    def extract_metadata(self, file_content: bytes) -> dict:
        # Detect Frontmatter title
        text = self.extract_text(file_content)
        meta = {}
        if text.startswith("---"):
            parts = text.split("---")
            if len(parts) > 2:
                for line in parts[1].split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")
        return meta

    def extract_structure(self, file_content: bytes) -> list[dict]:
        # Heading lists: H1, H2, H3 etc.
        text = self.extract_text(file_content)
        structure = []
        for line in text.split("\n"):
            if line.startswith("#"):
                hashes = line.split(" ")[0]
                if all(char == "#" for char in hashes):
                    title = line[len(hashes):].strip()
                    structure.append({
                        "level": str(len(hashes)),
                        "title": title
                    })
        return structure
        
