import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.documents.models import Document
from app.documents.enums import ProcessingStatus
from app.core.security import create_access_token
from app.storage.factory import StorageProviderFactory
from app.knowledge.models import KnowledgeEntry, DocumentStatistic

@pytest.mark.asyncio
async def test_scanned_pdf_ocr_and_knowledge_pipeline(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]

    token = create_access_token(data={"sub": str(user.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Upload mock scanned PDF file (empty text to force OCR trigger)
    pdf_bytes = b"scanned pdf content with no text metadata layers"
    
    files = {
        "file": ("scanned_invoice.pdf", pdf_bytes, "application/pdf")
    }
    data = {
        "workspace_id": str(ws.id),
        "project_id": str(proj.id)
    }

    upload_response = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Explicitly write file buffer to active storage provider
    stmt = select(Document).where(Document.id == doc_id)
    doc = (await db_session.execute(stmt)).scalar_one()
    
    provider = StorageProviderFactory.get_provider()
    await provider.save(pdf_bytes, doc.storage_path)

    # 1. Trigger Reprocess manually
    reprocess_response = await client.post(f"/api/v1/documents/{doc_id}/reprocess", headers=headers)
    assert reprocess_response.status_code == 200
    assert reprocess_response.json()["status"] == "success"

    # 2. Get Knowledge Entry
    knowledge_response = await client.get(f"/api/v1/knowledge/{doc_id}", headers=headers)
    assert knowledge_response.status_code == 200
    k_data = knowledge_response.json()
    assert k_data["processing_state"] == "READY"
    assert "extracted_text" in k_data
    assert k_data["language"] == "en"

    # 3. Get Summary
    summary_response = await client.get(f"/api/v1/knowledge/{doc_id}/summary", headers=headers)
    assert summary_response.status_code == 200
    assert "summary" in summary_response.json()

    # 4. Get statistics
    stats_response = await client.get(f"/api/v1/knowledge/{doc_id}/statistics", headers=headers)
    assert stats_response.status_code == 200
    assert stats_response.json()["word_count"] > 0

    # 5. Get Quality rating
    quality_response = await client.get(f"/api/v1/documents/{doc_id}/quality", headers=headers)
    assert quality_response.status_code == 200
    assert quality_response.json()["quality_score"] > 0.0

    # 6. Get Processing Events
    events_response = await client.get(f"/api/v1/documents/{doc_id}/processing", headers=headers)
    assert events_response.status_code == 200
    stages = [event["stage"] for event in events_response.json()]
    assert "EXTRACTING" in stages
    assert "OCR" in stages
    assert "ENRICHING" in stages
