from app.main import app

# Expose app at the module level for uvicorn runner
__all__ = ["app"]
