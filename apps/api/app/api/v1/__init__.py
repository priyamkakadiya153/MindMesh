from fastapi import APIRouter
from ...dashboard.router import router as dashboard_router
from ...projects.router import router as projects_router
from ...workspace.router import router as workspaces_router
from ...activity.router import router as activity_router
from ...notifications.router import router as notifications_router
from ...recent.router import router as recent_router
from ...favorites.router import router as favorites_router
from ...documents.router import router as documents_router
from ...documents.folders_router import router as folders_router
from ...knowledge.router import router as knowledge_router
from ...workspace.knowledge_workspace_router import router as workspace_experience_router
from .monitoring import router as monitoring_router
from .auth import router as auth_router
from .users import router as users_router
from .devices import router as devices_router
from .organizations import router as organizations_router
from ...roles.router import router as roles_router
from ...ai.embeddings.router import router as embeddings_router
from ...vector.router import router as vector_router
from ...search.router import router as search_router
from ...ai.context.router import router as context_router
from ...ai.prompt.router import router as prompt_router
from ...ai.conversation.router import router as conversation_router
from ...ai.chat.router import router as chat_router
from ...ai.gateway.router import router as ai_gateway_router
from ...ai.retrieval.router import router as retrieval_router
from ...ai.llm.router import router as llm_router
from ...ai.streaming.router import router as streaming_router
from ...ai.citation.router import router as citation_router
from ...ai.memory.router import router as memory_router
from ...agents.router import router as agents_router
from ...automation.automation.router import router as automation_router
from ...governance.router import router as governance_router
from ...invitations.router import router as invitations_router
from ...conversations.router import router as conversations_router
from ...conversations.messages_router import router as direct_messages_router
from ...conversations.groups_router import router as groups_router
from ...conversations.channels_router import router as channels_router
from ...members.router import router as members_router
from ...files.router import router as files_router
from ...conversations.advanced_router import router as advanced_messaging_router
from ...search.search_router import router as enterprise_search_router
from ...notifications.notifications_router import router as enterprise_notifications_router

router = APIRouter()


router.include_router(enterprise_search_router, prefix="/search", tags=["Enterprise Search Engine"])
router.include_router(enterprise_notifications_router, prefix="/notifications", tags=["Notifications & Activity"])

router.include_router(advanced_messaging_router, prefix="", tags=["Advanced Messaging Experience"])
router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
router.include_router(direct_messages_router, prefix="/messages", tags=["Direct Messages"])
router.include_router(groups_router, prefix="/groups", tags=["Group Chats"])
router.include_router(channels_router, prefix="/channels", tags=["Project Channels"])
router.include_router(files_router, prefix="/files", tags=["File Sharing & Media"])






router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(projects_router, prefix="/projects", tags=["Projects"])
router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
router.include_router(members_router, prefix="/members", tags=["Members & Directory"])

