"""Plan lifecycle management for Governor MCP"""

import uuid
from datetime import datetime
from typing import Any

from ..state import (
    Plan,
    PlanStep,
    PlanStatus,
    StepStatus,
    Assessment,
    Approval,
    RiskLevel,
)
from ..state.session import get_session


class PlanController:
    """Manages the lifecycle of execution plans for high-risk operations"""

    def __init__(self):
        self._session = get_session()

    def create_plan(
        self,
        name: str,
        description: str,
        assessment: Assessment,
        steps: list[dict[str, Any]],
    ) -> Plan:
        """
        Create a new execution plan for a high-risk operation.

        Args:
            name: Name of the plan
            description: Description of what the plan accomplishes
            assessment: The risk assessment that triggered plan creation
            steps: List of step definitions with keys:
                - description: What the step does
                - operation: The actual operation/command
                - expected_outcome: What should happen
                - rollback_action: How to undo (optional)

        Returns:
            The created Plan object
        """
        plan_steps = []
        for i, step_def in enumerate(steps):
            step = PlanStep(
                id=str(uuid.uuid4()),
                order=i + 1,
                description=step_def.get("description", f"Step {i + 1}"),
                operation=step_def.get("operation", ""),
                expected_outcome=step_def.get("expected_outcome", ""),
                rollback_action=step_def.get("rollback_action"),
            )
            plan_steps.append(step)

        plan = Plan(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            assessment_id=assessment.id,
            steps=plan_steps,
            status=PlanStatus.DRAFT,
        )

        self._session.store_plan(plan)
        return plan

    def submit_for_approval(self, plan_id: str) -> Plan | None:
        """
        Submit a plan for user approval.

        Args:
            plan_id: The plan ID

        Returns:
            Updated plan or None if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None

        if plan.status != PlanStatus.DRAFT:
            raise ValueError(f"Plan must be in DRAFT status to submit, current: {plan.status}")

        plan.status = PlanStatus.AWAITING_APPROVAL
        plan.updated_at = datetime.now()
        return plan

    def approve_plan(self, plan_id: str, reason: str | None = None) -> tuple[Plan | None, Approval | None]:
        """
        Record approval for an entire plan.

        Args:
            plan_id: The plan ID
            reason: Optional reason for approval

        Returns:
            Tuple of (Plan, Approval) or (None, None) if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None, None

        approval = Approval(
            id=str(uuid.uuid4()),
            target_type="plan",
            target_id=plan_id,
            approved=True,
            reason=reason,
        )
        self._session.store_approval(approval)

        plan.status = PlanStatus.IN_PROGRESS
        plan.updated_at = datetime.now()

        # Mark all steps as approved
        for step in plan.steps:
            step.status = StepStatus.APPROVED

        return plan, approval

    def deny_plan(self, plan_id: str, reason: str | None = None) -> tuple[Plan | None, Approval | None]:
        """
        Record denial for a plan.

        Args:
            plan_id: The plan ID
            reason: Optional reason for denial

        Returns:
            Tuple of (Plan, Approval) or (None, None) if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None, None

        approval = Approval(
            id=str(uuid.uuid4()),
            target_type="plan",
            target_id=plan_id,
            approved=False,
            reason=reason,
        )
        self._session.store_approval(approval)

        plan.status = PlanStatus.ABORTED
        plan.updated_at = datetime.now()
        plan.completed_at = datetime.now()

        return plan, approval

    def approve_step(
        self,
        plan_id: str,
        step_id: str,
        reason: str | None = None,
    ) -> tuple[PlanStep | None, Approval | None]:
        """
        Record approval for a specific step.

        Args:
            plan_id: The plan ID
            step_id: The step ID
            reason: Optional reason for approval

        Returns:
            Tuple of (PlanStep, Approval) or (None, None) if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None, None

        step = None
        for s in plan.steps:
            if s.id == step_id:
                step = s
                break

        if not step:
            return None, None

        approval = Approval(
            id=str(uuid.uuid4()),
            target_type="step",
            target_id=step_id,
            approved=True,
            reason=reason,
        )
        self._session.store_approval(approval)

        step.status = StepStatus.APPROVED
        plan.updated_at = datetime.now()

        return step, approval

    def deny_step(
        self,
        plan_id: str,
        step_id: str,
        reason: str | None = None,
    ) -> tuple[PlanStep | None, Approval | None]:
        """
        Record denial for a specific step.

        Args:
            plan_id: The plan ID
            step_id: The step ID
            reason: Optional reason for denial

        Returns:
            Tuple of (PlanStep, Approval) or (None, None) if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None, None

        step = None
        for s in plan.steps:
            if s.id == step_id:
                step = s
                break

        if not step:
            return None, None

        approval = Approval(
            id=str(uuid.uuid4()),
            target_type="step",
            target_id=step_id,
            approved=False,
            reason=reason,
        )
        self._session.store_approval(approval)

        step.status = StepStatus.DENIED
        plan.updated_at = datetime.now()

        return step, approval

    def start_step_execution(self, plan_id: str, step_id: str) -> PlanStep | None:
        """
        Mark a step as executing.

        Args:
            plan_id: The plan ID
            step_id: The step ID

        Returns:
            Updated step or None if not found
        """
        return self._session.update_step_status(
            plan_id, step_id, StepStatus.EXECUTING
        )

    def complete_step(
        self,
        plan_id: str,
        step_id: str,
        result: str,
    ) -> PlanStep | None:
        """
        Mark a step as completed successfully.

        Args:
            plan_id: The plan ID
            step_id: The step ID
            result: The result of the step execution

        Returns:
            Updated step or None if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None

        step = self._session.update_step_status(
            plan_id, step_id, StepStatus.COMPLETED, result=result
        )

        if step:
            # Check if all steps are completed
            all_completed = all(
                s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
                for s in plan.steps
            )
            if all_completed:
                plan.status = PlanStatus.COMPLETED
                plan.completed_at = datetime.now()

        return step

    def fail_step(
        self,
        plan_id: str,
        step_id: str,
        error: str,
    ) -> PlanStep | None:
        """
        Mark a step as failed.

        Args:
            plan_id: The plan ID
            step_id: The step ID
            error: The error message

        Returns:
            Updated step or None if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None

        step = self._session.update_step_status(
            plan_id, step_id, StepStatus.FAILED, error=error
        )

        if step:
            plan.status = PlanStatus.FAILED
            plan.updated_at = datetime.now()

        return step

    def abort_plan(self, plan_id: str, reason: str | None = None) -> dict[str, Any] | None:
        """
        Abort a plan and generate rollback suggestions.

        Args:
            plan_id: The plan ID
            reason: Optional reason for abortion

        Returns:
            Dictionary with abort info and rollback suggestions, or None if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None

        # Collect rollback suggestions for completed steps
        rollback_suggestions = []
        for step in plan.steps:
            if step.status == StepStatus.COMPLETED and step.rollback_action:
                rollback_suggestions.append({
                    "step_id": step.id,
                    "step_order": step.order,
                    "step_description": step.description,
                    "rollback_action": step.rollback_action,
                })

        # Mark remaining pending/approved steps as skipped
        for step in plan.steps:
            if step.status in (StepStatus.PENDING, StepStatus.APPROVED):
                step.status = StepStatus.SKIPPED

        plan.status = PlanStatus.ABORTED
        plan.updated_at = datetime.now()
        plan.completed_at = datetime.now()

        return {
            "plan_id": plan_id,
            "reason": reason,
            "rollback_suggestions": list(reversed(rollback_suggestions)),  # Reverse order for rollback
            "completed_steps": sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED),
            "skipped_steps": sum(1 for s in plan.steps if s.status == StepStatus.SKIPPED),
        }

    def get_plan_status(self, plan_id: str) -> dict[str, Any] | None:
        """
        Get detailed status of a plan.

        Args:
            plan_id: The plan ID

        Returns:
            Status dictionary or None if not found
        """
        plan = self._session.get_plan(plan_id)
        if not plan:
            return None

        step_summary = {
            "pending": 0,
            "approved": 0,
            "denied": 0,
            "executing": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
        }

        for step in plan.steps:
            step_summary[step.status.value] = step_summary.get(step.status.value, 0) + 1

        current_step = plan.get_current_step()

        return {
            "plan": plan.to_dict(),
            "current_step": current_step.to_dict() if current_step else None,
            "step_summary": step_summary,
            "progress": f"{step_summary['completed']}/{len(plan.steps)}",
            "is_active": plan.status in (PlanStatus.AWAITING_APPROVAL, PlanStatus.IN_PROGRESS),
        }
