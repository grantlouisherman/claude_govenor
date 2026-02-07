"""Governor abort tool - cancel plans and get rollback suggestions"""

from typing import Any

from ..core import PlanController
from ..state import RiskLevel
from ..state.session import get_session
from ..state.audit import get_audit_logger


async def governor_abort(
    plan_id: str,
    reason: str = "",
) -> dict[str, Any]:
    """
    Abort a plan and get rollback suggestions for completed steps.

    Use this tool when:
    - A step fails and you need to rollback
    - The user requests to cancel the operation
    - A critical deviation is detected

    The tool will:
    1. Mark the plan as aborted
    2. Skip any pending steps
    3. Generate rollback suggestions for completed steps (in reverse order)

    Args:
        plan_id: ID of the plan to abort
        reason: Reason for aborting the plan

    Returns:
        Abort confirmation including:
        - aborted: Whether abort succeeded
        - rollback_suggestions: Steps to undo completed work
        - completed_steps: Number of steps that were completed
        - skipped_steps: Number of steps that were skipped
    """
    session = get_session()
    audit = get_audit_logger()
    plan_controller = PlanController()

    # Get the plan first for logging
    plan = session.get_plan(plan_id)
    if not plan:
        return {"error": f"Plan not found: {plan_id}"}

    # Get assessment for risk level
    assessment = session.get_assessment(plan.assessment_id)
    risk_level = assessment.risk_level if assessment else RiskLevel.HIGH

    # Abort the plan
    result = plan_controller.abort_plan(plan_id, reason or None)

    if not result:
        return {"error": f"Failed to abort plan: {plan_id}"}

    # Log the abort
    audit.log(
        action="abort_plan",
        operation=plan.name,
        risk_level=risk_level,
        details={
            "reason": reason,
            "completed_steps": result["completed_steps"],
            "skipped_steps": result["skipped_steps"],
        },
        plan_id=plan_id,
    )

    response: dict[str, Any] = {
        "aborted": True,
        "plan_id": plan_id,
        "plan_name": plan.name,
        "reason": reason or "No reason provided",
        "completed_steps": result["completed_steps"],
        "skipped_steps": result["skipped_steps"],
    }

    # Include rollback suggestions
    if result["rollback_suggestions"]:
        response["rollback_suggestions"] = result["rollback_suggestions"]
        response["rollback_instructions"] = (
            "To rollback, execute these actions in the order shown "
            "(reverse of original execution order):"
        )

        # Create a simple rollback guide
        rollback_steps = []
        for i, suggestion in enumerate(result["rollback_suggestions"], 1):
            rollback_steps.append(
                f"{i}. Undo '{suggestion['step_description']}': {suggestion['rollback_action']}"
            )
        response["rollback_guide"] = rollback_steps
    else:
        response["rollback_suggestions"] = []
        response["rollback_instructions"] = (
            "No rollback actions available. Either no steps were completed "
            "or completed steps did not have rollback actions defined."
        )

    return response
