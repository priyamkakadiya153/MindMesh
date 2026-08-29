import logging
from sqlalchemy.ext.asyncio import AsyncSession
from ..ai.embeddings.generator import EmbeddingGenerator
from ..vector.repository import VectorRepository

logger = logging.getLogger(__name__)

async def retrieve_vectors(
    db: AsyncSession,
    query_text: str,
    limit: int = 50,
    metric: str = "COSINE",
    filters: dict = None
) -> list[dict]:
    """Generates query embedding and runs similarity search against the vector repository."""
    logger.info(f"Translating query into vector space: '{query_text}'")
    # Generate query embedding using existing adapters
    query_embedding = EmbeddingGenerator.generate(query_text)
    
    # Run similarity search
    repo = VectorRepository(db)
    results = await repo.search(
        query_vector=query_embedding,
        limit=limit,
        metric=metric,
        filters=filters
    )
    return results
