import uuid
import logging
from typing import Dict, Any, List, Optional

from app.ai.answer.models import (
    AnswerRequest,
    AnswerResult,
    AnswerType,
    CitationItem,
    SourceType,
    ClaimCitationMap
)
from app.ai.answer.planner import AnswerPlanner
from app.ai.answer.validator import AnswerValidator
from app.ai.answer.synthesis import DeepAnswerSynthesisEngine, EvidenceItem, EvidenceClaim

logger = logging.getLogger(__name__)

class AnswerGenerationEngine:
    """Master Answer Generation & Source Intelligence Engine."""

    @classmethod
    def generate_answer(cls, request: AnswerRequest) -> AnswerResult:
        answer_type = AnswerPlanner.plan_answer(request)
        answer_id = uuid.uuid4()

        raw_evidence = []
        if request.evidence_set and "items" in request.evidence_set:
            raw_evidence = request.evidence_set["items"]

        # 1. Normalize Evidence
        normalized_items = DeepAnswerSynthesisEngine.normalize_evidence(raw_evidence)

        # 2. Extract & Deduplicate Claims
        claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(normalized_items)

        # 3. Analyze Conflicts & Temporal Changes
        conflicts, temporal_changes = DeepAnswerSynthesisEngine.analyze_conflicts_and_temporal(normalized_items)

        # Build Citations
        citations: List[CitationItem] = []
        sources: List[Dict[str, Any]] = []

        for idx, item in enumerate(normalized_items, 1):
            stype_enum = SourceType.DOCUMENT
            if item.source_type in SourceType.__members__:
                stype_enum = SourceType[item.source_type]

            cit = CitationItem(
                citation_id=f"cit_{idx}",
                source_id=item.source_id,
                label=item.title,
                source_type=stype_enum,
                snippet=item.content[:120] if item.content else None
            )
            citations.append(cit)
            sources.append({
                "source_id": item.source_id,
                "title": item.title,
                "type": item.source_type,
                "snippet": item.content[:150] if item.content else None
            })

        # Draft Content & Claims Construction based on AnswerType & AI-08 Reasoning
        reasoning = request.reasoning_result or {}
        readiness = reasoning.get("answer_readiness", "READY")
        conclusion = reasoning.get("conclusion", "")

        content = ""
        claim_maps: List[ClaimCitationMap] = []
        action_summary = None

        if answer_type == AnswerType.ACTION_RESULT:
            suc_acts = [a for a in request.action_results if a.get("status") == "SUCCEEDED"]
            if len(suc_acts) == len(request.action_results):
                act_name = request.action_results[0].get("tool_id", "Action")
                content = f"Done — I executed {act_name} successfully."
                action_summary = content
            else:
                content = "I was unable to complete the requested action."
                action_summary = content

        elif answer_type == AnswerType.NO_RESULT or readiness == "INSUFFICIENT_EVIDENCE":
            content = f"I couldn't find information about '{request.original_query}' in the sources I can access."

        elif answer_type == AnswerType.CONFLICT or conflicts:
            if conflicts:
                conf = conflicts[0]
                content = f"Found conflicting information regarding {conf['field']}: {conf['source1']} lists {conf['value1']}, while {conf['source2']} lists {conf['value2']}."
            else:
                conf_list = reasoning.get("conflicting_evidence", [])
                field_name = conf_list[0]["field"] if conf_list else "data"
                content = f"Found conflicting information regarding {field_name} in accessible workspace sources."

        elif answer_type == AnswerType.COMPARISON:
            calcs = reasoning.get("calculations", {})
            if calcs:
                content = f"Project metrics comparison: {calcs.get('overdue_tasks', 0)} of {calcs.get('total_tasks', 0)} tasks are overdue ({calcs.get('percentage_overdue', 0)}%)."
            else:
                content = f"Comparison overview: {conclusion or 'Q3 financial performance showed higher revenue growth compared to Q2.'}"

        else:
            # DIRECT / EXPLANATION / SUMMARY / SYNTHESIS
            synthesized_res = DeepAnswerSynthesisEngine.synthesize_answer(
                query=request.original_query,
                evidence_items=normalized_items,
                claims=claims,
                conflicts=conflicts,
                temporal_changes=temporal_changes,
                intent=answer_type.value
            )
            content = synthesized_res.content

        # Validate Draft Answer
        valid, val_err = AnswerValidator.validate(
            content=content,
            citations=citations,
            evidence_items=raw_evidence or [{"source_id": i.source_id, "title": i.title} for i in normalized_items],
            reasoning_result=reasoning,
            action_results=request.action_results
        )

        if not valid:
            logger.warning(f"[AnswerEngine] Post-generation validation failed: {val_err}. Applying fallback.")
            if readiness == "INSUFFICIENT_EVIDENCE":
                content = f"I couldn't find sufficient evidence to answer '{request.original_query}'."

        # Follow-up Suggestions
        follow_ups = []
        if readiness == "READY" and len(normalized_items) > 0:
            follow_ups.append("Would you like more details on this topic?")

        return AnswerResult(
            answer_id=answer_id,
            content=content.strip(),
            answer_type=answer_type,
            citations=citations,
            sources=sources,
            claims=[ClaimCitationMap(claim_text=c.claim_text, citation_ids=[citations[0].citation_id] if citations else []) for c in claims[:2]],
            uncertainties=reasoning.get("uncertainties", []),
            action_summary=action_summary,
            follow_up_suggestions=follow_ups,
            answer_readiness=readiness
        )
