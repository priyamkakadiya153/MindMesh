from typing import List, Dict, Any
from .models import Citation

class CitationFormatter:
    @staticmethod
    def format_citations_as_markdown(citations: List[Citation]) -> str:
        """Compiles a list of citations into a clean Markdown reference/footnotes list."""
        if not citations:
            return ""
            
        lines = ["\n### References & Citations"]
        for idx, cit in enumerate(citations, 1):
            page_info = f", Page {cit.page}" if cit.page else ""
            section_info = f", Section: {cit.section}" if cit.section else ""
            lines.append(
                f"[{idx}] {cit.document} (v{cit.version}) "
                f"in Workspace: '{cit.workspace}'{page_info}{section_info} "
                f"[Confidence: {int(cit.confidence * 100)}%]"
            )
            
        return "\n".join(lines)
