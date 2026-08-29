from .splitter import BaseSplitter
from .statistics import TokenCounter

class RecursiveCharacterTextSplitter(BaseSplitter):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        if not text:
            return []

        paragraphs = text.split("\n\n")
        chunks = []
        
        current_chunk = ""
        for p in paragraphs:
            p_tokens = TokenCounter.count_tokens(p)
            if p_tokens > self.chunk_size:
                # If paragraph itself is too large, split by sentences
                sentences = p.split(". ")
                for s in sentences:
                    s_tokens = TokenCounter.count_tokens(s)
                    if TokenCounter.count_tokens(current_chunk + s) > self.chunk_size:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = s + ". "
                    else:
                        current_chunk += s + ". "
            else:
                if TokenCounter.count_tokens(current_chunk + p) > self.chunk_size:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = p + "\n\n"
                else:
                    current_chunk += p + "\n\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
