"""In-memory session management for Governor MCP"""

import uuid
from datetime import datetime

from .models import Assessment, Plan, PlanStep, Approval, StepStatus, PlanStatus


class SessionManager:
    """Manages in-memory state for assessments, plans, and approvals"""

    def __init__(self):
        self._assessments: dict[str, Assessment] = {}
        self._plans: dict[str, Plan] = {}
        self._approvals: dict[str, Approval] = {}
        self._session_id = str(uuid.uuid4())

    @property
    def session_id(self) -> str:
        return self._session_id

    # Assessment management
    def store_assessment(self, assessment: Assessment) -> str:
        self._assessments[assessment.id] = assessment
        return assessment.id

    def get_assessment(self, assessment_id: str) -> Assessment | None:
        return self._assessments.get(assessment_id)

    def list_assessments(self) -> list[Assessment]:
        return list(self._assessments.values())

    # Plan management
    def store_plan(self, plan: Plan) -> str:
        self._plans[plan.id] = plan
        return plan.id

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        return list(self._plans.values())

    def get_active_plans(self) -> list[Plan]:
        return [
            p for p in self._plans.values()
            if p.status in (PlanStatus.AWAITING_APPROVAL, PlanStatus.IN_PROGRESS)
        ]

    def update_plan_status(self, plan_id: str, status: PlanStatus) -> Plan | None:
        plan = self._plans.get(plan_id)
        if plan:
            plan.status = status
            plan.updated_at = datetime.now()
            if status in (PlanStatus.COMPLETED, PlanStatus.ABORTED, PlanStatus.FAILED):
                plan.completed_at = datetime.now()
        return plan

    def update_step_status(
        self,
        plan_id: str,
        step_id: str,
        status: StepStatus,
        result: str | None = None,
        error: str | None = None,
    ) -> PlanStep | None:
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        for step in plan.steps:
            if step.id == step_id:
                step.status = status
                step.result = result
                step.error = error
                if status in (StepStatus.COMPLETED, StepStatus.FAILED):
                    step.executed_at = datetime.now()
                plan.updated_at = datetime.now()
                return step
        return None

    # Approval management
    def store_approval(self, approval: Approval) -> str:
        self._approvals[approval.id] = approval
        return approval.id

    def get_approval(self, approval_id: str) -> Approval | None:
        return self._approvals.get(approval_id)

    def get_approvals_for_target(self, target_type: str, target_id: str) -> list[Approval]:
        return [
            a for a in self._approvals.values()
            if a.target_type == target_type and a.target_id == target_id
        ]

    def is_approved(self, target_type: str, target_id: str) -> bool:
        approvals = self.get_approvals_for_target(target_type, target_id)
        if not approvals:
            return False
        # Check if the most recent approval was positive
        latest = max(approvals, key=lambda a: a.timestamp)
        return latest.approved

    # Session utilities
    def clear_session(self):
        """Clear all session data"""
        self._assessments.clear()
        self._plans.clear()
        self._approvals.clear()
        self._session_id = str(uuid.uuid4())

    def get_session_summary(self) -> dict:
        """Get summary of current session state"""
        return {
            "session_id": self._session_id,
            "assessments_count": len(self._assessments),
            "plans_count": len(self._plans),
            "active_plans_count": len(self.get_active_plans()),
            "approvals_count": len(self._approvals),
        }


# Global session instance
_session: SessionManager | None = None


def get_session() -> SessionManager:
    """Get or create the global session manager"""
    global _session
    if _session is None:
        _session = SessionManager()
    return _session


def reset_session() -> SessionManager:
    """Reset the global session manager"""
    global _session
    _session = SessionManager()
    return _session
