from .providers import EmbeddingProvider

class EmbeddingGenerator:
    @staticmethod
    def generate(text: str) -> list[float]:
        return EmbeddingProvider.generate_embedding(text)

    @classmethod
    def generate_batch(cls, texts: list[str]) -> list[list[float]]:
        return [cls.generate(text) for text in texts]
