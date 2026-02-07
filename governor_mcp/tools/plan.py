"""Governor plan tool - create structured execution plans"""

from typing import Any

from ..core import PlanController
from ..state import RiskLevel
from ..state.session import get_session
from ..state.audit import get_audit_logger


async def governor_create_plan(
    assessment_id: str,
    name: str,
    description: str,
    steps: list[dict[str, str]],
    auto_submit: bool = True,
) -> dict[str, Any]:
    """
    Create a structured execution plan for a high-risk operation.

    High-risk operations require a plan with discrete steps that can be
    individually approved and executed. Each step should include a
    rollback action for recovery if needed.

    Args:
        assessment_id: ID of the risk assessment that triggered plan creation
        name: Short name for the plan
        description: Detailed description of what the plan accomplishes
        steps: List of step definitions, each containing:
            - description: What the step does
            - operation: The actual command/operation
            - expected_outcome: What should happen on success
            - rollback_action: How to undo this step (optional but recommended)
        auto_submit: Automatically submit for approval (default True)

    Returns:
        Plan details including:
        - plan_id: ID of the created plan
        - status: Current plan status
        - steps: List of step IDs and descriptions
        - next_steps: Guidance on what to do next

    Example:
        governor_create_plan(
            assessment_id="abc123",
            name="Database Cleanup",
            description="Remove stale records from user_sessions table",
            steps=[
                {
                    "description": "Create backup of user_sessions table",
                    "operation": "pg_dump -t user_sessions > backup.sql",
                    "expected_outcome": "Backup file created",
                    "rollback_action": "rm backup.sql"
                },
                {
                    "description": "Delete stale sessions older than 30 days",
                    "operation": "DELETE FROM user_sessions WHERE created_at < NOW() - INTERVAL '30 days'",
                    "expected_outcome": "Stale records removed",
                    "rollback_action": "psql < backup.sql"
                }
            ]
        )
    """
    session = get_session()
    audit = get_audit_logger()
    plan_controller = PlanController()

    # Get the assessment
    assessment = session.get_assessment(assessment_id)
    if not assessment:
        return {"error": f"Assessment not found: {assessment_id}"}

    # Validate steps
    if not steps:
        return {"error": "At least one step is required"}

    validated_steps = []
    for i, step in enumerate(steps):
        if not step.get("description"):
            return {"error": f"Step {i + 1} missing 'description'"}
        if not step.get("operation"):
            return {"error": f"Step {i + 1} missing 'operation'"}

        validated_steps.append({
            "description": step["description"],
            "operation": step["operation"],
            "expected_outcome": step.get("expected_outcome", "Step completed successfully"),
            "rollback_action": step.get("rollback_action"),
        })

    # Create the plan
    plan = plan_controller.create_plan(
        name=name,
        description=description,
        assessment=assessment,
        steps=validated_steps,
    )

    # Log plan creation
    audit.log(
        action="create_plan",
        operation=name,
        risk_level=assessment.risk_level,
        details={
            "description": description,
            "steps_count": len(steps),
        },
        assessment_id=assessment_id,
        plan_id=plan.id,
    )

    # Auto-submit if requested
    if auto_submit:
        plan_controller.submit_for_approval(plan.id)
        audit.log(
            action="submit_plan",
            operation=name,
            risk_level=assessment.risk_level,
            plan_id=plan.id,
        )

    # Build response
    response = {
        "plan_id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "status": plan.status.value,
        "assessment_id": assessment_id,
        "steps": [
            {
                "step_id": step.id,
                "order": step.order,
                "description": step.description,
                "has_rollback": step.rollback_action is not None,
            }
            for step in plan.steps
        ],
    }

    if auto_submit:
        response["next_steps"] = (
            f"Plan submitted for approval. Use governor_approve with "
            f"target_type='plan' and target_id='{plan.id}' to approve or deny."
        )
    else:
        response["next_steps"] = (
            f"Plan created in draft. Call governor_create_plan with "
            f"auto_submit=True or manually submit for approval."
        )

    return response
