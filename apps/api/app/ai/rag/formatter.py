import re
from typing import List, Dict, Any, Tuple

class RAGFormatter:
    @staticmethod
    def generate_suggested_questions(query: str, answer: str) -> List[str]:
        """Dynamically generates suggested next queries based on query context and answer words."""
        keywords = re.findall(r'\b\w{6,}\b', query.lower() + " " + answer.lower())
        unique_words = sorted(list(set(keywords)))
        
        suggestions = []
        if len(unique_words) >= 2:
            suggestions.append(f"Can you provide more details about {unique_words[0]}?")
            suggestions.append(f"How does {unique_words[1]} relate to the system design?")
        else:
            suggestions.append("Can you elaborate on that explanation?")
            suggestions.append("What are the key requirements mentioned in the documents?")
            
        return suggestions[:3]

    @staticmethod
    def format_response(raw_answer: str, citations: List[Dict[str, Any]], grounded: bool = True, confidence: float = 1.0) -> Tuple[str, List[Dict[str, Any]]]:
        """Formats answer and cleans up sources with system prompt leakage protection and boundary sanitization."""
        clean_answer = raw_answer or ""

        # 1. Remove XML context tags and contents
        clean_answer = re.sub(r'<source[^>]*>', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'</source>', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'<(document_id|version|workspace|project|pages|section|relevance_score)>[^<]*</\1>', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'</?(content|source|document_id|title|pages|section|relevance_score|version|workspace|project)>', '', clean_answer, flags=re.IGNORECASE)

        # 2. Remove Workspace Evidence markers and labels
        clean_answer = re.sub(r'\[Workspace Evidence #\d+\]', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'•\s*Workspace Evidence\s*(#\d+)?:\s*', '• ', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'Workspace Evidence\s*(#\d+)?', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'document_id=[^\s\n,]+', '', clean_answer, flags=re.IGNORECASE)

        # 3. Remove prompt section headers and instruction leakage
        clean_answer = re.sub(r'===\s*(SYSTEM INSTRUCTIONS|RETRIEVED KNOWLEDGE CONTEXT|CONVERSATION HISTORY|CURRENT USER QUESTION|ASSISTANT INSTRUCTIONS)\s*===', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'You are MindMesh (AI|Document|Organizational|Code|Project)[^\n]*\n?', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'Use prior conversation turns to resolve relative entity references[^\n]*\n?', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'Always cite your sources using bracketed numbers[^\n]*\n?', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'If no relevant context is found, reply naturally[^\n]*\n?', '', clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r'(debug_context|retrieved_context)', '', clean_answer, flags=re.IGNORECASE)

        # 4. Clean up multiple blank lines
        clean_answer = re.sub(r'\n{3,}', '\n\n', clean_answer).strip()

        if not clean_answer:
            clean_answer = "I couldn't find enough information in this workspace to answer that."

        sources = [
            {"id": c.get("document_id"), "title": c.get("title", "Document"), "page": c.get("page")}
            for c in (citations or [])
        ]
        return clean_answer, sources
