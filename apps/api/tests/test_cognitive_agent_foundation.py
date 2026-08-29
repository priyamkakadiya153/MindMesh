"""
MindMesh — CA-01 Cognitive Agent Foundation & Contract Validation Test Suite

Validates domain contracts, enum boundaries, safety invariants, ActionCandidate
conversion, and organization/workspace boundary contracts.
"""

import pytest
import uuid
from datetime import datetime

from app.agents.cognitive_contracts import (
    CognitiveAgentContract,
    CognitiveAgentStatus,
    CognitiveAgentType,
    CognitiveAgentScopeContract,
    CognitiveAgentScopeType,
    CognitiveAgentTriggerContract,
    CognitiveAgentTriggerType,
    CognitiveAgentOutputContract,
    CognitiveAgentOutputType,
    CognitiveAgentProvenanceContract,
    CognitiveAgentExecutionContract,
    CognitiveAgentExecutionStatus
)
from app.actions.candidate import CandidateStatus, ActionType, IntentCategory


def test_cognitive_agent_domain_contract():
    """Validates creation and field schema of CognitiveAgentContract."""
    org_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    agent = CognitiveAgentContract(
        organization_id=org_id,
        workspace_id=ws_id,
        owner_user_id=user_id,
        name="Discussion Summarizer",
        description="Summarizes group chat discussions",
        agent_type=CognitiveAgentType.DISCUSSION_ANALYZER,
        instructions="You parse conversations and output markdown summaries.",
        status=CognitiveAgentStatus.ACTIVE,
        knowledge_scope=CognitiveAgentScopeContract(
            scope_type=CognitiveAgentScopeType.WORKSPACE,
            workspace_id=ws_id
        ),
        triggers=[
            CognitiveAgentTriggerContract(
                trigger_type=CognitiveAgentTriggerType.CONVERSATION_EVENT,
                event_pattern="message:created"
            )
        ]
    )

    assert agent.organization_id == org_id
    assert agent.workspace_id == ws_id
    assert agent.owner_user_id == user_id
    assert agent.agent_type == CognitiveAgentType.DISCUSSION_ANALYZER
    assert agent.status == CognitiveAgentStatus.ACTIVE
    assert agent.knowledge_scope.scope_type == CognitiveAgentScopeType.WORKSPACE
    assert len(agent.triggers) == 1
    assert agent.triggers[0].trigger_type == CognitiveAgentTriggerType.CONVERSATION_EVENT


def test_action_candidate_output_conversion_mandates_user_confirmation():
    """
    CRITICAL SAFETY GUARANTEE:
    Validates that an ACTION_CANDIDATE agent output converts to an ActionCandidate
    with requires_user_confirmation set strictly to TRUE (AUTO-06 compliance).
    """
    agent_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())
    conv_id = str(uuid.uuid4())

    output = CognitiveAgentOutputContract(
        output_id=str(uuid.uuid4()),
        agent_id=agent_id,
        organization_id=org_id,
        workspace_id=ws_id,
        output_type=CognitiveAgentOutputType.ACTION_CANDIDATE,
        title="Review API Security Schema",
        body="Assigned review to senior architect before deployment",
        candidate_type="CREATE_TASK",
        action_type=ActionType.TASK,
        intent=IntentCategory.TASK_REQUEST,
        assignee_name="Lead Engineer",
        deadline="Tomorrow 5 PM",
        provenance=[
            CognitiveAgentProvenanceContract(
                source_type="CONVERSATION",
                source_id=conv_id,
                source_reference="Chat message in #architecture",
                confidence_score=0.92
            )
        ]
    )

    candidate = output.to_action_candidate()

    # Verify AUTO-06 & AUTO-01 integration requirements
    assert candidate.subject == "Review API Security Schema"
    assert candidate.description == "Assigned review to senior architect before deployment"
    assert candidate.requires_user_confirmation is True  # Mandatory safety check
    assert candidate.status == CandidateStatus.DETECTED
    assert candidate.confidence == 0.92
    assert candidate.provenance["agent_id"] == agent_id
    assert candidate.source.conversation_id == conv_id


def test_non_action_candidate_conversion_raises_error():
    """Validates that non-ACTION_CANDIDATE outputs cannot be converted into action candidates."""
    output = CognitiveAgentOutputContract(
        agent_id=str(uuid.uuid4()),
        organization_id=str(uuid.uuid4()),
        output_type=CognitiveAgentOutputType.INSIGHT,
        title="Project Progress Insight",
        body="All milestones are currently on track."
    )

    with pytest.raises(ValueError, match="Cannot convert output type"):
        output.to_action_candidate()


def test_cognitive_agent_execution_traceability():
    """Validates execution tracking model schema."""
    exec_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())

    execution = CognitiveAgentExecutionContract(
        execution_id=exec_id,
        agent_id=agent_id,
        organization_id=org_id,
        trigger_source=CognitiveAgentTriggerType.MANUAL,
        status=CognitiveAgentExecutionStatus.COMPLETED,
        action_candidates_generated=1
    )

    assert execution.execution_id == exec_id
    assert execution.status == CognitiveAgentExecutionStatus.COMPLETED
    assert execution.action_candidates_generated == 1
