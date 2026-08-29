import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.governance.policy_store import PolicyStore
from app.governance.policy_engine import PolicyEngine
from app.governance.enforcement import PolicyEnforcement
from app.governance.approvals import GovernanceApprovalGate
from app.governance.compliance import ComplianceEngine
from app.governance.reporting import ComplianceReporter
from app.governance.auditing import ActionAuditor
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_policy_store_and_engine_evaluations(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # 1. Create a security policy rules block
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Security Policy A",
        category="Security",
        rules={"blocked_keywords": ["secret_password", "private_key"]}
    )

    # Create a tool blacklist policy
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Tool Policy B",
        category="Tool",
        rules={"blacklisted_tools": ["delete_database"]}
    )

    # Create a privacy policy checking PII
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Privacy Policy C",
        category="Privacy",
        rules={"pii_protection": True}
    )

    await db_session.commit()

    # 2. Evaluate inputs via Engine
    allowed_1, violations_1 = await PolicyEngine.validate_policy(
        db=db_session,
        organization_id=org.id,
        category="Security",
        context_data={"text": "Here is my secret_password!"}
    )
    assert allowed_1 is False
    assert len(violations_1) == 1

    allowed_2, violations_2 = await PolicyEngine.validate_policy(
        db=db_session,
        organization_id=org.id,
        category="Tool",
        context_data={"tool": "delete_database"}
    )
    assert allowed_2 is False

@pytest.mark.asyncio
async def test_policy_enforcement_exceptions(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # Create active policies
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Security Policy A",
        category="Security",
        rules={"blocked_keywords": ["secret_password"]}
    )
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Privacy Policy B",
        category="Privacy",
        rules={"pii_protection": True}
    )
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Tool Policy C",
        category="Tool",
        rules={"blacklisted_tools": ["delete_database"]}
    )
    await db_session.commit()

    # 1. Enforce security prompt blocks keyword
    with pytest.raises(ValueError) as exc:
        await PolicyEnforcement.enforce_prompt(db_session, org.id, "my secret_password is plain text.")
    assert "blocked by Security Policy" in str(exc.value)

    # 2. Enforce privacy PII email check
    with pytest.raises(ValueError) as exc_privacy:
        await PolicyEnforcement.enforce_prompt(db_session, org.id, "Contact me at test@example.com")
    assert "blocked by Privacy Policy" in str(exc_privacy.value)

    # 3. Enforce tool blacklist block
    with pytest.raises(ValueError) as exc_tool:
        await PolicyEnforcement.enforce_tool_execution(db_session, org.id, "delete_database")
    assert "blocked by Tool Policy" in str(exc_tool.value)

@pytest.mark.asyncio
async def test_compliance_reporting_and_audit(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    import uuid

    # Create active policy
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Base Rule",
        category="Security",
        rules={}
    )

    # Add an audit record
    await ActionAuditor.log_action_decision(
        db=db_session,
        execution_id=uuid.uuid4(),
        organization_id=org.id,
        agent_name="SupervisorAgent",
        selected_tools=["read_file"],
        retrieved_documents=[],
        applied_policies=["Base Rule"],
        confidence_score=0.9,
        risk_score=0.1,
        trust_score=0.95
    )
    await db_session.commit()

    # 1. Fetch compliance metrics
    stats = await ComplianceEngine.get_compliance_stats(db_session, org.id)
    assert stats["total_governed_policies"] == 1
    assert stats["total_audited_transactions"] == 1

    # 2. Export auditor report pack
    report = await ComplianceReporter.generate_audit_export(db_session, org.id)
    assert report["organization_id"] == str(org.id)
    assert len(report["recent_decision_audits"]) == 1
    assert report["recent_decision_audits"][0]["agent_name"] == "SupervisorAgent"
