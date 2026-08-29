class TokenCounter:
    @staticmethod
    def count_tokens(text: str) -> int:
        """Estimates the token count of a given string (averaging 4 characters per token)."""
        if not text:
            return 0
            
        # Standard fallback estimation
        char_count = len(text)
        words = len(text.split())
        
        # Tiktoken approximation: words * 1.3 or chars / 4
        approx_tokens = int(max(words * 1.3, char_count / 4))
        return max(1, approx_tokens)