router.include_router(activity_router, prefix="/activity", tags=["Activity Feed"])
router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
router.include_router(recent_router, prefix="/recent", tags=["Recent Items"])
router.include_router(favorites_router, prefix="/favorites", tags=["Favorites Bookmarks"])
router.include_router(documents_router, prefix="", tags=["Documents"])
router.include_router(folders_router, prefix="", tags=["Folders"])
router.include_router(knowledge_router, prefix="", tags=["Knowledge Intelligence"])
router.include_router(workspace_experience_router, prefix="", tags=["Workspace Intelligence & Operations"])
router.include_router(monitoring_router, prefix="", tags=["Monitoring"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(devices_router, prefix="/devices", tags=["Devices"])
router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
router.include_router(invitations_router, prefix="/invitations", tags=["Invitations"])
from ...settings.router import router as settings_router

router.include_router(settings_router, prefix="", tags=["Settings & Audit"])
router.include_router(roles_router, prefix="", tags=["Roles & Permissions"])


router.include_router(embeddings_router, prefix="", tags=["AI Embeddings"])
router.include_router(vector_router, prefix="", tags=["Vector Platform"])
router.include_router(search_router, prefix="", tags=["Search Platform"])
router.include_router(context_router, prefix="", tags=["AI Context"])
router.include_router(prompt_router, prefix="", tags=["AI Prompt"])
router.include_router(conversation_router, prefix="", tags=["AI Conversation"])
router.include_router(ai_gateway_router, prefix="", tags=["AI Gateway Infrastructure"])
router.include_router(chat_router, prefix="", tags=["AI Chat & RAG"])
router.include_router(retrieval_router, prefix="", tags=["Hybrid Retrieval Engine"])
router.include_router(llm_router, prefix="", tags=["Multi-LLM Provider Platform"])
router.include_router(streaming_router, prefix="", tags=["AI Streaming Response Engine"])
router.include_router(citation_router, prefix="", tags=["Citation Rendering & Source Attribution"])
router.include_router(memory_router, prefix="", tags=["Conversation Memory & AI Summarization"])
router.include_router(agents_router, prefix="", tags=["Enterprise AI Agents"])
from ...agents.cognitive_router import router as cognitive_agents_router
router.include_router(cognitive_agents_router, prefix="", tags=["Cognitive Agents Persistence Layer"])
router.include_router(automation_router, prefix="", tags=["Enterprise Workflow Automation"])
from ...governance.router import router as governance_router
from ...timeline.router import router as timeline_router
from ...knowledge.hub_router import router as hub_router
from ...tasks.router import router as task_router
from ...projects.intelligence_router import router as project_intelligence_router
from ...intelligence.router import router as proactive_intelligence_router
from ...me.router import router as me_context_router
from ...evidence.router import router as evidence_router
from ...governance.router import router as governance_router
from ...operations.router import router as operations_router
from ...actions.router import router as actions_router
from ...workflows.router import router as workflows_router
from ...conversation_intelligence.router import router as conversation_intelligence_router
from ...search.universal_router import router as universal_search_router
from ...copilot.router import router as copilot_router
from ...me_context.adaptive_router import router as adaptive_context_router
from ...proactive.anticipatory_router import router as anticipatory_proactive_router
from ...governance.trust_router import router as trust_governance_router
from ...knowledge.relationship_router import router as relationship_graph_router
from ...knowledge.discovery_router import router as discovery_navigation_router
from ...knowledge.synthesis_router import router as synthesis_engine_router
from ...memory.os_router import router as memory_os_router
from ...agentic.action_router import router as agentic_action_router
from ...operations.autonomous_router import router as autonomous_operations_router
from ...collaboration.intelligence_router import router as collaborative_intelligence_router
from ...learning.learning_router import router as organizational_learning_router
from ...predictive.predictive_router import router as predictive_intelligence_router
from ...graph.memory_graph_router import router as memory_graph_router
from ...search.universal_search_router import router as universal_knowledge_search_router
from ...assistant.contextual_assistant_router import router as contextual_assistant_router
from ...proactive.workspace_router import router as proactive_workspace_router
from ...governance.knowledge_governance_router import router as governance_trust_router
from ...quality.knowledge_quality_router import router as knowledge_stewardship_quality_router
from ...workspace.knowledge_workspace_router import router as workspace_experience_router
from ...orchestration.memory_orchestrator_router import router as memory_orchestration_router
from ...learning.organizational_learning_router import router as learning_feedback_router
from ...decisions.decision_intelligence_router import router as decision_intelligence_router
from ...execution.execution_intelligence_router import router as execution_intelligence_router
from ...proactive.proactive_intelligence_router import router as proactive_intelligence_router
from ...maintenance.knowledge_maintenance_router import router as knowledge_maintenance_router
from ...graph.organizational_knowledge_graph_router import router as organizational_knowledge_graph_router
from ...memory.organizational_memory_fabric_router import router as organizational_memory_fabric_router
from ...workflows.workflow_orchestration_router import router as workflow_orchestration_router
from ...agents.multi_agent_orchestration_router import router as multi_agent_orchestration_router
from ...proactive.proactive_organizational_intelligence_router import router as proactive_organizational_intelligence_router
from ...workspace.knowledge_operating_system_router import router as knowledge_operating_system_router
from ...governance.knowledge_trust_quality_router import router as knowledge_trust_quality_router
from ...security.zero_trust_security_governance_router import router as zero_trust_security_governance_router
from ...operations.production_reliability_observability_router import router as production_reliability_observability_router
from ...performance.performance_scalability_router import router as performance_scalability_router
from ...analytics.advanced_data_intelligence_analytics_router import router as advanced_data_intelligence_analytics_router
from ...analytics.knowledge_automation_adaptive_learning_router import router as knowledge_automation_adaptive_learning_router
from ...execution.autonomous_work_execution_router import router as autonomous_work_execution_router
from ...interface.universal_knowledge_interface_router import router as universal_knowledge_interface_router
from ...analytics.proactive_intelligence_early_warning_router import router as proactive_intelligence_early_warning_router
from ...graph.organizational_graph_causal_reasoning_router import router as organizational_graph_causal_reasoning_router
from ...analytics.knowledge_synthesis_decision_intelligence_router import router as knowledge_synthesis_decision_intelligence_router
from ...analytics.organizational_experience_learning_router import router as organizational_experience_learning_router
from ...workflows.adaptive_workflow_router import router as adaptive_workflow_router
from ...agents.multi_agent_orchestration_router import router as multi_agent_orchestration_router
from ...extensions.extension_marketplace_router import router as extension_marketplace_router
from ...governance.policy_engine_router import router as policy_engine_router
from ...compliance.compliance_intelligence_router import router as compliance_intelligence_router
from ...simulation.organizational_simulation_router import router as organizational_simulation_router
from ...actions.router import router as action_engine_router
from ...actions.audit_router import router as audit_router
from ...proactive.detection_router import router as proactive_action_detection_router

router.include_router(proactive_action_detection_router, prefix="", tags=["AUTO-08 Proactive Action & Deadline Detection"])
router.include_router(timeline_router, prefix="", tags=["Knowledge Timeline"])
router.include_router(audit_router, prefix="", tags=["Action Audit Trail & Action Memory"])
router.include_router(hub_router, prefix="/knowledge", tags=["Unified Knowledge Hub"])
router.include_router(task_router, prefix="", tags=["Task Intelligence"])
router.include_router(project_intelligence_router, prefix="", tags=["Project Intelligence"])
router.include_router(proactive_intelligence_router, prefix="", tags=["Proactive Intelligence"])
router.include_router(me_context_router, prefix="", tags=["Personal User Context"])
router.include_router(evidence_router, prefix="", tags=["Knowledge Evidence & Quality"])
router.include_router(governance_router, prefix="", tags=["Knowledge Governance"])
router.include_router(operations_router, prefix="", tags=["Knowledge Operations & Analytics"])
router.include_router(actions_router, prefix="", tags=["Knowledge-to-Action Intelligence"])
router.include_router(workflows_router, prefix="", tags=["Agentic Workflows & Intelligent Orchestration"])
router.include_router(conversation_intelligence_router, prefix="", tags=["Intelligent Conversation & Meeting Intelligence"])
router.include_router(universal_search_router, prefix="", tags=["Universal Knowledge Search & Retrieval"])
router.include_router(copilot_router, prefix="", tags=["Knowledge Copilot & Grounded Q&A Engine"])
router.include_router(adaptive_context_router, prefix="", tags=["Personal Context & Adaptive Intelligence"])
router.include_router(anticipatory_proactive_router, prefix="", tags=["Proactive Knowledge & Anticipatory Intelligence"])
router.include_router(trust_governance_router, prefix="", tags=["Knowledge Governance & Trust Layer"])
router.include_router(relationship_graph_router, prefix="", tags=["Knowledge Graph & Relationship Intelligence"])
router.include_router(discovery_navigation_router, prefix="", tags=["Knowledge Discovery & Intelligent Navigation"])
router.include_router(synthesis_engine_router, prefix="", tags=["Knowledge Synthesis & Organizational Memory"])
router.include_router(memory_os_router, prefix="", tags=["Organizational Memory Operating System"])
router.include_router(agentic_action_router, prefix="", tags=["Agentic Action & Controlled Execution"])
router.include_router(autonomous_operations_router, prefix="", tags=["Autonomous Knowledge Operations & Continuous Memory"])
router.include_router(collaborative_intelligence_router, prefix="", tags=["Collaborative Intelligence & Team Memory"])
router.include_router(organizational_learning_router, prefix="", tags=["Organizational Learning & Knowledge Evolution"])
router.include_router(predictive_intelligence_router, prefix="", tags=["Predictive Project Intelligence & Decision Support"])
router.include_router(memory_graph_router, prefix="", tags=["Organizational Memory Graph & Knowledge Navigation"])
router.include_router(universal_knowledge_search_router, prefix="", tags=["Universal Knowledge Discovery & Intelligent Search"])
router.include_router(contextual_assistant_router, prefix="", tags=["Contextual AI Assistant & Knowledge Copilot"])
router.include_router(proactive_workspace_router, prefix="", tags=["Proactive Knowledge Workspace & Intelligent Workflow Orchestration"])
router.include_router(governance_trust_router, prefix="", tags=["Knowledge Governance, Trust & Organizational Control"])
router.include_router(knowledge_stewardship_quality_router, prefix="", tags=["Knowledge Stewardship, Quality & Continuous Maintenance"])
router.include_router(workspace_experience_router, prefix="", tags=["Knowledge Operations, Discovery & Intelligent Workspace Experience"])
router.include_router(memory_orchestration_router, prefix="", tags=["Organizational Memory Orchestration & Knowledge Graph Intelligence"])
router.include_router(learning_feedback_router, prefix="", tags=["Organizational Learning, Feedback & Adaptive Intelligence"])
router.include_router(decision_intelligence_router, prefix="", tags=["Decision Intelligence, Organizational Reasoning & Actionable Knowledge"])
router.include_router(execution_intelligence_router, prefix="", tags=["Execution Intelligence, Workflow Orchestration & Closed-Loop Action"])
router.include_router(proactive_intelligence_router, prefix="", tags=["Proactive Intelligence, Early Warning & Organizational Awareness"])
router.include_router(knowledge_maintenance_router, prefix="", tags=["Autonomous Knowledge Maintenance, Contextual Memory & Self-Improving Organizational Intelligence"])
router.include_router(organizational_knowledge_graph_router, prefix="", tags=["Organizational Knowledge Graph, Causal Intelligence & System-Wide Reasoning"])
router.include_router(organizational_memory_fabric_router, prefix="", tags=["Organizational Memory Fabric, Knowledge Synthesis & Continuous Context"])
router.include_router(workflow_orchestration_router, prefix="", tags=["Intelligent Workflow Orchestration & Controlled Autonomous Action"])
router.include_router(multi_agent_orchestration_router, prefix="", tags=["Multi-Agent Intelligence, Specialized AI Roles & Collaborative Reasoning"])
router.include_router(proactive_organizational_intelligence_router, prefix="", tags=["Proactive Organizational Intelligence & Anticipatory Decision Support"])
router.include_router(knowledge_operating_system_router, prefix="", tags=["Knowledge Operating System, Universal Workspace & Intelligent Information Experience"])
router.include_router(knowledge_trust_quality_router, prefix="", tags=["Trust, Knowledge Governance & Intelligence Quality System"])
router.include_router(zero_trust_security_governance_router, prefix="", tags=["Zero-Trust Security, Privacy & Data Governance"])
router.include_router(production_reliability_observability_router, prefix="", tags=["Reliability, Observability, Self-Healing & Production Operations"])
router.include_router(performance_scalability_router, prefix="", tags=["Performance, Scalability & High-Scale Architecture"])
router.include_router(advanced_data_intelligence_analytics_router, prefix="", tags=["Advanced Data Intelligence, Analytics & Organizational Insight"])
router.include_router(knowledge_automation_adaptive_learning_router, prefix="", tags=["Knowledge Automation, Continuous Learning & Adaptive Intelligence"])
router.include_router(autonomous_work_execution_router, prefix="", tags=["Autonomous Knowledge Operations & Intelligent Work Execution"])
router.include_router(universal_knowledge_interface_router, prefix="", tags=["Universal Knowledge Interface & Natural Language Operating Layer"])
router.include_router(proactive_intelligence_early_warning_router, prefix="", tags=["Proactive Intelligence, Predictive Understanding & Early-Warning System"])
router.include_router(organizational_graph_causal_reasoning_router, prefix="", tags=["Organizational Graph Intelligence, Causal Context & Systemic Reasoning"])
router.include_router(knowledge_synthesis_decision_intelligence_router, prefix="", tags=["Knowledge Synthesis, Organizational Reasoning & Decision Intelligence"])
router.include_router(organizational_experience_learning_router, prefix="", tags=["Organizational Memory, Experience Learning & Continuous Improvement"])
router.include_router(adaptive_workflow_router, prefix="", tags=["Adaptive Workflows & Intelligent Work Execution"])
router.include_router(multi_agent_orchestration_router, prefix="", tags=["Multi-Agent Intelligence & Specialist Collaboration"])
router.include_router(extension_marketplace_router, prefix="", tags=["Extension Platform, Marketplace & Plugin Ecosystem"])
router.include_router(policy_engine_router, prefix="", tags=["Enterprise Governance, Policy Control & Guardrails"])
router.include_router(compliance_intelligence_router, prefix="", tags=["Continuous Compliance, Risk Intelligence & Audit Operations"])
router.include_router(organizational_simulation_router, prefix="", tags=["Organizational Simulation, Digital Twin & What-If Intelligence"])
router.include_router(action_engine_router, prefix="", tags=["MindMesh Action & Intent Engine"])
