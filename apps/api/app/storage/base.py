from abc import ABC, abstractmethod
from typing import Optional, Tuple

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file_bytes: bytes, filename: str, folder: str = "attachments") -> Tuple[str, str]:
        """
        Saves file bytes to storage.
        Returns Tuple of (storage_filename, storage_path).
        """
        pass

    @abstractmethod
    async def get_file(self, storage_path: str) -> bytes:
        """
        Retrieves file bytes from storage path.
        """
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """
        Deletes file from physical storage.
        """
        pass

    @abstractmethod
    def get_url(self, storage_path: str) -> str:
        """
        Returns public or relative URL path for accessing the file.
        """
        pass

BaseStorageProvider = StorageProvider

