import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.ai.context.ranker import ContextRanker

def test_conflict_detection():
    print("=== Starting MindMesh Phase 2.3 Conflict Detection Test ===")

    chunks = [
        {
            "title": "Architecture Sync Document",
            "content": "JWT access tokens expire after 15 minutes.",
            "source_type": "document",
            "score": 0.9
        },
        {
            "title": "Security Specification 2026",
            "content": "JWT access tokens expire after 30 minutes.",
            "source_type": "document",
            "score": 0.88
        }
    ]

    res = ContextRanker.rank_and_deduplicate_chunks(chunks, "What is the JWT access token expiry?", top_k=5)

    assert res["conflicts_detected"] == True
    assert len(res["conflict_details"]) > 0

    conflict = res["conflict_details"][0]
    print(f"--> [SUCCESS] Conflict detected between '{conflict['source_a']}' and '{conflict['source_b']}'!")
    print(f"    Conflicting claim: '{conflict['claim']}'")
    print("=== Conflict Detection Test Passed 100%! ===")

if __name__ == "__main__":
    test_conflict_detection()
