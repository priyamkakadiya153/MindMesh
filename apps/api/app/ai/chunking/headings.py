class HeadingsSplitter:
    @staticmethod
    def extract_heading_chunks(normalized_content: dict) -> list[dict]:
        """Maps content sections paragraphs directly under active headings scopes."""
        sections = normalized_content.get("sections", [])
        paragraphs = normalized_content.get("paragraphs", [])
        
        chunks = []
        # Fallback to simple recursive splits if no headings sections map exists
        if not sections:
            return []
            
        current_heading = "General"
        current_text = []
        
        for p in paragraphs:
            text = p.get("text", "")
            # Check if paragraph matches any heading block
            matching_section = next((s for s in sections if s["title"] in text), None)
            if matching_section:
                if current_text:
                    chunks.append({
                        "content": "\n\n".join(current_text),
                        "heading": current_heading
                    })
                    current_text = []
                current_heading = matching_section["title"]
            current_text.append(text)
            
        if current_text:
            chunks.append({
                "content": "\n\n".join(current_text),
                "heading": current_heading
            })
            
        return chunks
