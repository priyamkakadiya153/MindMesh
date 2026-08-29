from fastapi import HTTPException, status

class ProjectError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class ProjectNotFoundError(ProjectError):
    def __init__(self, detail: str = "Project not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class DuplicateProjectNameError(ProjectError):
    def __init__(self, detail: str = "A project with this name already exists in this workspace"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ProjectAccessDeniedError(ProjectError):
    def __init__(self, detail: str = "Access to this project is denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
