import re
from collections import Counter

class DocumentSummarizer:
    @staticmethod
    def generate_summary(text: str, max_sentences: int = 3) -> str:
        """Extracts first few sentences of text as summary."""
        if not text or not text.strip():
            return ""
            
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        clean_sentences = [s.strip() for s in sentences if s.strip()]
        
        return " ".join(clean_sentences[:max_sentences])

    @staticmethod
    def extract_keywords(text: str, limit: int = 8) -> list[str]:
        """Simple frequency frequency extraction of keywords filtering short words."""
        if not text:
            return []
            
        words = re.findall(r'\b[a-zA-Z]{4,15}\b', text.lower())
        stopwords = {
            "this", "that", "with", "from", "they", "them", "their", "have", "were",
            "about", "would", "could", "should", "there", "their", "these", "other"
        }
        filtered = [w for w in words if w not in stopwords]
        
        counter = Counter(filtered)
        return [item[0] for item in counter.most_common(limit)]

    @staticmethod
    def extract_topics(text: str) -> list[str]:
        """Classifies text into simple matching topics keywords groups."""
        if not text:
            return []
            
        topics = []
        text_lower = text.lower()
        
        rules = {
            "Engineering": ["engineering", "architecture", "design", "development", "build"],
            "Business": ["business", "revenue", "strategy", "finance", "marketing", "sales"],
            "Legal": ["legal", "contract", "agreement", "compliance", "policy", "retention"],
            "Medical": ["medical", "clinical", "health", "patient", "trial", "medicine"],
            "Technology": ["technology", "software", "database", "api", "server", "code"]
        }
        
        for topic, keywords in rules.items():
            if any(k in text_lower for k in keywords):
                topics.append(topic)
                
        if not topics:
            topics.append("General")
            
        return topics
