"""Governor history tool - retrieve audit trail"""

from datetime import datetime
from typing import Any

from ..state import RiskLevel
from ..state.audit import get_audit_logger


async def governor_get_history(
    limit: int = 20,
    offset: int = 0,
    risk_level: str = "",
    action: str = "",
    plan_id: str = "",
    assessment_id: str = "",
    success_only: bool = False,
    failures_only: bool = False,
    include_stats: bool = False,
) -> dict[str, Any]:
    """
    Retrieve the audit trail of governor actions.

    Use this tool to review past operations, investigate issues,
    or generate compliance reports.

    Args:
        limit: Maximum number of entries to return (default 20)
        offset: Number of entries to skip (for pagination)
        risk_level: Filter by risk level - "low", "medium", or "high"
        action: Filter by action type (e.g., "assess", "approve", "execute_step")
        plan_id: Filter by plan ID
        assessment_id: Filter by assessment ID
        success_only: Only show successful actions
        failures_only: Only show failed actions
        include_stats: Include audit statistics

    Returns:
        Audit history including:
        - entries: List of audit entries
        - total: Total number of matching entries
        - stats: Audit statistics (if include_stats is True)
    """
    audit = get_audit_logger()

    # Parse risk level filter
    level_filter = None
    if risk_level:
        try:
            level_filter = RiskLevel(risk_level.lower())
        except ValueError:
            pass

    # Get filtered entries
    entries = audit.get_entries(
        limit=limit,
        offset=offset,
        risk_level=level_filter,
        action=action or None,
        plan_id=plan_id or None,
        assessment_id=assessment_id or None,
        success_only=success_only,
        failures_only=failures_only,
    )

    # Get total count (without pagination)
    all_entries = audit.get_entries(
        risk_level=level_filter,
        action=action or None,
        plan_id=plan_id or None,
        assessment_id=assessment_id or None,
        success_only=success_only,
        failures_only=failures_only,
    )

    response: dict[str, Any] = {
        "entries": [entry.to_dict() for entry in entries],
        "returned": len(entries),
        "total": len(all_entries),
        "offset": offset,
        "limit": limit,
    }

    # Add filter info
    active_filters = []
    if risk_level:
        active_filters.append(f"risk_level={risk_level}")
    if action:
        active_filters.append(f"action={action}")
    if plan_id:
        active_filters.append(f"plan_id={plan_id}")
    if assessment_id:
        active_filters.append(f"assessment_id={assessment_id}")
    if success_only:
        active_filters.append("success_only=true")
    if failures_only:
        active_filters.append("failures_only=true")

    if active_filters:
        response["filters"] = active_filters

    # Include stats if requested
    if include_stats:
        stats = audit.get_stats()
        response["stats"] = stats

    # Add pagination info
    has_more = (offset + len(entries)) < len(all_entries)
    response["has_more"] = has_more
    if has_more:
        response["next_offset"] = offset + limit

    return response
