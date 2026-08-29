import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.service import DocumentService
from app.ai.extraction.file_analyzer import FileIntelligenceAnalyzer
from app.parsers.dst_parser import DSTParser

async def test_specialized_dst_file():
    print("=== Starting MindMesh Phase 2.5 Tajima DST Specialized File Test ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Create DST header (512 bytes)
        header_str = (
            "LA:DRAGON_LOGO\r"
            "ST:   12500\r"
            "CO:    4\r"
            "+X:  250\r"
            "-X:  250\r"
            "+Y:  300\r"
            "-Y:  300\r"
            "\x1a"
        )
        dst_binary = header_str.encode("ascii").ljust(512, b"\x00") + b"\x00" * 100

        # Verify DSTParser direct parsing
        parser = DSTParser()
        parser = DSTParser()
        parsed = parser.parse(dst_binary)
        dst_meta = parsed.get("metadata", {})
        print("--> [DST PARSER DIRECT] Extracted:", dst_meta)

        assert dst_meta["format"] == "Tajima DST Embroidery"
        assert dst_meta["label"] == "DRAGON_LOGO"
        assert dst_meta["stitch_count"] == 12500
        assert dst_meta["color_changes"] == 4
        assert dst_meta["width_mm"] == 50.0
        assert dst_meta["height_mm"] == 60.0

        # Upload DST Document to DB
        org = Organization(name="DST Test Org", slug=f"dst-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="DST Workspace", slug=f"dst-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"dst_user_{u_id}@mindmesh.com",
            username=f"dst_user_{u_id}",
            first_name="DST",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=dst_binary,
            filename="dragon_logo.dst",
            content_type="application/x-tajima-dst",
            org_id=org.id,
            workspace_id=ws.id,
            user_id=user.id,
            title="Dragon Embroidery Logo",
            visibility="private"
        )
        await session.commit()

        # Run FileIntelligenceAnalyzer
        analyzer = FileIntelligenceAnalyzer(session)
        intel = await analyzer.analyze_document(doc.id)

        print(f"--> [FILE INTELLIGENCE] Document Type: {intel.document_type}")
        print(f"--> [FILE INTELLIGENCE] Summary: {intel.summary}")
        print(f"--> [FILE INTELLIGENCE] Topics: {intel.topics}")
        print(f"--> [FILE INTELLIGENCE] Facts: {[f['fact'] for f in intel.facts]}")

        assert intel.status == "COMPLETED"
        assert "Embroidery" in intel.document_type
        assert "12,500" in intel.summary or "12500" in intel.summary
        assert any("12,500" in f["fact"] or "12500" in f["fact"] for f in intel.facts)
        assert any("50.0" in f["fact"] or "width" in f["fact"].lower() for f in intel.facts)

    print("=== Tajima DST Specialized File Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_specialized_dst_file())
