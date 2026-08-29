import logging
import asyncio
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.ai.rag.retrieval import RAGRetrieval
from app.ai.context.builder import ContextBuilder
from app.ai.prompt.builder import PromptBuilder
from app.ai.llm.factory import LLMProviderFactory
from app.ai.llm.base import LLMSettings, UnifiedLLMResponse
from app.ai.rag.citations import RAGCitations
from app.ai.rag.evaluation import RAGEvaluator
from app.ai.rag.formatter import RAGFormatter
from app.ai.chat.session import ChatSessionManager
from app.ai.conversation.memory import ConversationMemoryManager
from app.ai.chat.history import ChatHistoryLoader
from app.ai.chat.analytics import ChatAnalytics

from app.ai.understanding import SemanticUnderstandingEngine, ContextResolver, CapabilityType, RequestIntent
from app.ai.capabilities.domain_executors import DomainExecutors
from app.actions.classifier import ActionClassifier
from app.actions.types import ActionStatus, ActionProposal, ActionIntentType

logger = logging.getLogger(__name__)

class MindMeshAIOrchestrator:
    """
    Universal MindMesh AI Conversational Intelligence Orchestrator.
    
    Owns semantic query understanding, context resolution, capability execution,
    multi-domain query execution, action proposal integration, grounded RAG synthesis,
    and conversation memory management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.retrieval = RAGRetrieval(db)

    async def execute(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        conversation_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider: str = "gemini",
        model: Optional[str] = None,
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 1024
    ) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()

        # 1. Resolve Chat Session & Save User Message
        chat = await ChatSessionManager.get_or_create_session(
            db=self.db,
            organization_id=org_id,
            user_id=user_id,
            workspace_id=workspace_id,
            chat_id=conversation_id,
            name=f"Query: {query[:25]}"
        )

        await ChatSessionManager.save_user_message(
            db=self.db,
            chat_id=chat.id,
            sender_id=user_id,
            organization_id=org_id,
            content=query
        )
        await self.db.commit()

        # 2. Load Conversation History & Pending Action State
        history = await ChatHistoryLoader.load_and_format_history(
            db=self.db,
            chat_id=chat.id,
            limit_count=20,
            token_limit=3000
        )
        pending_act = await ChatSessionManager.get_pending_action(self.db, chat.id)

        # 3. Conversational Understanding & Request Interpretation
        understanding = SemanticUnderstandingEngine.parse_request(query, history=history, pending_action=pending_act)
        capability = understanding.required_capability
        query_text = getattr(understanding, "rewritten_query", None) or query

        logger.info(f"[Orchestrator] Intent: {understanding.intent.value} | Capability: {capability.value}")

        ans = None
        action_proposal_dict = None
        citations = []

        # 4. Capability Execution
        if capability == CapabilityType.GENERAL_LLM:
            ans = await DomainExecutors.execute_general_knowledge(query_text, provider=provider, model=model or "gemini-2.5-flash")

        elif capability == CapabilityType.SQL_METADATA:
            ans = await DomainExecutors.execute_sql_metadata(self.db, org_id, workspace_id, query_text)

        elif capability == CapabilityType.TASK_SERVICE:
            ans = await DomainExecutors.execute_task_query(self.db, org_id, workspace_id, query_text)

        elif capability == CapabilityType.GRAPH_SERVICE:
            ans = await DomainExecutors.execute_graph_query(self.db, org_id, workspace_id, query_text)

        elif capability == CapabilityType.CONVERSATION_SEARCH_SERVICE:
            ans = await DomainExecutors.execute_conversation_query(self.db, org_id, workspace_id, query_text, user_id=user_id)

        elif capability == CapabilityType.SHARED_FILES_SERVICE:
            ans = await DomainExecutors.execute_shared_files_query(self.db, org_id, workspace_id, query_text, user_id=user_id)

        elif capability == CapabilityType.ACTION_AUDIT_SERVICE:
            ans = await DomainExecutors.execute_action_audit_query(self.db, user_id, org_id)

        elif capability == CapabilityType.MULTI_DOC_COMPARE:
            ans = await DomainExecutors.execute_multi_doc_compare(self.db, org_id, workspace_id, query_text, provider=provider, model=model or "gemini-2.5-flash")

        elif capability == CapabilityType.CONVERSATIONAL_SMALLTALK:
            ans = "Hello! How can I help you with your workspace documents, projects, tasks, or decisions today?"

        elif capability == CapabilityType.CLARIFY:
            ans = understanding.ambiguity or "What would you like me to add — a task, reminder, document, or something else?"

        elif capability == CapabilityType.ACTION_WORKFLOW:
            if understanding.entities and "fill_field" in understanding.entities:
                fill_field = understanding.entities.get("fill_field")
                val = understanding.entities.get("value")
                action_intent = understanding.entities.get("action_intent")
                if action_intent == "CREATE_REMINDER":
                    rem_text = understanding.entities.get("reminder_text") or "Review files"
                    prop = ActionProposal(
                        proposal_id=f"prop-{str(uuid4())[:8]}",
                        intent_type=ActionIntentType.CREATE_REMINDER,
                        title=f"Set Reminder: {rem_text} ({val})",
                        description=f"Action proposal to schedule reminder for {val}.",
                        parameters={"reminder_text": rem_text, "time_str": val},
                        workspace_id=str(workspace_id) if workspace_id else None,
                        user_id=str(user_id) if user_id else None,
                        confirmation_required=True,
                        status=ActionStatus.READY_FOR_CONFIRMATION
                    )
                else:
                    prop = ActionProposal(
                        proposal_id=f"prop-{str(uuid4())[:8]}",
                        intent_type=ActionIntentType.CREATE_TASK,
                        title=f"Create Task: {val}",
                        description=f"Action proposal to create task '{val}'.",
                        parameters={"title": val},
                        workspace_id=str(workspace_id) if workspace_id else None,
                        user_id=str(user_id) if user_id else None,
                        confirmation_required=True,
                        status=ActionStatus.READY_FOR_CONFIRMATION
                    )
            elif understanding.entities and "title" in understanding.entities:
                title = understanding.entities["title"]
                prop = ActionProposal(
                    proposal_id=f"prop-{str(uuid4())[:8]}",
                    intent_type=ActionIntentType.CREATE_TASK,
                    title=f"Create Task: {title}",
                    description=f"Action proposal to create task '{title}'.",
                    parameters={"title": title},
                    workspace_id=str(workspace_id) if workspace_id else None,
                    user_id=str(user_id) if user_id else None,
                    confirmation_required=True,
                    status=ActionStatus.READY_FOR_CONFIRMATION
                )
            else:
                prop = ActionClassifier.classify(query, workspace_id=workspace_id, user_id=user_id, resolved_context=understanding.conversation_refs)

            if prop:
                if prop.status == ActionStatus.NEEDS_CLARIFICATION:
                    pending_data = {
                        "intent": prop.intent_type.value,
                        "missing": prop.parameters.get("missing", ["title"]),
                        "reminder_text": prop.parameters.get("reminder_text")
                    }
                    await ChatSessionManager.set_pending_action(self.db, chat.id, pending_data)
                    ans = prop.clarification_prompt or "Sure. What should the task be about?"
                else:
                    await ChatSessionManager.set_pending_action(self.db, chat.id, None)
                    action_proposal_dict = prop.dict()
                    ans = f"I've prepared an action proposal: '{prop.title}'. Please confirm below to proceed."
            else:
                ans = "I can help with that. What details would you like to set?"

        else:
            # Universal Knowledge Intelligence Synthesis (DOCUMENT_RAG, KNOWLEDGE_SYNTHESIS, TASK_EXTRACTION, DISCUSSION_SUMMARY, etc.)
            template_name = "KnowledgeSynthesis"
            if capability == CapabilityType.TASK_EXTRACTION or understanding.intent == RequestIntent.EXTRACTION_REQUEST:
                template_name = "TaskAndDecisionExtraction"
            elif capability == CapabilityType.DISCUSSION_SUMMARY or understanding.intent == RequestIntent.SUMMARY_REQUEST:
                template_name = "DiscussionSummary"
            elif capability == CapabilityType.DOCUMENT_RAG or understanding.intent == RequestIntent.DOCUMENT_QUERY:
                template_name = "DocumentQA"

            retrieved_chunks = await self.retrieval.retrieve_grounded_chunks(
                user_id=user_id,
                org_id=org_id,
                query=query_text,
                workspace_id=workspace_id,
                project_id=project_id,
                limit=10,
                history=history
            )

            if retrieved_chunks and retrieved_chunks[0].get("not_found"):
                ans = f"I could not find the document '{retrieved_chunks[0]['document_name']}' in this workspace."
            elif not retrieved_chunks:
                if capability in [
                    CapabilityType.KNOWLEDGE_SYNTHESIS,
                    CapabilityType.DOCUMENT_RAG,
                    CapabilityType.TASK_EXTRACTION,
                    CapabilityType.DISCUSSION_SUMMARY,
                    CapabilityType.DECISION_SERVICE,
                    CapabilityType.PROJECT_SERVICE
                ] or any(w in query_text.lower() for w in ["workspace", "document", "file", "pdf", "project", "task", "decision", "discussion", "architect", "extract", "summar"]):
                    ans = "I couldn't find enough information in the available workspace knowledge to answer that reliably."
                else:
                    ans = await DomainExecutors.execute_general_knowledge(query_text, provider=provider, model=model or "gemini-2.5-flash")
            else:
                builder_chunks = [
                    {
                        "document_id": str(c["document_id"]),
                        "title": c.get("title"),
                        "content": c["content"],
                        "page": c["page"],
                        "score": c["score"],
                        "workspace_id": str(workspace_id) if workspace_id else None,
                        "project_id": str(project_id) if project_id else None
                    }
                    for c in retrieved_chunks
                ]

                context_res = await ContextBuilder.build_context(
                    db=self.db,
                    user_id=user_id,
                    org_id=org_id,
                    chunks=builder_chunks,
                    workspace_id=workspace_id,
                    project_id=project_id
                )

                prompt_res = PromptBuilder.build_prompt(
                    query=query_text,
                    context_string=context_res["context_string"],
                    history=history or [],
                    template_name=template_name
                )

                llm_provider = LLMProviderFactory.get_provider(provider, model or "gemini-2.5-flash")
                sys_prompt = prompt_res["messages"][0]["content"] if prompt_res["messages"] and prompt_res["messages"][0]["role"] == "system" else None
                user_prompt = prompt_res["messages"][-1]["content"] if prompt_res["messages"] else query

                from app.ai.gateway.models import AIRequest
                ai_req = AIRequest(
                    user_id=user_id,
                    organization_id=org_id,
                    workspace_id=workspace_id,
                    conversation_id=chat.id,
                    message=user_prompt,
                    system_context=sys_prompt,
                    conversation_context=history,
                    generation_parameters={"temperature": temperature or 0.2, "max_tokens": max_tokens or 1024}
                )

                llm_response = await llm_provider.generate_response(ai_req)
                ans = DomainExecutors.sanitize_answer(llm_response.content)

                citations = await RAGCitations.extract_citations(
                    db=self.db,
                    user_id=user_id,
                    org_id=org_id,
                    answer_text=ans,
                    retrieved_chunks=retrieved_chunks
                )

        latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

        ans = DomainExecutors.sanitize_answer(ans or "")

        # 5. Save Assistant Response in Database
        asst_msg = await ChatSessionManager.save_assistant_message(
            db=self.db,
            chat_id=chat.id,
            organization_id=org_id,
            content=ans,
            model=model or "gemini-2.5-flash",
            token_count=len(ans.split()),
            latency_ms=latency_ms,
            citations=citations,
            msg_metadata={
                "intent": understanding.intent.value,
                "capability": capability.value,
                "confidence": understanding.confidence
            }
        )
        await self.db.commit()

        # Update Conversation Memory Context
        await ConversationMemoryManager.update_context(
            db=self.db,
            chat_id=chat.id,
            org_id=org_id,
            user_message=query,
            assistant_response=ans
        )

        res_obj = {
            "answer": ans,
            "content": ans,
            "citations": citations,
            "confidence": understanding.confidence,
            "grounded": True,
            "intent": understanding.intent.value,
            "capability": capability.value,
            "conversation_id": chat.id,
            "chat_id": chat.id,
            "message_id": asst_msg.id,
            "latency_ms": latency_ms,
            "debug_info": {
                "understanding": understanding.dict(),
                "capability": capability.value,
                "latency_ms": latency_ms
            }
        }
        if action_proposal_dict:
            res_obj["action_proposal"] = action_proposal_dict

        return res_obj

    async def stream_execute(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        conversation_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider: str = "gemini",
        model: Optional[str] = None,
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 1024
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes SSE streaming query orchestration driven by universal capability routing.
        """
        # 1. Resolve Session & User Message
        chat = await ChatSessionManager.get_or_create_session(
            db=self.db,
            organization_id=org_id,
            user_id=user_id,
            workspace_id=workspace_id,
            chat_id=conversation_id,
            name=f"Query: {query[:25]}"
        )

        await ChatSessionManager.save_user_message(
            db=self.db,
            chat_id=chat.id,
            sender_id=user_id,
            organization_id=org_id,
            content=query
        )
        await self.db.commit()

        # Load History & Pending Action State
        history = await ChatHistoryLoader.load_and_format_history(
            db=self.db,
            chat_id=chat.id,
            limit_count=20,
            token_limit=3000
        )
        pending_act = await ChatSessionManager.get_pending_action(self.db, chat.id)

        # Conversational Understanding & Request Interpretation
        understanding = SemanticUnderstandingEngine.parse_request(query, history=history, pending_action=pending_act)
        capability = understanding.required_capability
        query_text = getattr(understanding, "rewritten_query", None) or query

        # Emit initial session metadata event
        yield {
            "type": "session",
            "conversation_id": str(chat.id),
            "chat_id": str(chat.id),
            "intent": understanding.intent.value,
            "capability": capability.value
        }

        ans = None
        action_proposal_dict = None
        citations = []

        if capability == CapabilityType.GENERAL_LLM:
            ans = await DomainExecutors.execute_general_knowledge(query_text, provider=provider, model=model or "gemini-2.5-flash")

        elif capability == CapabilityType.SQL_METADATA:
            ans = await DomainExecutors.execute_sql_metadata(self.db, org_id, workspace_id, query_text)

        elif capability == CapabilityType.TASK_SERVICE:
            ans = await DomainExecutors.execute_task_query(self.db, org_id, workspace_id, query_text)

        elif capability == CapabilityType.GRAPH_SERVICE:
            ans = await DomainExecutors.execute_graph_query(self.db, org_id, workspace_id, query_text)

        elif capability == CapabilityType.CONVERSATION_SEARCH_SERVICE:
            ans = await DomainExecutors.execute_conversation_query(self.db, org_id, workspace_id, query_text, user_id=user_id)

        elif capability == CapabilityType.SHARED_FILES_SERVICE:
            ans = await DomainExecutors.execute_shared_files_query(self.db, org_id, workspace_id, query_text, user_id=user_id)

        elif capability == CapabilityType.ACTION_AUDIT_SERVICE:
            ans = await DomainExecutors.execute_action_audit_query(self.db, user_id, org_id)

        elif capability == CapabilityType.MULTI_DOC_COMPARE:
            ans = await DomainExecutors.execute_multi_doc_compare(self.db, org_id, workspace_id, query_text, provider=provider, model=model or "gemini-2.5-flash")

        elif capability == CapabilityType.CONVERSATIONAL_SMALLTALK:
            ans = "Hello! How can I help you with your workspace documents, projects, tasks, or decisions today?"

        elif capability == CapabilityType.CLARIFY:
            ans = understanding.ambiguity or "What would you like me to add — a task, reminder, document, or something else?"

        elif capability == CapabilityType.ACTION_WORKFLOW:
            if understanding.entities and "fill_field" in understanding.entities:
                fill_field = understanding.entities.get("fill_field")
                val = understanding.entities.get("value")
                action_intent = understanding.entities.get("action_intent")
                if action_intent == "CREATE_REMINDER":
                    rem_text = understanding.entities.get("reminder_text") or "Review files"
                    prop = ActionProposal(
                        proposal_id=f"prop-{str(uuid4())[:8]}",
                        intent_type=ActionIntentType.CREATE_REMINDER,
                        title=f"Set Reminder: {rem_text} ({val})",
                        description=f"Action proposal to schedule reminder for {val}.",
                        parameters={"reminder_text": rem_text, "time_str": val},
                        workspace_id=str(workspace_id) if workspace_id else None,
                        user_id=str(user_id) if user_id else None,
                        confirmation_required=True,
                        status=ActionStatus.READY_FOR_CONFIRMATION
                    )
                else:
                    prop = ActionProposal(
                        proposal_id=f"prop-{str(uuid4())[:8]}",
                        intent_type=ActionIntentType.CREATE_TASK,
                        title=f"Create Task: {val}",
                        description=f"Action proposal to create task '{val}'.",
                        parameters={"title": val},
                        workspace_id=str(workspace_id) if workspace_id else None,
                        user_id=str(user_id) if user_id else None,
                        confirmation_required=True,
                        status=ActionStatus.READY_FOR_CONFIRMATION
                    )
            elif understanding.entities and "title" in understanding.entities:
                title = understanding.entities["title"]
                prop = ActionProposal(
                    proposal_id=f"prop-{str(uuid4())[:8]}",
                    intent_type=ActionIntentType.CREATE_TASK,
                    title=f"Create Task: {title}",
                    description=f"Action proposal to create task '{title}'.",
                    parameters={"title": title},
                    workspace_id=str(workspace_id) if workspace_id else None,
                    user_id=str(user_id) if user_id else None,
                    confirmation_required=True,
                    status=ActionStatus.READY_FOR_CONFIRMATION
                )
            else:
                prop = ActionClassifier.classify(query, workspace_id=workspace_id, user_id=user_id, resolved_context=understanding.conversation_refs)

            if prop:
                if prop.status == ActionStatus.NEEDS_CLARIFICATION:
                    pending_data = {
                        "intent": prop.intent_type.value,
                        "missing": prop.parameters.get("missing", ["title"]),
                        "reminder_text": prop.parameters.get("reminder_text")
                    }
                    await ChatSessionManager.set_pending_action(self.db, chat.id, pending_data)
                    ans = prop.clarification_prompt or "Sure. What should the task be about?"
                else:
                    await ChatSessionManager.set_pending_action(self.db, chat.id, None)
                    action_proposal_dict = json.loads(json.dumps(prop.dict(), default=str))
                    ans = f"I've prepared an action proposal: '{prop.title}'. Please confirm below to proceed."
                    yield {"type": "action_proposal", "action_proposal": action_proposal_dict}
            else:
                ans = "I can help with that. What details would you like to set?"

        else:
            # Universal Knowledge Intelligence Synthesis (DOCUMENT_RAG, KNOWLEDGE_SYNTHESIS, TASK_EXTRACTION, DISCUSSION_SUMMARY, etc.)
            template_name = "KnowledgeSynthesis"
            if capability == CapabilityType.TASK_EXTRACTION or understanding.intent == RequestIntent.EXTRACTION_REQUEST:
                template_name = "TaskAndDecisionExtraction"
            elif capability == CapabilityType.DISCUSSION_SUMMARY or understanding.intent == RequestIntent.SUMMARY_REQUEST:
                template_name = "DiscussionSummary"
            elif capability == CapabilityType.DOCUMENT_RAG or understanding.intent == RequestIntent.DOCUMENT_QUERY:
                template_name = "DocumentQA"

            retrieved_chunks = await self.retrieval.retrieve_grounded_chunks(
                user_id=user_id,
                org_id=org_id,
                query=query_text,
                workspace_id=workspace_id,
                project_id=project_id,
                limit=10,
                history=history
            )

            if retrieved_chunks and retrieved_chunks[0].get("not_found"):
                ans = f"I could not find the document '{retrieved_chunks[0]['document_name']}' in this workspace."
            elif not retrieved_chunks:
                if capability in [
                    CapabilityType.KNOWLEDGE_SYNTHESIS,
                    CapabilityType.DOCUMENT_RAG,
                    CapabilityType.TASK_EXTRACTION,
                    CapabilityType.DISCUSSION_SUMMARY,
                    CapabilityType.DECISION_SERVICE,
                    CapabilityType.PROJECT_SERVICE
                ] or any(w in query_text.lower() for w in ["workspace", "document", "file", "pdf", "project", "task", "decision", "discussion", "architect", "extract", "summar"]):
                    ans = "I couldn't find enough information in the available workspace knowledge to answer that reliably."
                else:
                    ans = await DomainExecutors.execute_general_knowledge(query_text, provider=provider, model=model or "gemini-2.5-flash")
            else:
                builder_chunks = [
                    {
                        "document_id": str(c["document_id"]),
                        "title": c.get("title"),
                        "content": c["content"],
                        "page": c["page"],
                        "score": c["score"],
                        "workspace_id": str(workspace_id) if workspace_id else None,
                        "project_id": str(project_id) if project_id else None
                    }
                    for c in retrieved_chunks
                ]

                context_res = await ContextBuilder.build_context(
                    db=self.db,
                    user_id=user_id,
                    org_id=org_id,
                    chunks=builder_chunks,
                    workspace_id=workspace_id,
                    project_id=project_id
                )

                prompt_res = PromptBuilder.build_prompt(
                    query=query_text,
                    context_string=context_res["context_string"],
                    history=history or [],
                    template_name=template_name
                )

                llm_provider = LLMProviderFactory.get_provider(provider, model or "gemini-2.5-flash")
                sys_prompt = prompt_res["messages"][0]["content"] if prompt_res["messages"] and prompt_res["messages"][0]["role"] == "system" else None
                user_prompt = prompt_res["messages"][-1]["content"] if prompt_res["messages"] else query

                from app.ai.gateway.models import AIRequest
                ai_req = AIRequest(
                    user_id=user_id,
                    organization_id=org_id,
                    workspace_id=workspace_id,
                    conversation_id=chat.id,
                    message=user_prompt,
                    system_context=sys_prompt,
                    conversation_context=history,
                    generation_parameters={"temperature": temperature or 0.2, "max_tokens": max_tokens or 1024}
                )

                full_text = ""
                async for stream_event in llm_provider.stream_response(ai_req):
                    if stream_event.type == "TOKEN" and stream_event.content:
                        full_text += stream_event.content
                        yield {"type": "token", "content": stream_event.content}

                ans = DomainExecutors.sanitize_answer(full_text)

                citations = await RAGCitations.extract_citations(
                    db=self.db,
                    user_id=user_id,
                    org_id=org_id,
                    answer_text=ans,
                    retrieved_chunks=retrieved_chunks
                )

        # Stream tokens if not already streamed in LLM path
        is_knowledge_streamed = capability not in [
            CapabilityType.GENERAL_LLM, CapabilityType.SQL_METADATA, CapabilityType.TASK_SERVICE,
            CapabilityType.GRAPH_SERVICE, CapabilityType.CONVERSATION_SEARCH_SERVICE,
            CapabilityType.SHARED_FILES_SERVICE,
            CapabilityType.ACTION_AUDIT_SERVICE, CapabilityType.MULTI_DOC_COMPARE,
            CapabilityType.CONVERSATIONAL_SMALLTALK, CapabilityType.CLARIFY, CapabilityType.ACTION_WORKFLOW
        ] and bool(retrieved_chunks and not retrieved_chunks[0].get("not_found"))

        if ans and not is_knowledge_streamed:
            for word in ans.split(" "):
                yield {"type": "token", "content": word + " "}
                await asyncio.sleep(0.01)

        # Save assistant message with action proposal metadata
        meta = {}
        if action_proposal_dict:
            meta["action_proposal"] = action_proposal_dict

        await ChatSessionManager.save_assistant_message(
            db=self.db,
            chat_id=chat.id,
            organization_id=org_id,
            content=ans or "",
            model=model or "gemini-2.5-flash",
            citations=citations,
            msg_metadata=meta if meta else None
        )
        await self.db.commit()

        final_evt = {
            "type": "final",
            "conversation_id": str(chat.id),
            "chat_id": str(chat.id),
            "answer": ans,
            "citations": citations,
            "confidence": understanding.confidence,
            "grounded": True,
            "intent": understanding.intent.value,
            "debug_info": {
                "understanding": understanding.dict(),
                "capability": capability.value
            }
        }
        if action_proposal_dict:
            final_evt["action_proposal"] = action_proposal_dict

        yield final_evt
