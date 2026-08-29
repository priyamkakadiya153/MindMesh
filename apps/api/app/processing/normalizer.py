from typing import Dict, Any

class ContentNormalizer:
    @staticmethod
    def normalize(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and coerces parsed output into the strict Unified Content Model."""
        normalized = {
            "title": str(raw_data.get("title", "")),
            "metadata": dict(raw_data.get("metadata", {})),
            "sections": [],
            "paragraphs": [],
            "tables": [],
            "images": [],
            "links": [],
            "language": str(raw_data.get("language", "en")),
            "statistics": dict(raw_data.get("statistics", {}))
        }

        # Normalize sections
        for section in raw_data.get("sections", []):
            if isinstance(section, dict) and "level" in section and "title" in section:
                normalized["sections"].append({
                    "level": str(section["level"]),
                    "title": str(section["title"]),
                    "page": section.get("page")
                })

        # Normalize paragraphs
        for p in raw_data.get("paragraphs", []):
            text_val = ""
            if isinstance(p, dict) and "text" in p:
                text_val = str(p["text"])
            elif isinstance(p, str):
                text_val = p
            
            if text_val.strip():
                normalized["paragraphs"].append({"text": text_val.strip()})

        # Normalize tables
        for table in raw_data.get("tables", []):
            if isinstance(table, dict) and "data" in table:
                normalized["tables"].append({
                    "table_index": table.get("table_index"),
                    "sheet_name": table.get("sheet_name"),
                    "data": list(table["data"])
                })

        # Normalize images
        for img in raw_data.get("images", []):
            if isinstance(img, dict):
                normalized["images"].append({
                    "image_index": img.get("image_index"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "format": img.get("format"),
                    "src": img.get("src"),
                    "alt": img.get("alt")
                })

        # Statistics checks and fallbacks
        stats = normalized["statistics"]
        stats["word_count"] = int(stats.get("word_count", 0))
        stats["character_count"] = int(stats.get("character_count", 0))
        stats["page_count"] = int(stats.get("page_count", 1))
        stats["table_count"] = int(stats.get("table_count", len(normalized["tables"])))
        stats["image_count"] = int(stats.get("image_count", len(normalized["images"])))

        return normalized
