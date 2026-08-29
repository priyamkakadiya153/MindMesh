import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.core.security import create_access_token
from app.documents.models import Document
from app.storage.factory import StorageProviderFactory

@pytest.mark.asyncio
async def test_monitoring_routes(client: AsyncClient):
    """Ensures health checkpoints report connected/healthy states successfully."""
    # 1. Test liveness
    liveness_res = await client.get("/api/v1/monitoring/liveness")
    assert liveness_res.status_code == 200
    assert liveness_res.json()["status"] == "alive"

    # 2. Test readiness
    readiness_res = await client.get("/api/v1/monitoring/readiness")
    assert readiness_res.status_code == 200
    assert readiness_res.json()["status"] == "ready"

    # 3. Test health details
    health_res = await client.get("/api/v1/monitoring/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"
    assert health_res.json()["services"]["database"] == "connected"

@pytest.mark.asyncio
async def test_full_document_lifecycle_flow(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    """Validates complete upload, metadata update, reprocess, and deletion cycles."""
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]

    token = create_access_token(data={"sub": str(user.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Step 1: Upload PDF document
    pdf_content = b"pdf raw content stream to parse and index"
    files = {
        "file": ("manual.pdf", pdf_content, "application/pdf")
    }
    data = {
        "workspace_id": str(ws.id),
        "project_id": str(proj.id)
      }

    upload_res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Write file content to mock storage path
    stmt = select(Document).where(Document.id == doc_id)
    doc = (await db_session.execute(stmt)).scalar_one()
    provider = StorageProviderFactory.get_provider()
    await provider.save(pdf_content, doc.storage_path)

    # Step 2: PATCH Custom Metadata
    meta_payload = {
        "title": "Corporate Ingestion Manual",
        "description": "Integration procedures guide",
        "confidentiality": "restricted"
    }
    meta_res = await client.patch(f"/api/v1/documents/{doc_id}/metadata", json=meta_payload, headers=headers)
    assert meta_res.status_code == 200
    assert meta_res.json()["title"] == "Corporate Ingestion Manual"

    # Step 3: Run pipeline processing
    proc_res = await client.post(f"/api/v1/documents/{doc_id}/reprocess", headers=headers)
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "success"

    # Step 4: Retrieve Statistics
    stats_res = await client.get(f"/api/v1/knowledge/{doc_id}/statistics", headers=headers)
    assert stats_res.status_code == 200
    assert stats_res.json()["word_count"] > 0

    # Step 5: Soft Delete Document
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify document is deactivated
    db_session.expire_all()
    doc_check = (await db_session.execute(select(Document).where(Document.id == doc_id))).scalar_one()
    assert doc_check.is_active is False
