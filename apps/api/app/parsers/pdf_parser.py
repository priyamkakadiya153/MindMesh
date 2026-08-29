import io
from .base import BaseParser

class PDFParser(BaseParser):
    def parse(self, file_content: bytes) -> dict:
        text = self.extract_text(file_content)
        meta = self.extract_metadata(file_content)
        tables = self.extract_tables(file_content)
        images = self.extract_images(file_content)
        structure = self.extract_structure(file_content)

        # Count statistics
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
            "language": meta.get("language", "en"),
            "statistics": {
                "word_count": words,
                "character_count": chars,
                "page_count": meta.get("page_count", 1),
                "table_count": len(tables),
                "image_count": len(images)
            }
        }

    def extract_text(self, file_content: bytes) -> str:
        # 1. Try PyMuPDF (fitz) - fastest & high fidelity
        try:
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            text_parts = []
            for page in doc:
                page_txt = page.get_text()
                if page_txt:
                    text_parts.append(page_txt.strip())
            joined = "\n\n".join(text_parts).strip()
            if joined:
                return joined
        except Exception:
            pass

        # 2. Try pypdf fallback
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            text_parts = []
            for page in reader.pages:
                page_txt = page.extract_text()
                if page_txt:
                    text_parts.append(page_txt.strip())
            joined = "\n\n".join(text_parts).strip()
            if joined:
                return joined
        except Exception:
            pass

        # 3. Try pdfplumber fallback
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_txt = page.extract_text()
                    if page_txt:
                        text_parts.append(page_txt.strip())
            joined = "\n\n".join(text_parts).strip()
            if joined:
                return joined
        except Exception:
            pass

        return ""

    def extract_tables(self, file_content: bytes) -> list[dict]:
        try:
            import pdfplumber
            tables_data = []
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    extracted = page.extract_tables()
                    for table in extracted:
                        tables_data.append({
                            "page": idx + 1,
                            "data": table
                        })
            return tables_data
        except Exception:
            return []

    def extract_images(self, file_content: bytes) -> list[dict]:
        try:
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            images_list = []
            for page_idx in range(len(doc)):
                for img in doc.get_page_images(page_idx):
                    images_list.append({
                        "page": page_idx + 1,
                        "xref": img[0],
                        "width": img[2],
                        "height": img[3],
                        "mime": f"image/{img[7]}" if len(img) > 7 else "image/jpeg"
                    })
            return images_list
        except Exception:
            return []

    def extract_metadata(self, file_content: bytes) -> dict:
        # Try fitz
        try:
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            meta = dict(doc.metadata) if doc.metadata else {}
            meta["page_count"] = len(doc)
            return meta
        except Exception:
            pass

        # Try pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            meta = {}
            if reader.metadata:
                for k, v in reader.metadata.items():
                    key = k.lstrip("/").lower()
                    meta[key] = str(v)
            meta["page_count"] = len(reader.pages)
            return meta
        except Exception:
            return {"page_count": 1}

    def extract_structure(self, file_content: bytes) -> list[dict]:
        try:
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            toc = doc.get_toc()
            structure = []
            for level, title, page in toc:
                structure.append({
                    "level": level,
                    "title": title,
                    "page": page
                })
            return structure
        except Exception:
            return []
