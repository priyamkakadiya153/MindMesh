class AgentException(Exception):
    """Base exception for all agent-related errors."""
    pass

class AgentNotFoundException(AgentException):
    """Raised when a requested agent cannot be found."""
    pass

class ToolException(AgentException):
    """Base exception for all tool-related errors."""
    pass

class ToolNotFoundException(ToolException):
    """Raised when a requested tool cannot be found in the registry."""
    pass

class PermissionDeniedException(AgentException):
    """Raised when an agent or user lacks permissions to execute an action or tool."""
    pass

class SessionException(AgentException):
    """Raised when session creation or management fails."""
    pass
