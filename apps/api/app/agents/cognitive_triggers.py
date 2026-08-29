import logging
from datetime import datetime, timezone as dt_timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.cognitive_agent import CognitiveAgent, CognitiveAgentTrigger, CognitiveAgentExecution
from app.models.user import User
from app.automation.schedule_calculator import ScheduleCalculator
from app.agents.cognitive_engine import CognitiveAgentExecutionEngine

logger = logging.getLogger(__name__)

SUPPORTED_SCHEDULE_TYPES = {"ONE_TIME", "DAILY", "WEEKLY", "WEEKDAYS", "MONTHLY"}
SUPPORTED_EVENT_TYPES = {"DOCUMENT_ADDED", "MESSAGE_RECEIVED", "TASK_CREATED", "PROJECT_UPDATED"}

class CognitiveAgentTriggerService:
    """
    Service layer for Cognitive Agent Triggers & Scheduling (CA-06).
    Handles trigger lifecycle, schedule calculation, atomic worker claiming, and event dispatch.
    """

    @staticmethod
    async def create_trigger(
        db: AsyncSession,
        agent_id: UUID,
        payload: Dict[str, Any],
        current_user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> CognitiveAgentTrigger:
        # Validate agent existence and scope
        stmt = select(CognitiveAgent).where(
            CognitiveAgent.id == agent_id,
            CognitiveAgent.organization_id == organization_id,
            CognitiveAgent.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()

        if not agent:
            raise HTTPException(status_code=404, detail="Cognitive Agent not found.")

        trigger_type = str(payload.get("trigger_type", "SCHEDULE")).upper()
        if trigger_type not in {"SCHEDULE", "EVENT", "MANUAL"}:
            raise HTTPException(status_code=400, detail="Invalid trigger_type. Must be SCHEDULE or EVENT.")

        schedule_type = None
        time_str = payload.get("time_str")
        day_of_week = payload.get("day_of_week")
        tz_name = payload.get("timezone") or "Asia/Kolkata"
        event_type = None
        event_filters = payload.get("event_filters")
        next_run_at = None

        if trigger_type == "SCHEDULE":
            st = str(payload.get("schedule_type", "DAILY")).upper()
            if st not in SUPPORTED_SCHEDULE_TYPES:
                raise HTTPException(status_code=400, detail=f"Unsupported schedule_type: {st}")
            schedule_type = st

            # Calculate initial next_run_at
            from_utc = None
            if st == "ONE_TIME" and payload.get("run_at"):
                try:
                    from_utc = datetime.fromisoformat(str(payload["run_at"]).replace("Z", "+00:00"))
                except Exception:
                    from_utc = None

            next_run_at = ScheduleCalculator.calculate_next_run(
                schedule_type=schedule_type,
                time_str=time_str,
                day_of_week=day_of_week,
                tz_name=tz_name,
                from_utc=from_utc
            )

        elif trigger_type == "EVENT":
            et = str(payload.get("event_type", "")).upper()
            if et not in SUPPORTED_EVENT_TYPES:
                raise HTTPException(status_code=400, detail=f"Unsupported event_type: {et}")
            event_type = et

        trigger = CognitiveAgentTrigger(
            agent_id=agent.id,
            organization_id=organization_id,
            workspace_id=workspace_id or agent.workspace_id,
            created_by_user_id=current_user.id,
            trigger_type=trigger_type,
            status="ACTIVE",
            schedule_type=schedule_type,
            time_str=time_str,
            day_of_week=day_of_week,
            timezone=tz_name,
            event_type=event_type,
            event_filters=event_filters,
            next_run_at=next_run_at
        )

        db.add(trigger)
        await db.commit()
        await db.refresh(trigger)
        return trigger

    @staticmethod
    async def list_triggers(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> List[CognitiveAgentTrigger]:
        stmt = select(CognitiveAgentTrigger).where(
            CognitiveAgentTrigger.agent_id == agent_id,
            CognitiveAgentTrigger.organization_id == organization_id,
            CognitiveAgentTrigger.deleted_at.is_(None)
        ).order_by(CognitiveAgentTrigger.created_at.desc())

        if workspace_id:
            stmt = stmt.where(CognitiveAgentTrigger.workspace_id == workspace_id)

        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def pause_trigger(
        db: AsyncSession,
        trigger_id: UUID,
        organization_id: UUID
    ) -> CognitiveAgentTrigger:
        stmt = select(CognitiveAgentTrigger).where(
            CognitiveAgentTrigger.id == trigger_id,
            CognitiveAgentTrigger.organization_id == organization_id,
            CognitiveAgentTrigger.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        trigger = res.scalar_one_or_none()

        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger record not found.")

        trigger.status = "PAUSED"
        await db.commit()
        await db.refresh(trigger)
        return trigger

    @staticmethod
    async def resume_trigger(
        db: AsyncSession,
        trigger_id: UUID,
        organization_id: UUID
    ) -> CognitiveAgentTrigger:
        stmt = select(CognitiveAgentTrigger).where(
            CognitiveAgentTrigger.id == trigger_id,
            CognitiveAgentTrigger.organization_id == organization_id,
            CognitiveAgentTrigger.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        trigger = res.scalar_one_or_none()

        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger record not found.")

        trigger.status = "ACTIVE"
        # Recalculate next run if scheduled
        if trigger.trigger_type == "SCHEDULE" and trigger.schedule_type:
            trigger.next_run_at = ScheduleCalculator.calculate_next_run(
                schedule_type=trigger.schedule_type,
                time_str=trigger.time_str,
                day_of_week=trigger.day_of_week,
                tz_name=trigger.timezone
            )

        await db.commit()
        await db.refresh(trigger)
        return trigger

    @staticmethod
    async def delete_trigger(
        db: AsyncSession,
        trigger_id: UUID,
        organization_id: UUID
    ) -> bool:
        stmt = select(CognitiveAgentTrigger).where(
            CognitiveAgentTrigger.id == trigger_id,
            CognitiveAgentTrigger.organization_id == organization_id,
            CognitiveAgentTrigger.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        trigger = res.scalar_one_or_none()

        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger record not found.")

        trigger.deleted_at = datetime.utcnow()
        trigger.status = "DISABLED"
        await db.commit()
        return True

    @staticmethod
    async def run_scheduled_trigger_sweep(db: AsyncSession) -> int:
        """
        Worker sweep method called by background scheduler loop.
        Queries due triggers, atomically claims them (skip_locked), re-validates permissions,
        invokes CA-05 Execution Engine, and updates next_run_at.
        """
        now_utc = datetime.utcnow()

        # Query due active triggers with database lock (skip_locked=True for worker concurrency safety)
        stmt = select(CognitiveAgentTrigger).where(
            CognitiveAgentTrigger.trigger_type == "SCHEDULE",
            CognitiveAgentTrigger.status == "ACTIVE",
            CognitiveAgentTrigger.next_run_at <= now_utc,
            CognitiveAgentTrigger.deleted_at.is_(None)
        ).with_for_update(skip_locked=True)

        res = await db.execute(stmt)
        due_triggers = res.scalars().all()

        executed_count = 0

        for trigger in due_triggers:
            # 1. Fetch parent agent & verify ACTIVE status
            stmt_agent = select(CognitiveAgent).where(
                CognitiveAgent.id == trigger.agent_id,
                CognitiveAgent.deleted_at.is_(None)
            )
            res_agent = await db.execute(stmt_agent)
            agent = res_agent.scalar_one_or_none()

            if not agent or agent.status != "ACTIVE" or not agent.enabled:
                logger.info(f"[TriggerService] Agent {trigger.agent_id} is not ACTIVE. Skipping trigger {trigger.id}.")
                continue

            # 2. Fetch owner/creator user entity for authorization
            user_id_to_fetch = trigger.created_by_user_id or agent.owner_user_id
            stmt_user = select(User).where(User.id == user_id_to_fetch)
            res_user = await db.execute(stmt_user)
            owner_user = res_user.scalar_one_or_none()

            if not owner_user:
                logger.warning(f"[TriggerService] Owner user {user_id_to_fetch} not found. Skipping trigger {trigger.id}.")
                continue

            # 3. Execute Agent via CA-05 Execution Engine
            trig_id = trigger.id
            trig_sched_type = trigger.schedule_type
            trig_time_str = trigger.time_str
            trig_dow = trigger.day_of_week
            trig_tz = trigger.timezone

            logger.info(f"[TriggerService] Executing scheduled trigger {trig_id} for agent {agent.id} ({agent.name}).")
            try:
                execution, output = await CognitiveAgentExecutionEngine.execute_agent(
                    db=db,
                    agent_id=agent.id,
                    current_user=owner_user,
                    organization_id=trigger.organization_id,
                    workspace_id=trigger.workspace_id,
                    trigger_type="SCHEDULED",
                    input_context={"trigger_id": str(trig_id), "scheduled_time": trigger.next_run_at.isoformat() if trigger.next_run_at else None}
                )

                # Re-query trigger after execute_agent commit/rollback
                stmt_trig = select(CognitiveAgentTrigger).where(CognitiveAgentTrigger.id == trig_id)
                res_trig = await db.execute(stmt_trig)
                active_trig = res_trig.scalar_one_or_none()

                if active_trig:
                    active_trig.last_run_at = now_utc
                    if execution:
                        active_trig.last_execution_id = execution.id

                    # 4. Update trigger lifecycle / calculate next_run_at
                    if active_trig.schedule_type == "ONE_TIME":
                        active_trig.status = "COMPLETED"
                        active_trig.next_run_at = None
                    elif active_trig.schedule_type:
                        active_trig.next_run_at = ScheduleCalculator.calculate_next_run(
                            schedule_type=active_trig.schedule_type,
                            time_str=active_trig.time_str,
                            day_of_week=active_trig.day_of_week,
                            tz_name=active_trig.timezone,
                            from_utc=now_utc
                        )

                    db.add(active_trig)
                    await db.commit()
                    executed_count += 1

            except Exception as exc:
                logger.error(f"[TriggerService] Failed executing scheduled trigger {trig_id}: {exc}")
                await db.rollback()
                # Re-query trigger to save next_run_at safely
                stmt_trig = select(CognitiveAgentTrigger).where(CognitiveAgentTrigger.id == trig_id)
                res_trig = await db.execute(stmt_trig)
                failed_trig = res_trig.scalar_one_or_none()
                if failed_trig and trig_sched_type and trig_sched_type != "ONE_TIME":
                    failed_trig.next_run_at = ScheduleCalculator.calculate_next_run(
                        schedule_type=trig_sched_type,
                        time_str=trig_time_str,
                        day_of_week=trig_dow,
                        tz_name=trig_tz,
                        from_utc=now_utc
                    )
                    db.add(failed_trig)
                    await db.commit()

        return executed_count

    @staticmethod
    async def dispatch_event_trigger(
        db: AsyncSession,
        event_type: str,
        organization_id: UUID,
        workspace_id: UUID,
        source_entity_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> List[CognitiveAgentExecution]:
        """
        Dispatches workspace events (e.g. DOCUMENT_ADDED, MESSAGE_RECEIVED, TASK_CREATED).
        Applies debouncing/coalescing and invokes CA-05 Execution Engine.
        """
        now_utc = datetime.utcnow()

        stmt = select(CognitiveAgentTrigger).where(
            CognitiveAgentTrigger.trigger_type == "EVENT",
            CognitiveAgentTrigger.event_type == event_type.upper(),
            CognitiveAgentTrigger.status == "ACTIVE",
            CognitiveAgentTrigger.organization_id == organization_id,
            CognitiveAgentTrigger.deleted_at.is_(None)
        )
        if workspace_id:
            stmt = stmt.where(CognitiveAgentTrigger.workspace_id == workspace_id)

        res = await db.execute(stmt)
        active_event_triggers = res.scalars().all()

        executions: List[CognitiveAgentExecution] = []

        for trigger in active_event_triggers:
            # 1. Event Debouncing check (10 second window per trigger)
            if trigger.last_run_at:
                delta = (now_utc - trigger.last_run_at).total_seconds()
                if delta < 10.0:
                    logger.info(f"[TriggerService] Debouncing event {event_type} for trigger {trigger.id} ({delta:.1f}s < 10s).")
                    continue

            # 2. Fetch agent & check status
            stmt_agent = select(CognitiveAgent).where(
                CognitiveAgent.id == trigger.agent_id,
                CognitiveAgent.deleted_at.is_(None)
            )
            res_agent = await db.execute(stmt_agent)
            agent = res_agent.scalar_one_or_none()

            if not agent or agent.status != "ACTIVE" or not agent.enabled:
                continue

            # 3. Fetch owner user
            user_id_to_fetch = trigger.created_by_user_id or agent.owner_user_id
            stmt_user = select(User).where(User.id == user_id_to_fetch)
            res_user = await db.execute(stmt_user)
            owner_user = res_user.scalar_one_or_none()

            if not owner_user:
                continue

            # 4. Execute Agent via CA-05 Engine
            try:
                execution, output = await CognitiveAgentExecutionEngine.execute_agent(
                    db=db,
                    agent_id=agent.id,
                    current_user=owner_user,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    trigger_type="EVENT",
                    input_context={"event_type": event_type, "source_entity_id": source_entity_id, "payload": payload}
                )

                trigger.last_run_at = now_utc
                if execution:
                    trigger.last_execution_id = execution.id
                    executions.append(execution)

                db.add(trigger)
                await db.commit()
            except Exception as exc:
                logger.error(f"[TriggerService] Failed event trigger execution for trigger {trigger.id}: {exc}", exc_info=True)

        return executions
