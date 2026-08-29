from fastapi import HTTPException, status

class DocumentNotFoundException(HTTPException):
    def __init__(self, document_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} was not found or access is denied."
        )

class InvalidFileException(HTTPException):
    def __init__(self, detail: str = "The uploaded file is invalid or empty."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class FileSizeExceededException(HTTPException):
    def __init__(self, max_size_bytes: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum limit of {max_size_bytes / (1024 * 1024):.1f} MB."
        )

class UnsupportedFileExtensionException(HTTPException):
    def __init__(self, ext: str, allowed: list[str]):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '.{ext}' is not supported. Allowed formats: {', '.join(allowed)}."
        )
