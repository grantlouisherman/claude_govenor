"""Governor approve tool - record user approval/denial"""

from typing import Any

from ..core import PlanController
from ..state import RiskLevel
from ..state.session import get_session
from ..state.audit import get_audit_logger


async def governor_approve(
    target_type: str,
    target_id: str,
    approved: bool,
    reason: str = "",
) -> dict[str, Any]:
    """
    Record user approval or denial for an assessment, plan, or step.

    Use this tool to record the user's decision before proceeding with
    medium or high risk operations.

    Args:
        target_type: Type of target - "assessment", "plan", or "step"
        target_id: ID of the assessment, plan, or step
        approved: True if approved, False if denied
        reason: Optional reason for the decision

    Returns:
        Approval record including:
        - approval_id: ID of the approval record
        - approved: Whether approved
        - target: Information about what was approved/denied
        - next_steps: Guidance on what to do next
    """
    session = get_session()
    audit = get_audit_logger()
    plan_controller = PlanController()

    if target_type not in ("assessment", "plan", "step"):
        return {
            "error": f"Invalid target_type: {target_type}. Must be 'assessment', 'plan', or 'step'."
        }

    response: dict[str, Any] = {
        "target_type": target_type,
        "target_id": target_id,
        "approved": approved,
        "reason": reason or None,
    }

    if target_type == "assessment":
        assessment = session.get_assessment(target_id)
        if not assessment:
            return {"error": f"Assessment not found: {target_id}"}

        # Create approval record
        from ..state import Approval
        import uuid
        approval = Approval(
            id=str(uuid.uuid4()),
            target_type="assessment",
            target_id=target_id,
            approved=approved,
            reason=reason or None,
        )
        session.store_approval(approval)

        # Log the approval
        audit.log(
            action="approve" if approved else "deny",
            operation=assessment.operation,
            risk_level=assessment.risk_level,
            details={"reason": reason},
            assessment_id=target_id,
        )

        response["approval_id"] = approval.id
        response["assessment"] = {
            "operation": assessment.operation,
            "risk_level": assessment.risk_level.value,
        }

        if approved:
            if assessment.risk_level == RiskLevel.HIGH:
                response["next_steps"] = (
                    "Assessment approved. Since this is HIGH risk, create a plan using "
                    f"governor_create_plan with assessment_id='{target_id}'."
                )
            else:
                response["next_steps"] = "Approved. You may proceed with the operation."
        else:
            response["next_steps"] = "Denied. Operation should not proceed."

    elif target_type == "plan":
        if approved:
            plan, approval = plan_controller.approve_plan(target_id, reason or None)
        else:
            plan, approval = plan_controller.deny_plan(target_id, reason or None)

        if not plan:
            return {"error": f"Plan not found: {target_id}"}

        # Get the assessment for logging
        assessment = session.get_assessment(plan.assessment_id)
        risk_level = assessment.risk_level if assessment else RiskLevel.HIGH

        audit.log(
            action="approve_plan" if approved else "deny_plan",
            operation=plan.name,
            risk_level=risk_level,
            details={"reason": reason},
            plan_id=target_id,
        )

        response["approval_id"] = approval.id if approval else None
        response["plan"] = {
            "name": plan.name,
            "status": plan.status.value,
            "steps_count": len(plan.steps),
        }

        if approved:
            first_step = plan.steps[0] if plan.steps else None
            if first_step:
                response["next_steps"] = (
                    f"Plan approved. Execute steps in order using governor_execute_step. "
                    f"First step: {first_step.description} (step_id: {first_step.id})"
                )
            else:
                response["next_steps"] = "Plan approved but has no steps."
        else:
            response["next_steps"] = "Plan denied. Consider revising or abandoning the operation."

    elif target_type == "step":
        # For step approval, we need the plan_id from context
        # Find the plan containing this step
        plans = session.list_plans()
        target_plan = None
        for plan in plans:
            for step in plan.steps:
                if step.id == target_id:
                    target_plan = plan
                    break
            if target_plan:
                break

        if not target_plan:
            return {"error": f"Step not found: {target_id}"}

        if approved:
            step, approval = plan_controller.approve_step(target_plan.id, target_id, reason or None)
        else:
            step, approval = plan_controller.deny_step(target_plan.id, target_id, reason or None)

        if not step:
            return {"error": f"Failed to update step: {target_id}"}

        assessment = session.get_assessment(target_plan.assessment_id)
        risk_level = assessment.risk_level if assessment else RiskLevel.HIGH

        audit.log(
            action="approve_step" if approved else "deny_step",
            operation=step.operation,
            risk_level=risk_level,
            details={"reason": reason, "step_description": step.description},
            plan_id=target_plan.id,
            step_id=target_id,
        )

        response["approval_id"] = approval.id if approval else None
        response["step"] = {
            "order": step.order,
            "description": step.description,
            "status": step.status.value,
        }
        response["plan_id"] = target_plan.id

        if approved:
            response["next_steps"] = (
                f"Step approved. Execute using governor_execute_step with "
                f"plan_id='{target_plan.id}' and step_id='{target_id}'."
            )
        else:
            response["next_steps"] = "Step denied. Consider skipping or aborting the plan."

    return response
