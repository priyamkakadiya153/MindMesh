import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.documents.models import Document
from app.documents.enums import ProcessingStatus
from app.processing.models import DocumentContent
from app.core.security import create_access_token
from app.storage.factory import StorageProviderFactory

@pytest.mark.asyncio
async def test_markdown_parsing_pipeline(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]

    token = create_access_token(data={"sub": str(user.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Upload mock markdown content first
    md_content = b"""---
title: Spec Ingestion
author: MindMesh Dev
---

# Heading 1
This is paragraph A content.

## Heading 2
This is paragraph B content with a markdown table.

| Col A | Col B |
|---|---|
| Value 1 | Value 2 |

![Image Alt Text](http://example.com/logo.png)
"""
    
    files = {
        "file": ("spec.md", md_content, "text/markdown")
    }
    data = {
        "workspace_id": str(ws.id),
        "project_id": str(proj.id)
    }

    upload_response = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Retrieve local storage provider to write mock file explicitly for ingestion pipeline simulation
    stmt = select(Document).where(Document.id == doc_id)
    doc = (await db_session.execute(stmt)).scalar_one()
    
    provider = StorageProviderFactory.get_provider()
    await provider.save(md_content, doc.storage_path)

    # 1. Trigger process pipeline explicitly
    process_response = await client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert process_response.status_code == 200
    assert process_response.json()["status"] == "success"

    # 2. Get normalized content
    content_response = await client.get(f"/api/v1/documents/{doc_id}/content", headers=headers)
    assert content_response.status_code == 200
    content_json = content_response.json()
    
    assert "Heading 1" in [s["title"] for s in content_json["sections"]]
    assert len(content_json["paragraphs"]) >= 2
    assert len(content_json["tables"]) == 1
    assert content_json["tables"][0]["data"][0] == ["Col A", "Col B"]
    assert len(content_json["images"]) == 1
    assert content_json["images"][0]["alt"] == "Image Alt Text"

    # 3. Get structure sections
    struct_response = await client.get(f"/api/v1/documents/{doc_id}/structure", headers=headers)
    assert struct_response.status_code == 200
    assert len(struct_response.json()) == 2
    assert struct_response.json()[0]["title"] == "Heading 1"

    # 4. Get statistics
    stats_response = await client.get(f"/api/v1/documents/{doc_id}/statistics", headers=headers)
    assert stats_response.status_code == 200
    assert stats_response.json()["word_count"] > 10
    assert stats_response.json()["table_count"] == 1
    assert stats_response.json()["image_count"] == 1
