from ..documents.enums import ProcessingStatus

def is_terminal_status(status: str) -> bool:
    return status in [ProcessingStatus.READY, ProcessingStatus.FAILED, ProcessingStatus.ARCHIVED]
