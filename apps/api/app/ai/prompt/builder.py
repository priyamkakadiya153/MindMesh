import re
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

PROMPT_VERSION = "mindmesh-chat-v1"

# Try importing tiktoken for accurate BPE token counting
try:
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        if not text:
            return 0
        return len(encoder.encode(text))
except Exception:
    def count_tokens(text: str) -> int:
        if not text:
            return 0
        return int(len(text.split()) * 1.3)

def normalize_user_message(query: Optional[str], max_length: int = 32000) -> str:
    """
    Normalizes user message before sending it to the model.
    Trims leading/trailing whitespace, rejects empty messages, and enforces length limits.
    """
    if query is None:
        raise ValueError("User message payload cannot be None.")
    
    normalized = query.strip()
    if not normalized:
        raise ValueError("User message cannot be empty or whitespace only.")
        
    if len(normalized) > max_length:
        raise ValueError(f"User message length ({len(normalized)} chars) exceeds maximum allowed limit of {max_length} chars.")
        
    return normalized

class TokenBudgetManager:
    """Manages dynamic token budget allocation for LLM prompt components."""
    def __init__(self, max_total_tokens: int = 8000):
        self.max_total_tokens = max_total_tokens
        self.system_max = min(1000, int(max_total_tokens * 0.15))
        self.retrieved_max = int(max_total_tokens * 0.50)
        self.history_max = int(max_total_tokens * 0.25)
        self.user_query_max = min(500, int(max_total_tokens * 0.10))
        self.reserved_response = min(2000, int(max_total_tokens * 0.25))

    def trim_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trims conversation history starting from oldest messages to fit within budget."""
        trimmed = []
        current_tokens = 0
        for msg in reversed(messages):
            t_count = count_tokens(msg.get("content", ""))
            if current_tokens + t_count > self.history_max:
                break
            trimmed.insert(0, msg)
            current_tokens += t_count
        return trimmed

    def trim_retrieved_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trims retrieved knowledge chunks starting from lowest score to fit within budget."""
        trimmed = []
        current_tokens = 0
        for chunk in chunks:
            c_text = chunk.get("content", "")
            t_count = count_tokens(c_text)
            if current_tokens + t_count > self.retrieved_max:
                break
            trimmed.append(chunk)
            current_tokens += t_count
        return trimmed

class PromptTemplateRegistry:
    """Pre-configured prompt templates for specific user workflows."""
    TEMPLATES = {
        "GeneralQA": (
            "You are MindMesh AI, an enterprise Knowledge Intelligence assistant.\n"
            "Answer the user's question accurately and concisely using the provided retrieved context and conversation history.\n"
            "Ground your answer strictly in the available context without hallucinating or inventing details.\n"
            "If insufficient evidence exists to answer reliably, respond: \"I couldn't find enough information in the available workspace knowledge to answer that reliably.\""
        ),
        "KnowledgeSynthesis": (
            "You are MindMesh AI, an enterprise Knowledge Intelligence assistant.\n"
            "Synthesize a clear, concise, factual answer to the user's question grounded strictly in the provided workspace knowledge context (documents, discussions, tasks, decisions).\n"
            "Present key facts, architectural decisions, and specifications accurately.\n"
            "If the provided context does not contain enough information to answer reliably, respond: \"I couldn't find enough information in the available workspace knowledge to answer that reliably.\""
        ),
        "TaskAndDecisionExtraction": (
            "You are MindMesh AI, an enterprise Knowledge Intelligence assistant.\n"
            "Your goal is to extract all tasks, responsibilities, deadlines, and decisions from the provided workspace discussion and context.\n"
            "Format the extraction in clean Markdown with clear sections:\n\n"
            "### Tasks\n"
            "- List each task with responsible person and deadline if mentioned.\n\n"
            "### Decisions\n"
            "- List each decision made.\n\n"
            "Only include tasks, assignments, deadlines, and decisions that are explicitly supported by the provided context. Do NOT invent missing items.\n"
            "If no relevant tasks or decisions exist in the context, respond: \"I couldn't find enough information in the available workspace knowledge to answer that reliably.\""
        ),
        "DiscussionSummary": (
            "You are MindMesh AI, an enterprise Knowledge Intelligence assistant.\n"
            "Summarize the provided project discussion or workspace context into a structured, readable summary covering:\n"
            "- Key discussion points\n"
            "- Decisions made\n"
            "- Completed work\n"
            "- Pending tasks and deadlines\n\n"
            "Only include information supported by the retrieved context.\n"
            "If no relevant context is available, respond: \"I couldn't find enough information in the available workspace knowledge to answer that reliably.\""
        ),
        "DocumentQA": (
            "You are MindMesh AI, an enterprise Knowledge Intelligence assistant.\n"
            "Answer the user's question grounded directly in the provided workspace document context.\n"
            "Reference the specific document name and page/section where available.\n"
            "If the document context does not contain enough information to answer reliably, respond: \"I couldn't find enough information in the available workspace knowledge to answer that reliably.\""
        ),
        "DocumentAnalysis": (
            "You are MindMesh Document Intelligence System.\n"
            "Analyze the provided document context below and present a structured analysis covering key findings, decisions, and technical specifications."
        ),
        "Summarization": (
            "You are MindMesh Organizational Memory Summarizer.\n"
            "Summarize the retrieved context and discussions into bullet points highlighting decisions, action items, and owners."
        ),
        "CodeReview": (
            "You are MindMesh Code & Architecture Reviewer.\n"
            "Evaluate the provided technical documentation and code blocks for security vulnerabilities, performance bottlenecks, and architectural consistency."
        ),
        "ProjectQuestions": (
            "You are MindMesh Project Intelligence Assistant.\n"
            "Retrieve project milestones, ownership, and current status from the provided context."
        )
    }

    @classmethod
    def get_template(cls, name: str = "GeneralQA") -> str:
        return cls.TEMPLATES.get(name, cls.TEMPLATES["GeneralQA"])

