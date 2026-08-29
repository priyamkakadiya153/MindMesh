class StatisticsService:
    @staticmethod
    def estimate_reading_time(word_count: int) -> int:
        """Calculates estimated reading time in minutes (assumes 200 words per minute)."""
        minutes = word_count // 200
        return max(1, minutes)

    @classmethod
    def generate_statistics(cls, normalized_content: dict) -> dict:
        """Extracts complete statistics structure from normalized content JSON."""
        stats = normalized_content.get("statistics", {})
        
        words = stats.get("word_count", 0)
        chars = stats.get("character_count", 0)
        pages = stats.get("page_count", 1)
        
        paragraphs = len(normalized_content.get("paragraphs", []))
        tables = len(normalized_content.get("tables", []))
        images = len(normalized_content.get("images", []))
        headings = len(normalized_content.get("sections", []))
        
        reading_time = cls.estimate_reading_time(words)
        
        return {
            "pages": pages,
            "words": words,
            "characters": chars,
            "paragraphs": paragraphs,
            "tables": tables,
            "images": images,
            "headings": headings,
            "reading_time": reading_time
        }
