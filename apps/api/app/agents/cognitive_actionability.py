import logging
import hashlib
import json
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cognitive_agent import CognitiveAgent, CognitiveAgentExecution, CognitiveAgentOutput
from app.models.proactive_suggestion import ProactiveSuggestion
from app.models.user import User

logger = logging.getLogger(__name__)

WEAK_SPECULATIVE_PHRASES = [
    "could consider", "might consider", "perhaps", "maybe",
    "suggests that we could", "would be nice to", "optionally"
]

class CognitiveAgentActionabilityService:
    """
    CA-08 — Cognitive Agent → Action Inbox Integration Service.
    Parses Agent Output (CA-07), validates provenance, enforces conservative actionability,
    applies role-aware dual-POV logic (AUTO-10), performs deterministic hash deduplication (AUTO-09),
    and creates persistent ProactiveSuggestion candidates without silent DB mutations.
    """

    @staticmethod
    async def evaluate_and_create_candidates(
        db: AsyncSession,
        agent: CognitiveAgent,
        execution: CognitiveAgentExecution,
        output: CognitiveAgentOutput,
        current_user: User,
        organization_id: UUID,
        workspace_id: UUID
    ) -> List[ProactiveSuggestion]:
        """
        Main entrypoint called after Cognitive Agent output persistence.
        Analyzes output for actionable obligations and persists AUTO-09 candidates.
        """
        if not output or not output.provenance or len(output.provenance) == 0:
            logger.info(f"[ActionabilityService] Output {output.id if output else 'None'} has 0 provenance sources. Skipping candidate generation.")
            return []

        # 1. Actionability Assessment
        findings = CognitiveAgentActionabilityService._extract_actionable_findings(output)
        if not findings:
            logger.info(f"[ActionabilityService] Output {output.id} contains no conservative actionable findings.")
            return []

        created_suggestions: List[ProactiveSuggestion] = []

        for finding in findings:
            title = finding.get("title", output.title)
            body = finding.get("summary", output.body)
            action_type_raw = str(finding.get("candidate_type") or finding.get("action_type") or "TASK").upper()
            deadline_str = finding.get("deadline")

            # Validate phrasing
            if CognitiveAgentActionabilityService._is_weak_or_speculative(title + " " + body):
                logger.info(f"[ActionabilityService] Finding '{title}' contains weak speculative phrasing. Rejected.")
                continue

            # Determine Action Type (TASK vs REMINDER)
            detected_action_type = "REMINDER" if action_type_raw in ["REMINDER", "DEADLINE"] else "TASK"
            pending_action_type = "CREATE_REMINDER" if detected_action_type == "REMINDER" else "CREATE_TASK"

            # Parse Grounded Provenance Source
            first_prov = output.provenance[0] if output.provenance else {}
            source_id = first_prov.get("source_id") or first_prov.get("conversation_id") or str(agent.id)
            conv_id = first_prov.get("conversation_id") or str(source_id)
            msg_id = first_prov.get("message_id")
            source_type_label = first_prov.get("source_type", "knowledge")

            # Check Completion Signal / Dual-POV Role Awareness (AUTO-10)
            if "completed" in body.lower() or "finished" in body.lower():
                # If speaker completed task, do not create self-task. Create REVIEW candidate for leader if specified.
                if action_type_raw not in ["REVIEW", "VERIFY", "FOLLOW_UP"]:
                    logger.info(f"[ActionabilityService] Completion signal detected in '{title}'. Self-task candidate suppressed.")
                    continue

            # Target user & Assignee
            target_user_id = current_user.id
            assignee_name = current_user.username or current_user.full_name or "Current User"

            # Normalize Deadline
            norm_deadline = CognitiveAgentActionabilityService._parse_normalized_deadline(deadline_str)

            # Actionability Explanation Reason
            reason = finding.get("reason") or f"Detected {action_type_raw.lower()} obligation from Cognitive Agent: {agent.name}"

            # Deterministic Deduplication Hash
            hash_str = f"{workspace_id}:{agent.id}:{source_id}:{detected_action_type}:{title}:{deadline_str or ''}"
            action_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

            # Check existing candidate per user
            stmt = select(ProactiveSuggestion).where(
                ProactiveSuggestion.user_id == target_user_id,
                ProactiveSuggestion.detected_action_hash == action_hash,
                ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN", "DISMISSED", "ACCEPTED"])
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                if existing.status == "DISMISSED":
                    logger.info(f"[ActionabilityService] Candidate {action_hash} was previously DISMISSED by user. Skipping duplicate creation.")
                    continue
                else:
                    logger.info(f"[ActionabilityService] Active candidate already exists for hash {action_hash}. Updating timestamp.")
                    existing.updated_at = datetime.now(timezone.utc)
                    created_suggestions.append(existing)
                    continue

            # Persist AUTO-09 Candidate
            suggestion = ProactiveSuggestion(
                organization_id=organization_id,
                workspace_id=workspace_id,
                user_id=target_user_id,
                source_type="COGNITIVE_AGENT",
                conversation_id=conv_id,
                message_id=msg_id,
                detected_action_type=detected_action_type,
                title=title,
                description=reason,
                deadline=deadline_str,
                normalized_deadline=norm_deadline,
                assignee_id=target_user_id,
                assignee_name=assignee_name,
                confidence=0.9,
                confidence_level="HIGH",
                status="DETECTED",
                detected_action_hash=action_hash,
                source_label=f"Cognitive Agent: {agent.name}",
                source_content=body[:500],
                pending_target_action_type=pending_action_type,
                agent_id=agent.id,
                agent_execution_id=execution.id,
                agent_output_id=output.id
            )
            db.add(suggestion)
            created_suggestions.append(suggestion)

        if created_suggestions:
            await db.commit()
            for s in created_suggestions:
                await db.refresh(s)

        return created_suggestions

    @staticmethod
    def _extract_actionable_findings(output: CognitiveAgentOutput) -> List[Dict[str, Any]]:
        """
        Extracts structured findings from output record.
        """
        findings = []

        # Check structured_payload
        if output.structured_payload and isinstance(output.structured_payload, dict):
            if "findings" in output.structured_payload and isinstance(output.structured_payload["findings"], list):
                for f in output.structured_payload["findings"]:
                    if isinstance(f, dict) and f.get("is_actionable"):
                        findings.append(f)
            elif output.output_type == "ACTION_CANDIDATE":
                findings.append(output.structured_payload)

        # Fallback for output_type ACTION_CANDIDATE if no structured payload findings list
        if not findings and output.output_type == "ACTION_CANDIDATE":
            findings.append({
                "title": output.title,
                "summary": output.body,
                "candidate_type": output.candidate_type or "TASK",
                "deadline": None,
                "reason": f"Cognitive Agent detected actionable finding: {output.title}"
            })

        return findings

    @staticmethod
    def _is_weak_or_speculative(text: str) -> bool:
        lower = text.lower()
        for phrase in WEAK_SPECULATIVE_PHRASES:
            if phrase in lower:
                return True
        return False

    @staticmethod
    def _parse_normalized_deadline(deadline_str: Optional[str]) -> Optional[datetime]:
        if not deadline_str:
            return None
        d_lower = deadline_str.lower().strip()
        now = datetime.now(timezone.utc)
        if "tomorrow" in d_lower:
            return now + timedelta(days=1)
        elif "today" in d_lower:
            return now + timedelta(hours=8)
        elif "friday" in d_lower:
            # Days until next Friday
            days = (4 - now.weekday()) % 7
            if days == 0:
                days = 7
            return now + timedelta(days=days)
        elif "next week" in d_lower:
            return now + timedelta(days=7)
        return None
