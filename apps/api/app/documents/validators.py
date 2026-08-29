import os
import re
from .exceptions import InvalidFileException, FileSizeExceededException, UnsupportedFileExtensionException
from .constants import MIME_TYPE_MAPPING, ALLOWED_EXTENSIONS, REJECTED_EXECUTABLE_EXTENSIONS
from ..core.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename by stripping path separators and non-printable characters."""
    clean_name = os.path.basename(filename).strip()
    clean_name = re.sub(r'[\r\n\t\0]', '', clean_name)
    clean_name = re.sub(r'[^a-zA-Z0-9_.\- ]', '_', clean_name)
    return clean_name or "unnamed_file"

def validate_file_attributes(filename: str, size: int, content_type: str):
    # Reject empty files
    if size <= 0:
        raise InvalidFileException("Cannot upload empty file.")

    # Validate file size (default max 100MB if setting not configured)
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 104857600)
    if size > max_size:
        raise FileSizeExceededException(max_size)

    # Sanitize and extract extension
    clean_filename = sanitize_filename(filename)
    ext = clean_filename.split(".")[-1].lower() if "." in clean_filename else ""

    # Security check: explicit rejection of executable / script files
    if ext in REJECTED_EXECUTABLE_EXTENSIONS:
        raise InvalidFileException(f"Security violation: Executable extension '.{ext}' is strictly prohibited.")

    # Validate file extension against allowed whitelist
    allowed = ALLOWED_EXTENSIONS
    if ext not in allowed:
        raise UnsupportedFileExtensionException(ext, list(allowed))

    # Validate MIME type or fallback extension compatibility
    if content_type not in MIME_TYPE_MAPPING:
        # Check if extension maps back to a valid MIME type
        valid_mime_found = any(e == ext for e in MIME_TYPE_MAPPING.values())
        if not valid_mime_found and content_type != "application/octet-stream":
            raise InvalidFileException(f"Unsupported content type: {content_type}")

