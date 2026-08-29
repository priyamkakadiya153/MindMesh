import pytest
from app.main import app

@pytest.mark.asyncio
async def test_shared_files_endpoints_schema():
    """Verify Shared Files router definitions and endpoints including Phase 2 enterprise features."""
    routes = [r.path for r in app.routes]
    assert "/api/v1/files/upload" in routes
    assert "/api/v1/files" in routes
    assert "/api/v1/files/storage/stats" in routes
    assert "/api/v1/files/{id}" in routes
    assert "/api/v1/files/{id}/download" in routes
    assert "/api/v1/files/{id}/preview" in routes
    assert "/api/v1/files/{id}/restore" in routes
    assert "/api/v1/files/{id}/versions" in routes
    assert "/api/v1/files/{id}/versions/{version_number}/restore" in routes
    assert "/api/v1/files/{id}/versions/{version_number}/download" in routes
    assert "/api/v1/files/{id}/audit" in routes
    print("[TEST PASSED] All Shared Files Phase 1 & Phase 2 router endpoints registered successfully.")
