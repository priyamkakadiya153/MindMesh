import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ConversationSummarizer:
    @staticmethod
    def generate_history_summary(messages: List[Dict[str, str]]) -> str:
        """Heuristically condenses past discussion turns into a single summary paragraph.
        
        Extracts key sentences and topic cues from user and assistant turns.
        """
        if not messages:
            return ""
            
        user_queries = []
        assistant_facts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "").strip()
            if not content:
                continue
                
            if role == "user":
                # Take first 50 chars of query
                snippet = content.split("\n")[0]
                if len(snippet) > 60:
                    snippet = snippet[:60] + "..."
                user_queries.append(snippet)
            else:
                # Take assistant sentences
                sentences = content.split(". ")
                if sentences:
                    assistant_facts.append(sentences[0])
                    
        summary_parts = []
        if user_queries:
            summary_parts.append(f"User discussed: {'; '.join(user_queries[:3])}.")
        if assistant_facts:
            summary_parts.append(f"AI details provided: {'. '.join(assistant_facts[:2])}.")
            
        return " ".join(summary_parts) if summary_parts else "Previous conversation history."