class PromptValidator:
    """Validates prompt integrity and strips sensitive credentials."""
    SECRET_REGEXES = [
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}", re.IGNORECASE),
        re.compile(r"Bearer\s+[a-zA-Z0-9\._-]{20,}", re.IGNORECASE),
        re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        sanitized = text
        for reg in cls.SECRET_REGEXES:
            sanitized = reg.sub("[REDACTED_SECRET]", sanitized)
        return sanitized

    @classmethod
    def validate(cls, user_query: str, total_tokens: int, max_budget: int) -> None:
        if not user_query or not user_query.strip():
            raise ValueError("User query cannot be empty.")
        if total_tokens > max_budget:
            raise ValueError(f"Assembled prompt total tokens ({total_tokens}) exceeds maximum budget ({max_budget}).")

class PromptBuilder:
    """Assembles structured, token-budgeted, validated prompts for LLM execution."""
    PROMPT_VERSION = PROMPT_VERSION

    def __init__(self, max_tokens: int = 8000):
        self.budget_mgr = TokenBudgetManager(max_total_tokens=max_tokens)

    @classmethod
    def build_prompt(
        cls,
        query: str,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        context_string: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        workspace_name: Optional[str] = None,
        organization_name: Optional[str] = None,
        template_name: str = "GeneralQA",
        max_tokens: int = 8000
    ) -> Dict[str, Any]:
        """Assembles prompt text, citation sources, and token statistics."""
        sanitized_raw = PromptValidator.sanitize(query)
        sanitized_query = normalize_user_message(sanitized_raw)

        budget_mgr = TokenBudgetManager(max_total_tokens=max_tokens)

        # 1. System Prompt & Instructions
        system_prompt = PromptTemplateRegistry.get_template(template_name)
        if organization_name or workspace_name:
            system_prompt += f"\nOrganization: {organization_name or 'Default'} | Workspace: {workspace_name or 'Default'}"

        # 2. Trim Retrieved Knowledge Chunks & Build Citation Index
        trimmed_chunks = budget_mgr.trim_retrieved_chunks(retrieved_chunks or [])
        sources = []
        context_blocks = []

        if context_string:
            retrieved_context_text = context_string
        else:
            for idx, chunk in enumerate(trimmed_chunks, start=1):
                citation_tag = f"[{idx}]"
                doc_title = chunk.get("title", "Untitled Document")
                sec_title = chunk.get("section_title")
                page = chunk.get("page_number") or chunk.get("page")

                heading_info = f"Document: {doc_title}"
                if sec_title:
                    heading_info += f" | Section: {sec_title}"
                if page:
                    heading_info += f" | Page: {page}"

                context_blocks.append(f"{citation_tag} {heading_info}\n{chunk.get('content', '')}")

                sources.append({
                    "citation_index": idx,
                    "citation_tag": citation_tag,
                    "chunk_id": str(chunk.get("chunk_id", "")),
                    "document_id": str(chunk.get("document_id", "")),
                    "title": doc_title,
                    "section_title": sec_title,
                    "page_number": page,
                    "score": chunk.get("score", 0.0)
                })

            retrieved_context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant documents retrieved."

        # 3. Trim Conversation History
        history_msgs = conversation_history or history or []
        trimmed_history = budget_mgr.trim_history(history_msgs)
        history_blocks = []

        for msg in trimmed_history:
            role = msg.get("role", "user").capitalize()
            content = PromptValidator.sanitize(msg.get("content", ""))
            history_blocks.append(f"{role}: {content}")

        history_text = "\n".join(history_blocks) if history_blocks else "No prior conversation history."

        # 4. Assemble Final Prompt Structure
        prompt_sections = [
            f"=== SYSTEM INSTRUCTIONS ===\n{system_prompt}",
            f"=== RETRIEVED KNOWLEDGE CONTEXT ===\n{retrieved_context_text}",
            f"=== CONVERSATION HISTORY ===\n{history_text}",
            f"=== CURRENT USER QUESTION ===\n{sanitized_query}",
            "=== ASSISTANT INSTRUCTIONS ===\nProvide a clear, direct answer referencing the citation tags like [1] or [2] where applicable."
        ]

        assembled_prompt = "\n\n".join(prompt_sections)
        total_tokens = count_tokens(assembled_prompt)

        # 5. Validate Prompt Integrity
        PromptValidator.validate(sanitized_query, total_tokens, budget_mgr.max_total_tokens)

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n=== RETRIEVED KNOWLEDGE CONTEXT ===\n{retrieved_context_text}"},
            {"role": "user", "content": sanitized_query}
        ]

        return {
            "prompt": assembled_prompt,
            "system_prompt": system_prompt,
            "user_query": sanitized_query,
            "messages": messages,
            "prompt_version": cls.PROMPT_VERSION,
            "template_name": template_name,
            "token_count": total_tokens,
            "sources": sources,
            "budget_summary": {
                "max_total_tokens": budget_mgr.max_total_tokens,
                "system_tokens": count_tokens(system_prompt),
                "context_tokens": count_tokens(retrieved_context_text),
                "history_tokens": count_tokens(history_text),
                "query_tokens": count_tokens(sanitized_query),
                "chunks_count": len(trimmed_chunks),
                "history_count": len(trimmed_history)
            }
        }
