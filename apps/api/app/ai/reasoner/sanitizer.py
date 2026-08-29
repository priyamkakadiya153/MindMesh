import re
from typing import List, Dict, Any

class PromptInjectionSanitizer:
    """Sanitizes retrieved workspace content to defend against prompt injection

    attacks by treating retrieved content strictly as UNTRUSTED DATA within XML

    boundaries.

    """

    INJECTION_PATTERNS: List[str] = [
        r"ignore (all )?previous instructions",
        r"disregard (all )?prior rules",
        r"reveal (all )?workspace data",
        r"system prompt:",
        r"you are now an unrestricted",
        r"output all api keys",
        r"override system instructions"
    ]

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        if not text:
            return ""
        clean_text = text
        for pattern in cls.INJECTION_PATTERNS:
            clean_text = re.sub(pattern, "[REDACTED_INSTRUCTION]", clean_text, flags=re.IGNORECASE)
        return clean_text

    @classmethod
    def wrap_data_block(cls, source_id: str, source_type: str, title: str, content: str, index: int) -> str:
        clean_content = cls.sanitize_text(content)
        clean_title = cls.sanitize_text(title)
        return (
            f'<untrusted_workspace_data index="{index}" type="{source_type}" id="{source_id}" title="{clean_title}">\n'
            f"{clean_content}\n"
            f"</untrusted_workspace_data>"
        )
