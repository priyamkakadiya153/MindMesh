import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ApprovalPolicies:
    @staticmethod
    def evaluate(policy_type: str, votes: Dict[str, str], assigned_approvers_count: int = 1) -> str:
        """Evaluates votes against the designated approval policy.

        Returns "Approved", "Rejected", or "Waiting".
        """
        if not votes:
            return "Waiting"

        # Check if any voter rejected. Rejection is immediate failure.
        if any(v == "Rejected" for v in votes.values()):
            return "Rejected"

        total_votes = len(votes)
        approvals_count = sum(1 for v in votes.values() if v == "Approved")

        if policy_type in ["Single", "Department"]:
            # Single approval from any assigned voter completes the approval
            if approvals_count >= 1:
                return "Approved"
            return "Waiting"

        elif policy_type in ["Multi", "Executive"]:
            # Multi/Executive requires all assigned approvers to vote Approved
            if approvals_count >= assigned_approvers_count:
                return "Approved"
            return "Waiting"

        elif policy_type == "Majority":
            # Majority requires >50% approval
            needed = (assigned_approvers_count / 2.0)
            if approvals_count > needed:
                return "Approved"
            elif (total_votes - approvals_count) >= needed:
                # Impossible to reach majority due to abstentions/failures
                return "Rejected"
            return "Waiting"

        return "Waiting"
