from fastapi import HTTPException, status

class WorkspaceError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class WorkspaceNotFoundError(WorkspaceError):
    def __init__(self, detail: str = "Workspace not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class DuplicateWorkspaceNameError(WorkspaceError):
    def __init__(self, detail: str = "A workspace with this name already exists in the organization"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class WorkspaceAccessDeniedError(WorkspaceError):
    def __init__(self, detail: str = "Access to this workspace is denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
