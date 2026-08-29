from enum import Enum

class StorageProvider(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"

class ProcessingStatus(str, Enum):
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

class DocumentVisibility(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    INTERNAL = "internal"
