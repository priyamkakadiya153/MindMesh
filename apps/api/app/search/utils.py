import re

def normalize_text(text: str) -> str:
    """Normalizes text by lowering case, removing excess spacing, and sanitizing inputs."""
    if not text:
        return ""
    # Lowercase and replace carriage returns/newlines/tabs with spaces
    text = text.lower().strip()
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Condense multiple spaces into a single space
    text = re.sub(r'\s+', ' ', text)
    return text
