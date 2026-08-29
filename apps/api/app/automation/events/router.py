import logging
import fnmatch
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class EventRouter:
    @staticmethod
    def match_topic(pattern: str, event_type: str) -> bool:
        """Matches event names with wildcards (e.g. 'document.*' matches 'document_uploaded')."""
        # Convert underscores/dots to fnmatch style
        pat = pattern.replace(".", "*").replace("_", "*")
        evt = event_type.replace(".", "*").replace("_", "*")
        return fnmatch.fnmatch(evt, pat)
