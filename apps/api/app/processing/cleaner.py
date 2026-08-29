import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Normalizes and cleans extracted raw document text while preserving semantic structure."""
        if not raw_text:
            return ""

        # 1. Normalize Unicode to NFC
        text = unicodedata.normalize("NFC", raw_text)

        # 2. Remove non-printable control characters except \n, \t, \r
        text = "".join(ch for ch in text if ch in ("\n", "\t", "\r") or (ord(ch) >= 32 and ord(ch) != 127))

        # 3. Normalize line endings (\r\n -> \n, \r -> \n)
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 4. Remove broken line wraps within paragraphs (e.g. hyphenated linebreaks: "commu-\nnication" -> "communication")
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # 5. Trim trailing whitespace on each line
        lines = [re.sub(r"[ \t]+$", "", line) for line in text.split("\n")]
        text = "\n".join(lines)

        # 6. Collapse 3+ consecutive newlines to double newlines (\n\n) to standardize paragraph breaks
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
