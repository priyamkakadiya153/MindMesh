from .language import LanguageService
from .summarizer import DocumentSummarizer
from .statistics import StatisticsService
from .quality import QualityAssessor

class EnrichmentService:
    @staticmethod
    def enrich_document_content(normalized_content: dict) -> dict:
        """Enriches normalized content with summaries, keywords, language, statistics, and quality ratings."""
        # 1. Concat paragraph texts
        paragraphs = normalized_content.get("paragraphs", [])
        text = "\n\n".join([p["text"] for p in paragraphs if isinstance(p, dict) and "text" in p])
        
        # 2. Language detection
        lang, lang_conf = LanguageService.detect_language(text)
        
        # 3. Summarization
        summary = DocumentSummarizer.generate_summary(text)
        keywords = DocumentSummarizer.extract_keywords(text)
        topics = DocumentSummarizer.extract_topics(text)
        
        # 4. Statistics
        stats = StatisticsService.generate_statistics(normalized_content)
        
        # 5. Quality Score
        quality = QualityAssessor.assess_quality(normalized_content)
        
        return {
            "extracted_text": text,
            "language": lang,
            "summary": summary,
            "keywords": keywords,
            "topics": topics,
            "statistics": stats,
            "quality_score": quality
        }
