import logging
from typing import Dict, Any
from app.automation.approval.models import ApprovalRequest
from app.automation.approval.policies import ApprovalPolicies

logger = logging.getLogger(__name__)

class ApprovalEngine:
    @staticmethod
    def process_decision(approval: ApprovalRequest, user_id: str, vote: str) -> str:
        """Applies a voter decision and returns the evaluated request status (Approved/Rejected/Waiting)."""
        votes = dict(approval.approvers_voted or {})
        votes[user_id] = vote
        approval.approvers_voted = votes

        # Calculate expected total approvers
        # For simplicity, count assigned approver comma-separated list or default to 1
        approver_str = approval.assigned_approver or ""
        assigned_count = len([x for x in approver_str.split(",") if x.strip()]) if approver_str else 1
        if assigned_count == 0:
            assigned_count = 1

        new_status = ApprovalPolicies.evaluate(approval.policy_type, votes, assigned_count)
        return new_status
