import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.ai.prompt.builder import (
    PromptBuilder,
    TokenBudgetManager,
    PromptTemplateRegistry,
    PromptValidator,
    count_tokens
)

def test_prompt_builder_unit():
    print("--- Starting MindMesh Phase 3.5 Prompt Builder & Context Assembly Test ---")

    # 1. Test Sanitization & Security Validation
    dirty_text = "Here is my secret key: sk-proj-1234567890abcdef1234567890 and Bearer eyJhbGciOiJIUzI1NiIsInR..."
    clean_text = PromptValidator.sanitize(dirty_text)
    assert "sk-proj-" not in clean_text
    assert "[REDACTED_SECRET]" in clean_text
    print("--> Verified PromptValidator Security Sanitization (Secrets & API Keys stripped).")

    # 2. Test Token Budgeting & Trimming
    budget_mgr = TokenBudgetManager(max_total_tokens=1000)
    messages = [
        {"role": "user", "content": "Message 1 " * 50},
        {"role": "assistant", "content": "Message 2 " * 50},
        {"role": "user", "content": "Message 3 " * 50},
        {"role": "assistant", "content": "Message 4 " * 50},
    ]
    trimmed_msgs = budget_mgr.trim_history(messages)
    assert len(trimmed_msgs) < len(messages)
    assert trimmed_msgs[-1]["content"].startswith("Message 4")
    print(f"--> Verified TokenBudgetManager History Trimming (Retained newest {len(trimmed_msgs)} of {len(messages)} messages).")

    # 3. Test Template System & Modular Assembly
    chunks = [
        {
            "chunk_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "title": "Architecture Specification",
            "section_title": "Database Overview",
            "page_number": 3,
            "content": "MindMesh uses PostgreSQL with pgvector for storing document embeddings.",
            "score": 0.94
        },
        {
            "chunk_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "title": "Deployment Manual",
            "section_title": "Kubernetes Setup",
            "page_number": 12,
            "content": "Run `kubectl apply -f mindmesh-deployment.yaml` to launch the API backend.",
            "score": 0.88
        }
    ]

    builder = PromptBuilder(max_tokens=4000)
    res = builder.build_prompt(
        query="How do I set up the database and deploy MindMesh?",
        retrieved_chunks=chunks,
        conversation_history=messages,
        workspace_name="Engineering Core",
        template_name="GeneralQA"
    )

    assert "=== SYSTEM INSTRUCTIONS ===" in res["prompt"]
    assert "=== RETRIEVED KNOWLEDGE CONTEXT ===" in res["prompt"]
    assert "=== CONVERSATION HISTORY ===" in res["prompt"]
    assert "=== CURRENT USER QUESTION ===" in res["prompt"]

    assert len(res["sources"]) == 2
    assert res["sources"][0]["citation_tag"] == "[1]"
    assert res["sources"][0]["title"] == "Architecture Specification"
    assert res["sources"][1]["citation_tag"] == "[2]"
    assert res["sources"][1]["title"] == "Deployment Manual"

    assert res["token_count"] > 0
    assert res["token_count"] <= 4000
    print(f"--> Verified PromptBuilder Modular Assembly ({res['token_count']} tokens, {len(res['sources'])} citation sources).")

    # 4. Test Template Switching
    doc_analysis_res = builder.build_prompt(
        query="Analyze the architecture document.",
        retrieved_chunks=chunks,
        template_name="DocumentAnalysis"
    )
    assert "Document Intelligence System" in doc_analysis_res["system_prompt"]
    print("--> Verified Template Switching (DocumentAnalysis template loaded).")

    print("=== MindMesh Phase 3.5 Prompt Builder & Context Assembly Tests Passed Successfully! ===")

if __name__ == "__main__":
    test_prompt_builder_unit()
