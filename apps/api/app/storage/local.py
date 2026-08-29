import os
import uuid
import aiofiles
from pathlib import Path
from typing import AsyncGenerator, Tuple
from .base import BaseStorageProvider
from ..core.config import settings

class LocalStorageProvider(BaseStorageProvider):
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, path: str) -> Path:
        return self.upload_dir / path.lstrip("/")

    async def save_file(self, file_bytes: bytes, filename: str, folder: str = "attachments") -> Tuple[str, str]:
        storage_filename = f"{uuid.uuid4().hex}_{filename}"
        destination_path = f"{folder}/{storage_filename}"
        full_path = self._get_full_path(destination_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_bytes)
        return storage_filename, destination_path

    async def get_file(self, storage_path: str) -> bytes:
        return await self.download(storage_path)

    async def delete_file(self, storage_path: str) -> bool:
        return await self.delete(storage_path)

    def get_url(self, storage_path: str) -> str:
        return f"/api/v1/files/download/{storage_path}"

    async def save(self, file_content: bytes, destination_path: str) -> str:
        full_path = self._get_full_path(destination_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_content)
        
        return destination_path

    async def download(self, source_path: str) -> bytes:
        full_path = self._get_full_path(source_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")
        
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, source_path: str) -> bool:
        full_path = self._get_full_path(source_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, source_path: str) -> bool:
        full_path = self._get_full_path(source_path)
        return full_path.exists()

    async def generate_url(self, source_path: str, expire_seconds: int = 3600) -> str:
        # Returns a mock localhost API download URL path
        return f"http://localhost:{settings.PORT}/api/v1/documents/download-path/{source_path}"

    async def stream(self, source_path: str, chunk_size: int = 1024 * 64) -> AsyncGenerator[bytes, None]:
        full_path = self._get_full_path(source_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")
        
        async with aiofiles.open(full_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
