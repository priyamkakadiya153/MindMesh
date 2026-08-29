import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Basic PII regex patterns
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b')

class PromptSafetyPolicy:
    @staticmethod
    def inspect_and_scrub_prompt(prompt_text: str, scrub_pii: bool = True) -> Tuple[str, bool]:
        """Inspects prompt for potential jailbreaks or toxicity, and scrubs PII if enabled."""
        if not prompt_text:
            return "", True

        is_safe = True
        
        # 1. Check for typical injection triggers
        jailbreak_indicators = [
            "ignore previous instructions",
            "system override",
            "you are now a chat mode",
            "bypass safety filters",
            "disregard constraints"
        ]
        
        lower_text = prompt_text.lower()
        for indicator in jailbreak_indicators:
            if indicator in lower_text:
                logger.warning(f"Jailbreak attempt flagged: '{indicator}' detected in user query.")
                is_safe = False
                break
                
        # 2. Scrub PII
        scrubbed_text = prompt_text
        if scrub_pii:
            scrubbed_text = EMAIL_REGEX.sub("[EMAIL_REDACTED]", scrubbed_text)
            scrubbed_text = PHONE_REGEX.sub("[PHONE_REDACTED]", scrubbed_text)
            
        return scrubbed_text, is_safe
