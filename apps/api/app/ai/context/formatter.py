from typing import List, Dict, Any

class ContextFormatter:
    @staticmethod
    def format_context_for_prompt(chunks: List[Dict[str, Any]]) -> str:
        """Formats context chunks into a clear XML structured string for LLMs.
        
        Using XML tags allows LLMs to easily segment different documents,
        extract metadata, and trace sources for generation.
        """
        if not chunks:
            return "No relevant context found."
            
        formatted_parts = []
        for idx, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("title") or chunk.get("document_name") or "Unnamed Document"
            doc_id = chunk.get("document_id") or "unknown"
            score = chunk.get("score") or chunk.get("ranking_score") or 0.0
            
            # Extract citation specifics
            page = chunk.get("page")
            pages = chunk.get("pages")
            if pages:
                page_str = ", ".join(str(p) for p in sorted(list(set(pages))))
            elif page:
                page_str = str(page)
            else:
                page_str = "1"
                
            workspace = chunk.get("workspace") or "General"
            project = chunk.get("project") or "General"
            version = chunk.get("version") or 1
            section = chunk.get("metadata", {}).get("heading") or chunk.get("section") or "General"
            
            part = (
                f'<source index="{idx}">\n'
                f'  <document_id>{doc_id}</document_id>\n'
                f'  <title>{doc_name}</title>\n'
                f'  <version>{version}</version>\n'
                f'  <workspace>{workspace}</workspace>\n'
                f'  <project>{project}</project>\n'
                f'  <pages>{page_str}</pages>\n'
                f'  <section>{section}</section>\n'
                f'  <relevance_score>{score}</relevance_score>\n'
                f'  <content>\n'
                f'{chunk["content"]}\n'
                f'  </content>\n'
                f'</source>'
            )
            formatted_parts.append(part)
            
        return "\n\n".join(formatted_parts)
