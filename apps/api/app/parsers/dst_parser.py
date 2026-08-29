import re
from typing import Dict, Any
from .base import BaseParser

class DSTParser(BaseParser):
    """
    Parser for Tajima DST Embroidery files.
    Parses binary 512-byte header to extract design metadata (stitch count, dimensions, color changes)
    without attempting raw text extraction or sending binary data to LLM.
    """

    def extract_text(self, file_content: bytes) -> str:
        parsed = self.parse(file_content)
        meta = parsed.get("metadata", {})
        label = meta.get("label", "Untitled Design")
        stitches = meta.get("stitch_count", 0)
        colors = meta.get("color_changes", 0)
        width = meta.get("width_mm", 0.0)
        height = meta.get("height_mm", 0.0)

        return (
            f"Tajima DST Embroidery File Metadata:\n"
            f"Design Label: {label}\n"
            f"Stitch Count: {stitches:,}\n"
            f"Color Changes: {colors}\n"
            f"Dimensions: {width:.1f}mm x {height:.1f}mm\n"
            f"Format: Tajima DST Embroidery Design"
        )

    def extract_metadata(self, file_content: bytes) -> Dict[str, Any]:
        return self.parse(file_content).get("metadata", {})

    def extract_structure(self, file_content: bytes) -> Dict[str, Any]:
        return self.parse(file_content)

    def extract_tables(self, file_content: bytes) -> list:
        return []

    def extract_images(self, file_content: bytes) -> list:
        return []

    def parse(self, file_content: bytes) -> Dict[str, Any]:
        header_bytes = file_content[:512]
        try:
            header_str = header_bytes.decode("ascii", errors="ignore")
        except Exception:
            header_str = ""

        # Extract header fields
        def get_val(key: str) -> str:
            m = re.search(rf"{key}:(.*?)(?:\r|\n|\x1a|$)", header_str)
            return m.group(1).strip() if m else ""

        label = get_val("LA") or "Untitled Design"
        try:
            stitch_count = int(get_val("ST") or "0")
        except ValueError:
            stitch_count = 0

        try:
            color_changes = int(get_val("CO") or "0")
        except ValueError:
            color_changes = 0

        try:
            pos_x = float(get_val(r"\+X") or "0")
            neg_x = float(get_val(r"-X") or "0")
            pos_y = float(get_val(r"\+Y") or "0")
            neg_y = float(get_val(r"-Y") or "0")

            width_mm = (pos_x + neg_x) / 10.0
            height_mm = (pos_y + neg_y) / 10.0
        except ValueError:
            width_mm = 0.0
            height_mm = 0.0

        metadata = {
            "format": "Tajima DST Embroidery",
            "label": label,
            "stitch_count": stitch_count,
            "color_changes": color_changes,
            "width_mm": round(width_mm, 1),
            "height_mm": round(height_mm, 1),
            "is_specialized_file": True
        }

        text_representation = (
            f"Tajima DST Embroidery File: {label}. "
            f"Stitch Count: {stitch_count}. Color Changes: {color_changes}. "
            f"Dimensions: {width_mm:.1f}mm x {height_mm:.1f}mm."
        )

        return {
            "title": label,
            "paragraphs": [{"text": text_representation}],
            "sections": [
                {
                    "title": "Embroidery Specifications",
                    "content": text_representation
                }
            ],
            "metadata": metadata,
            "statistics": {
                "pages": 1,
                "words": len(text_representation.split()),
                "characters": len(text_representation)
            }
        }
