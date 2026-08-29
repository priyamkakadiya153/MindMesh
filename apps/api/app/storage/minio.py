import os
import asyncio
from typing import AsyncGenerator
from .base import BaseStorageProvider
from ..core.config import settings

class MinIOStorageProvider(BaseStorageProvider):
    def __init__(self):
        self.endpoint_url = os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000")
        self.bucket_name = os.getenv("MINIO_BUCKET", "mindmesh-docs")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self._client = None

    def _get_client(self):
        import boto3
        if not self._client:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=boto3.session.Config(signature_version="s3v4")
            )
        return self._client

    async def save(self, file_content: bytes, destination_path: str) -> str:
        client = self._get_client()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: client.put_object(
                Bucket=self.bucket_name,
                Key=destination_path,
                Body=file_content
            )
        )
        return destination_path

    async def download(self, source_path: str) -> bytes:
        client = self._get_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.get_object(Bucket=self.bucket_name, Key=source_path)
        )
        return response["Body"].read()

    async def delete(self, source_path: str) -> bool:
        client = self._get_client()
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: client.delete_object(Bucket=self.bucket_name, Key=source_path)
            )
            return True
        except Exception:
            return False

    async def exists(self, source_path: str) -> bool:
        client = self._get_client()
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: client.head_object(Bucket=self.bucket_name, Key=source_path)
            )
            return True
        except Exception:
            return False

    async def generate_url(self, source_path: str, expire_seconds: int = 3600) -> str:
        client = self._get_client()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": source_path},
                ExpiresIn=expire_seconds
            )
        )

    async def stream(self, source_path: str, chunk_size: int = 1024 * 64) -> AsyncGenerator[bytes, None]:
        client = self._get_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.get_object(Bucket=self.bucket_name, Key=source_path)
        )
        body = response["Body"]
        while True:
            chunk = await loop.run_in_executor(None, lambda: body.read(chunk_size))
            if not chunk:
                break
            yield chunk
