from .base import BaseStorageProvider
from .local import LocalStorageProvider
from .s3 import S3StorageProvider
from .minio import MinIOStorageProvider
from ..core.config import settings

class StorageProviderFactory:
    _instance = None

    @classmethod
    def get_provider(cls) -> BaseStorageProvider:
        if cls._instance is not None:
            return cls._instance

        provider_name = settings.STORAGE_PROVIDER.lower()
        if provider_name == "s3":
            cls._instance = S3StorageProvider()
        elif provider_name == "minio":
            cls._instance = MinIOStorageProvider()
        else:
            cls._instance = LocalStorageProvider()
        
        return cls._instance
