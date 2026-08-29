import os
import aiofiles
from pathlib import Path
from uuid import uuid4
from typing import Tuple, Optional
from .base import StorageProvider
import logging

logger = logging.getLogger("mindmesh.storage")

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_path = Path(base_dir)
        else:
            # Default to apps/api/storage/uploads
            current_dir = Path(__file__).resolve().parent.parent.parent
            self.base_path = current_dir / "storage" / "uploads"
        
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _sanitize_path(self, relative_path: str) -> Path:
        target_path = (self.base_path / relative_path).resolve()
        if not str(target_path).startswith(str(self.base_path.resolve())):
            raise ValueError("Path traversal attempt detected.")
        return target_path

    async def save_file(self, file_bytes: bytes, filename: str, folder: str = "attachments") -> Tuple[str, str]:
        ext = os.path.splitext(filename)[1].lower()
        unique_id = uuid4().hex
        storage_filename = f"{unique_id}{ext}"
        
        folder_path = self.base_path / folder / unique_id[:2]
        folder_path.mkdir(parents=True, exist_ok=True)
        
        full_file_path = folder_path / storage_filename
        relative_storage_path = f"{folder}/{unique_id[:2]}/{storage_filename}"

        async with aiofiles.open(full_file_path, "wb") as f:
            await f.write(file_bytes)

        return storage_filename, relative_storage_path

    async def get_file(self, storage_path: str) -> bytes:
        full_file_path = self._sanitize_path(storage_path)
        if not full_file_path.exists():
            raise FileNotFoundError(f"File not found at path {storage_path}")

        async with aiofiles.open(full_file_path, "rb") as f:
            return await f.read()

    async def delete_file(self, storage_path: str) -> bool:
        try:
            full_file_path = self._sanitize_path(storage_path)
            if full_file_path.exists():
                os.remove(full_file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file at {storage_path}: {e}")
            return False

    def get_url(self, storage_path: str) -> str:
        return f"/api/v1/files/preview?path={storage_path}"

default_storage_provider = LocalStorageProvider()
