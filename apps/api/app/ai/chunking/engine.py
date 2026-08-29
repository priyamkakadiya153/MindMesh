from .recursive import RecursiveCharacterTextSplitter
from .tables import TableSplitter
from .headings import HeadingsSplitter
from .metadata import ChunkMetadataBuilder
from .statistics import TokenCounter

class ChunkingEngine:
    @staticmethod
    def chunk_document(doc_rec: any, normalized_content: dict) -> list[dict]:
        """Orchestrates recursive, headings and tables splitting strategies on parsed document."""
        chunks = []
        
        # 1. Table chunks extraction
        table_chunks = TableSplitter.extract_table_chunks(normalized_content)
        for idx, tc in enumerate(table_chunks):
            meta = ChunkMetadataBuilder.build_metadata(
                doc_rec=doc_rec,
                heading="Tabular Data",
                custom=tc["metadata"]
            )
            chunks.append({
                "content": tc["content"],
                "token_count": TokenCounter.count_tokens(tc["content"]),
                "metadata": meta
            })

        # 2. Heading-aware chunk extraction
        heading_chunks = HeadingsSplitter.extract_heading_chunks(normalized_content)
        if heading_chunks:
            for hc in heading_chunks:
                # If chunk content is too large, split recursively
                splitter = RecursiveCharacterTextSplitter()
                sub_chunks = splitter.split(hc["content"])
                for sc in sub_chunks:
                    meta = ChunkMetadataBuilder.build_metadata(
                        doc_rec=doc_rec,
                        heading=hc["heading"]
                    )
                    chunks.append({
                        "content": sc,
                        "token_count": TokenCounter.count_tokens(sc),
                        "metadata": meta
                    })
        else:
            # Fallback to simple paragraph-level recursive splitting
            paragraphs = normalized_content.get("paragraphs", [])
            text = "\n\n".join([p["text"] for p in paragraphs if isinstance(p, dict) and "text" in p])
            splitter = RecursiveCharacterTextSplitter()
            text_chunks = splitter.split(text)
            for sc in text_chunks:
                meta = ChunkMetadataBuilder.build_metadata(
                    doc_rec=doc_rec,
                    heading="General"
                )
                chunks.append({
                    "content": sc,
                    "token_count": TokenCounter.count_tokens(sc),
                    "metadata": meta
                })

        return chunks
