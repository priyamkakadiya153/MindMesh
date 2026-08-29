from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_content: bytes) -> dict:
        """Parses the document and returns a normalized dictionary layout."""
        pass

    @abstractmethod
    def extract_text(self, file_content: bytes) -> str:
        """Extracts all plain text content from the file."""
        pass

    @abstractmethod
    def extract_tables(self, file_content: bytes) -> list[dict]:
        """Extracts structured tables data from the file."""
        pass

    @abstractmethod
    def extract_images(self, file_content: bytes) -> list[dict]:
        """Extracts embedded images metadata from the file."""
        pass

    @abstractmethod
    def extract_metadata(self, file_content: bytes) -> dict:
        """Extracts document property metadata."""
        pass

    @abstractmethod
    def extract_structure(self, file_content: bytes) -> list[dict]:
        """Extracts heading tree/sections hierarchy structure."""
        pass
