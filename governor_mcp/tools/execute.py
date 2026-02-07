"""Governor execute tool - execute approved plan steps with deviation detection"""

from typing import Any

from ..core import PlanController, DeviationDetector
from ..state import StepStatus, PlanStatus, RiskLevel
from ..state.session import get_session
from ..state.audit import get_audit_logger


async def governor_execute_step(
    plan_id: str,
    step_id: str,
    actual_operation: str = "",
    actual_outcome: str = "",
    skip: bool = False,
) -> dict[str, Any]:
    """
    Execute an approved step with deviation detection.

    Call this tool to record step execution and check for deviations
    from the planned operation. The tool will:
    1. Verify the step is approved
    2. Mark the step as executing
    3. Compare actual vs planned operation/outcome
    4. Detect and report any deviations
    5. Mark step as completed or failed

    Args:
        plan_id: ID of the plan containing the step
        step_id: ID of the step to execute
        actual_operation: The operation that was actually executed
        actual_outcome: The actual result/outcome of execution
        skip: Set to True to skip this step (marks as skipped)

    Returns:
        Execution result including:
        - step: Updated step information
        - deviation_report: Analysis of any deviations
        - next_step: Information about the next step (if any)
        - plan_status: Current status of the plan
    """
    session = get_session()
    audit = get_audit_logger()
    plan_controller = PlanController()
    deviation_detector = DeviationDetector()

    # Get the plan
    plan = session.get_plan(plan_id)
    if not plan:
        return {"error": f"Plan not found: {plan_id}"}

    # Find the step
    step = None
    step_index = -1
    for i, s in enumerate(plan.steps):
        if s.id == step_id:
            step = s
            step_index = i
            break

    if not step:
        return {"error": f"Step not found: {step_id}"}

    # Get assessment for risk level
    assessment = session.get_assessment(plan.assessment_id)
    risk_level = assessment.risk_level if assessment else RiskLevel.HIGH

    # Handle skip
    if skip:
        session.update_step_status(plan_id, step_id, StepStatus.SKIPPED)
        audit.log(
            action="skip_step",
            operation=step.operation,
            risk_level=risk_level,
            details={"step_description": step.description},
            plan_id=plan_id,
            step_id=step_id,
        )

        # Get next step
        next_step = None
        if step_index + 1 < len(plan.steps):
            next_step = plan.steps[step_index + 1]

        return {
            "step": {
                "step_id": step_id,
                "status": "skipped",
                "description": step.description,
            },
            "skipped": True,
            "next_step": {
                "step_id": next_step.id,
                "description": next_step.description,
                "status": next_step.status.value,
            } if next_step else None,
            "plan_status": plan.status.value,
        }

    # Check step status
    if step.status not in (StepStatus.APPROVED, StepStatus.PENDING):
        return {
            "error": f"Step cannot be executed. Current status: {step.status.value}",
            "step": step.to_dict(),
        }

    # Mark as executing
    plan_controller.start_step_execution(plan_id, step_id)

    # Perform deviation detection
    deviation_report = deviation_detector.detect(
        step=step,
        actual_operation=actual_operation or step.operation,
        actual_outcome=actual_outcome or "",
    )

    # Log the execution
    audit.log(
        action="execute_step",
        operation=step.operation,
        risk_level=risk_level,
        details={
            "step_description": step.description,
            "actual_operation": actual_operation,
            "actual_outcome": actual_outcome,
            "deviation_detected": deviation_report.has_deviation,
            "deviation_severity": deviation_report.severity,
        },
        plan_id=plan_id,
        step_id=step_id,
    )

    # Determine if we should mark as completed or failed
    if deviation_report.severity == "critical":
        # Critical deviation - mark as failed
        plan_controller.fail_step(plan_id, step_id, "Critical deviation detected")
        step_status = "failed"
        success = False
    else:
        # Complete the step
        plan_controller.complete_step(plan_id, step_id, actual_outcome or "Completed")
        step_status = "completed"
        success = True

    # Refresh plan status
    plan = session.get_plan(plan_id)

    # Get next step
    next_step = None
    if success and step_index + 1 < len(plan.steps):
        next_step = plan.steps[step_index + 1]

    # Build response
    response: dict[str, Any] = {
        "step": {
            "step_id": step_id,
            "order": step.order,
            "description": step.description,
            "status": step_status,
            "planned_operation": step.operation,
            "actual_operation": actual_operation or step.operation,
            "expected_outcome": step.expected_outcome,
            "actual_outcome": actual_outcome,
        },
        "success": success,
        "deviation_report": deviation_report.to_dict(),
        "plan_status": plan.status.value,
    }

    if next_step:
        response["next_step"] = {
            "step_id": next_step.id,
            "order": next_step.order,
            "description": next_step.description,
            "operation": next_step.operation,
            "status": next_step.status.value,
        }
        response["next_steps"] = (
            f"Proceed to next step: {next_step.description}. "
            f"Use governor_execute_step with step_id='{next_step.id}'."
        )
    else:
        if plan.status == PlanStatus.COMPLETED:
            response["next_steps"] = "Plan completed successfully. All steps executed."
        elif plan.status == PlanStatus.FAILED:
            response["next_steps"] = (
                "Plan failed due to critical deviation. "
                f"Use governor_abort with plan_id='{plan_id}' for rollback suggestions."
            )
        else:
            response["next_steps"] = "No more steps in plan."

    return response
