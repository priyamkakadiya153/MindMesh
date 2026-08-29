import re
from typing import List, Dict, Any, Set

class QueryProcessor:
    """Normalizes query text, extracts keywords, preserves technical symbols,

    filenames, acronyms, and codes.

    """

    STOP_WORDS: Set[str] = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
        "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
        "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
        "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
        "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
        "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
        "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
        "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
        "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
        "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
        "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
        "they've", "this", "those", "through", "to", "too", "under", "until", "up",
        "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
        "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
        "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
        "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
        "yourself", "yourselves"
    }

    @classmethod
    def process(cls, raw_query: str) -> Dict[str, Any]:
        if not raw_query:
            return {
                "raw_query": "",
                "clean_query": "",
                "keywords": [],
                "important_keywords": [],
                "technical_tokens": [],
                "acronyms": []
            }

        clean_query = raw_query.strip()
        tokens = re.split(r'\s+', clean_query)

        keywords: List[str] = []
        important_keywords: List[str] = []
        technical_tokens: List[str] = []
        acronyms: List[str] = []

        for token in tokens:
            cleaned = token.strip(".,;:!?()[]{}'\"")
            if not cleaned:
                continue

            lowered = cleaned.lower()
            keywords.append(lowered)

            # Technical token check (contains underscore, dot, hyphen, digits, or mixed case)
            if any(char in cleaned for char in [".", "_", "-", "/", "\\", "@", "#"]) or any(char.isdigit() for char in cleaned):
                technical_tokens.append(cleaned)
                important_keywords.append(lowered)
            elif cleaned.isupper() and len(cleaned) >= 2:
                acronyms.append(cleaned)
                important_keywords.append(lowered)
            elif lowered not in cls.STOP_WORDS:
                important_keywords.append(lowered)

        return {
            "raw_query": raw_query,
            "clean_query": clean_query,
            "keywords": keywords,
            "important_keywords": important_keywords if important_keywords else keywords,
            "technical_tokens": technical_tokens,
            "acronyms": acronyms
        }
