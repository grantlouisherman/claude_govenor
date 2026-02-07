"""Governor assess tool - primary entry point for risk assessment"""

from typing import Any

from ..core import RiskAssessor
from ..state import RiskLevel
from ..state.session import get_session
from ..state.audit import get_audit_logger


async def governor_assess(
    operation: str,
    description: str = "",
    context: str = "",
) -> dict[str, Any]:
    """
    Assess the risk level of an operation before execution.

    This is the primary entry point for the Governor MCP. Call this tool
    before performing any operation to determine:
    - LOW RISK: Proceed without additional approval
    - MEDIUM RISK: Request user confirmation
    - HIGH RISK: Create a structured plan with step-by-step approval

    Args:
        operation: The operation to assess (command, action description, etc.)
        description: Human-readable description of what the operation does
        context: Additional context (file paths, URLs, targets, etc.)

    Returns:
        Assessment result including:
        - risk_level: "low", "medium", or "high"
        - risk_score: Numeric score
        - recommendations: List of suggested actions
        - assessment_id: ID for tracking
    """
    assessor = RiskAssessor()
    session = get_session()
    audit = get_audit_logger()

    # Perform assessment
    assessment = assessor.assess(operation, description, context)

    # Store in session
    session.store_assessment(assessment)

    # Log the assessment
    audit.log(
        action="assess",
        operation=operation,
        risk_level=assessment.risk_level,
        details={
            "description": description,
            "context": context,
            "risk_score": assessment.risk_score,
        },
        assessment_id=assessment.id,
    )

    # Build response based on risk level
    response = {
        "assessment_id": assessment.id,
        "operation": operation,
        "risk_level": assessment.risk_level.value,
        "risk_score": assessment.risk_score,
        "factors": assessment.factors,
        "recommendations": assessment.recommendations,
    }

    # Add next steps guidance
    if assessment.risk_level == RiskLevel.LOW:
        response["next_steps"] = "Operation can proceed without additional approval."
        response["requires_approval"] = False
        response["requires_plan"] = False
    elif assessment.risk_level == RiskLevel.MEDIUM:
        response["next_steps"] = (
            "User confirmation required. Use governor_approve with "
            f"target_type='assessment' and target_id='{assessment.id}' to record approval."
        )
        response["requires_approval"] = True
        response["requires_plan"] = False
    else:  # HIGH
        response["next_steps"] = (
            "Create a structured execution plan. Use governor_create_plan with "
            f"assessment_id='{assessment.id}' to create a plan with detailed steps."
        )
        response["requires_approval"] = True
        response["requires_plan"] = True

    return response
