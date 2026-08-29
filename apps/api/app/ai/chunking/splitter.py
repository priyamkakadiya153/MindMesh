from abc import ABC, abstractmethod

class BaseSplitter(ABC):
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """Splits the text into clean text chunks strings."""
        pass
