import logging

logger = logging.getLogger(__name__)

def validate_vector_dimension(vector: list[float], expected: int = 1536) -> bool:
    """Validates that the generated vector dimension matches specifications."""
    if not isinstance(vector, list):
        return False
    return len(vector) == expected
