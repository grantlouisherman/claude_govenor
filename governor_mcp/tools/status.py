"""Governor status tool - query plan and session status"""

from typing import Any

from ..state.session import get_session


async def governor_check_status(
    plan_id: str = "",
    assessment_id: str = "",
    include_session_summary: bool = False,
) -> dict[str, Any]:
    """
    Query the status of a plan, assessment, or the entire session.

    Use this tool to:
    - Check the current status of a specific plan
    - Review an assessment
    - Get an overview of the current session

    Args:
        plan_id: ID of a specific plan to check (optional)
        assessment_id: ID of a specific assessment to check (optional)
        include_session_summary: Include overview of all session state

    Returns:
        Status information for the requested item(s):
        - plan: Plan details if plan_id provided
        - assessment: Assessment details if assessment_id provided
        - session: Session overview if include_session_summary is True
    """
    session = get_session()
    response: dict[str, Any] = {}

    # Check specific plan
    if plan_id:
        plan = session.get_plan(plan_id)
        if plan:
            # Get step summary
            step_counts = {}
            for step in plan.steps:
                status = step.status.value
                step_counts[status] = step_counts.get(status, 0) + 1

            # Find current step
            current_step = plan.get_current_step()

            response["plan"] = {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "status": plan.status.value,
                "assessment_id": plan.assessment_id,
                "total_steps": len(plan.steps),
                "step_counts": step_counts,
                "current_step": {
                    "id": current_step.id,
                    "order": current_step.order,
                    "description": current_step.description,
                    "status": current_step.status.value,
                } if current_step else None,
                "steps": [
                    {
                        "id": s.id,
                        "order": s.order,
                        "description": s.description,
                        "status": s.status.value,
                    }
                    for s in plan.steps
                ],
                "created_at": plan.created_at.isoformat(),
                "updated_at": plan.updated_at.isoformat(),
            }

            # Check if plan has approval
            approvals = session.get_approvals_for_target("plan", plan_id)
            if approvals:
                latest = max(approvals, key=lambda a: a.timestamp)
                response["plan"]["approval"] = {
                    "approved": latest.approved,
                    "reason": latest.reason,
                    "timestamp": latest.timestamp.isoformat(),
                }
        else:
            response["plan"] = {"error": f"Plan not found: {plan_id}"}

    # Check specific assessment
    if assessment_id:
        assessment = session.get_assessment(assessment_id)
        if assessment:
            response["assessment"] = {
                "id": assessment.id,
                "operation": assessment.operation,
                "description": assessment.description,
                "risk_level": assessment.risk_level.value,
                "risk_score": assessment.risk_score,
                "resource_type": assessment.resource_type,
                "action_type": assessment.action_type,
                "scope": assessment.scope,
                "factors": assessment.factors,
                "recommendations": assessment.recommendations,
                "timestamp": assessment.timestamp.isoformat(),
            }

            # Check if assessment has approval
            approvals = session.get_approvals_for_target("assessment", assessment_id)
            if approvals:
                latest = max(approvals, key=lambda a: a.timestamp)
                response["assessment"]["approval"] = {
                    "approved": latest.approved,
                    "reason": latest.reason,
                    "timestamp": latest.timestamp.isoformat(),
                }
        else:
            response["assessment"] = {"error": f"Assessment not found: {assessment_id}"}

    # Include session summary
    if include_session_summary:
        summary = session.get_session_summary()

        # Get active plans
        active_plans = session.get_active_plans()
        active_plan_info = [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status.value,
            }
            for p in active_plans
        ]

        # Get recent assessments
        assessments = session.list_assessments()
        recent_assessments = sorted(
            assessments,
            key=lambda a: a.timestamp,
            reverse=True
        )[:5]

        response["session"] = {
            "session_id": summary["session_id"],
            "counts": {
                "assessments": summary["assessments_count"],
                "plans": summary["plans_count"],
                "active_plans": summary["active_plans_count"],
                "approvals": summary["approvals_count"],
            },
            "active_plans": active_plan_info,
            "recent_assessments": [
                {
                    "id": a.id,
                    "operation": a.operation[:50] + "..." if len(a.operation) > 50 else a.operation,
                    "risk_level": a.risk_level.value,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in recent_assessments
            ],
        }

    # If nothing specific was requested, show session summary
    if not plan_id and not assessment_id and not include_session_summary:
        response["message"] = (
            "No specific item requested. Use plan_id, assessment_id, "
            "or include_session_summary=True to get status information."
        )
        response["session"] = session.get_session_summary()

    return response
