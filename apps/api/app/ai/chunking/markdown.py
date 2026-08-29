from .splitter import BaseSplitter

class MarkdownSplitter(BaseSplitter):
    def split(self, text: str) -> list[str]:
        if not text:
            return []
            
        chunks = []
        lines = text.split("\n")
        
        current_chunk = []
        for line in lines:
            if line.startswith("#") and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
                
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return [c.strip() for c in chunks if c.strip()]
